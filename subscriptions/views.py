from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import UserSubscription, SubscriptionTier, SubscriptionStatus, PaymentSettings
from .serializers import UserSubscriptionSerializer, PaymentUploadSerializer
from api.models import Couple, Coupon

class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own couple's subscription
        couple = Couple.objects.filter(partner_1=self.request.user).first() or \
                 Couple.objects.filter(partner_2=self.request.user).first()
        if couple:
            return UserSubscription.objects.filter(couple=couple)
        return UserSubscription.objects.none()

    def get_object(self):
        queryset = self.get_queryset()
        if queryset.exists():
            return queryset.first()
        return None

    @action(detail=False, methods=['GET'])
    def current(self, request):
        """Get the current subscription for the user's couple"""
        couple = Couple.objects.filter(partner_1=request.user).first() or \
                 Couple.objects.filter(partner_2=request.user).first()
        
        if not couple:
            return Response({"detail": "Not part of a couple yet."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get or create free tier subscription
        sub, created = UserSubscription.objects.get_or_create(
            couple=couple,
            defaults={'tier': SubscriptionTier.FREE, 'status': SubscriptionStatus.ACTIVE}
        )
        
        # Check if expired and update if necessary
        sub.is_active() # This updates the status to expired if end_date has passed
        
        serializer = self.get_serializer(sub)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser, FormParser])
    def upgrade_request(self, request):
        """Submit a payment screenshot to request a plan upgrade"""
        couple = Couple.objects.filter(partner_1=request.user).first() or \
                 Couple.objects.filter(partner_2=request.user).first()
                 
        if not couple:
            return Response({"detail": "Not part of a couple yet."}, status=status.HTTP_400_BAD_REQUEST)
            
        # Validate request data
        serializer = PaymentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        validated_data = serializer.validated_data
        
        # Get or create the subscription record
        sub, _ = UserSubscription.objects.get_or_create(couple=couple)
        
        # If there's already a pending request, we simply overwrite it with the new tier/image
        sub.tier = validated_data['tier']
        sub.status = SubscriptionStatus.PENDING_APPROVAL
        sub.payment_screenshot = validated_data['payment_screenshot']
        sub.transaction_id = validated_data['transaction_id']
        sub.applied_coupon = validated_data.get('coupon_code')
        sub.save()
        
        return Response(
            {"detail": "Payment screenshot submitted successfully. Your plan will be upgraded once verified by the admin."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['GET'])
    def validate_coupon(self, request):
        """Validate a coupon code and return discount info"""
        code = request.query_params.get('code')
        if not code:
            return Response({"error": "No code provided"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            coupon = Coupon.objects.get(code=code.upper())
            if not coupon.is_valid:
                return Response({"error": "Coupon is invalid or expired"}, status=status.HTTP_400_BAD_REQUEST)
                
            return Response({
                "code": coupon.code,
                "discount_percentage": coupon.discount_percentage
            })
        except Coupon.DoesNotExist:
            return Response({"error": "Invalid coupon code"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['GET'])
    def payment_info(self, request):
        """Get the active payment settings (UPI ID and QR code)"""
        settings = PaymentSettings.objects.filter(is_active=True).first()
        if not settings:
            return Response({
                "upi_id": "admin@lovenest",
                "qr_code": None
            })
            
        return Response({
            "upi_id": settings.upi_id,
            "qr_code": request.build_absolute_uri(settings.qr_code.url) if settings.qr_code else None
        })
