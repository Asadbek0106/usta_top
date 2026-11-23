from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action, display

from .models import Kategoriya, Sevimli, Shahar, Usta, Xizmat


@admin.register(Shahar)
class ShaharAdmin(ModelAdmin):
    list_display = ('nomi', 'ustalar_soni')
    search_fields = ('nomi',)

    @display(description="Ustalar")
    def ustalar_soni(self, obj):
        return obj.ustalar.count()


@admin.register(Kategoriya)
class KategoriyaAdmin(ModelAdmin):
    list_display = ('nomi', 'slug', 'faol')
    list_editable = ('faol',)
    list_filter = ('faol',)
    search_fields = ('nomi',)
    prepopulated_fields = {'slug': ('nomi',)}


class XizmatInline(TabularInline):
    model = Xizmat
    extra = 0
    autocomplete_fields = ('kategoriya',)
    tab = True  # usta sahifasida alohida "Xizmatlar" tabi


@admin.register(Usta)
class UstaAdmin(ModelAdmin):
    list_display = ('usta', 'shahar', 'holat', 'reyting', 'sharhlar_soni', 'yaratilgan')
    list_filter = ('tasdiqlangan', 'shahar', 'kategoriyalar')
    list_filter_submit = True
    search_fields = ('user__telefon', 'user__first_name', 'user__last_name')
    autocomplete_fields = ('user', 'shahar')
    list_select_related = ('user', 'shahar')
    readonly_fields = ('yaratilgan', 'yangilangan')
    fieldsets = (
        (None, {'fields': ('user', 'shahar', 'tavsif', 'tasdiqlangan')}),
        ("Sanalar", {'fields': ('yaratilgan', 'yangilangan'), 'classes': ('collapse',)}),
    )
    inlines = [XizmatInline]
    actions = ['tasdiqlash', 'tasdiqni_bekor_qilish']
    actions_detail = ['tasdiqlash_sahifada']
    warn_unsaved_form = True

    def get_queryset(self, request):
        return super().get_queryset(request).reyting_bilan()

    @display(description="Usta", header=True, ordering='user__first_name')
    def usta(self, obj):
        return obj.user.get_full_name() or "Ismsiz", obj.user.telefon

    @display(description="Holat", ordering='tasdiqlangan', label={
        "Tasdiqlangan": 'success',
        "Tasdiq kutmoqda": 'warning',
    })
    def holat(self, obj):
        return "Tasdiqlangan" if obj.tasdiqlangan else "Tasdiq kutmoqda"

    @display(description="Reyting", ordering='reyting')
    def reyting(self, obj):
        return f"★ {obj.reyting:.1f}" if obj.reyting else '—'

    @display(description="Sharhlar", ordering='sharhlar_soni')
    def sharhlar_soni(self, obj):
        return obj.sharhlar_soni

    @action(description="Tanlanganlarni tasdiqlash", icon='verified')
    def tasdiqlash(self, request, queryset):
        soni = queryset.filter(tasdiqlangan=False).update(tasdiqlangan=True)
        self.message_user(request, f"{soni} ta usta tasdiqlandi va katalogda ko'rinadi.", messages.SUCCESS)

    @action(description="Tasdiqni bekor qilish (katalogdan yashirish)", icon='block')
    def tasdiqni_bekor_qilish(self, request, queryset):
        soni = queryset.filter(tasdiqlangan=True).update(tasdiqlangan=False)
        self.message_user(request, f"{soni} ta usta katalogdan yashirildi.", messages.WARNING)

    @action(description="Tasdiqlash", icon='verified', url_path='tasdiqlash')
    def tasdiqlash_sahifada(self, request, object_id):
        usta = Usta.objects.get(pk=object_id)
        if usta.tasdiqlangan:
            self.message_user(request, "Bu usta allaqachon tasdiqlangan.", messages.INFO)
        else:
            Usta.objects.filter(pk=object_id).update(tasdiqlangan=True)
            self.message_user(request, f"{usta} tasdiqlandi va katalogda ko'rinadi.", messages.SUCCESS)
        return redirect(reverse('admin:ustalar_usta_change', args=[object_id]))


@admin.register(Sevimli)
class SevimliAdmin(ModelAdmin):
    list_display = ('user', 'usta', 'yaratilgan')
    list_select_related = ('user', 'usta__user')
    search_fields = ('user__telefon', 'usta__user__telefon')
    autocomplete_fields = ('user', 'usta')
