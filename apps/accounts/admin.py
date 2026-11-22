from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserCreateForm, UserEditForm
from .models import TelefonTasdiq, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserCreateForm
    form = UserEditForm

    ordering = ('-date_joined',)
    list_display = ('telefon', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('telefon', 'first_name', 'last_name', 'email')

    fieldsets = (
        (None, {'fields': ('telefon', 'password')}),
        ("Shaxsiy ma'lumotlar", {'fields': ('first_name', 'last_name', 'email')}),
        ("Ruxsatlar", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ("Muhim sanalar", {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('telefon', 'usable_password', 'password1', 'password2'),
        }),
    )


@admin.register(TelefonTasdiq)
class TelefonTasdiqAdmin(admin.ModelAdmin):
    list_display = ('telefon', 'yaratilgan', 'urinishlar', 'ishlatilgan')
    list_filter = ('ishlatilgan',)
    search_fields = ('telefon',)
    # Kodlar faqat ko'rish uchun: admin ularni qo'lda yaratmaydi va o'zgartirmaydi
    readonly_fields = ('telefon', 'kod', 'chat_id', 'urinishlar', 'ishlatilgan', 'yaratilgan')

    def has_add_permission(self, request):
        return False
