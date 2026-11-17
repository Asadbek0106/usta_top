from rest_framework.permissions import BasePermission


class IsArizaUstasi(BasePermission):
    message = "Bu amalni faqat arizaga biriktirilgan usta bajara oladi."

    def has_object_permission(self, request, view, obj):
        return obj.usta.user_id == request.user.id


class IsArizaMijozi(BasePermission):
    message = "Bu amalni faqat arizani yuborgan mijoz bajara oladi."

    def has_object_permission(self, request, view, obj):
        return obj.mijoz_id == request.user.id