from rest_framework import serializers
from .models import (
    User, Couple, Memory, ImportantDate, Rule, BucketItem, LoveNote,
    LoveLanguage, LoveLanguageAction, GratitudeEntry, DateIdea, Question, Answer, Todo, Notification,
    AnnouncementPopup, ContactMessage, SupportTicket, TicketMessage
)
from django.contrib.auth import authenticate

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'phone_number',
            'gender', 'relationship_status', 'date_of_birth', 'anniversary_date',
            'profile_image', 'current_mood', 'mood_updated_at', 'is_superuser', 'is_staff'
        ]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    relationship_status = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    date_of_birth = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)
    anniversary_date = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)

    invite_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, default=None)

    class Meta:
        model = User
        fields = [
            'username', 'password', 'email', 'first_name', 'last_name',
            'phone_number', 'gender', 'relationship_status', 'date_of_birth',
            'anniversary_date', 'invite_code'
        ]

    def validate_date_of_birth(self, value):
        """Accept empty string as None"""
        return value or None

    def validate_email(self, value):
        from .models import User
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists. Please log in.")
        return value

    def validate_anniversary_date(self, value):
        """Accept empty string as None"""
        return value or None

    def validate_invite_code(self, value):
        if value:
            code = value.strip().upper()
            try:
                couple = Couple.objects.get(invite_code=code)
                if couple.partner_2:
                    raise serializers.ValidationError("This invitation code has already been used.")
            except Couple.DoesNotExist:
                raise serializers.ValidationError("Invalid invitation code. Please check and try again.")
        return value

    def create(self, validated_data):
        # invite_code is not a model field, so we must pop it before creating user
        validated_data.pop('invite_code', None)
        user = User.objects.create_user(**validated_data)
        return user

class AnnouncementPopupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnouncementPopup
        fields = ['id', 'title', 'message', 'image', 'image_url', 'is_active', 'display_frequency', 'created_at']
        read_only_fields = ['id', 'title', 'message', 'image', 'image_url', 'is_active', 'display_frequency', 'created_at']

class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone_number', 'country', 'address', 'message']

class CoupleSerializer(serializers.ModelSerializer):
    partner_1 = UserSerializer(read_only=True)
    partner_2 = UserSerializer(read_only=True)

    class Meta:
        model = Couple
        fields = ['id', 'partner_1', 'partner_2', 'invite_code', 'anniversary_start', 'theme_color', 'created_at', 
                 'is_deletion_pending', 'deletion_requested_by', 'deletion_requested_at']

class MemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = ['id', 'title', 'description', 'date', 'image', 'created_at']
        read_only_fields = ['couple']

class ImportantDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportantDate
        fields = ['id', 'title', 'date', 'created_at']
        read_only_fields = ['couple']

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ['id', 'text', 'priority', 'created_at']
        read_only_fields = ['couple']

class BucketItemSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = BucketItem
        fields = ['id', 'title', 'description', 'category', 'category_display', 'is_completed', 'created_at']
        read_only_fields = ['couple']
class LoveNoteSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = LoveNote
        fields = ['id', 'sender', 'content', 'is_read', 'created_at']
        read_only_fields = ['couple', 'sender']

class DashboardSerializer(serializers.Serializer):
    couple = CoupleSerializer()
    memories = MemorySerializer(many=True)
    important_dates = ImportantDateSerializer(many=True)
    rules = RuleSerializer(many=True)
    bucket_items = BucketItemSerializer(many=True)
    love_notes = LoveNoteSerializer(many=True)

# Phase 1: Advanced Features Serializers

class LoveLanguageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    primary_language_display = serializers.CharField(source='get_primary_language_display', read_only=True)
    secondary_language_display = serializers.CharField(source='get_secondary_language_display', read_only=True)
    
    class Meta:
        model = LoveLanguage
        fields = [
            'id', 'user', 'primary_language', 'primary_language_display',
            'secondary_language', 'secondary_language_display',
            'quiz_completed', 'quiz_completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['couple', 'user']

class LoveLanguageActionSerializer(serializers.ModelSerializer):
    giver = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    language_type_display = serializers.CharField(source='get_language_type_display', read_only=True)
    
    class Meta:
        model = LoveLanguageAction
        fields = [
            'id', 'giver', 'receiver', 'language_type', 'language_type_display',
            'description', 'date'
        ]
        read_only_fields = ['couple', 'giver', 'receiver']

class GratitudeEntrySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = GratitudeEntry
        fields = ['id', 'author', 'content', 'date', 'is_read', 'created_at']
        read_only_fields = ['couple', 'author', 'date']

class DateIdeaSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = DateIdea
        fields = [
            'id', 'created_by', 'title', 'description', 'category', 'category_display',
            'budget', 'is_completed', 'completed_date', 'rating', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['couple', 'created_by']

class AnswerSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Answer
        fields = ['id', 'question', 'author', 'text', 'created_at', 'updated_at']
        read_only_fields = ['author', 'question']

class QuestionSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'creator', 'text', 'category', 'category_display', 
            'created_at', 'answers'
        ]
        read_only_fields = ['couple', 'creator']

class TodoSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='assigned_to', write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Todo
        fields = [
            'id', 'title', 'is_completed', 'created_by', 'assigned_to', 'assigned_to_id',
            'due_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['couple', 'created_by', 'created_at', 'updated_at']


class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'verb', 'target_model', 'target_id', 'description', 'is_read', 'created_at']
        read_only_fields = ['recipient', 'created_at']

class TicketMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'ticket', 'sender', 'message', 'is_admin_reply', 'created_at']
        read_only_fields = ['id', 'ticket', 'sender', 'is_admin_reply', 'created_at']

class SupportTicketSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    messages = TicketMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = ['id', 'user', 'subject', 'message', 'status', 'admin_reply', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['couple', 'user', 'admin_reply', 'status', 'messages']
