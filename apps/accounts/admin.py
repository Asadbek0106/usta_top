from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework_simplejwt.token_blacklist.admin import (
    BlacklistedTokenAdmin as BaseBlacklistedTokenAdmin,
)
from rest_framework_simplejwt.token_blacklist.admin import (
    OutstandingTokenAdmin as BaseOutstandingTokenAdmin,
)
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from unfold.admin import ModelAdmin
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm

from .forms import UserCreateForm, UserEditForm
from .models import TelefonTasdiq, User


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    add_form = UserCreateForm
    form = UserEditForm
    change_password_form = AdminPasswordChangeForm

    ordering = ('-date_joined',)
    list_display = ('foydalanuvchi', 'rol', 'faol', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    list_filter_submit = True
    search_fields = ('telefon', 'first_name', 'last_name', 'email')

    fieldsets = (
        (None, {'fields': ('telefon', 'password')}),
        ("Shaxsiy ma'lumotlar", {'fields': ('first_name', 'last_name', 'email')}),
        ("Ruxsatlar", {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ("Muhim sanalar", {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telefon', 'first_name', 'last_name', 'usable_password', 'password1', 'password2'),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usta_profil')

    @display(description="Foydalanuvchi", header=True, ordering='first_name')
    def foydalanuvchi(self, obj):
        return obj.get_full_name() or "Ismsiz", obj.telefon

    @display(description="Rol", label={"Admin": 'danger', "Xodim": 'warning', "Usta": 'primary', "Mijoz": 'info'})
    def rol(self, obj):
        if obj.is_superuser:
            return "Admin"
        if obj.is_staff:
            return "Xodim"
        if hasattr(obj, 'usta_profil'):
            return "Usta"
        return "Mijoz"

    @display(description="Faol", boolean=True, ordering='is_active')
    def faol(self, obj):
        return obj.is_active


@admin.register(TelefonTasdiq)
class TelefonTasdiqAdmin(ModelAdmin):
    list_display = ('telefon', 'maqsad_belgi', 'yaratilgan', 'urinishlar', 'ishlatilgan')
    list_filter = ('maqsad', 'ishlatilgan')
    search_fields = ('telefon',)
    # Kodlar faqat ko'rish uchun: admin ularni qo'lda yaratmaydi va o'zgartirmaydi
    readonly_fields = ('telefon', 'maqsad', 'kod', 'chat_id', 'urinishlar', 'ishlatilgan', 'yaratilgan')

    def has_add_permission(self, request):
        return False

    @display(description="Maqsad", ordering='maqsad', label={
        TelefonTasdiq.Maqsad.ROYXAT.label: 'info',
        TelefonTasdiq.Maqsad.TIKLASH.label: 'warning',
    })
    def maqsad_belgi(self, obj):
        return obj.get_maqsad_display()


# Django va simplejwt o'z admin klasslarini ro'yxatdan o'tkazgan: ularni unfold uslubidagisiga almashtiramiz
admin.site.unregister(Group)
admin.site.unregister(OutstandingToken)
admin.site.unregister(BlacklistedToken)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(OutstandingToken)
class OutstandingTokenAdmin(BaseOutstandingTokenAdmin, ModelAdmin):
    pass


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(BaseBlacklistedTokenAdmin, ModelAdmin):
    pass
