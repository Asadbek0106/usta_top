from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.arizalar.models import Sharh
from apps.arizalar.serializers import SharhSerializer
from apps.core.exceptions import BiznesXatosi

from .models import Kategoriya, Shahar, Usta, Xizmat
from .permissions import IsUsta
from .serializers import (
    KategoriyaSerializer,
    ShaharSerializer,
    UstaCreateSerializer,
    UstaDetailSerializer,
    UstaListSerializer,
    UstaUpdateSerializer,
    XizmatimSerializer,
)


class ShaharViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Shahar.objects.all()
    serializer_class = ShaharSerializer
    permission_classes = [AllowAny]


class KategoriyaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Kategoriya.objects.filter(faol=True)
    serializer_class = KategoriyaSerializer
    permission_classes = [AllowAny]


class UstaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Usta.objects.faol().reyting_bilan().select_related('user', 'shahar')
        if self.action == 'retrieve':
            return qs.prefetch_related('xizmatlar__kategoriya')
        return qs.prefetch_related('kategoriyalar')

    def get_serializer_class(self):
        if self.action == 'create':
            return UstaCreateSerializer
        if self.action == 'retrieve':
            return UstaDetailSerializer
        return UstaListSerializer

    @extend_schema(responses=SharhSerializer(many=True))
    @action(detail=True, methods=['get'])
    def sharhlar(self, request, pk=None):
        usta = self.get_object()
        sharhlar = Sharh.objects.filter(ariza__usta=usta)
        return Response(SharhSerializer(sharhlar, many=True).data)

    @extend_schema(methods=['GET'], responses=UstaDetailSerializer)
    @extend_schema(methods=['PATCH'], request=UstaUpdateSerializer, responses=UstaDetailSerializer)
    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsUsta])
    def men(self, request):
        """Ustaning o'z profili: ko'rish (GET) va tahrirlash (PATCH)."""
        usta = request.user.usta_profil
        if request.method == 'PATCH':
            serializer = UstaUpdateSerializer(usta, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        usta = (
            Usta.objects.reyting_bilan()
            .select_related('user', 'shahar')
            .prefetch_related('xizmatlar__kategoriya')
            .get(pk=usta.pk)
        )
        return Response(UstaDetailSerializer(usta).data)


class XizmatimViewSet(viewsets.ModelViewSet):
    """Usta o'z xizmatlarini (kategoriya, narx, tajriba) boshqaradi."""

    serializer_class = XizmatimSerializer
    permission_classes = [IsAuthenticated, IsUsta]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Xizmat.objects.none()
        return Xizmat.objects.filter(usta__user=self.request.user).select_related('kategoriya')

    def perform_create(self, serializer):
        serializer.save(usta=self.request.user.usta_profil)

    def perform_destroy(self, instance):
        if instance.usta.xizmatlar.count() <= 1:
            raise BiznesXatosi("Ustada kamida bitta xizmat qolishi kerak.", code='oxirgi_xizmat')
        instance.delete()
