#!/bin/sh
set -e

echo "🔄 Ejecutando migrate..."
python manage.py migrate --noinput

echo "👤 Creando superusuario si no existe..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email    = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✅ Superusuario '{username}' creado.")
else:
    print(f"ℹ️  Superusuario '{username}' ya existe, se omite.")
EOF

echo "🚀 Iniciando Gunicorn..."
exec gunicorn delba.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -