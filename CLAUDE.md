# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Development Commands

**All Django commands must run inside the Docker container.** Never use the local venv.

```powershell
# Start services (PostgreSQL + Redis + Django on :8000)
.\scripts\webber.ps1 up

# Start frontend (Vite on :5173) — run in a separate terminal
.\scripts\webber.ps1 vite

# Apply migrations
.\scripts\webber.ps1 migrate

# Create migrations for a specific app
.\scripts\webber.ps1 makemig modulo_demanda

# Seed demo data (test users, orgs, parametros)
.\scripts\webber.ps1 setup

# Stop all services
.\scripts\webber.ps1 down

# View backend logs
.\scripts\webber.ps1 logs

# Run any manage.py command
.\scripts\webber.ps1 manage showmigrations
.\scripts\webber.ps1 manage shell
```

Direct Docker equivalents (without the script):
```powershell
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py makemigrations modulo_xxx
docker compose exec backend python manage.py setup_dev
```

### Running Tests
```powershell
.\scripts\webber.ps1 test
# Or directly:
docker compose exec backend python manage.py test
```

### Frontend only
```powershell
cd frontend
npm run dev      # dev server
npm run build    # production build
```

### Env file
Copy `backend/.env.example` to `backend/.env` before first run. Key vars:
- `USE_POSTGRES=False` → SQLite (dev without Docker DB); `True` → PostgreSQL
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`

---

## Architecture

### Stack
- **Backend**: Django 5.1 + Django REST Framework + simplejwt, Python 3.x
- **Frontend**: React 18 + Vite + Zustand + Tailwind CSS
- **DB**: PostgreSQL 13 (prod/Docker) or SQLite (dev without Docker)
- **Cache/Queue**: Redis 7

### Procurement Workflow
Each contratação follows a strict linear chain:

```
NecessidadePlanejamento → DFD → ETP → TR → Procedimento (licitação/dispensa) → Contrato
```

Each step has status state machines with `TRANSICOES_PERMITIDAS` dicts enforcing valid transitions. Skipping steps requires explicit bypass (e.g., ETP may be dispensed for low-value contracts).

### Multi-Tenancy

`TenantMiddleware` (`backend/core/middleware.py`) decodes the JWT on every request and sets:
- `request.org_id` — the authenticated user's org (used as the primary filter in all ViewSets)
- `request.papel` — role string (e.g., `'analista'`, `'solicitante'`)
- `request.tipo_unidade` — unit type (`'demandante'`, `'licitante'`, `'contratante'`, `'planejamento'`)

Every ViewSet that inherits `IsMultiTenant` filters its queryset by `org_id=request.org_id`. When adding new ViewSets, always apply `permission_classes = [IsAuthenticated, IsMultiTenant]` and filter by `request.org_id`.

### Organizational Hierarchy

Two-level hierarchy:
- **Órgão pai** (e.g., SSP): has own planning/licitante/contratante units; accepts delegated demands from children.
- **Órgãos filhos** (e.g., PMBA, CBMBA): have their own planning and demand units; can send needs (`tipo_execucao='externa'`) to the parent via an aceite queue.

`NecessidadePlanejamento.aceite_pai` tracks the delegation handoff (`pendente → aceita/recusada`).

### BaseModel (abstract)

All domain models extend `BaseModel` (`backend/core/models.py`):
```python
class BaseModel(models.Model):
    org_id      = models.ForeignKey(Orgao, on_delete=models.CASCADE)
    created_by  = models.ForeignKey(User, ...)
    updated_by  = models.ForeignKey(User, ...)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True
        indexes = [Index(fields=['org_id', '-created_at'])]
```

`create()` in serializers must set `org_id_id = request.org_id` and `created_by = request.user`.

### Authentication Flow

1. `POST /api/token/` → `WebberTokenObtainPairSerializer` issues JWT with custom claims: `org_id`, `orgao_sigla`, `orgao_nome`, `unidade_id`, `tipo_unidade`, `papel`, `flags` (feature flags from `ParametroSistema`).
2. Frontend stores `access_token` / `refresh_token` in `localStorage`.
3. `frontend/src/services/api.js` request interceptor injects `Authorization: Bearer` on every call.
4. On 401, the response interceptor auto-refreshes via `/api/token/refresh/` and retries once; on failure it redirects to `/login`.

### Feature Flags

`ParametroSistema` records (key/value) control module visibility. Flags are embedded in the JWT and read by `useAuthStore` on the frontend:
- `modulo_planejamento_ativo`
- `modulo_orcamento_ativo`
- `modulo_etp_ativo`
- `modulo_mapa_ativo`
- `dfd_exige_planejamento`

The Layout sidebar and `buildModuleCards()` (`frontend/src/config/moduleCards.jsx`) use these flags to show/hide sections.

### Role-Based Access

Eight roles: `admin`, `analista`, `gestor_planejamento`, `gestor_contrato`, `fiscal_contrato`, `ordenador`, `solicitante`, `responsavel_tecnico`.

Permission groups are defined in `backend/core/permissions.py`. The frontend enforces the same matrix in `RequireRole` (`frontend/src/components/RequireRole.jsx`) and `Layout.jsx` — **keep these two in sync when changing access rules**.

**Mandatory rule:** whenever a route prefix is added to `moduleCards.jsx` (`MODULE_CARDS_DEF[].to`) or to a nav item in `Layout.jsx`, the same prefix must be added to `ACESSO_POR_PAPEL`/`ACESSO_EXTRA_POR_UNIDADE` in `RequireRole.jsx` for every role/unit that is supposed to see it, **in the same change**. `moduleCards.jsx` and `Layout.jsx` only control what is *shown*; `RequireRole.jsx` is what actually *grants* access — a card or nav link with no matching entry in `RequireRole.jsx` silently redirects the user to `/sem-acesso`. This exact gap happened with `/config` and `/calendario` (fixed 20/08/2026) — both were fully built and advertised in the UI but reachable only by `admin` because `RequireRole.jsx` was never updated.

### Backend Module Structure

Each `modulo_*` app follows the same layout:
```
modulo_xxx/
  models.py       # domain models + TRANSICOES_PERMITIDAS dicts
  serializers.py  # DRF serializers (list + detail variants)
  views.py        # ModelViewSet(s) + custom @action endpoints for status transitions
  urls.py         # router registration
  migrations/
```

Status transitions are handled by a `_transicao(instance, novo_status, usuario, motivo)` helper pattern that validates the transition, saves the model, and writes an immutable `Historico*` record.

### Frontend Module Structure

```
frontend/src/
  pages/          # One List + Create + Detail component per domain entity
  stores/         # Zustand store per module (authStore + one per backend module)
  components/     # Shared UI (Layout, OrgaoHero, ModuleCard/Grid, etc.)
  config/         # Static data: moduleCards.jsx (module definitions + access rules), orgaoLogos.js
  services/api.js # Axios instance with auth interceptors
```

Page components follow the `List / Create / Detail` pattern. The store handles API calls; pages subscribe to the store. `useAuthStore` is the source of truth for the current user's org, unit, role, and feature flags.

### Item Catalog & SIMPAS Codes

`ItemCatalogo` (`backend/core/models.py`) stores items with:
- Internal code `WBR-XXXXX` (auto-generated)
- SIMPAS code (format `42.40.20.00016900-5`) — first two segments (e.g., `42.40`) are extracted automatically as `familia` on save.

`familia` drives procurement grouping suggestions in the Plano de Compras (`/indicadores/agrupamento/`) and controls teto de dispensa tracking per `(org, exercicio, familia)`.

### Procedure Numbering

Procedimentos get auto-numbered as `{PREFIXO}-{UNIDADE_SIGLA}-{SEQ:03d}/{ANO}` via a `pre_save` signal. Prefixes: `PE`, `CC`, `DE`, `DT`, `INEX`. The `unidade_gestora` FK on `Procedimento` provides the sigla; falls back to `org.sigla` if not set.

### PDF Export

`reportlab` is used for PDF generation (via `exportacao/` module). HTML export targets SEI import. Documents requiring signatures embed creator + approver names.

---

## Ajuda Contextual — Regra de Manutenção

O sistema possui ajuda contextual por página via dois componentes:
- `HelpTip` — tooltip `?` inline ao lado de botões e campos críticos
- `PageHelpPanel` — painel lateral acessível pelo botão `?` flutuante no canto inferior direito

### Regra obrigatória

**Sempre que uma página ganhar, remover ou alterar um botão, ação ou campo relevante, o bloco `export const pageHelp` no topo do arquivo deve ser atualizado na mesma operação.**

Páginas novas devem:
1. Exportar `pageHelp` no topo do arquivo (após os imports)
2. Ter a rota registrada em `frontend/src/help/helpContent.js`

### Estrutura do pageHelp

```jsx
// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo:    'Nome da Página',
  descricao: 'Explicação do propósito da página em 1-2 frases.',
  acoes: [
    { label: 'Nome do Botão', texto: 'O que este botão faz e suas implicações.' },
  ],
  fluxo: [  // opcional — para páginas com fluxo de status
    { status: 'Rascunho', descricao: 'Descrição do estado.' },
  ],
  dica:      'Dica prática para o usuário.',  // opcional
  baseLegal: 'Lei 14.133/2021 — Art. XX.',   // opcional
}
// ─────────────────────────────────────────────────────────────────────────────
```

### Validar cobertura

```powershell
node scripts/check-help.js
```

---

### Test Users (from `setup_dev`)
| Username | Password | Role | Org |
|---|---|---|---|
| admin | admin123 | admin | SSP |
| analista_ssp | admin123 | analista | SSP |
| plan_ssp | admin123 | gestor_planejamento | SSP / CPLAM |
| solicitante_ssp | admin123 | solicitante | SSP / CMP |
| analista_pmba | admin123 | analista | PMBA |
| plan_pmba | admin123 | gestor_planejamento | PMBA / DEPLAN |
| gestor_contrato | admin123 | gestor_contrato | SSP / CCC |
| fiscal | admin123 | fiscal_contrato | SSP / CCC |
| ordenador | admin123 | ordenador | SSP |
