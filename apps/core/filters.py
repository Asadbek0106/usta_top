from django.db.models import F
from rest_framework.filters import OrderingFilter


class NullsLastOrderingFilter(OrderingFilter):
    """Tartiblashda NULL qiymatlarni (masalan, hali sharhi yo'q ustaning reytingi)
    yo'nalishdan qat'i nazar har doim oxiriga qo'yadi.

    Oddiy OrderingFilter'da PostgreSQL `?ordering=-reyting` bo'lganda NULL'larni
    birinchi qo'yadi: reytingi yo'q ustalar ro'yxat boshiga chiqib qoladi.
    """

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset
        ifodalar = []
        for maydon in ordering:
            if maydon.startswith('-'):
                ifodalar.append(F(maydon[1:]).desc(nulls_last=True))
            else:
                ifodalar.append(F(maydon).asc(nulls_last=True))
        return queryset.order_by(*ifodalar, 'pk')
