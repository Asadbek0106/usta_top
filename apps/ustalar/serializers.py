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


class XizmatimSerializer(XizmatSerializer):
    """Usta o'z xizmatlarini boshqarishi uchun (/xizmatlarim/)."""

    def validate(self, attrs):
        usta = self.context['request'].user.usta_profil
        kategoriya = attrs.get('kategoriya')
        if kategoriya is not None:
            takror = usta.xizmatlar.filter(kategoriya=kategoriya)
            if self.instance is not None:
                takror = takror.exclude(pk=self.instance.pk)
            if takror.exists():
                raise serializers.ValidationError(
                    {'kategoriya_id': "Bu kategoriyada sizda allaqachon xizmat bor."}
                )
        return attrs


class UstaListSerializer(serializers.ModelSerializer):
    ism = serializers.CharField(source='user.get_full_name', read_only=True)
    shahar = serializers.StringRelatedField()
    kategoriyalar = serializers.StringRelatedField(many=True)
    reyting = serializers.FloatField(read_only=True)
    sharhlar_soni = serializers.IntegerField(read_only=True)
    eng_arzon = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, default=None,
                                         help_text="Ustaning eng arzon xizmati qaysi narxdan boshlanadi")
    tajriba_yil = serializers.IntegerField(read_only=True, default=None, help_text="Eng katta tajriba, yil")
    # Kirgan foydalanuvchi shu ustani saqlab qo'yganmi (mehmon uchun doim false)
    sevimli = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Usta
        fields = ('id', 'ism', 'shahar', 'kategoriyalar', 'reyting', 'sharhlar_soni',
                  'eng_arzon', 'tajriba_yil', 'sevimli')


class UstaDetailSerializer(UstaListSerializer):
    telefon = serializers.CharField(source='user.telefon', read_only=True)
    shahar = ShaharSerializer(read_only=True)
    xizmatlar = XizmatSerializer(many=True, read_only=True)

    class Meta(UstaListSerializer.Meta):
        fields = ('id', 'ism', 'telefon', 'shahar', 'tavsif', 'xizmatlar',
                  'reyting', 'sharhlar_soni', 'sevimli', 'yaratilgan')


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


class UstaUpdateSerializer(serializers.ModelSerializer):
    """Usta o'z profilini tahrirlashi uchun. `tasdiqlangan` ataylab kiritilmagan."""

    class Meta:
        model = Usta
        fields = ('shahar', 'tavsif')


class OyStatistikaSerializer(serializers.Serializer):
    oy = serializers.CharField(help_text="YYYY-MM")
    nomi = serializers.CharField()
    arizalar = serializers.IntegerField()
    bajarildi = serializers.IntegerField()
    daromad = serializers.IntegerField()


class ShuOyStatistikaSerializer(serializers.Serializer):
    arizalar = serializers.IntegerField()
    bajarildi = serializers.IntegerField()
    daromad = serializers.IntegerField()


class KategoriyaStatistikaSerializer(serializers.Serializer):
    nomi = serializers.CharField()
    soni = serializers.IntegerField()


class UstaStatistikaSerializer(serializers.Serializer):
    """Faqat hujjat (Swagger) uchun: javob services.usta_statistikasi() dan tayyor holda keladi."""

    jami_arizalar = serializers.IntegerField()
    holatlar = serializers.DictField(child=serializers.IntegerField())
    daromad = serializers.IntegerField(help_text="Bajarilgan arizalarning kelishilgan narxlari yig'indisi, so'm")
    bajarish_foizi = serializers.IntegerField(allow_null=True)
    shu_oy = ShuOyStatistikaSerializer()
    oylar = OyStatistikaSerializer(many=True)
    reyting = serializers.FloatField(allow_null=True)
    sharhlar_soni = serializers.IntegerField()
    baholar = serializers.DictField(child=serializers.IntegerField())
    kategoriyalar = KategoriyaStatistikaSerializer(many=True)
