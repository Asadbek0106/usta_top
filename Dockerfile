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



USER app

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]

