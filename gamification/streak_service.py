from datetime import date, timedelta
from django.utils import timezone
from .models import Streak, Badge, CoupleBadge

class StreakService:
    @staticmethod
    def update_interaction(couple):
        """Update the couple's streak when they interact with the app"""
        streak, created = Streak.objects.get_or_create(couple=couple)
        today = date.today()

        if streak.last_interaction_date == today:
            return streak

        if streak.last_interaction_date == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            # Reset if missed a day
            streak.current_streak = 1
        
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
            
        streak.last_interaction_date = today
        streak.save()
        
        # Check for streak badges
        StreakService.check_badges(couple, streak.current_streak)
        return streak

    @staticmethod
    def check_badges(couple, current_value):
        """Check if any badges should be awarded based on current metrics"""
        # 1. Check streak badges
        eligible_badges = Badge.objects.filter(
            badge_type='streak', 
            requirement_value__lte=current_value
        ).exclude(earned_by__couple=couple)
        
        for badge in eligible_badges:
            CoupleBadge.objects.get_or_create(couple=couple, badge=badge)

        # 2. Check milestone badges (e.g., total memories)
        # We can call this from specific places or do a general check
        from api.models import Memory
        memory_count = Memory.objects.filter(couple=couple).count()
        milestone_badges = Badge.objects.filter(
            badge_type='milestone',
            requirement_value__lte=memory_count
        ).exclude(earned_by__couple=couple)
        
        for badge in milestone_badges:
            # For specific milestone badges that need manual check
            if badge.name == "Memory Keepers":
                CoupleBadge.objects.get_or_create(couple=couple, badge=badge)
