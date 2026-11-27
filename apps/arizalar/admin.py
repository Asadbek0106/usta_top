from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.decorators import display

from .models import Ariza, ArizaRasm, ArizaTarixi, Sharh

STATUS_RANGLARI = {
    Ariza.Status.YANGI.label: 'info',
    Ariza.Status.NARX_TAKLIF.label: 'primary',
    Ariza.Status.QABUL.label: 'warning',
    Ariza.Status.BAJARILDI.label: 'success',
    Ariza.Status.BEKOR.label: 'default',
}


class SharhInline(StackedInline):
    model = Sharh
    extra = 0
    tab = True
    readonly_fields = ('javob_vaqti',)


class ArizaRasmInline(TabularInline):
    model = ArizaRasm
    extra = 0
    tab = True
    fields = ('korinish', 'rasm', 'yaratilgan')
    readonly_fields = ('korinish', 'yaratilgan')

    @display(description="Ko'rinish")
    def korinish(self, obj):
        if not obj.rasm:
            return '—'
        return format_html(
            '<a href="{0}" target="_blank" rel="noopener"><img src="{0}" alt="" '
            'style="height:72px;width:96px;object-fit:cover;border-radius:6px"></a>',
            obj.rasm.url,
        )


class ArizaTarixiInline(TabularInline):
    model = ArizaTarixi
    extra = 0
    tab = True
    # Tarix faqat ko'rish uchun: uni ilova o'zi yozadi, qo'lda o'zgartirilmaydi
    fields = ('vaqt', 'eski_status', 'yangi_status', 'kim', 'izoh')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Ariza)
class ArizaAdmin(ModelAdmin):
    list_display = ('raqam', 'mijoz', 'usta', 'kategoriya', 'holat', 'narx', 'yaratilgan')
    list_filter = ('status', 'kategoriya')
    list_filter_submit = True
    search_fields = ('mijoz__telefon', 'usta__user__telefon', 'manzil', 'tavsif')
    autocomplete_fields = ('mijoz', 'usta', 'kategoriya')
    list_select_related = ('mijoz', 'usta__user', 'kategoriya')
    readonly_fields = ('yaratilgan', 'yangilangan')
    fieldsets = (
        (None, {'fields': ('mijoz', 'usta', 'kategoriya', 'status', 'kelishilgan_narx')}),
        ("Usta taklifi", {'fields': ('taklif_narx', 'taklif_izoh')}),
        ("Ish haqida", {'fields': ('tavsif', 'manzil')}),
        ("Sanalar", {'fields': ('yaratilgan', 'yangilangan'), 'classes': ('collapse',)}),
    )
    date_hierarchy = 'yaratilgan'
    inlines = [ArizaRasmInline, ArizaTarixiInline, SharhInline]
    warn_unsaved_form = True

    @display(description="№", ordering='pk')
    def raqam(self, obj):
        return f"#{obj.pk}"

    @display(description="Holat", ordering='status', label=STATUS_RANGLARI)
    def holat(self, obj):
        return obj.get_status_display()

    @display(description="Narx", ordering='kelishilgan_narx')
    def narx(self, obj):
        if obj.kelishilgan_narx is None:
            return '—'
        return f"{int(obj.kelishilgan_narx):,} so'm".replace(',', ' ')


@admin.register(Sharh)
class SharhAdmin(ModelAdmin):
    list_display = ('ariza', 'yulduzlar', 'matn_qisqa', 'javob_berilgan', 'yaratilgan')
    list_filter = ('baho',)
    search_fields = ('matn', 'usta_javobi', 'ariza__usta__user__telefon')
    list_select_related = ('ariza__usta__user', 'ariza__mijoz')
    autocomplete_fields = ('ariza',)
    readonly_fields = ('javob_vaqti',)

    @display(description="Baho", ordering='baho')
    def yulduzlar(self, obj):
        return '★' * obj.baho + '☆' * (5 - obj.baho)

    @display(description="Izoh")
    def matn_qisqa(self, obj):
        return (obj.matn[:60] + '…') if len(obj.matn) > 60 else (obj.matn or '—')

    @display(description="Usta javob bergan", boolean=True)
    def javob_berilgan(self, obj):
        return bool(obj.usta_javobi)
