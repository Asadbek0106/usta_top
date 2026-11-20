from rest_framework.permissions import BasePermission


class IsUsta(BasePermission):
    message = "Bu amal faqat ustalar uchun."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'usta_profil')
        )
