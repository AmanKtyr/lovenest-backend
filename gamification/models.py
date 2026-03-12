from django.db import models
from api.models import Couple, User

class QuizQuestion(models.Model):
    """Global quiz questions for the 'How well do you know me?' feature"""
    text = models.CharField(max_length=500)
    category = models.CharField(max_length=100, default='General')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text

class QuizAnswer(models.Model):
    """Stores answers provided by each partner to a global QuizQuestion"""
    question = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE, related_name='answers')
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='quiz_answers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_answers')
    
    # In a "How well do you know me?" quiz, User A answers what they think User B would say.
    # We'll store both: 
    # 1. My actual answer about me
    # 2. My guess about my partner
    my_own_answer = models.TextField(help_text="My own answer to this question")
    guess_partner_answer = models.TextField(help_text="What I think my partner will say")
    
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['question', 'couple', 'user']

    def __str__(self):
        return f"{self.user.username}'s quiz answer"

class Badge(models.Model):
    """Definitions of earnable badges"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_name = models.CharField(max_length=50, help_text="Lucide icon name")
    badge_type = models.CharField(max_length=50, choices=[
        ('streak', 'Daily Streak'),
        ('milestone', 'Milestone Achievement'),
        ('engagement', 'Engagement Badge'),
    ])
    requirement_value = models.PositiveIntegerField(help_text="Value to reach for this badge")

    def __str__(self):
        return self.name

class CoupleBadge(models.Model):
    """Badges earned by a couple"""
    couple = models.ForeignKey(Couple, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='earned_by')
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['couple', 'badge']

    def __str__(self):
        return f"{self.couple} earned {self.badge.name}"

class Streak(models.Model):
    """Daily interaction streaks for couples"""
    couple = models.OneToOneField(Couple, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_interaction_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.couple} - {self.current_streak} days"
