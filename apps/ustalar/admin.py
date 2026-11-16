from django.contrib import admin

from .models import Kategoriya, Shahar, Usta, Xizmat


@admin.register(Shahar)
class ShaharAdmin(admin.ModelAdmin):
    search_fields = ('nomi',)


@admin.register(Kategoriya)
class KategoriyaAdmin(admin.ModelAdmin):
    list_display = ('nomi', 'slug', 'faol')
    list_editable = ('faol',)
    list_filter = ('faol',)
    search_fields = ('nomi',)
    prepopulated_fields = {'slug': ('nomi',)}


class XizmatInline(admin.TabularInline):
    model = Xizmat
    extra = 1
    autocomplete_fields = ('kategoriya',)


@admin.register(Usta)
class UstaAdmin(admin.ModelAdmin):
    list_display = ('user', 'shahar', 'tasdiqlangan', 'reyting', 'sharhlar_soni', 'yaratilgan')
    list_filter = ('tasdiqlangan', 'shahar', 'kategoriyalar')
    list_editable = ('tasdiqlangan',)
    search_fields = ('user__telefon', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'shahar')
    list_select_related = ('user', 'shahar')
    readonly_fields = ('yaratilgan', 'yangilangan')
    inlines = [XizmatInline]
    actions = ['tasdiqlash']

    def get_queryset(self, request):
        return super().get_queryset(request).reyting_bilan()

    @admin.display(description='Reyting', ordering='reyting')
    def reyting(self, obj):
        return round(obj.reyting, 1) if obj.reyting else '—'

    @admin.display(description='Sharhlar', ordering='sharhlar_soni')
    def sharhlar_soni(self, obj):
        return obj.sharhlar_soni

    @admin.action(description="Tanlangan ustalarni tasdiqlash")
    def tasdiqlash(self, request, queryset):
        soni = queryset.update(tasdiqlangan=True)
        self.message_user(request, f"{soni} ta usta tasdiqlandi.")