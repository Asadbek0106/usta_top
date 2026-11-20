from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.ustalar.models import Kategoriya, Usta

from .models import Ariza, Sharh


class SharhSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sharh
        fields = ('id', 'baho', 'matn', 'yaratilgan')


class UstaQisqaSerializer(serializers.ModelSerializer):
    ism = serializers.CharField(source='user.get_full_name', read_only=True)
    telefon = serializers.CharField(source='user.telefon', read_only=True)

    class Meta:
        model = Usta
        fields = ('id', 'ism', 'telefon')


class ArizaSerializer(serializers.ModelSerializer):
    mijoz = serializers.StringRelatedField()
    usta = UstaQisqaSerializer(read_only=True)
    kategoriya = serializers.StringRelatedField()
    status_nomi = serializers.CharField(source='get_status_display', read_only=True)
    sharh = SharhSerializer(read_only=True)

    class Meta:
        model = Ariza
        fields = ('id', 'mijoz', 'usta', 'kategoriya', 'tavsif', 'manzil',
                  'status', 'status_nomi', 'kelishilgan_narx', 'sharh', 'yaratilgan')


class ArizaCreateSerializer(serializers.ModelSerializer):
    mijoz = serializers.HiddenField(default=serializers.CurrentUserDefault())
    usta = serializers.PrimaryKeyRelatedField(queryset=Usta.objects.faol())
    kategoriya = serializers.PrimaryKeyRelatedField(queryset=Kategoriya.objects.filter(faol=True))

    class Meta:
        model = Ariza
        fields = ('id', 'mijoz', 'usta', 'kategoriya', 'tavsif', 'manzil')

    def validate(self, attrs):
        try:
            Ariza(**attrs).clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(serializers.as_serializer_error(e)) from e
        return attrs


class ArizaUpdateSerializer(serializers.ModelSerializer):
    """Mijoz arizani faqat "yangi" holatida tahrirlay oladi.
    status, usta va kelishilgan_narx ataylab kiritilmagan: ular faqat action'lar orqali o'zgaradi."""

    class Meta:
        model = Ariza
        fields = ('tavsif', 'manzil')

    def validate(self, attrs):
        if self.instance.status != Ariza.Status.YANGI:
            raise serializers.ValidationError("Faqat yangi arizani tahrirlash mumkin.")
        return attrs


class QabulSerializer(serializers.Serializer):
    kelishilgan_narx = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
    )
