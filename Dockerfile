# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================
# STAGE 2: Production
# ============================================
FROM python:3.12-slim

WORKDIR /app

# Instalar TODAS las dependencias del sistema DE UNA VEZ
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    libpng16-16 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN mkdir -p /app/media /app/staticfiles
RUN python manage.py collectstatic --noinput

# Crear usuario con directorio home
RUN mkdir -p /home/django && \
    addgroup --system django && \
    adduser --system --home /home/django --ingroup django django && \
    chown -R django:django /app /home/django

# Copiar entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Cambiar a usuario no root
USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]