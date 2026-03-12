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

class UserSubscription(models.Model):
    couple = models.OneToOneField(Couple, on_delete=models.CASCADE, related_name='subscription')
    tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
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
        
    def is_active(self):
        if self.status != SubscriptionStatus.ACTIVE:
            return False
            
        if self.tier == SubscriptionTier.FREE:
            return True
            
        if self.end_date and timezone.now() > self.end_date:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.save()
            return False
            
        return True

class PaymentSettings(models.Model):
    upi_id = models.CharField(max_length=100, default='admin@lovenest')
    qr_code = models.ImageField(upload_to='payment_qr/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Payment Settings"

    def __str__(self):
        return f"Payment Info (Last updated: {self.updated_at.strftime('%Y-%m-%d')})"
