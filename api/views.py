from rest_framework import viewsets, status, generics, permissions, parsers
from rest_framework.response import Response
from django.http import HttpResponse, Http404
from dateutil.relativedelta import relativedelta
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.utils.crypto import get_random_string
from django.utils import timezone
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from .models import (
    User, Couple, Memory, ImportantDate, Rule, BucketItem, LoveNote,
    LoveLanguage, LoveLanguageAction, GratitudeEntry, DateIdea, Question, Answer, Todo, Notification,
    AnnouncementPopup, ContactMessage, SupportTicket, TicketMessage, VerificationCode, SiteSetting
)
from .mailer import InternalMailer
from django.conf import settings
from .media_handlers import decrypt_image
from .serializers import (
    UserSerializer, RegisterSerializer, CoupleSerializer,
    MemorySerializer, ImportantDateSerializer, RuleSerializer, DashboardSerializer,
    BucketItemSerializer, LoveNoteSerializer,
    LoveLanguageSerializer, LoveLanguageActionSerializer,
    GratitudeEntrySerializer, DateIdeaSerializer, QuestionSerializer, AnswerSerializer,
    TodoSerializer, NotificationSerializer, AnnouncementPopupSerializer,
    ContactMessageCreateSerializer, SupportTicketSerializer
)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    return Response({
        'status': 'ok',
        'message': 'LoveNest API is running smoothly!',
        'timestamp': timezone.now()
    }, status=status.HTTP_200_OK)


class ContactMessageCreateView(generics.CreateAPIView):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageCreateSerializer
    permission_classes = [permissions.AllowAny]


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        invite_code = request.data.get('invite_code')
        google_id_token = request.data.get('google_id_token')
        google_access_token = request.data.get('google_access_token')
        
        # Verify Google Token if present
        is_google_signup = False
        idinfo = None
        if google_id_token:
            try:
                client_id = os.environ.get('GOOGLE_CLIENT_ID', 'not_set')
                idinfo = id_token.verify_oauth2_token(google_id_token, google_requests.Request(), client_id)
            except ValueError:
                return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        elif google_access_token:
            import requests as regular_requests
            resp = regular_requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={'Authorization': f'Bearer {google_access_token}'})
            if resp.status_code == 200:
                idinfo = resp.json()
            else:
                return Response({'error': 'Invalid Google access token.'}, status=status.HTTP_400_BAD_REQUEST)

        if idinfo:
            if idinfo.get('email') != request.data.get('email'):
                return Response({'error': 'Email mismatch with Google authentication.'}, status=status.HTTP_400_BAD_REQUEST)
            is_google_signup = True
            
            # Extract profile picture URL from Google if present and not provided by user
            if 'picture' in idinfo:
                request.data['profile_image_url'] = idinfo['picture']

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            if is_google_signup:
                user.email_verified = True
                profile_url = request.data.get('profile_image_url')
                if profile_url and not user.profile_image:
                    import requests as req
                    from django.core.files.base import ContentFile
                    try:
                        img_resp = req.get(profile_url)
                        if img_resp.status_code == 200:
                            user.profile_image.save(f"google_prof_{user.id}.jpg", ContentFile(img_resp.content), save=False)
                    except Exception:
                        pass
                user.save()

            token, _ = Token.objects.get_or_create(user=user)
            
            # Handle Invitation Code Join
            if invite_code:
                try:
                    code = invite_code.strip().upper()
                    couple = Couple.objects.get(invite_code=code)
                    if not couple.partner_2:
                        couple.partner_2 = user
                        couple.save()
                        # Notify P1
                        dashboard_url = f"{settings.CORS_ALLOWED_ORIGINS[0]}/dashboard" if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS else "http://localhost:3000/dashboard"
                        InternalMailer.send_partner_joined(couple.partner_1, user.first_name or user.username, dashboard_url)
                except Couple.DoesNotExist:
                    pass # Silently fail? Or maybe we should return a message? Let's just pass for now to not break reg.

            # Generate and send verification code
            requires_verification = not is_google_signup
            if requires_verification:
                code = get_random_string(6, allowed_chars='0123456789')
                VerificationCode.objects.create(
                    user=user,
                    code=code,
                    purpose='register',
                    expires_at=timezone.now() + timezone.timedelta(minutes=15)
                )
                InternalMailer.send_verification_code(user, code)
            
            return Response({'token': token.key, 'user': UserSerializer(user).data, 'requires_verification': requires_verification}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def verify_email(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'error': 'Verification code is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if request.user.email_verified:
            return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)
            
        verification = VerificationCode.objects.filter(
            user=request.user, 
            code=code, 
            purpose='register',
            is_verified=False
        ).first()
        
        if not verification or not verification.is_valid:
            return Response({'error': 'Invalid or expired verification code.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Mark as verified
        verification.is_verified = True
        verification.save()
        
        request.user.email_verified = True
        request.user.save()
        
        return Response({
            'message': 'Email verified successfully!', 
            'user': UserSerializer(request.user).data
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def resend_verification_code(self, request):
        email = request.data.get('email')
        if not email:
            if request.user.is_authenticated:
                email = request.user.email
            else:
                return Response({'error': 'Email field is required.'}, status=status.HTTP_400_BAD_REQUEST)
                
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'No account found with this email address.'}, status=status.HTTP_404_NOT_FOUND)
            
        if user.email_verified:
            return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)
            
        # Rate Limiting: 60 seconds
        last_code = VerificationCode.objects.filter(
            user=user,
            purpose='register',
            created_at__gt=timezone.now() - timezone.timedelta(seconds=60)
        ).first()
        
        if last_code:
            return Response({
                'error': 'Please wait 60 seconds before requesting another code.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
        # Generate and send
        code = get_random_string(6, allowed_chars='0123456789')
        VerificationCode.objects.create(
            user=user,
            code=code,
            purpose='register',
            expires_at=timezone.now() + timezone.timedelta(minutes=15)
        )
        InternalMailer.send_verification_code(user, code)
        
        return Response({'message': f'A new verification code has been sent to {email}.'})

    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email=email).first()
        if not user:
            # Professional existence check as requested by USER
            return Response({
                'error': 'No account found with this email address. Please check and try again.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Industrial Ready: Rate Limiting
        # Check if a valid, unexpired code was sent in the last 60 seconds
        last_code = VerificationCode.objects.filter(
            user=user, 
            purpose='forgot_password',
            created_at__gt=timezone.now() - timezone.timedelta(seconds=60)
        ).first()
        
        if last_code:
            return Response({
                'error': 'A recovery code was recently sent. Please wait 60 seconds before requesting another.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # Generate new code
        code = get_random_string(6, allowed_chars='0123456789')
        VerificationCode.objects.create(
            user=user,
            code=code,
            purpose='forgot_password',
            expires_at=timezone.now() + timezone.timedelta(minutes=15)
        )
        
        # Send Email
        InternalMailer.send_password_reset_otp(user.email, code)
        
        return Response({
            'message': f'A 6-digit recovery code has been sent to {email}.',
            'email': email
        })

    @action(detail=False, methods=['post'])
    def reset_password_with_otp(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        
        if not all([email, code, new_password]):
            return Response({'error': 'Email, code, and new_password are required'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
            
        verification = VerificationCode.objects.filter(
            user=user, 
            code=code, 
            purpose='forgot_password',
            is_verified=False
        ).first()
        
        if not verification or not verification.is_valid:
            return Response({'error': 'Invalid or expired code'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Update password
        user.set_password(new_password)
        user.save()
        
        verification.is_verified = True
        verification.save()
        
        # Invalidate old tokens and issue a new one
        Token.objects.filter(user=user).delete()
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({'message': 'Password reset successful', 'token': token.key, 'user': UserSerializer(user).data})

    @action(detail=False, methods=['post'])
    def reset_password_with_partner(self, request):
        """Reset password by verifying partner's password"""
        username_or_email = request.data.get('username_or_email')
        partner_password = request.data.get('partner_password')
        new_password = request.data.get('new_password')
        
        if not all([username_or_email, partner_password, new_password]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Find the user trying to reset
        user = User.objects.filter(username=username_or_email).first() or \
               User.objects.filter(email=username_or_email).first()
               
        if not user:
            return Response({'error': 'Account not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Find partner
        couple = getattr(user, 'couple_as_p1', None) or getattr(user, 'couple_as_p2', None)
        if not couple:
            return Response({'error': 'You are not in a space with a partner'}, status=status.HTTP_400_BAD_REQUEST)
            
        partner = couple.get_other_user(user)
        if not partner:
            return Response({'error': 'Partner has not joined the space yet'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Authenticate partner's password
        is_partner_authenticated = authenticate(username=partner.username, password=partner_password)
        if not is_partner_authenticated:
            return Response({'error': 'Incorrect partner password'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Reset password
        user.set_password(new_password)
        user.save()
        
        # Invalidate old tokens and issue a new one
        Token.objects.filter(user=user).delete()
        token, _ = Token.objects.get_or_create(user=user)
        
        # Optionally notify partner that their password was used
        from .signals import create_notification
        create_notification(
            sender_user=user,
            couple=couple,
            verb="used your password to recover their account",
            target_model='User',
            target_id=user.id
        )
        
        return Response({'message': 'Password reset successful', 'token': token.key, 'user': UserSerializer(user).data})

    @action(detail=False, methods=['get', 'patch'], permission_classes=[permissions.IsAdminUser])
    def site_settings(self, request):
        settings_obj = SiteSetting.get_settings()
        
        if request.method == 'GET':
            return Response({
                'smtp_host': settings_obj.smtp_host,
                'smtp_port': settings_obj.smtp_port,
                'smtp_user': settings_obj.smtp_user,
                'use_tls': settings_obj.use_tls,
                # Intentionally omitting password from GET for security
            })
            
        # PATCH
        settings_obj.smtp_host = request.data.get('smtp_host', settings_obj.smtp_host)
        settings_obj.smtp_port = request.data.get('smtp_port', settings_obj.smtp_port)
        settings_obj.smtp_user = request.data.get('smtp_user', settings_obj.smtp_user)
        settings_obj.use_tls = request.data.get('use_tls', settings_obj.use_tls)
        
        if 'smtp_password' in request.data and request.data['smtp_password']:
            settings_obj.smtp_password = request.data['smtp_password']
            
        settings_obj.save()
        return Response({'message': 'Settings updated successfully'})

    @action(detail=False, methods=['get'])
    def check_username(self, request):
        username = request.query_params.get('username')
        if not username:
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(username__iexact=username).exists()
        return Response({'available': not exists})

    @action(detail=False, methods=['get'])
    def check_email(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email__iexact=email).exists()
        return Response({'available': not exists})

    @action(detail=False, methods=['post'])
    def login(self, request):
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        # Try authenticating by username first
        user = authenticate(username=username_or_email, password=password)
        
        # If that fails and it looks like an email, try authenticating by email
        if not user and username_or_email and '@' in username_or_email:
            # We look up the user by email, then use their true username to authenticate
            user_obj = User.objects.filter(email__iexact=username_or_email).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
                
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data})
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def google_login(self, request):
        google_id_token = request.data.get('google_id_token')
        google_access_token = request.data.get('google_access_token')
        
        if not google_id_token and not google_access_token:
            return Response({'error': 'Google token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        idinfo = None
        if google_id_token:
            try:
                client_id = os.environ.get('GOOGLE_CLIENT_ID', 'not_set')
                idinfo = id_token.verify_oauth2_token(google_id_token, google_requests.Request(), client_id)
            except ValueError:
                return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        elif google_access_token:
            import requests as regular_requests
            resp = regular_requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={'Authorization': f'Bearer {google_access_token}'})
            if resp.status_code == 200:
                idinfo = resp.json()
            else:
                return Response({'error': 'Invalid Google access token.'}, status=status.HTTP_400_BAD_REQUEST)
        
        email = idinfo.get('email') if idinfo else None
            
        if not email:
            return Response({'error': 'Google authentication did not contain an email address.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(email=email).first()
        if user:
            # Update profile image if missing but Google provided it
            if not user.profile_image and 'picture' in idinfo:
                import requests as req
                from django.core.files.base import ContentFile
                try:
                    img_resp = req.get(idinfo['picture'])
                    if img_resp.status_code == 200:
                        user.profile_image.save(f"google_prof_{user.id}.jpg", ContentFile(img_resp.content), save=True)
                except Exception:
                    pass

            # Login user
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data})
        else:
            # User doesn't exist, tell frontend to redirect to signup
            
            # Google idinfo doesn't natively return birthday/gender by default via standard scopes, 
            # but sometimes available via People API. We'll pass them safely if they miraculously exist, 
            # otherwise just empty strings as before.
            return Response({
                'error': 'Account not found. Please sign up.',
                'needs_signup': True,
                'google_data': {
                    'email': email,
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', ''),
                    'picture': idinfo.get('picture', ''),
                    'gender': idinfo.get('gender', ''), 
                    'birthday': idinfo.get('birthday', ''),
                    'google_access_token': google_access_token,
                    'google_id_token': google_id_token
                }
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_mood(self, request):
        mood = request.data.get('mood')
        if not mood:
            return Response({'error': 'Mood is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user.current_mood = mood
        user.save()

        # Notify partner
        from .signals import create_notification
        create_notification(
            sender_user=user,
            couple=user.couple_as_p1 if hasattr(user, 'couple_as_p1') else user.couple_as_p2,
            verb=f"updated their mood to: {mood}",
            target_model='User',
            target_id=user.id
        )

        return Response(UserSerializer(user).data)

    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated], parser_classes=[parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser])
    def update_profile(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CoupleViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate_invite(self, request):
        if not request.user.email_verified:
            return Response({'error': 'Email verification required to create a space'}, status=status.HTTP_403_FORBIDDEN)
            
        # Check if user is already in a couple with a partner
        if (hasattr(request.user, 'couple_as_p1') and request.user.couple_as_p1.partner_2) or \
           (hasattr(request.user, 'couple_as_p2')):
            return Response({'error': 'You are already in a connected space with a partner.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user is P1 of a solo space, just return that code
        if hasattr(request.user, 'couple_as_p1') and not request.user.couple_as_p1.partner_2:
            couple = request.user.couple_as_p1
            return Response({'code': couple.invite_code, 'couple': CoupleSerializer(couple).data})

        # Generate unique code
        while True:
            code = get_random_string(6).upper()
            if not Couple.objects.filter(invite_code=code).exists():
                break
        
        # Use anniversary_date from request if provided, otherwise fallback to user's existing field
        anniversary_start = request.data.get('anniversary_date')
        if anniversary_start:
            request.user.anniversary_date = anniversary_start
            request.user.save()
        else:
            anniversary_start = request.user.anniversary_date

        couple = Couple.objects.create(partner_1=request.user, invite_code=code, anniversary_start=anniversary_start)
        
        # Send space created email
        dashboard_url = f"{settings.CORS_ALLOWED_ORIGINS[0]}/dashboard" if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS else "http://localhost:3000/dashboard"
        InternalMailer.send_space_created(request.user, dashboard_url, code)
        
        return Response({'code': code, 'couple': CoupleSerializer(couple).data})

    @action(detail=False, methods=['post'])
    def join(self, request):
        code = request.data.get('code', '').strip().upper()
        
        if not code:
            return Response({'error': 'Invitation code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user is already in a connected couple
        if (hasattr(request.user, 'couple_as_p1') and request.user.couple_as_p1.partner_2) or \
           (hasattr(request.user, 'couple_as_p2')):
            return Response({'error': 'You are already in a connected space. Please delete your current space to join a new one.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user is in a solo space, delete it to allow joining a new one
        if hasattr(request.user, 'couple_as_p1') and not request.user.couple_as_p1.partner_2:
            request.user.couple_as_p1.delete()
        
        # Find couple with this invite code
        try:
            couple = Couple.objects.get(invite_code=code)
        except Couple.DoesNotExist:
            return Response({'error': 'Invalid or expired invitation code. Please check and try again.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if couple already has partner_2
        if couple.partner_2:
            return Response({'error': 'This space is already full.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if trying to join own code (shouldn't happen with delete above, but safety first)
        if couple.partner_1 == request.user:
            return Response({'error': 'You cannot join your own space.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Add user as partner_2
        couple.partner_2 = request.user
        couple.save()
        
        # Send connection emails
        dashboard_url = f"{settings.CORS_ALLOWED_ORIGINS[0]}/dashboard" if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS else "http://localhost:3000/dashboard"
        InternalMailer.send_partner_joined(couple.partner_1, request.user.first_name or request.user.username, dashboard_url)
        InternalMailer.send_partner_joined(request.user, couple.partner_1.first_name or couple.partner_1.username, dashboard_url)
        
        return Response(CoupleSerializer(couple).data)
    
    @action(detail=False, methods=['post'])
    def create_solo(self, request):
        # Professional check
        if (hasattr(request.user, 'couple_as_p1') and request.user.couple_as_p1.partner_2) or \
           (hasattr(request.user, 'couple_as_p2')):
            return Response({'error': 'You are already in a connected space.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If user is already P1 of a solo space, return it
        if hasattr(request.user, 'couple_as_p1') and not request.user.couple_as_p1.partner_2:
            return Response(CoupleSerializer(request.user.couple_as_p1).data)

        # Generate unique invite code
        while True:
            invite_code = get_random_string(6).upper()
            if not Couple.objects.filter(invite_code=invite_code).exists():
                break
                
        # Use anniversary_date from request if provided, otherwise fallback to user's existing field
        anniversary_start = request.data.get('anniversary_date')
        if anniversary_start:
            request.user.anniversary_date = anniversary_start
            request.user.save()
        else:
            anniversary_start = request.user.anniversary_date

        couple = Couple.objects.create(partner_1=request.user, invite_code=invite_code, anniversary_start=anniversary_start)
        return Response(CoupleSerializer(couple).data)

    @action(detail=False, methods=['patch'])
    def update_settings(self, request):
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
            
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = CoupleSerializer(couple, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Sync to current user's individual anniversary_date for consistency
            anniversary_start = request.data.get('anniversary_start')
            if anniversary_start:
                # Convert from DateTime string to Date if needed, or just take the date part
                # anniversary_start is usually ISO string "YYYY-MM-DDTHH:MM"
                date_part = anniversary_start.split('T')[0]
                request.user.anniversary_date = date_part
                request.user.save()
                
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_couple(self, request):
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
        
        if couple:
            return Response(CoupleSerializer(couple).data)
        return Response({'message': 'No couple found', 'couple': None})
    
    @action(detail=False, methods=['post'])
    def regenerate_code(self, request):
        """Regenerate invitation code for the couple"""
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
        
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate new code
        new_code = get_random_string(6).upper()
        couple.invite_code = new_code
        couple.save()
        
        return Response({'invite_code': new_code, 'message': 'Code regenerated successfully'})

    @action(detail=False, methods=['post'])
    def request_deletion(self, request):
        """Initiate space deletion request"""
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
        
        if not couple:
            # If user somehow reached here without a couple, just delete their account
            request.user.delete()
            return Response({'message': 'Account deleted successfully', 'deleted': True, 'account_deleted': True})

        # If user is the only one in the couple, delete user account (which also drops the couple due to CASCADE)
        if not couple.partner_2:
            request.user.delete()
            return Response({'message': 'Account deleted successfully', 'deleted': True, 'account_deleted': True})

        # Logic for 2 users:
        if couple.is_deletion_pending:
            return Response({'error': 'Deletion already requested'}, status=status.HTTP_400_BAD_REQUEST)

        couple.is_deletion_pending = True
        couple.deletion_requested_by = request.user
        couple.deletion_requested_at = timezone.now()
        couple.save()

        # Notify partner
        partner = couple.get_other_user(request.user)
        from .signals import create_notification
        if partner:
            create_notification(
                sender_user=request.user,
                couple=couple,
                verb="requested to delete the space",
                target_model='Couple',
                target_id=couple.id, # Using couple ID as target
                description="Please confirm deletion in Settings."
            )

        return Response({'message': 'Deletion requested. Waiting for partner confirmation.', 'deleted': False})

    @action(detail=False, methods=['post'])
    def confirm_deletion(self, request):
        """Confirm space deletion"""
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
        
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)

        if not couple.is_deletion_pending:
            return Response({'error': 'No deletion requested'}, status=status.HTTP_400_BAD_REQUEST)
        
        if couple.deletion_requested_by == request.user:
            return Response({'error': 'You cannot confirm your own request'}, status=status.HTTP_400_BAD_REQUEST)

        # Confirm deletion - DELETE EVERYTHING
        # Django's cascading delete will handle related models if configured correctly
        couple.delete()
        
        return Response({'message': 'Space deleted successfully', 'deleted': True})

    @action(detail=False, methods=['post'])
    def cancel_deletion(self, request):
        """Cancel space deletion request"""
        couple = None
        if hasattr(request.user, 'couple_as_p1'):
            couple = request.user.couple_as_p1
        elif hasattr(request.user, 'couple_as_p2'):
            couple = request.user.couple_as_p2
        
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)

        if not couple.is_deletion_pending:
            return Response({'error': 'No deletion requested'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Allow anyone to cancel? Or just the requester? 
        # Usually both should be able to cancel in a "safe" design, or at least the partner rejecting it.
        # Let's say "Reject" calls this too.
        
        couple.is_deletion_pending = False
        couple.deletion_requested_by = None
        couple.deletion_requested_at = None
        couple.save()
        
        return Response({'message': 'Deletion request cancelled'})

class BaseCoupleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_couple(self):
        user = self.request.user
        if hasattr(user, 'couple_as_p1'):
            return user.couple_as_p1
        elif hasattr(user, 'couple_as_p2'):
            return user.couple_as_p2
        return None

    def get_queryset(self):
        couple = self.get_couple()
        if not couple:
            return self.queryset.none()
        return self.queryset.filter(couple=couple)

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple to add items.")
        serializer.save(couple=couple)

class MemoryViewSet(BaseCoupleViewSet):
    queryset = Memory.objects.all()
    serializer_class = MemorySerializer

    @action(detail=True, methods=['get'])
    def secure_image(self, request, pk=None):
        memory = self.get_object()
        if not memory.image:
            raise Http404("No image")
        
        try:
            with open(memory.image.path, 'rb') as f:
                encrypted_data = f.read()
            
            from .media_handlers import decrypt_image
            decrypted_data = decrypt_image(encrypted_data)
            
            # Since we compress to JPEG in our utility, we serve as image/jpeg
            return HttpResponse(decrypted_data, content_type="image/jpeg")
        except Exception:
            # Fallback if decryption fails (might be an old unencrypted image)
            try:
                with open(memory.image.path, 'rb') as f:
                    return HttpResponse(f.read(), content_type="image/jpeg")
            except Exception:
                raise Http404("Image could not be served")

class ImportantDateViewSet(BaseCoupleViewSet):
    queryset = ImportantDate.objects.all()
    serializer_class = ImportantDateSerializer

class RuleViewSet(BaseCoupleViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer

class BucketItemViewSet(BaseCoupleViewSet):
    queryset = BucketItem.objects.all()
    serializer_class = BucketItemSerializer

class LoveNoteViewSet(BaseCoupleViewSet):
    queryset = LoveNote.objects.all()
    serializer_class = LoveNoteSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple to add items.")
        serializer.save(couple=couple, sender=self.request.user)

# Phase 1: Advanced Features ViewSets

class LoveLanguageViewSet(BaseCoupleViewSet):
    queryset = LoveLanguage.objects.all()
    serializer_class = LoveLanguageSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        serializer.save(couple=couple, user=self.request.user)

    @action(detail=False, methods=['post'])
    def submit_quiz(self, request):
        """Submit love language quiz results"""
        couple = self.get_couple()
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
        
        primary = request.data.get('primary_language')
        secondary = request.data.get('secondary_language', '')
        
        if not primary:
            return Response({'error': 'Primary language is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create love language
        love_lang, created = LoveLanguage.objects.update_or_create(
            couple=couple,
            user=request.user,
            defaults={
                'primary_language': primary,
                'secondary_language': secondary,
                'quiz_completed': True,
                'quiz_completed_at': timezone.now()
            }
        )
        
        return Response(LoveLanguageSerializer(love_lang).data)

    @action(detail=False, methods=['get'])
    def partner_language(self, request):
        """Get partner's love language"""
        couple = self.get_couple()
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
        
        partner = couple.get_other_user(request.user)
        if not partner:
            return Response({'message': 'Partner not joined yet'})
        
        try:
            love_lang = LoveLanguage.objects.get(couple=couple, user=partner)
            return Response(LoveLanguageSerializer(love_lang).data)
        except LoveLanguage.DoesNotExist:
            return Response({'message': 'Partner has not completed quiz yet'})

class LoveLanguageActionViewSet(BaseCoupleViewSet):
    queryset = LoveLanguageAction.objects.all()
    serializer_class = LoveLanguageActionSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        
        partner = couple.get_other_user(self.request.user)
        serializer.save(couple=couple, giver=self.request.user, receiver=partner)

class GratitudeEntryViewSet(BaseCoupleViewSet):
    queryset = GratitudeEntry.objects.all()
    serializer_class = GratitudeEntrySerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        serializer.save(couple=couple, author=self.request.user)

    @action(detail=False, methods=['get'])
    def partner_entries(self, request):
        """Get partner's gratitude entries"""
        couple = self.get_couple()
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
        
        partner = couple.get_other_user(request.user)
        entries = GratitudeEntry.objects.filter(couple=couple, author=partner)
        return Response(GratitudeEntrySerializer(entries, many=True).data)

class DateIdeaViewSet(BaseCoupleViewSet):
    queryset = DateIdea.objects.all()
    serializer_class = DateIdeaSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        serializer.save(couple=couple, created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def complete_date(self, request, pk=None):
        """Mark a date as completed with rating and notes"""
        date_idea = self.get_object()
        
        rating = request.data.get('rating')
        notes = request.data.get('notes', '')
        
        date_idea.is_completed = True
        date_idea.completed_date = timezone.now().date()
        if rating:
            date_idea.rating = rating
        if notes:
            date_idea.notes = notes
        date_idea.save()
        
        return Response(DateIdeaSerializer(date_idea).data)

class QuestionViewSet(BaseCoupleViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        serializer.save(couple=couple, creator=self.request.user)
    
    @action(detail=False, methods=['get'])
    def category(self, request):
        """Get questions by category"""
        category = request.query_params.get('category')
        if not category:
            return Response({'error': 'Category required'}, status=status.HTTP_400_BAD_REQUEST)
        
        couple = self.get_couple()
        questions = Question.objects.filter(couple=couple, category=category)
        return Response(QuestionSerializer(questions, many=True).data)

class AnswerViewSet(BaseCoupleViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        
        question_id = self.request.data.get('question')
        question = Question.objects.get(id=question_id)
        
        # Check if user already answered
        if Answer.objects.filter(question=question, author=self.request.user).exists():
            raise serializers.ValidationError("You have already answered this question.")
            
        serializer.save(question=question, author=self.request.user)

class TodoViewSet(BaseCoupleViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple.")
        serializer.save(couple=couple, created_by=self.request.user)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read and then delete them"""
        Notification.objects.filter(recipient=request.user, is_read=False).delete()
        return Response({'status': 'marked all as read and deleted'})

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a single notification as read and then delete it"""
        notification = self.get_object()
        notification.delete()
        return Response({'status': 'marked as read and deleted'})

class CalendarViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_couple(self):
        user = self.request.user
        if hasattr(user, 'couple_as_p1'):
            return user.couple_as_p1
        elif hasattr(user, 'couple_as_p2'):
            return user.couple_as_p2
        return None

    @action(detail=False, methods=['get'])
    def events(self, request):
        """Get all calendar events (memories and important dates)"""
        couple = self.get_couple()
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. Important Dates (Recurring yearly)
        important_dates = ImportantDate.objects.filter(couple=couple)
        
        # 2. Memories (Historical, "On this day" in past years)
        memories = Memory.objects.filter(couple=couple)
        
        events = []
        
        # Format Important Dates
        for date_obj in important_dates:
            events.append({
                'id': f"date_{date_obj.id}",
                'type': 'important_date',
                'title': date_obj.title,
                'date': date_obj.date.isoformat(),
                'recurring': True, # Repeats every year
                'original_year': date_obj.date.year
            })
            
        # Format Memories
        for memory in memories:
            events.append({
                'id': f"memory_{memory.id}",
                'type': 'memory',
                'title': memory.title,
                'description': memory.description,
                'date': memory.date.isoformat(),
                'image': request.build_absolute_uri(memory.image.url) if memory.image else None,
                'recurring': False,
                'original_year': memory.date.year
            })
            
        return Response(events)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events for the next 30 days"""
        couple = self.get_couple()
        if not couple:
            return Response({'error': 'Not in a couple'}, status=status.HTTP_400_BAD_REQUEST)
            
        today = timezone.now().date()
        thirty_days_later = today + relativedelta(days=30)
        
        upcoming_events = []

        # Check Couple Anniversary
        if couple.anniversary_start:
            anniversary = couple.anniversary_start.date()
            this_year_anniversary = anniversary.replace(year=today.year)
            if this_year_anniversary < today:
                try:
                    this_year_anniversary = this_year_anniversary.replace(year=today.year + 1)
                except ValueError: # Leap year
                    this_year_anniversary = anniversary + relativedelta(years=(today.year + 1 - anniversary.year))
            
            if today <= this_year_anniversary <= thirty_days_later:
                years = this_year_anniversary.year - anniversary.year
                upcoming_events.append({
                    'id': 'couple_anniversary',
                    'type': 'important_date',
                    'title': 'Relationship Anniversary ❤️',
                    'date': this_year_anniversary.isoformat(),
                    'days_left': (this_year_anniversary - today).days,
                    'anniversary': f"{years} year" if years == 1 else f"{years} years"
                })
        
        # Check Important Dates
        important_dates = ImportantDate.objects.filter(couple=couple)
        for date_obj in important_dates:
            # Create a virtual date for the current/next year
            this_year_date = date_obj.date.replace(year=today.year)
            
            # If the date has already passed this year, look at next year
            if this_year_date < today:
                try:
                    this_year_date = this_year_date.replace(year=today.year + 1)
                except ValueError:
                    # Handle Feb 29 for non-leap years by falling back to Feb 28 or Mar 1
                    this_year_date = date_obj.date + relativedelta(years=(today.year + 1 - date_obj.date.year))
                
            if today <= this_year_date <= thirty_days_later:
                years_anniversary = this_year_date.year - date_obj.date.year
                upcoming_events.append({
                    'id': f"date_{date_obj.id}",
                    'type': 'important_date',
                    'title': date_obj.title,
                    'date': this_year_date.isoformat(),
                    'days_left': (this_year_date - today).days,
                    'anniversary': f"{years_anniversary} year" if years_anniversary == 1 else f"{years_anniversary} years" if years_anniversary > 1 else "upcoming"
                })
                
        # Sort by days left
        upcoming_events.sort(key=lambda x: x['days_left'])
        
        # Return up to 5 upcoming events
        return Response(upcoming_events[:5])

class ActivePopupView(generics.RetrieveAPIView):
    serializer_class = AnnouncementPopupSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return AnnouncementPopup.objects.filter(is_active=True).order_by('-created_at').first()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance:
            return Response({'message': 'No active popup'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class UserSupportTicketViewSet(BaseCoupleViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer

    def perform_create(self, serializer):
        couple = self.get_couple()
        if not couple:
            raise serializers.ValidationError("You must be in a couple to create a ticket.")
        ticket = serializer.save(couple=couple, user=self.request.user)
        TicketMessage.objects.create(
            ticket=ticket,
            sender=self.request.user,
            message=ticket.message,
            is_admin_reply=False
        )

    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        ticket = self.get_object()
        if ticket.status == 'resolved':
            return Response({'error': 'Cannot reply to a resolved ticket.'}, status=status.HTTP_400_BAD_REQUEST)
        
        message_text = request.data.get('message')
        if not message_text:
            return Response({'error': 'Message cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)
            
        TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=message_text,
            is_admin_reply=False
        )
        if ticket.status == 'in_progress':
            ticket.status = 'open'
            ticket.save()
            
        return Response(SupportTicketSerializer(ticket).data)

class SecureProfileImageView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404("User not found")
        
        # Security Check: Only allow self, partner, or staff
        is_self = request.user == target_user
        is_partner = False
        
        user_couple = getattr(request.user, 'couple_as_p1', None) or getattr(request.user, 'couple_as_p2', None)
        if user_couple:
            partner = user_couple.get_other_user(request.user)
            if partner == target_user:
                is_partner = True
        
        if not (is_self or is_partner or request.user.is_staff):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        if not target_user.profile_image:
            raise Http404("No profile image")
            
        try:
            from .media_handlers import decrypt_image
            with open(target_user.profile_image.path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = decrypt_image(encrypted_data)
            return HttpResponse(decrypted_data, content_type="image/jpeg")
        except Exception:
            # Fallback for unencrypted old images
            try:
                with open(target_user.profile_image.path, 'rb') as f:
                    return HttpResponse(f.read(), content_type="image/jpeg")
            except Exception:
                raise Http404("Image could not be served")




