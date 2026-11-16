from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema

from apps.arizalar.models import Sharh
from apps.arizalar.serializers import SharhSerializer

from .permissions import IsUsta

from .models import Kategoriya, Shahar, Usta
from .serializers import (
    KategoriyaSerializer,
    ShaharSerializer,
    UstaCreateSerializer,
    UstaDetailSerializer,
    UstaListSerializer,
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


    @extend_schema(responses=UstaDetailSerializer)
    @action(detail=False, methods=['get'], permission_classes=[IsUsta])
    def men(self, request):
        usta = (
            Usta.objects.reyting_bilan()
            .select_related('user', 'shahar')
            .prefetch_related('xizmatlar__kategoriya')
            .get(user=request.user)
        )
        return Response(UstaDetailSerializer(usta).data)