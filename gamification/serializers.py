from rest_framework import serializers
from .models import QuizQuestion, QuizAnswer, Badge, CoupleBadge, Streak

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'category']

class QuizAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAnswer
        fields = ['id', 'question', 'user', 'my_own_answer', 'guess_partner_answer', 'answered_at']
        read_only_fields = ['user', 'answered_at']

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['id', 'name', 'description', 'icon_name', 'badge_type']

class CoupleBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()
    class Meta:
        model = CoupleBadge
        fields = ['badge', 'earned_at']

class StreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streak
        fields = ['current_streak', 'longest_streak', 'last_interaction_date']
