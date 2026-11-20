from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from . import services
from .filters import ArizaFilter
from .models import Ariza
from .permissions import IsArizaMijozi, IsArizaUstasi
from .serializers import (
    ArizaCreateSerializer,
    ArizaSerializer,
    ArizaUpdateSerializer,
    QabulSerializer,
    SharhSerializer,
)


class ArizaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']  # PUT va DELETE yo'q
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ArizaFilter
    ordering_fields = ['yaratilgan', 'yangilangan']
    ordering = ['-yaratilgan']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        user = self.request.user
        return (
            Ariza.objects
            .filter(Q(mijoz=user) | Q(usta__user=user))
            .select_related('mijoz', 'usta__user', 'kategoriya', 'sharh')
        )

    def get_throttles(self):
        # Spamdan himoya: yangi ariza yuborish alohida, qattiqroq cheklangan
        if self.action == 'create':
            self.throttle_scope = 'ariza'
            return [*super().get_throttles(), ScopedRateThrottle()]
        return super().get_throttles()

    def get_permissions(self):
        if self.action == 'partial_update':
            return [IsAuthenticated(), IsArizaMijozi()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return ArizaCreateSerializer
        if self.action == 'partial_update':
            return ArizaUpdateSerializer
        return ArizaSerializer

    def _javob(self, ariza, status_code=status.HTTP_200_OK):
        return Response(ArizaSerializer(self.get_queryset().get(pk=ariza.pk)).data, status=status_code)

    @extend_schema(responses={201: ArizaSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = serializer.save()
        return self._javob(ariza, status.HTTP_201_CREATED)

    @extend_schema(request=ArizaUpdateSerializer, responses=ArizaSerializer)
    def partial_update(self, request, *args, **kwargs):
        ariza = self.get_object()
        serializer = self.get_serializer(ariza, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return self._javob(ariza)

    @extend_schema(request=QabulSerializer, responses=ArizaSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArizaUstasi])
    def qabul(self, request, pk=None):
        ariza = self.get_object()
        serializer = QabulSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = services.qabul_qilish(ariza, **serializer.validated_data)
        return self._javob(ariza)

    @extend_schema(request=None, responses=ArizaSerializer)
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArizaUstasi])
    def bajarildi(self, request, pk=None):
        ariza = services.bajarildi_deb_belgilash(self.get_object())
        return self._javob(ariza)

    @extend_schema(request=None, responses=ArizaSerializer)
    @action(detail=True, methods=['post'])
    def bekor(self, request, pk=None):
        # get_queryset faqat mijoz yoki ustaning arizalarini qaytaradi,
        # shuning uchun bekor qilishni faqat shu ikkisi qila oladi.
        ariza = services.bekor_qilish(self.get_object())
        return self._javob(ariza)

    @extend_schema(request=SharhSerializer, responses={201: SharhSerializer})
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsArizaMijozi])
    def sharh(self, request, pk=None):
        ariza = self.get_object()
        serializer = SharhSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sharh = services.sharh_qoldirish(ariza, **serializer.validated_data)
        return Response(SharhSerializer(sharh).data, status=status.HTTP_201_CREATED)
