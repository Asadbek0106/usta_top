from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.ustalar.models import Kategoriya, Usta

from . import services
from .models import Ariza, ArizaRasm, ArizaTarixi, Sharh


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
        fields = ('id', 'eski_status', 'eski_status_nomi', 'yangi_status', 'yangi_status_nomi', 'kim', 'izoh', 'vaqt')

    def get_eski_status_nomi(self, obj) -> str | None:
        return obj.get_eski_status_display() if obj.eski_status else None


class UstaQisqaSerializer(serializers.ModelSerializer):
    ism = serializers.CharField(source='user.get_full_name', read_only=True)
    telefon = serializers.CharField(source='user.telefon', read_only=True)

    class Meta:
        model = Usta
        fields = ('id', 'ism', 'telefon')


class ArizaRasmSerializer(serializers.ModelSerializer):
    # Nisbiy manzil (/media/...): frontend uni o'z domenidan so'raydi, proxy backendga uzatadi
    rasm = serializers.SerializerMethodField()

    class Meta:
        model = ArizaRasm
        fields = ('id', 'rasm')

    def get_rasm(self, obj) -> str:
        return obj.rasm.url


class ArizaSerializer(serializers.ModelSerializer):
    mijoz = serializers.StringRelatedField()
    usta = UstaQisqaSerializer(read_only=True)
    kategoriya = serializers.StringRelatedField()
    status_nomi = serializers.CharField(source='get_status_display', read_only=True)
    sharh = SharhSerializer(read_only=True)
    tarix = ArizaTarixiSerializer(many=True, read_only=True)
    rasmlar = ArizaRasmSerializer(many=True, read_only=True)

    class Meta:
        model = Ariza
        fields = ('id', 'mijoz', 'usta', 'kategoriya', 'tavsif', 'manzil', 'rasmlar',
                  'status', 'status_nomi', 'taklif_narx', 'taklif_izoh', 'kelishilgan_narx',
                  'sharh', 'tarix', 'yaratilgan')


class ArizaCreateSerializer(serializers.ModelSerializer):
    mijoz = serializers.HiddenField(default=serializers.CurrentUserDefault())
    usta = serializers.PrimaryKeyRelatedField(queryset=Usta.objects.faol())
    kategoriya = serializers.PrimaryKeyRelatedField(queryset=Kategoriya.objects.filter(faol=True))
    # multipart/form-data: bir nechta fayl bitta "rasmlar" nomi bilan yuboriladi
    rasmlar = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        max_length=settings.ARIZA_RASM_SONI,
        error_messages={'max_length': f"Ko'pi bilan {settings.ARIZA_RASM_SONI} ta rasm yuklash mumkin."},
    )

    class Meta:
        model = Ariza
        fields = ('id', 'mijoz', 'usta', 'kategoriya', 'tavsif', 'manzil', 'rasmlar')

    def validate_rasmlar(self, rasmlar):
        chegara = settings.ARIZA_RASM_HAJMI_MB
        for rasm in rasmlar:
            if rasm.size > chegara * 1024 * 1024:
                raise serializers.ValidationError(f"«{rasm.name}» juda katta: har bir rasm {chegara} MB dan oshmasin.")
        return rasmlar

    def validate(self, attrs):
        malumot = {k: v for k, v in attrs.items() if k != 'rasmlar'}
        try:
            Ariza(**malumot).clean()
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


class NarxTaklifSerializer(serializers.Serializer):
    """Usta ish uchun so'ragan narx (va ixtiyoriy izoh: "material narxi ichida", "2 kunda bitadi")."""

    narx = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    izoh = serializers.CharField(max_length=1000, required=False, allow_blank=True, trim_whitespace=True)


class NarxRozilikSerializer(serializers.Serializer):
    narx = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        help_text="Mijoz ekranda ko'rgan narx. Usta shu orada narxni o'zgartirgan bo'lsa, so'rov rad etiladi.",
    )


class NarxRadSerializer(serializers.Serializer):
    sabab = serializers.CharField(max_length=400, required=False, allow_blank=True, trim_whitespace=True)
