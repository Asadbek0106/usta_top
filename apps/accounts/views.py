import hmac
import logging

from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .telegram import update_ni_qayta_ishla, webhook_maxfiy_kalit

logger = logging.getLogger(__name__)


def tokenlar(user):
    refresh = RefreshToken.for_user(user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


@extend_schema_view(
    post=extend_schema(
        responses={
            201: inline_serializer(
                name='RegisterJavob',
                fields={
                    'user': UserSerializer(),
                    'tokens': inline_serializer(
                        name='Tokenlar',
                        fields={'access': serializers.CharField(), 'refresh': serializers.CharField()},
                    ),
                },
            ),
        },
    ),
)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'user': UserSerializer(user).data, 'tokens': tokenlar(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class TelegramSozlamaView(APIView):
    """Frontend uchun: ro'yxatdan o'tishda kod kerakmi va qaysi botga yo'naltirish kerak."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=inline_serializer(
        name='TelegramSozlama',
        fields={
            'tasdiqlash_kerak': serializers.BooleanField(),
            'bot': serializers.CharField(allow_null=True),
            'havola': serializers.CharField(allow_null=True),
        },
    ))
    def get(self, request):
        bot = settings.TELEGRAM_BOT_USERNAME or None
        return Response({
            'tasdiqlash_kerak': settings.TELEFON_TASDIQLASH,
            'bot': bot,
            'havola': f'https://t.me/{bot}' if bot else None,
        })


@extend_schema(exclude=True)
class TelegramWebhookView(APIView):
    """Telegram bot xabarlarini shu manzilga yuboradi (setWebhook). Faqat Telegram uchun."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    def post(self, request):
        if not settings.TELEGRAM_BOT_TOKEN:
            return Response(status=status.HTTP_404_NOT_FOUND)
        kalit = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
        if not hmac.compare_digest(kalit, webhook_maxfiy_kalit()):
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            update_ni_qayta_ishla(request.data)
        except Exception:
            # Telegram xato javob olsa, shu update'ni qayta-qayta yuboraveradi — shuning uchun doim 200
            logger.exception('Telegram update qayta ishlanmadi')
        return Response({'ok': True})
