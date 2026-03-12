from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminAnalyticsView, AdminCoupleViewSet, ContactMessageViewSet,
    AnnouncementPopupViewSet, CouponViewSet, AdminNotificationView,
    BackupRestoreView, UserActivityTrackerView, AdminSubscriptionViewSet,
    AdminSupportTicketViewSet
)

router = DefaultRouter()
router.register(r'spaces', AdminCoupleViewSet, basename='admin-spaces')
router.register(r'contact', ContactMessageViewSet, basename='admin-contact')
router.register(r'popups', AnnouncementPopupViewSet, basename='admin-popups')
router.register(r'coupons', CouponViewSet, basename='admin-coupons')
router.register(r'subscriptions', AdminSubscriptionViewSet, basename='admin-subscriptions')
router.register(r'support_tickets', AdminSupportTicketViewSet, basename='admin-support-tickets')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/', AdminAnalyticsView.as_view(), name='admin-analytics'),
    path('notifications/', AdminNotificationView.as_view(), name='admin-notifications'),
    path('backup/', BackupRestoreView.as_view(), name='admin-backup'),
    path('ping/', UserActivityTrackerView.as_view(), name='user-ping'),
]
