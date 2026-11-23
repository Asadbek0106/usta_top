from django import forms
from unfold.forms import UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminTextInputWidget

from .models import User


class TelefonTozalashMixin:
    """Admin formalarida telefondagi bo'sh joy va chiziqchalarni olib tashlaydi."""

    def clean_telefon(self):
        return User.objects.normalize_telefon(self.cleaned_data['telefon'])


class UserCreateForm(TelefonTozalashMixin, UserCreationForm):
    # Tozalashdan oldin "+998 90 123-45-67" (17 belgi) ham qabul qilinishi uchun
    telefon = forms.CharField(label="Telefon raqam", max_length=20, widget=UnfoldAdminTextInputWidget)

    class Meta:
        model = User
        fields = ('telefon', 'first_name', 'last_name')


class UserEditForm(TelefonTozalashMixin, UserChangeForm):
    telefon = forms.CharField(label="Telefon raqam", max_length=20, widget=UnfoldAdminTextInputWidget)

    class Meta:
        model = User
        fields = '__all__'
