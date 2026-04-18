# Setup Local — WEBBER System

## Pré-requisitos

- **Python 3.11+**: [Download](https://www.python.org/)
- **Node.js 18+** e npm: [Download](https://nodejs.org/)
- **Docker & Docker Compose** (para modo PostgreSQL): [Download](https://www.docker.com/)
- **Git**: [Download](https://git-scm.com/)

---

## Opção A — Modo rápido com SQLite

Ideal para desenvolvimento inicial. Sem necessidade de Docker.

### 1. Clone o repositório

```bash
git clone <repo-url>
cd webber-system
```

### 2. Crie o virtualenv e instale dependências Python

```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate   # Windows: ..\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp ../.env.example .env
# Verifique que USE_POSTGRES=False (já é o padrão)
```

### 4. Execute as migrações

```bash
python manage.py migrate
```

### 5. Popule os dados iniciais

```bash
python manage.py setup_dev
python manage.py populate_elementos_despesa
```

### 6. Inicie o backend

```bash
python manage.py runserver
```

### 7. Inicie o frontend (novo terminal)

```bash
cd ../frontend
npm install
npm run dev
```

Acesse: http://localhost:5173  
Login: `admin` / `admin123`

---

## Opção B — Modo completo com PostgreSQL via Docker

### 1–2. Clone e virtualenv (igual à Opção A)

### 3. Suba o banco e Redis com Docker

```bash
# Na raiz do projeto (onde está o docker-compose.yml)
docker compose up -d db redis
```

Aguarde o healthcheck do PostgreSQL (cerca de 10 segundos):

```bash
docker compose ps   # coluna "Status" deve mostrar "healthy" para db
```

### 4. Configure o arquivo .env

```bash
cd backend
cp ../.env.example .env
```

Edite `.env` e altere:

```
USE_POSTGRES=True
DB_HOST=localhost   # já está correto — Docker expõe na porta 5432
```

### 5. Execute as migrações

```bash
source ../venv/bin/activate
python manage.py migrate
```

### 6. Popule os dados iniciais

```bash
python manage.py setup_dev
python manage.py populate_elementos_despesa
```

### 7. Inicie backend e frontend (igual à Opção A, passos 6–7)

Acesse: http://localhost:5173  
Login: `admin` / `admin123`

---

## Comandos úteis

| Comando | Descrição |
|---|---|
| `python manage.py setup_dev` | Cria organização e superusuário de desenvolvimento |
| `python manage.py populate_elementos_despesa` | Popula os ~40 elementos de despesa padronizados (Lei 14.133) |
| `docker compose up -d db redis` | Inicia PostgreSQL + Redis em background |
| `docker compose ps` | Verifica status dos containers |
| `docker compose down` | Para os containers |
| `docker compose down -v` | Para e remove os volumes (apaga todos os dados) |

---

## Variáveis de ambiente relevantes

| Variável | Padrão | Descrição |
|---|---|---|
| `USE_POSTGRES` | `False` | `True` para usar PostgreSQL, `False` para SQLite |
| `DB_NAME` | `webber_db` | Nome do banco PostgreSQL |
| `DB_USER` | `webber_user` | Usuário do banco |
| `DB_PASSWORD` | `webber_pass` | Senha do banco |
| `DB_HOST` | `localhost` | Host do banco |
| `DB_PORT` | `5432` | Porta do banco |
| `REDIS_URL` | `redis://localhost:6379/0` | URL do Redis |
| `SECRET_KEY` | — | Chave secreta Django (trocar em produção) |
| `DEBUG` | `True` | Modo debug (desativar em produção) |
