from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class TelefonTozalashMixin:
    """Admin formalarida telefondagi bo'sh joy va chiziqchalarni olib tashlaydi."""

    def clean_telefon(self):
        return User.objects.normalize_telefon(self.cleaned_data['telefon'])


class UserCreateForm(TelefonTozalashMixin, AdminUserCreationForm):
    # Tozalashdan oldin "+998 90 123-45-67" (17 belgi) ham qabul qilinishi uchun
    telefon = forms.CharField(label="Telefon raqam", max_length=20)

    class Meta:
        model = User
        fields = ('telefon',)


class UserEditForm(TelefonTozalashMixin, UserChangeForm):
    telefon = forms.CharField(label="Telefon raqam", max_length=20)

    class Meta:
        model = User
        fields = '__all__'
