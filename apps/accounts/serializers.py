from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import User, telefon_validator


class TelefonField(serializers.CharField):
    """Raqamdagi bo'sh joy va chiziqchalarni olib tashlaydi, keyin validatsiya qiladi."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        return User.objects.normalize_telefon(value)


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

    class Meta:
        model = User
        fields = ('id', 'telefon', 'first_name', 'last_name', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': "Parollar mos kelmadi."})
        try:
            validate_password(attrs['password'], user=User(telefon=attrs['telefon']))
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    usta_mi = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'telefon', 'first_name', 'last_name', 'email', 'usta_mi', 'date_joined')
        read_only_fields = ('telefon', 'date_joined')

    def get_usta_mi(self, obj):
        return hasattr(obj, 'usta_profil')