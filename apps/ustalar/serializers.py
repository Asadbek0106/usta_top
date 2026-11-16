from django.db import transaction
from rest_framework import serializers

from .models import Kategoriya, Shahar, Usta, Xizmat


class ShaharSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shahar
        fields = ('id', 'nomi')


class KategoriyaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kategoriya
        fields = ('id', 'nomi', 'slug')


class XizmatSerializer(serializers.ModelSerializer):
    kategoriya = KategoriyaSerializer(read_only=True)
    kategoriya_id = serializers.PrimaryKeyRelatedField(
        queryset=Kategoriya.objects.filter(faol=True),
        source='kategoriya',
        write_only=True,
    )

    class Meta:
        model = Xizmat
        fields = ('id', 'kategoriya', 'kategoriya_id', 'narx_dan', 'tajriba')
        extra_kwargs = {'narx_dan': {'min_value': 0}}


class UstaListSerializer(serializers.ModelSerializer):
    ism = serializers.CharField(source='user.get_full_name', read_only=True)
    shahar = serializers.StringRelatedField()
    kategoriyalar = serializers.StringRelatedField(many=True)
    reyting = serializers.FloatField(read_only=True)
    sharhlar_soni = serializers.IntegerField(read_only=True)

    class Meta:
        model = Usta
        fields = ('id', 'ism', 'shahar', 'kategoriyalar', 'reyting', 'sharhlar_soni')


class UstaDetailSerializer(UstaListSerializer):
    telefon = serializers.CharField(source='user.telefon', read_only=True)
    shahar = ShaharSerializer(read_only=True)
    xizmatlar = XizmatSerializer(many=True, read_only=True)

    class Meta(UstaListSerializer.Meta):
        fields = ('id', 'ism', 'telefon', 'shahar', 'tavsif', 'xizmatlar',
                  'reyting', 'sharhlar_soni', 'yaratilgan')


class UstaCreateSerializer(serializers.ModelSerializer):
    xizmatlar = XizmatSerializer(many=True)

    class Meta:
        model = Usta
        fields = ('id', 'shahar', 'tavsif', 'xizmatlar')

    def validate_xizmatlar(self, value):
        if not value:
            raise serializers.ValidationError("Kamida bitta xizmat ko'rsating.")
        kategoriya_idlar = [x['kategoriya'].id for x in value]
        if len(kategoriya_idlar) != len(set(kategoriya_idlar)):
            raise serializers.ValidationError("Bitta kategoriya ikki marta ko'rsatilgan.")
        return value

    def validate(self, attrs):
        user = self.context['request'].user
        if Usta.objects.filter(user=user).exists():
            raise serializers.ValidationError("Sizda allaqachon usta profili bor.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        xizmatlar = validated_data.pop('xizmatlar')
        usta = Usta.objects.create(user=self.context['request'].user, **validated_data)
        Xizmat.objects.bulk_create([Xizmat(usta=usta, **x) for x in xizmatlar])
        return usta