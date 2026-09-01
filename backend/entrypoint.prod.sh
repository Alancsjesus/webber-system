#!/bin/sh
set -e

echo "==> Aplicando migrações..."
python manage.py migrate --noinput

echo "==> [DIAGNÓSTICO TEMPORÁRIO] Estado das migrações do app core:"
python manage.py showmigrations core
echo "==> [DIAGNÓSTICO TEMPORÁRIO] Contagem de SecaoArtefato por tipo:"
python manage.py shell -c "
from core.models import SecaoArtefato
for t in ['DFD','ETP','TR']:
    qs = SecaoArtefato.objects.filter(tipo=t)
    print(f'{t}: total={qs.count()} ativas={qs.filter(ativo=True).count()}')
"

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

# Gatilho manual único: definir RUN_SETUP_DEV=True nas env vars do serviço
# (ex: Render, sem acesso a Shell no plano free) para criar órgãos/usuários de
# teste. Idempotente (setup_dev checa existência antes de criar) — mas depois
# de rodar uma vez, remova a variável ou volte para False.
if [ "$RUN_SETUP_DEV" = "True" ]; then
    echo "==> RUN_SETUP_DEV=True — rodando setup_dev..."
    python manage.py setup_dev || echo "==> setup_dev falhou (ver log acima), seguindo mesmo assim."
fi

echo "==> Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
