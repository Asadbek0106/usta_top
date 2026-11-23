from django.contrib import admin

from .models import Ariza, ArizaTarixi, Sharh


class SharhInline(admin.StackedInline):
    model = Sharh
    extra = 0


class ArizaTarixiInline(admin.TabularInline):
    model = ArizaTarixi
    extra = 0
    # Tarix faqat ko'rish uchun: uni ilova o'zi yozadi, qo'lda o'zgartirilmaydi
    readonly_fields = ('eski_status', 'yangi_status', 'kim', 'vaqt')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ariza)
class ArizaAdmin(admin.ModelAdmin):
    list_display = ('id', 'mijoz', 'usta', 'kategoriya', 'status', 'kelishilgan_narx', 'yaratilgan')
    list_filter = ('status', 'kategoriya')
    search_fields = ('mijoz__telefon', 'usta__user__telefon', 'manzil')
    autocomplete_fields = ('mijoz', 'usta', 'kategoriya')
    list_select_related = ('mijoz', 'usta__user', 'kategoriya')
    readonly_fields = ('yaratilgan', 'yangilangan')
    date_hierarchy = 'yaratilgan'
    inlines = [SharhInline, ArizaTarixiInline]


@admin.register(Sharh)
class SharhAdmin(admin.ModelAdmin):
    list_display = ('ariza', 'baho', 'javob_berilgan', 'yaratilgan')
    list_filter = ('baho',)
    list_select_related = ('ariza__usta__user',)
    autocomplete_fields = ('ariza',)

    @admin.display(boolean=True, description="Usta javob bergan")
    def javob_berilgan(self, obj):
        return bool(obj.usta_javobi)
