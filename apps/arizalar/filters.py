import django_filters

from .models import Ariza


class ArizaFilter(django_filters.FilterSet):
    class Rol:
        MIJOZ = 'mijoz'
        USTA = 'usta'

    status = django_filters.ChoiceFilter(choices=Ariza.Status.choices)
    rol = django_filters.ChoiceFilter(
        choices=[(Rol.MIJOZ, "Men yuborgan arizalar"), (Rol.USTA, "Menga kelgan arizalar")],
        method='filter_rol',
        label="Rol",
    )

    class Meta:
        model = Ariza
        fields = ['status', 'rol']

    def filter_rol(self, queryset, name, value):
        user = self.request.user
        if value == self.Rol.MIJOZ:
            return queryset.filter(mijoz=user)
        return queryset.filter(usta__user=user)
