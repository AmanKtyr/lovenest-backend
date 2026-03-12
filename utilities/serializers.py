from rest_framework import serializers
from .models import GiftIdea, Expense

class GiftIdeaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftIdea
        fields = ['id', 'title', 'description', 'price_estimate', 'url', 'for_event', 'event_date', 'is_purchased', 'created_at']
        read_only_fields = ['id', 'created_at']

class ExpenseSerializer(serializers.ModelSerializer):
    payer_name = serializers.ReadOnlyField(source='payer.username')
    
    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'date', 'category', 'split_type', 'payer', 'payer_name']
        read_only_fields = ['id', 'date', 'payer', 'payer_name']
