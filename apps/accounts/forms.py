from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import User


class UserCreateForm(AdminUserCreationForm):
    class Meta:
        model = User
        fields = ('telefon',)


class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'