from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/', include('subscriptions.urls')),
    path('api/ai/', include('ai_features.urls')),
    path('api/gamification/', include('gamification.urls')),
    path('api/utilities/', include('utilities.urls')),
    path('api/superadmin/', include('superadmin.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
