from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, telefon, password, **extra_fields):
        if not telefon:
            raise ValueError("Telefon raqam kiritilishi shart")
        telefon = self.normalize_telefon(telefon)
        user = self.model(telefon=telefon, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save(using=self._db)
        return user

    @staticmethod
    def normalize_telefon(telefon):
        return telefon.replace(' ', '').replace('-', '')

    def create_user(self, telefon, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(telefon, password, **extra_fields)

    def create_superuser(self, telefon, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields['is_staff'] is not True:
            raise ValueError("Superuser uchun is_staff=True bo'lishi kerak")
        if extra_fields['is_superuser'] is not True:
            raise ValueError("Superuser uchun is_superuser=True bo'lishi kerak")
        return self._create_user(telefon, password, **extra_fields)