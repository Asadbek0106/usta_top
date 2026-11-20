from rest_framework.routers import SimpleRouter

from .views import ArizaViewSet

router = SimpleRouter()
router.register('arizalar', ArizaViewSet, basename='ariza')

urlpatterns = router.urls
