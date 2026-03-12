from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GiftIdeaViewSet, ExpenseViewSet

router = DefaultRouter()
router.register(r'gifts', GiftIdeaViewSet, basename='gifts')
router.register(r'expenses', ExpenseViewSet, basename='expenses')

urlpatterns = [
    path('', include(router.urls)),
]
