import smtplib
from email.message import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import SiteSetting
from django.conf import settings
import threading

class InternalMailer:
    @staticmethod
    def _send_email(subject, html_content, recipient_list):
        """Internal worker to send email using SiteSettings or fallback to console"""
        site_settings = SiteSetting.get_settings()
        
        # If no SMTP configured, just print to console (useful for dev)
        if not site_settings.smtp_user or not site_settings.smtp_password:
            print(f"----- MOCK EMAIL -----")
            print(f"To: {recipient_list}")
            print(f"Subject: {subject}")
            print(f"Content:\n{html_content}")
            print(f"----------------------")
            return

        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = f"LoveNest <{site_settings.smtp_user}>"
            msg['To'] = ", ".join(recipient_list)
            
            # Set text/html
            msg.set_content(strip_tags(html_content)) # Fallback plain text
            msg.add_alternative(html_content, subtype='html')

            # Send Email
            server = smtplib.SMTP(site_settings.smtp_host, site_settings.smtp_port)
            if site_settings.use_tls:
                server.starttls()
            server.login(site_settings.smtp_user, site_settings.smtp_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")

    @classmethod
    def send_email_async(cls, subject, html_content, recipient_list):
        """Non-blocking email sender"""
        thread = threading.Thread(
            target=cls._send_email,
            args=(subject, html_content, recipient_list)
        )
        thread.start()

    @classmethod
    def send_verification_code(cls, user, code):
        """Send 6-digit verification code to user's registered email"""
        cls.send_verification_code_to_email(user.email, user.first_name or user.username, code)

    @classmethod
    def send_verification_code_to_email(cls, email, name, code):
        """Send 6-digit verification code to a specific email"""
        html_message = render_to_string('emails/verification.html', {
            'name': name,
            'code': code
        })
        cls.send_email_async(
            subject="LoveNest - Your Verification Code",
            html_content=html_message,
            recipient_list=[email]
        )

    @classmethod
    def send_space_created(cls, user, dashboard_url, code=None):
        """Notify user that their space is ready"""
        html_message = render_to_string('emails/space_created.html', {
            'name': user.first_name or user.username,
            'code': code,
            'dashboard_url': dashboard_url
        })
        cls.send_email_async(
            subject="Your Private LoveNest is Ready! 🏰",
            html_content=html_message,
            recipient_list=[user.email]
        )

    @classmethod
    def send_partner_joined(cls, user, partner_name, dashboard_url):
        """Notify user that their partner has connected"""
        html_message = render_to_string('emails/partner_joined.html', {
            'name': user.first_name or user.username,
            'partner_name': partner_name,
            'dashboard_url': dashboard_url
        })
        cls.send_email_async(
            subject="It's Official! Your Partner Joined LoveNest ❤️",
            html_content=html_message,
            recipient_list=[user.email]
        )

    @classmethod
    def send_password_reset_otp(cls, email, code):
        """Send OTP for password recovery"""
        html_message = render_to_string('emails/verification.html', {
            'name': "User",
            'code': code
        })
        # reusing verification template since the layout is identical
        html_message = html_message.replace(
            "Welcome to LoveNest! You're one step away from joining your private sanctuary. To ensure the security of your account, please verify your email address.",
            "We received a request to reset your LoveNest password. Please use the code below to securely change your password."
        )
        
        cls.send_email_async(
            subject="LoveNest - Password Reset Code",
            html_content=html_message,
            recipient_list=[email]
        )
