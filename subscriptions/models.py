from django.db import models
from django.utils import timezone
from api.models import Couple, Coupon

class SubscriptionTier(models.TextChoices):
    FREE = 'FREE', 'Free'
    PREMIUM = 'PREMIUM', 'Premium'
    ULTRA = 'ULTRA', 'Ultra'

class SubscriptionStatus(models.TextChoices):
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    ACTIVE = 'ACTIVE', 'Active'
    EXPIRED = 'EXPIRED', 'Expired'
    REJECTED = 'REJECTED', 'Rejected'

class PlanDuration(models.TextChoices):
    MONTHLY = 'MONTHLY', '1 Month'
    YEARLY = 'YEARLY', '1 Year'
    LIFETIME = 'LIFETIME', 'Lifetime'

class UserSubscription(models.Model):
    couple = models.OneToOneField(Couple, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
    )
    plan_duration = models.CharField(
        max_length=20,
        choices=PlanDuration.choices,
        default=PlanDuration.MONTHLY,
        null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # For manual payments
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True, help_text="Reference ID from the payment app")
    applied_coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.couple}'s {self.tier} Plan - {self.status}"
        
    @property
    def days_left(self):
        if self.tier == SubscriptionTier.FREE or not self.end_date:
            return None
        
        if self.status != SubscriptionStatus.ACTIVE:
            return 0
            
        remaining = self.end_date - timezone.now()
        days = remaining.days
        return max(0, days)

    def is_active(self):
        if self.status != SubscriptionStatus.ACTIVE:
            return False
            
        if self.tier == SubscriptionTier.FREE:
            return True
            
        if self.end_date and timezone.now() > self.end_date:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            # Reset duration for free tier
            self.plan_duration = None
            self.save()
            return False
            
        return True

class PaymentSettings(models.Model):
    upi_id = models.CharField(max_length=100, default='Q836094841@ybl')
    qr_code = models.ImageField(upload_to='payment_qr/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"Payment Info (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"
