from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, CoupleViewSet, MemoryViewSet, ImportantDateViewSet, RuleViewSet,
    BucketItemViewSet, LoveNoteViewSet,
    LoveLanguageViewSet, LoveLanguageActionViewSet, GratitudeEntryViewSet,
    DateIdeaViewSet, QuestionViewSet, AnswerViewSet, TodoViewSet, NotificationViewSet,
    CalendarViewSet, ActivePopupView, ContactMessageCreateView, UserSupportTicketViewSet,
    SecureProfileImageView, health_check, CountdownViewSet
)

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'couple', CoupleViewSet, basename='couple')
router.register(r'memories', MemoryViewSet, basename='memories')
router.register(r'dates', ImportantDateViewSet, basename='dates')
router.register(r'rules', RuleViewSet, basename='rules')
router.register(r'bucket', BucketItemViewSet, basename='bucket')
router.register(r'notes', LoveNoteViewSet, basename='notes')
router.register(r'countdowns', CountdownViewSet, basename='countdowns')

# Phase 1: Advanced Features
router.register(r'love_languages', LoveLanguageViewSet, basename='love_languages')
router.register(r'love_actions', LoveLanguageActionViewSet, basename='love_actions')
router.register(r'gratitude', GratitudeEntryViewSet, basename='gratitude')
router.register(r'date_ideas', DateIdeaViewSet, basename='date_ideas')
router.register(r'questions', QuestionViewSet, basename='questions')
router.register(r'answers', AnswerViewSet, basename='answers')
router.register(r'todos', TodoViewSet, basename='todos')
router.register(r'support_tickets', UserSupportTicketViewSet, basename='support_tickets')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'calendar', CalendarViewSet, basename='calendar')

urlpatterns = [
    path('health-check/', health_check, name='health-check'),
    path('', include(router.urls)),
    path('active-popup/', ActivePopupView.as_view(), name='active-popup'),
    path('contact/', ContactMessageCreateView.as_view(), name='contact'),
    path('secure-profile/<int:user_id>/', SecureProfileImageView.as_view(), name='secure-profile-image'),
    path('superadmin/', include('superadmin.urls')),
]
