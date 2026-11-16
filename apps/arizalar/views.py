from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import Ariza
from .serializers import ArizaCreateSerializer, ArizaSerializer


class ArizaViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Ariza.objects.none()
        user = self.request.user
        return (
            Ariza.objects
            .filter(Q(mijoz=user) | Q(usta__user=user))
            .select_related('mijoz', 'usta__user', 'kategoriya', 'sharh')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return ArizaCreateSerializer
        return ArizaSerializer

    @extend_schema(responses={201: ArizaSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ariza = serializer.save()
        return Response(ArizaSerializer(ariza).data, status=status.HTTP_201_CREATED)