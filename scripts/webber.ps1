# ============================================================
# WEBBER — Comandos de desenvolvimento via Docker
# Uso: .\scripts\webber.ps1 <comando> [argumentos]
#
# IMPORTANTE: TODOS os comandos Django rodam dentro do
# container backend. Nunca use o venv local diretamente.
# ============================================================

param([string]$cmd = "help", [Parameter(ValueFromRemainingArguments)][string[]]$args)

$COMPOSE = "docker compose"
$BACKEND = "$COMPOSE exec backend"

function Show-Help {
    Write-Host ""
    Write-Host "WEBBER — Comandos de desenvolvimento" -ForegroundColor Cyan
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Servicos:" -ForegroundColor Yellow
    Write-Host "  up          Sobe todos os servicos (db, redis, backend)"
    Write-Host "  down        Para todos os servicos"
    Write-Host "  restart     Reinicia o backend"
    Write-Host "  logs        Exibe logs do backend (Ctrl+C para sair)"
    Write-Host "  status      Exibe status dos containers"
    Write-Host ""
    Write-Host "Django (via container):" -ForegroundColor Yellow
    Write-Host "  migrate     Aplica todas as migrations pendentes"
    Write-Host "  makemig     Cria novas migrations (ex: makemig modulo_demanda)"
    Write-Host "  setup       Executa setup_dev (dados iniciais)"
    Write-Host "  shell       Abre Django shell interativo"
    Write-Host "  manage      Executa management command (ex: manage showmigrations)"
    Write-Host "  test        Executa os testes"
    Write-Host ""
    Write-Host "Frontend:" -ForegroundColor Yellow
    Write-Host "  vite        Inicia o servidor Vite (frontend local)"
    Write-Host ""
    Write-Host "Exemplos:" -ForegroundColor Green
    Write-Host "  .\scripts\webber.ps1 up"
    Write-Host "  .\scripts\webber.ps1 migrate"
    Write-Host "  .\scripts\webber.ps1 makemig modulo_demanda"
    Write-Host "  .\scripts\webber.ps1 manage createsuperuser"
    Write-Host "  .\scripts\webber.ps1 shell"
    Write-Host ""
}

switch ($cmd) {
    "up" {
        Write-Host "Subindo servicos..." -ForegroundColor Green
        Invoke-Expression "$COMPOSE up -d"
        Write-Host "Backend: http://localhost:8000 | Execute 'vite' para o frontend." -ForegroundColor Cyan
    }
    "down" {
        Invoke-Expression "$COMPOSE down"
    }
    "restart" {
        Write-Host "Reiniciando backend..." -ForegroundColor Yellow
        Invoke-Expression "$COMPOSE restart backend"
    }
    "logs" {
        Invoke-Expression "$COMPOSE logs -f backend"
    }
    "status" {
        Invoke-Expression "$COMPOSE ps"
    }
    "migrate" {
        Write-Host "Aplicando migrations via container..." -ForegroundColor Green
        Invoke-Expression "$BACKEND python manage.py migrate"
    }
    "makemig" {
        $app = if ($args.Count -gt 0) { $args[0] } else { "" }
        if ($app) {
            Write-Host "Criando migrations para $app..." -ForegroundColor Green
            Invoke-Expression "$BACKEND python manage.py makemigrations $app"
        } else {
            Invoke-Expression "$BACKEND python manage.py makemigrations"
        }
        Write-Host "Aplique as migrations com: .\scripts\webber.ps1 migrate" -ForegroundColor Yellow
    }
    "setup" {
        Write-Host "Executando setup_dev..." -ForegroundColor Green
        Invoke-Expression "$BACKEND python manage.py setup_dev"
    }
    "shell" {
        Write-Host "Abrindo Django shell (digite 'exit()' para sair)..." -ForegroundColor Green
        Invoke-Expression "$BACKEND python manage.py shell"
    }
    "manage" {
        $manageArgs = $args -join " "
        Invoke-Expression "$BACKEND python manage.py $manageArgs"
    }
    "test" {
        Invoke-Expression "$BACKEND python manage.py test"
    }
    "vite" {
        $env:PATH = "C:\Program Files\nodejs;$env:PATH"
        Write-Host "Iniciando Vite em http://localhost:5173 ..." -ForegroundColor Green
        Set-Location frontend
        & "C:\Program Files\nodejs\node.exe" "node_modules\vite\bin\vite.js"
        Set-Location ..
    }
    default {
        Show-Help
    }
}
