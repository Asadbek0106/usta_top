from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.ustalar.models import Kategoriya, Usta

from . import services
from .models import Ariza, ArizaTarixi, Sharh


class SharhSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sharh
        fields = ('id', 'baho', 'matn', 'usta_javobi', 'javob_vaqti', 'yaratilgan')
        read_only_fields = ('usta_javobi', 'javob_vaqti')


class SharhJavobSerializer(serializers.Serializer):
    matn = serializers.CharField(max_length=2000, trim_whitespace=True)


class ArizaTarixiSerializer(serializers.ModelSerializer):
    eski_status_nomi = serializers.SerializerMethodField()
    yangi_status_nomi = serializers.CharField(source='get_yangi_status_display', read_only=True)
    kim = serializers.StringRelatedField()

    class Meta:
        model = ArizaTarixi
        fields = ('id', 'eski_status', 'eski_status_nomi', 'yangi_status', 'yangi_status_nomi', 'kim', 'vaqt')

    def get_eski_status_nomi(self, obj) -> str | None:
        return obj.get_eski_status_display() if obj.eski_status else None


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
    tarix = ArizaTarixiSerializer(many=True, read_only=True)

    class Meta:
        model = Ariza
        fields = ('id', 'mijoz', 'usta', 'kategoriya', 'tavsif', 'manzil',
                  'status', 'status_nomi', 'kelishilgan_narx', 'sharh', 'tarix', 'yaratilgan')


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

    def create(self, validated_data):
        return services.ariza_yaratish(**validated_data)


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
