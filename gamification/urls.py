from django.urls import path
from .views import DailyQuizView, GamificationStatsView

urlpatterns = [
    path('quiz/daily/', DailyQuizView.as_view(), name='daily-quiz'),
    path('stats/', GamificationStatsView.as_view(), name='gamification-stats'),
]
