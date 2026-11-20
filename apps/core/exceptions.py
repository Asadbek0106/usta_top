from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class BiznesXatosi(Exception):
    """Biznes qoidasi buzilganda service qatlamidan ko'tariladi."""

    def __init__(self, message, code='biznes_xatosi'):
        super().__init__(message)
        self.message = message
        self.code = code


def custom_exception_handler(exc, context):
    if isinstance(exc, BiznesXatosi):
        return Response(
            {'detail': exc.message, 'code': exc.code},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if isinstance(exc, DjangoValidationError):
        exc = serializers.ValidationError(serializers.as_serializer_error(exc))
    return exception_handler(exc, context)
