from django.contrib import admin
from .models import UserSubscription, SubscriptionStatus, PaymentSettings

@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ('upi_id', 'is_active', 'updated_at')
    list_editable = ('is_active',)

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('couple', 'tier', 'status', 'start_date', 'end_date', 'last_updated')
    list_filter = ('tier', 'status')
    search_fields = ('couple__partner_1__username', 'couple__partner_2__username')
    readonly_fields = ('start_date', 'last_updated')
    actions = ['approve_subscription', 'reject_subscription']

    def approve_subscription(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        from .models import PlanDuration
        
        for sub in queryset:
            sub.status = SubscriptionStatus.ACTIVE
            sub.start_date = timezone.now()
            
            if sub.plan_duration == PlanDuration.MONTHLY:
                sub.end_date = sub.start_date + timedelta(days=30)
            elif sub.plan_duration == PlanDuration.YEARLY:
                sub.end_date = sub.start_date + timedelta(days=365)
            elif sub.plan_duration == PlanDuration.LIFETIME:
                sub.end_date = None
            
            sub.save()
            
    approve_subscription.short_description = "Approve selected subscriptions"

    def reject_subscription(self, request, queryset):
        queryset.update(status=SubscriptionStatus.REJECTED)
    reject_subscription.short_description = "Reject selected subscriptions"
