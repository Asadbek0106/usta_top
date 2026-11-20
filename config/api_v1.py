from django.urls import include, path

urlpatterns = [
    path('auth/', include('apps.accounts.urls')),
    path('', include('apps.ustalar.urls')),
    path('', include('apps.arizalar.urls')),
]
