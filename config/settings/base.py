from datetime import timedelta
from pathlib import Path

import environ
from django.templatetags.static import static
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

DJANGO_APPS = [
    # Admin panel mavzusi: django.contrib.admin'dan OLDIN turishi shart (shablonlarini almashtiradi)
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',

]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.ustalar',
    'apps.arizalar',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
}
DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=60)
DATABASES['default']['CONN_HEALTH_CHECKS'] = True

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
# Admin panel (unfold) matnlarining o'zbekcha tarjimasi: locale/uz/LC_MESSAGES/django.po
LOCALE_PATHS = [BASE_DIR / 'locale']
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Foydalanuvchi yuklagan fayllar (arizaga biriktirilgan rasmlar)
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env('MEDIA_ROOT', default=str(BASE_DIR / 'media')))
# Bitta arizaga nechta rasm va har biri necha MB gacha bo'lishi mumkin
ARIZA_RASM_SONI = 5
ARIZA_RASM_HAJMI_MB = 5

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardPagination',
    # Umumiy cheklov: bitta IP (anonim) yoki bitta foydalanuvchi daqiqasiga shuncha so'rov yubora oladi
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '300/minute',
        'auth': '5/minute',
        'ariza': '20/hour',
    },
}

# --- JWT ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- Swagger / OpenAPI ---
SPECTACULAR_SETTINGS = {
    'TITLE': 'Usta API',
    'DESCRIPTION': "Ustalarni topish va ularga ariza qoldirish platformasi",
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'COMPONENT_SPLIT_REQUEST': True,
    # Ariza.status va ArizaTarixi.eski/yangi_status bitta tanlovlar to'plami: sxemada bitta nom bilan chiqadi
    'ENUM_NAME_OVERRIDES': {
        'ArizaStatusEnum': 'apps.arizalar.models.Ariza.Status',
    },
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
}

# --- Telegram bot (ro'yxatdan o'tishda telefon raqamni tasdiqlash) ---
# Token BotFather'dan olinadi. Token berilmasa (lokal ishlab chiqish, testlar) tasdiqlash o'chiq turadi
# va ro'yxatdan o'tish avvalgidek kodsiz ishlaydi.
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_BOT_USERNAME = env('TELEGRAM_BOT_USERNAME', default='').lstrip('@')
TELEFON_TASDIQLASH = env.bool('TELEFON_TASDIQLASH', default=bool(TELEGRAM_BOT_TOKEN))
# Kod qancha vaqt amal qiladi va bitta kodni necha marta noto'g'ri kiritish mumkin
TASDIQ_KOD_MUDDATI = timedelta(minutes=10)
TASDIQ_KOD_URINISHLAR = 5


# --- Admin panel (django-unfold) ---
# /admin/login/ to'g'ridan-to'g'ri ochilganda kirgandan keyin Django /accounts/profile/ ga (404) yuboradi
LOGIN_REDIRECT_URL = reverse_lazy('admin:index')

UNFOLD = {
    'SITE_TITLE': "Usta admin",
    'SITE_HEADER': "Usta",
    'SITE_SUBHEADER': "Boshqaruv paneli",
    'SITE_SYMBOL': 'handyman',  # Material Symbols nomi
    'SITE_URL': env('FRONTEND_URL', default='/'),
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': False,
    'SHOW_BACK_BUTTON': True,
    'ENVIRONMENT': 'apps.core.admin_panel.muhit',
    'DASHBOARD_CALLBACK': 'apps.core.admin_panel.dashboard',
    'STYLES': [lambda request: static('core/admin.css')],
    'COLORS': {
        # Saytdagi indigo rang (#26406b = 700) asosida
        'primary': {
            '50': '#eef2f8',
            '100': '#dbe3f0',
            '200': '#b9c8e1',
            '300': '#8ea6cc',
            '400': '#6382b4',
            '500': '#44649a',
            '600': '#33507f',
            '700': '#26406b',
            '800': '#1f3557',
            '900': '#192a45',
            '950': '#0f1a2c',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': [
            {
                'title': "Asosiy",
                'items': [
                    {'title': "Dashboard", 'icon': 'dashboard', 'link': reverse_lazy('admin:index')},
                ],
            },
            {
                'title': "Platforma",
                'items': [
                    {
                        'title': "Ustalar",
                        'icon': 'engineering',
                        'link': reverse_lazy('admin:ustalar_usta_changelist'),
                        # Tasdiq kutayotgan ustalar soni (0 bo'lsa ko'rinmaydi)
                        'badge': 'apps.core.admin_panel.tasdiq_kutayotganlar',
                    },
                    {
                        'title': "Arizalar",
                        'icon': 'assignment',
                        'link': reverse_lazy('admin:arizalar_ariza_changelist'),
                        'badge': 'apps.core.admin_panel.yangi_arizalar',
                    },
                    {'title': "Sharhlar", 'icon': 'reviews', 'link': reverse_lazy('admin:arizalar_sharh_changelist')},
                    {
                        'title': "Sevimlilar",
                        'icon': 'favorite',
                        'link': reverse_lazy('admin:ustalar_sevimli_changelist'),
                    },
                ],
            },
            {
                'title': "Ma'lumotnomalar",
                'collapsible': True,
                'items': [
                    {
                        'title': "Kategoriyalar",
                        'icon': 'category',
                        'link': reverse_lazy('admin:ustalar_kategoriya_changelist'),
                    },
                    {
                        'title': "Shaharlar",
                        'icon': 'location_city',
                        'link': reverse_lazy('admin:ustalar_shahar_changelist'),
                    },
                ],
            },
            {
                'title': "Foydalanuvchilar",
                'collapsible': True,
                'items': [
                    {
                        'title': "Foydalanuvchilar",
                        'icon': 'person',
                        'link': reverse_lazy('admin:accounts_user_changelist'),
                    },
                    {
                        'title': "Guruhlar",
                        'icon': 'group',
                        'link': reverse_lazy('admin:auth_group_changelist'),
                        'permission': lambda request: request.user.is_superuser,
                    },
                    {
                        'title': "Telegram kodlari",
                        'icon': 'sms',
                        'link': reverse_lazy('admin:accounts_telefontasdiq_changelist'),
                        'permission': lambda request: request.user.is_superuser,
                    },
                ],
            },
        ],
    },
}
