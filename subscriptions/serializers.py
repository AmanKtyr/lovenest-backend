from rest_framework import serializers
from .models import UserSubscription, SubscriptionTier, SubscriptionStatus
from api.models import Coupon

class UserSubscriptionSerializer(serializers.ModelSerializer):
    tier_name = serializers.CharField(source='get_tier_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    couple_name = serializers.SerializerMethodField()
    couple_id = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(source='last_updated', read_only=True)
    applied_coupon_details = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'couple', 'couple_id', 'couple_name', 'tier', 'tier_name', 
            'status', 'status_display', 'start_date', 'end_date', 
            'payment_screenshot', 'transaction_id', 'applied_coupon', 'applied_coupon_details', 'created_at', 'last_updated',
            'is_active'
        ]
        read_only_fields = ['couple', 'status', 'start_date', 'end_date', 'last_updated']

    def get_couple_name(self, obj):
        p1 = obj.couple.partner_1.username
        p2 = obj.couple.partner_2.username if obj.couple.partner_2 else "Pending"
        return f"{p1} & {p2}"

    def get_couple_id(self, obj):
        return str(obj.couple.id.int)[:12]

    def get_applied_coupon_details(self, obj):
        if obj.applied_coupon:
            return {
                'code': obj.applied_coupon.code,
                'discount_percentage': obj.applied_coupon.discount_percentage
            }
        return None


class PaymentUploadSerializer(serializers.Serializer):
    tier = serializers.ChoiceField(choices=SubscriptionTier.choices)
    payment_screenshot = serializers.ImageField(required=True)
    transaction_id = serializers.CharField(required=True, max_length=100)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=50)

    def validate_coupon_code(self, value):
        if value:
            try:
                coupon = Coupon.objects.get(code=value)
                if not coupon.is_valid:
                    if not coupon.is_active:
                        raise serializers.ValidationError("This coupon is no longer active.")
                    from django.utils import timezone
                    if coupon.valid_until < timezone.now():
                        raise serializers.ValidationError("This coupon has expired.")
                    if coupon.current_uses >= coupon.max_uses:
                        raise serializers.ValidationError("This coupon usage limit has been reached.")
                    raise serializers.ValidationError("This coupon is invalid.")
                return coupon
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Invalid or expired coupon code.")
        return None
