from rest_framework.routers import SimpleRouter

from .views import KategoriyaViewSet, ShaharViewSet, UstaViewSet, XizmatimViewSet

router = SimpleRouter()
router.register('shaharlar', ShaharViewSet, basename='shahar')
router.register('kategoriyalar', KategoriyaViewSet, basename='kategoriya')
router.register('ustalar', UstaViewSet, basename='usta')
router.register('xizmatlarim', XizmatimViewSet, basename='xizmatim')

urlpatterns = router.urls
