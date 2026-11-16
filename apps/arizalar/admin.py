from django.contrib import admin

from .models import Ariza, Sharh


class SharhInline(admin.StackedInline):
    model = Sharh
    extra = 0


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mijoz', 'usta', 'kategoriya', 'status', 'kelishilgan_narx', 'yaratilgan')
    list_filter = ('status', 'kategoriya')
    search_fields = ('mijoz__telefon', 'usta__user__telefon', 'manzil')
    autocomplete_fields = ('mijoz', 'usta', 'kategoriya')
    list_select_related = ('mijoz', 'usta__user', 'kategoriya')
    readonly_fields = ('yaratilgan', 'yangilangan')
    date_hierarchy = 'yaratilgan'
    inlines = [SharhInline]


@admin.register(Sharh)
class SharhAdmin(admin.ModelAdmin):
    list_display = ('ariza', 'baho', 'yaratilgan')
    list_filter = ('baho',)
    list_select_related = ('ariza__usta__user',)
    autocomplete_fields = ('ariza',)
