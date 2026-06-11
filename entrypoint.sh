#!/bin/bash
# entrypoint.sh para maquinariasDevOps con PostgreSQL

echo "🔄 Esperando a que PostgreSQL esté listo..."
while ! nc -z db 5432; do
  sleep 1
done
echo "✅ PostgreSQL está listo!"

echo "📦 Ejecutando migraciones..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "🚀 Iniciando Gunicorn..."
exec gunicorn delba.wsgi:application --bind 0.0.0.0:8000 --workers 3