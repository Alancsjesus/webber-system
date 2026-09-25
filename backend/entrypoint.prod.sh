#!/bin/sh
set -e

echo "==> Aplicando migrações..."
python manage.py migrate --noinput

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

# Carga de demonstração ponta a ponta (core/fixtures/demo_webber.json.gz).
#   True      — só carrega com o banco vazio (sem DFD)
#   Atualizar — recarrega quando uma carga nova é publicada (APAGA o que foi
#               lançado no ambiente desde a carga anterior); reinícios sem carga
#               nova não mexem em nada
if [ "$RUN_CARGA_DEMO" = "True" ] || [ "$RUN_CARGA_DEMO" = "Atualizar" ]; then
    FLAG=""
    [ "$RUN_CARGA_DEMO" = "Atualizar" ] && FLAG="--atualizar"
    echo "==> RUN_CARGA_DEMO=$RUN_CARGA_DEMO — carga de demonstração..."
    python manage.py carregar_demo $FLAG || echo "==> carregar_demo falhou (ver log acima), seguindo mesmo assim."
fi

echo "==> Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
