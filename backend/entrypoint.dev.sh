#!/bin/sh
set -e

echo "==> Aplicando migrações..."
python manage.py migrate --noinput

echo "==> Iniciando servidor de desenvolvimento..."
exec python manage.py runserver 0.0.0.0:8000
