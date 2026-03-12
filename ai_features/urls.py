from django.urls import path
from .views import DatePlannerView, RelationshipCoachView, GenerateMemoryCaptionView, GiftGeneratorView

urlpatterns = [
    path('date-planner/', DatePlannerView.as_view(), name='date-planner'),
    path('relationship-coach/', RelationshipCoachView.as_view(), name='relationship-coach'),
    path('generate-caption/', GenerateMemoryCaptionView.as_view(), name='generate-caption'),
    path('gift-ideas/', GiftGeneratorView.as_view(), name='gift-ideas'),
]
