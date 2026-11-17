import django_filters
from django.db.models import Exists, OuterRef

from .models import Usta, Xizmat


class UstaFilter(django_filters.FilterSet):
    shahar = django_filters.NumberFilter(field_name='shahar_id', label="Shahar ID")
    kategoriya = django_filters.CharFilter(method='filter_xizmat', label="Kategoriya slug'i (masalan: santexnik)")
    narx_max = django_filters.NumberFilter(method='filter_xizmat', label="Eng ko'pi bilan shu narxdan boshlanadigan xizmat")
    reyting_min = django_filters.NumberFilter(field_name='reyting', lookup_expr='gte', label="Minimal reyting")

    class Meta:
        model = Usta
        fields = ['shahar', 'kategoriya', 'narx_max', 'reyting_min']

    def filter_xizmat(self, queryset, name, value):
        # Bu metod faqat bir marta, filter_queryset ichida ishlatiladi (pastga qarang)
        return queryset

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        kategoriya = self.form.cleaned_data.get('kategoriya')
        narx_max = self.form.cleaned_data.get('narx_max')
        if not kategoriya and narx_max is None:
            return queryset

        # Kategoriya va narx BITTA xizmatga tegishli bo'lishi kerak:
        # "santexnik xizmati 100 000 so'mgacha", "biror xizmati santexnik, boshqasi arzon" emas.
        xizmatlar = Xizmat.objects.filter(usta=OuterRef('pk'))
        if kategoriya:
            xizmatlar = xizmatlar.filter(kategoriya__slug=kategoriya)
        if narx_max is not None:
            xizmatlar = xizmatlar.filter(narx_dan__lte=narx_max)
        return queryset.filter(Exists(xizmatlar))
