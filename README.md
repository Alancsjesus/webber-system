# Webber — Sistema de Gestão de Contratações

Sistema web para gestão do processo de contratações públicas, seguindo o fluxo da Lei 14.133/2021 (Nova Lei de Licitações).

## Fluxo do Sistema

```
Necessidade → DFD → ETP → Termo de Referência
```

| Etapa | Descrição |
|-------|-----------|
| **Necessidade** | Unidade demandante identifica e registra uma necessidade de contratação |
| **Aceite** | Órgão pai aceita ou recusa necessidades externas (execução delegada) |
| **DFD** | Documento de Formalização de Demanda gerado a partir da necessidade aprovada |
| **ETP** | Estudo Técnico Preliminar elaborado com base no DFD aprovado |
| **TR** | Termo de Referência gerado a partir do ETP aprovado |

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Backend | Django 5.1 + Django REST Framework + JWT (simplejwt) |
| Frontend | React 18 + Vite + Zustand + Tailwind CSS |
| Banco de dados | PostgreSQL (produção) / SQLite (desenvolvimento) |
| Cache | Redis |

## Como Rodar Localmente

Consulte o guia completo em [SETUP-LOCAL.md](SETUP-LOCAL.md).

**Resumo rápido (SQLite):**

```bash
# Backend
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
python manage.py migrate
python manage.py setup_dev
python manage.py runserver

# Frontend (novo terminal)
cd frontend
cp .env.example .env
npm install
npm run dev
```

Acesse: http://localhost:5173

## Usuários de Teste

| Usuário | Senha | Papel | Órgão |
|---------|-------|-------|-------|
| `admin` | `admin123` | Administrador | SSP |
| `analista_ssp` | `admin123` | Analista | SSP |
| `plan_ssp` | `admin123` | Gestor de Planejamento | SSP |
| `plan_cbm` | `admin123` | Gestor de Planejamento | CBMBA |
| `plan_pm` | `admin123` | Gestor de Planejamento | PMBA |
| `solicitante` | `admin123` | Solicitante | CBMBA |
| `solicitante_pm` | `admin123` | Solicitante | PMBA |
| `gestor` | `admin123` | Gestor de Contrato | SSP |
| `dem_ssp` | `admin123` | Solicitante | SSP |

## Estrutura do Projeto

```
webber/
├── backend/
│   ├── config/              # Settings, URLs, WSGI
│   ├── core/                # Modelos base: Orgao, Unidade, UserProfile, permissões
│   ├── modulo_planejamento/ # Necessidades e Planos Orçamentários
│   ├── modulo_orcamento/    # Dotações, Ações, Fontes, Elementos de Despesa
│   ├── modulo_demanda/      # DFDs
│   ├── modulo_etp/          # Estudos Técnicos Preliminares
│   ├── modulo_tr/           # Termos de Referência
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # Uma página por rota
│   │   ├── stores/          # Zustand stores por módulo
│   │   ├── components/      # Layout, ProtectedRoute
│   │   └── services/        # Cliente axios (api.js)
│   └── package.json
├── docker-compose.yml       # PostgreSQL + Redis para desenvolvimento
├── .env.example             # Variáveis de ambiente (copiar para backend/.env)
└── SETUP-LOCAL.md           # Guia completo de instalação
```

## Hierarquia Organizacional

O sistema suporta uma hierarquia de dois níveis:

```
SSP (Secretaria de Segurança Pública)
├── CBMBA (Corpo de Bombeiros Militar da Bahia)
└── PMBA (Polícia Militar da Bahia)
```

Órgãos filhos podem delegar execução de necessidades ao órgão pai via workflow de aceite.

## Variáveis de Ambiente

Copie `.env.example` para `backend/.env` e ajuste conforme necessário.

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SECRET_KEY` | (inseguro) | Chave secreta Django — **trocar em produção** |
| `DEBUG` | `True` | Desativar em produção |
| `USE_POSTGRES` | `False` | `True` para PostgreSQL |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Hosts permitidos |
| `CORS_ALLOWED_ORIGINS` | localhost | Origens CORS permitidas |
