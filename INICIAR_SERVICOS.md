# Guia de Inicialização dos Serviços — WEBBER

> ⚠️ **Atenção:** A coluna "O que vai aparecer" mostra apenas o resultado esperado na tela.
> **Digite somente o que estiver na coluna "Digite no terminal".**

---

## Como abrir o terminal no VS Code

Pressione **Ctrl + `** (acento grave, tecla abaixo do Esc).
Para abrir um **segundo terminal**, pressione **Ctrl + Shift + `**.

---

## TERMINAL 1 — Backend (API)

| # | Digite no terminal | O que vai aparecer |
|---|--------------------|--------------------|
| 1 | `cd /workspace/backend` | *(prompt muda para backend)* |
| 2 | `python manage.py runserver 0.0.0.0:9000` | `Watching for file changes with StatReloader` e `Starting development server at http://0.0.0.0:9000/` |

O terminal vai **travar** (parar de aceitar comandos) — isso é normal, significa que está rodando.

✅ Backend no ar: **http://localhost:9000**

---

## TERMINAL 2 — Frontend (Interface)

Abra um **novo terminal** (Ctrl + Shift + `) sem fechar o primeiro.

| # | Digite no terminal | O que vai aparecer |
|---|--------------------|--------------------|
| 1 | `cd /workspace/frontend` | *(prompt muda para frontend)* |
| 2 | `npm run dev` | `VITE v5.4.21  ready` e `Local: http://localhost:5173/` |

O terminal vai **travar** também — normal.

✅ Sistema no ar: **http://localhost:5173**

---

## Encerrar os serviços

Clique no terminal que quer encerrar e pressione **Ctrl + C**.

---

## Problemas comuns

| O que apareceu | O que fazer |
|----------------|-------------|
| `Error: That port is already in use` (backend) | Feche todos os terminais com backend rodando, abra um novo e repita |
| `Port 5173 is in use, trying another one...` (frontend) | Normal — olhe qual porta aparece na linha `Local:` e use ela no browser |
| `ModuleNotFoundError` | Rode `pip install -r requirements.txt` antes de iniciar o backend |
| `Cannot find module` | Rode `npm install` antes de iniciar o frontend |
| `Your models have unapplied migrations` | Rode `python manage.py migrate` antes de iniciar o backend |

---

## Copie e cole — Iniciar tudo do zero

**Terminal 1 (backend):**
```
cd /workspace/backend
python manage.py runserver 0.0.0.0:9000
```

**Terminal 2 (frontend):**
```
cd /workspace/frontend
npm run dev
```
