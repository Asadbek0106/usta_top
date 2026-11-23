from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import TelefonTasdiq, User, telefon_validator


class TelefonField(serializers.CharField):
    """Raqamdagi bo'sh joy va chiziqchalarni olib tashlaydi, keyin validatsiya qiladi."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return User.objects.normalize_telefon(value)


def tasdiq_kodini_tekshir(telefon, kod, maqsad):
    """Telegram bot bergan kodni tekshiradi va TelefonTasdiq yozuvini qaytaradi (xato bo'lsa ValidationError)."""
    if not kod:
        raise serializers.ValidationError({'kod': "Telegram botdan olingan kodni kiriting."})
    tasdiq = TelefonTasdiq.objects.filter(
        telefon=telefon,
        maqsad=maqsad,
        ishlatilgan=False,
        yaratilgan__gte=timezone.now() - settings.TASDIQ_KOD_MUDDATI,
    ).first()
    if tasdiq is None:
        raise serializers.ValidationError(
            {'kod': "Bu raqam uchun amaldagi kod yo'q. Botga raqamingizni yuborib, yangi kod oling."},
        )
    if tasdiq.urinishlar >= settings.TASDIQ_KOD_URINISHLAR:
        raise serializers.ValidationError({'kod': "Urinishlar tugadi. Botdan yangi kod oling."})
    if tasdiq.kod != kod:
        # Kodni tanlab topishning oldini olish: har bir xato urinish hisoblanadi
        TelefonTasdiq.objects.filter(pk=tasdiq.pk).update(urinishlar=F('urinishlar') + 1)
        raise serializers.ValidationError({'kod': "Kod noto'g'ri."})
    return tasdiq


class RegisterSerializer(serializers.ModelSerializer):
    telefon = TelefonField(
        max_length=13,
        validators=[
            telefon_validator,
            UniqueValidator(queryset=User.objects.all(), message="Bu raqam allaqachon ro'yxatdan o'tgan."),
        ],
    )
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    # Telegram bot bergan tasdiqlash kodi (TELEFON_TASDIQLASH yoqilgan bo'lsa majburiy)
    kod = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=6)

    class Meta:
        model = User
        fields = ('id', 'telefon', 'first_name', 'last_name', 'password', 'password2', 'kod')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': "Parollar mos kelmadi."})
        try:
            validate_password(attrs['password'], user=User(telefon=attrs['telefon']))
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)}) from e
        if settings.TELEFON_TASDIQLASH:
            attrs['tasdiq'] = tasdiq_kodini_tekshir(
                attrs['telefon'], attrs.get('kod', '').strip(), TelefonTasdiq.Maqsad.ROYXAT,
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data.pop('kod', None)
        tasdiq = validated_data.pop('tasdiq', None)
        user = User.objects.create_user(**validated_data)
        if tasdiq is not None:
            TelefonTasdiq.objects.filter(pk=tasdiq.pk).update(ishlatilgan=True)
        return user


class ParolTiklashSerializer(serializers.Serializer):
    """Unutilgan parolni Telegram bot bergan kod bilan yangilash."""

    telefon = TelefonField(max_length=13, validators=[telefon_validator])
    kod = serializers.CharField(max_length=6, trim_whitespace=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': "Parollar mos kelmadi."})
        user = User.objects.filter(telefon=attrs['telefon'], is_active=True).first()
        if user is None:
            # Bot bu raqamga tiklash kodini bermagan bo'ladi, shuning uchun xabar kod haqida
            raise serializers.ValidationError(
                {'kod': "Bu raqam uchun amaldagi kod yo'q. Botga raqamingizni yuborib, yangi kod oling."},
            )
        try:
            validate_password(attrs['password'], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)}) from e
        attrs['tasdiq'] = tasdiq_kodini_tekshir(attrs['telefon'], attrs['kod'], TelefonTasdiq.Maqsad.TIKLASH)
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    usta_mi = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'telefon', 'first_name', 'last_name', 'email', 'usta_mi', 'date_joined')
        read_only_fields = ('telefon', 'date_joined')

    def get_usta_mi(self, obj) -> bool:
        return hasattr(obj, 'usta_profil')


class LoginSerializer(TokenObtainPairSerializer):
    """Kirishda ham telefon ro'yxatdan o'tishdagi kabi tozalanadi."""

    def validate(self, attrs):
        attrs[self.username_field] = User.objects.normalize_telefon(attrs[self.username_field])
        return super().validate(attrs)
