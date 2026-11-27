from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.views import health

urlpatterns = [
    path('health/', health, name='health'),
    path('', RedirectView.as_view(pattern_name='swagger-ui', permanent=False)),
    path('admin/', admin.site.urls),
    path('api/v1/', include('config.api_v1')),
    path('api-auth/', include('rest_framework.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Yuklangan rasmlar. Kichik loyiha uchun ularni Django'ning o'zi beradi (static() yordamchisi
    # faqat DEBUG'da ishlaydi, shuning uchun to'g'ridan-to'g'ri serve). Fayl nomlari tasodifiy UUID.
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
