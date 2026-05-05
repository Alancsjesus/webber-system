# WEBBER System — Setup de Desenvolvimento

## Princípio fundamental

> **TODOS os comandos Django (migrations, management commands, shell) devem ser executados
> dentro do container Docker.** Nunca use o venv local para comandos Django.

O venv local pode estar corrompido (caminho de Python aponta para usuário diferente).
O container garante o ambiente correto, consistente e idêntico ao de produção.

---

## Pré-requisitos

| Ferramenta | Versão mínima | Uso |
|---|---|---|
| Docker Desktop | 4.x | Backend + DB + Redis |
| Node.js | 20.x | Frontend (Vite) — local |
| Git | 2.x | Versionamento |

**NÃO é necessário** instalar Python, pip ou venv localmente.

---

## Primeiro uso

```powershell
# 1. Clonar o repositório
git clone https://github.com/Alancsjesus/webber-system.git
cd webber-system

# 2. Verificar/copiar o arquivo de configuração
copy backend\.env.example backend\.env   # editar conforme necessário

# 3. Subir todos os serviços
docker compose up -d

# 4. Criar dados iniciais (órgãos, usuários, parâmetros)
docker compose exec backend python manage.py setup_dev

# 5. Instalar dependências do frontend (uma vez)
cd frontend && npm install && cd ..

# 6. Iniciar o frontend
.\scripts\webber.ps1 vite
```

**Acesse:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- Login padrão: `admin` / `admin123`

---

## Fluxo diário de trabalho

```powershell
# Iniciar
.\scripts\webber.ps1 up      # sobe db + redis + backend
.\scripts\webber.ps1 vite    # inicia frontend (terminal separado)

# Parar
.\scripts\webber.ps1 down
# Ctrl+C no terminal do Vite
```

---

## Comandos Django — SEMPRE via container

```powershell
.\scripts\webber.ps1 migrate              # Aplicar migrations
.\scripts\webber.ps1 makemig app_name     # Criar migration
.\scripts\webber.ps1 shell                # Django shell interativo
.\scripts\webber.ps1 setup                # Recriar dados iniciais
.\scripts\webber.ps1 manage <comando>     # Qualquer management command
.\scripts\webber.ps1 logs                 # Ver logs do backend
```

### Equivalente direto (sem script)
```powershell
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations modulo_xxx
docker compose exec backend python manage.py shell
```

---

## Estrutura dos serviços

```
docker-compose.yml (desenvolvimento)
├── db       → PostgreSQL 13 (porta 5432)
├── redis    → Redis 7 (porta 6379)
└── backend  → Django 5.1 (porta 8000)
              ├── Volume: ./backend:/app  (hot-reload automático)
              └── entrypoint.dev.sh: migrate + runserver

frontend/ → Vite 5 + React (porta 5173) — roda LOCALMENTE
            Motivo: restrição de rede corporativa bloqueia npm no container
```

---

## Criar nova migration (fluxo correto)

```powershell
# 1. Alterar model em backend/modulo_xxx/models.py
# 2. Criar a migration NO CONTAINER
.\scripts\webber.ps1 makemig modulo_xxx
# 3. Verificar o arquivo gerado
# 4. Aplicar
.\scripts\webber.ps1 migrate
# 5. Comitar model + migration juntos
git add backend/modulo_xxx/models.py backend/modulo_xxx/migrations/
git commit -m "feat: ..."
```

> ⚠️ Nunca crie migrations com o Python local. O container usa a versão
> correta do Django e detecta exatamente o que mudou no banco.

---

## Deploy em produção

```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

O `Dockerfile` (produção) usa `entrypoint.prod.sh` que executa automaticamente:
1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. `gunicorn` com 3 workers

### Variáveis de ambiente em produção (nunca commitar)
```ini
SECRET_KEY=<chave-segura>
DEBUG=False
ALLOWED_HOSTS=meudominio.com.br
USE_POSTGRES=True
DB_HOST=db
DB_NAME=webber_db
DB_USER=webber_user
DB_PASSWORD=<senha-forte>
REDIS_URL=redis://redis:6379/0
CORS_ALLOWED_ORIGINS=https://meudominio.com.br
```

---

## Solução de problemas

| Problema | Comando |
|---|---|
| Backend não inicia | `.\scripts\webber.ps1 logs` |
| Conflito de migration | `.\scripts\webber.ps1 manage showmigrations` |
| Resetar banco (dev) | `docker compose down -v && docker compose up -d` |
| Frontend não atualiza | Ctrl+C e reiniciar o Vite |

---

## O que NÃO fazer

| ❌ Errado | ✅ Correto |
|---|---|
| `venv\Scripts\python.exe manage.py migrate` | `.\scripts\webber.ps1 migrate` |
| `python manage.py makemigrations` | `.\scripts\webber.ps1 makemig app` |
| `pip install` localmente | Editar `requirements.txt` + rebuildar |
| Commitar `.env` | Usar `.env.example` como referência |
