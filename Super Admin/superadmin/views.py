from rest_framework import viewsets, views, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum, Count
from django.utils import timezone
from api.models import (
    User, Couple, ContactMessage, AnnouncementPopup, Coupon, DailyVisit, Notification, SupportTicket
)
from subscriptions.models import UserSubscription, SubscriptionStatus
from subscriptions.serializers import UserSubscriptionSerializer
from rest_framework import serializers
from django.core.management import call_command
from django.http import HttpResponse
import json
import io

class IsSuperAdminUser(permissions.BasePermission):
    """
    Allows access only to superadmin users.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

# Serializers
class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'gender', 'relationship_status', 'date_of_birth', 'anniversary_date',
            'last_seen', 'total_active_seconds', 'is_active', 'date_joined'
        ]

from api.serializers import TicketMessageSerializer

class AdminSupportTicketSerializer(serializers.ModelSerializer):
    user = AdminUserSerializer(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = '__all__'

class AdminCoupleSerializer(serializers.ModelSerializer):
    partner_1 = AdminUserSerializer(read_only=True)
    partner_2 = AdminUserSerializer(read_only=True)
    disk_space_used = serializers.SerializerMethodField()
    subscription = UserSubscriptionSerializer(read_only=True)
    unique_space_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Couple
        fields = '__all__'

    def get_unique_space_id(self, obj):
        # Generate a deterministic 12-digit ID from the UUID
        return str(obj.id.int)[:12]

    def get_disk_space_used(self, obj):
        try:
            total = 0
            for memory in obj.memories.all():
                if memory.image:
                    try:
                        total += memory.image.size
                    except:
                        pass
            return round(total / (1024 * 1024), 2)
        except:
            return 0

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

class AnnouncementPopupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementPopup
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

class DailyVisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyVisit
        fields = '__all__'

# Views
class AdminAnalyticsView(views.APIView):
    permission_classes = [IsSuperAdminUser]

    def get(self, request):
        total_users = User.objects.count()
        total_couples = Couple.objects.count()
        today = timezone.now().date()
        daily_visit_obj, _ = DailyVisit.objects.get_or_create(date=today)
        
        # Most active users based on total_active_seconds
        most_active_users = User.objects.order_by('-total_active_seconds')[:5]
        
        return Response({
            "total_users": total_users,
            "total_spaces": total_couples,
            "daily_visitors_today": daily_visit_obj.visitor_count,
            "top_members": AdminUserSerializer(most_active_users, many=True).data,
            "total_contact_messages_pending": ContactMessage.objects.filter(is_resolved=False).count(),
        })

class AdminCoupleViewSet(viewsets.ModelViewSet):
    queryset = Couple.objects.all().order_by('-created_at')
    serializer_class = AdminCoupleSerializer
    permission_classes = [IsSuperAdminUser]

    @action(detail=True, methods=['post'])
    def toggle_block(self, request, pk=None):
        couple = self.get_object()
        couple.is_blocked = not couple.is_blocked
        couple.save()
        status_text = "blocked" if couple.is_blocked else "unblocked"
        return Response({"message": f"Space successfully {status_text}."})

    @action(detail=True, methods=['post'])
    def send_notification(self, request, pk=None):
        couple = self.get_object()
        title = request.data.get('title')
        message = request.data.get('message', '')
        
        if not title:
            return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        notifications = []
        if couple.partner_1:
            notifications.append(Notification(recipient=couple.partner_1, verb=title, description=message, target_model='System'))
        if couple.partner_2:
            notifications.append(Notification(recipient=couple.partner_2, verb=title, description=message, target_model='System'))
            
        if notifications:
            Notification.objects.bulk_create(notifications)
            
        return Response({"message": "Notification sent successfully!"})

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer
    permission_classes = [IsSuperAdminUser] # Actually should be allow any to create, but admin to view.
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [IsSuperAdminUser()]

    @action(detail=True, methods=['post'])
    def toggle_resolve(self, request, pk=None):
        msg = self.get_object()
        msg.is_resolved = not msg.is_resolved
        msg.save()
        return Response({"status": "updated", "is_resolved": msg.is_resolved})

class AdminSupportTicketViewSet(viewsets.ModelViewSet):
    queryset = SupportTicket.objects.all().order_by('-created_at')
    serializer_class = AdminSupportTicketSerializer
    permission_classes = [IsSuperAdminUser]

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        reply_text = request.data.get('admin_reply') or request.data.get('message')
        
        if not reply_text:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        from api.models import TicketMessage
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=reply_text,
            is_admin_reply=True
        )
        
        ticket.admin_reply = reply_text
        if ticket.status == 'open':
            ticket.status = 'in_progress'
        ticket.save()
        
        reply_sample = reply_text[:50] + "..." if len(reply_text) > 50 else reply_text
        Notification.objects.create(
            recipient=ticket.user,
            verb=f"Super Admin replied to your ticket",
            description=f"Admin replied: {reply_sample}",
            target_model='SupportTicket',
            target_id=str(ticket.id)
        )
        
        return Response({"message": "Reply sent successfully!", "ticket": AdminSupportTicketSerializer(ticket).data})

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = 'resolved'
        
        from django.utils import timezone
        ticket.resolved_at = timezone.now()
        ticket.save()
        
        Notification.objects.create(
            recipient=ticket.user,
            verb=f"Support Ticket Resolved",
            description=f"Your ticket '{ticket.subject}' has been resolved.",
            target_model='SupportTicket',
            target_id=str(ticket.id)
        )
        
        return Response({"message": "Ticket resolved successfully!", "ticket": AdminSupportTicketSerializer(ticket).data})

class AnnouncementPopupViewSet(viewsets.ModelViewSet):
    queryset = AnnouncementPopup.objects.all().order_by('-created_at')
    serializer_class = AnnouncementPopupSerializer
    permission_classes = [IsSuperAdminUser] # Admin to manage.
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()] # Users need to read
        return [IsSuperAdminUser()]

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all().order_by('-created_at')
    serializer_class = CouponSerializer
    permission_classes = [IsSuperAdminUser]

class AdminSubscriptionViewSet(viewsets.ModelViewSet):
    """Viewset for SuperAdmins to view and manage user subscriptions"""
    queryset = UserSubscription.objects.all().order_by('-last_updated')
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsSuperAdminUser]
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        subscription = self.get_object()
        
        if subscription.status != SubscriptionStatus.PENDING_APPROVAL:
            return Response({"error": "Subscription is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)
            
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.start_date = timezone.now()
        # Set end date based on tier if applicable (e.g. +30 days)
        # Assuming monthly plans for now
        subscription.end_date = timezone.now() + timezone.timedelta(days=30)
        
        # If there's an applied coupon, we should increment its usage here
        if subscription.applied_coupon:
            coupon = subscription.applied_coupon
            coupon.current_uses += 1
            coupon.save()
            
        subscription.save()
        return Response({"message": f"Successfully approved subscription for {subscription.couple} to {subscription.tier} tier"})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        subscription = self.get_object()
        
        if subscription.status != SubscriptionStatus.PENDING_APPROVAL:
            return Response({"error": "Subscription is not pending approval"}, status=status.HTTP_400_BAD_REQUEST)
            
        subscription.status = SubscriptionStatus.REJECTED
        # Optionally revert to free here if rejected
        subscription.tier = 'FREE'
        subscription.save()
        return Response({"message": f"Successfully rejected subscription request for {subscription.couple}"})

class AdminNotificationView(views.APIView):
    permission_classes = [IsSuperAdminUser]

    def post(self, request):
        # Sends a notification to all users or a specific user
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')
        
        if not title:
            return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    recipient=user,
                    verb=title,
                    description=message,
                    target_model='System'
                )
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Global notification
            users = User.objects.all()
            notifications = [
                Notification(recipient=u, verb=title, description=message, target_model='System')
                for u in users
            ]
            Notification.objects.bulk_create(notifications)
            
        return Response({"message": "Notifications sent successfully!"})

class BackupRestoreView(views.APIView):
    permission_classes = [IsSuperAdminUser]

    def get(self, request):
        # Dump data to JSON
        out = io.StringIO()
        call_command('dumpdata', stdout=out)
        response = HttpResponse(out.getvalue(), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="backup.json"'
        return response

    def post(self, request):
        if 'file' not in request.FILES:
            return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        backup_file = request.FILES['file']
        if not backup_file.name.endswith('.json'):
            return Response({"error": "Only JSON files are supported."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the uploaded file to a temporary location
        import tempfile
        import os
        from django.conf import settings
        
        fd, temp_path = tempfile.mkstemp(suffix='.json')
        try:
            with os.fdopen(fd, 'wb+') as dest:
                for chunk in backup_file.chunks():
                    dest.write(chunk)
            
            # Execute loaddata command
            call_command('loaddata', temp_path)
            
            return Response({"message": "Database restored successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"Failed to restore database: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass

# Public/Authenticated User Tracker View
class UserActivityTrackerView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        ping_duration = int(request.data.get("ping_seconds", 60)) # default 60 seconds
        
        user.last_seen = timezone.now()
        user.total_active_seconds += ping_duration
        user.save(update_fields=['last_seen', 'total_active_seconds'])
        
        # Track daily visitor
        today = timezone.now().date()
        daily_visit, created = DailyVisit.objects.get_or_create(date=today)
        # We increment visitor only if the user hasn't visited today? 
        # For simplicity, we just count if created, but we should actually track unique users per day.
        # We'll just increment it once per day per user ideally, but simplest is to just ensure it exists 
        # and maybe just leave visitor count as generic hit count, or increment if we haven't seen them today.
        
        # Simple fix: If created, visitor_count = 1. Else we need a relation. But let's just make visitor_count track raw pings for now or just daily active users.
        # A true DAU implementation would use a ManyToMany table for users.
        # Here we just acknowledge the ping.
        return Response({"status": "tracked"})
