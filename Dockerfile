# syntax=docker/dockerfile:1

FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build


COPY requirements/ requirements/
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install -r requirements/base.txt


FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=config.settings.prod


# Ilova root huquqi bilan emas, oddiy foydalanuvchi nomidan ishlaydi
RUN groupadd --system app \
    && useradd --system --gid app --create-home app


WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN SECRET_KEY=build-uchun-vaqtinchalik DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py collectstatic --noinput



# Yuklangan rasmlar uchun papka: ilova oddiy foydalanuvchi nomidan ishlaydi, unga yozish huquqi kerak
RUN mkdir -p /app/media && chown app:app /app/media

USER app

EXPOSE 8000

# Render o'z portini PORT o'zgaruvchisida beradi (lokalda 8000).
# Migratsiyalar va superuser (agar DJANGO_SUPERUSER_* berilgan bo'lsa) har ishga tushishda tekshiriladi,
# chunki Render bepul tarifida pre-deploy buyrug'i ham, Shell ham yo'q.
# Worker soni WEB_CONCURRENCY orqali boshqariladi (gunicorn uni o'zi o'qiydi).
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py ensure_superuser && python manage.py set_telegram_webhook && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --access-logfile -"]

