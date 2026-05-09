import { Navigate, useLocation } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

/**
 * Matriz de permissões por papel.
 * Cada entrada lista os prefixos de rota permitidos.
 * 'admin' tem acesso irrestrito.
 * 'tipo_unidade' pode ampliar o acesso do solicitante.
 */
const ACESSO_POR_PAPEL = {
  admin: ['*'],

  analista: [
    '/',
    '/painel',
    '/ajuda',
    '/plano-compras',
    '/planejamento',
    '/demanda',
    '/pesquisa',
    '/etp',
    '/analise-tecnica',
    '/orcamento',
    '/licitacao',
    '/contratos',
  ],

  gestor_planejamento: [
    '/',
    '/painel',
    '/ajuda',
    '/plano-compras',
    '/planejamento',
    '/demanda',
    '/pesquisa',
    '/orcamento',
  ],

  gestor_contrato: [
    '/',
    '/painel',
    '/ajuda',
    '/demanda',
    '/analise-tecnica',
    '/licitacao',
    '/contratos',
  ],

  fiscal_contrato: [
    '/',
    '/painel',
    '/ajuda',
    '/demanda',
    '/contratos',
  ],

  ordenador: [
    '/',
    '/painel',
    '/ajuda',
    '/plano-compras',
    '/orcamento',
    '/contratos',
    '/licitacao',
  ],

  responsavel_tecnico: [
    '/',
    '/painel',
    '/ajuda',
    '/demanda',
    '/pesquisa',
    '/etp',
    '/analise-tecnica',
  ],

  solicitante: [
    '/',
    '/painel',
    '/ajuda',
    '/demanda',
    '/planejamento',
    '/pesquisa',
    '/etp',
    '/analise-tecnica',
  ],
}

// Extensões por tipo de unidade (ampliam o papel base)
const ACESSO_EXTRA_POR_UNIDADE = {
  licitante:    ['/licitacao', '/etp', '/analise-tecnica', '/pesquisa', '/contratos', '/plano-compras'],
  planejamento: ['/orcamento', '/planejamento', '/plano-compras'],
  contratante:  ['/contratos', '/licitacao'],
  demandante:   ['/demanda', '/pesquisa'],
}

function temAcesso(path, papel, tipoUnidade) {
  if (papel === 'admin') return true

  const rotas = ACESSO_POR_PAPEL[papel] || []
  const extras = ACESSO_EXTRA_POR_UNIDADE[tipoUnidade] || []
  const todas  = [...new Set([...rotas, ...extras])]

  // Normaliza path para prefixo (/demanda/dfd/1 → /demanda)
  const prefixo = '/' + (path.split('/')[1] || '')

  return todas.includes('/') || todas.some(r => path === r || path.startsWith(r + '/') || prefixo === r)
}

export default function RequireRole({ children }) {
  const papel      = useAuthStore(s => s.papel)
  const tipoUnidade = useAuthStore(s => s.tipoUnidade)
  const location   = useLocation()

  if (!papel) return <Navigate to="/login" replace />

  if (!temAcesso(location.pathname, papel, tipoUnidade)) {
    return <Navigate to="/sem-acesso" replace state={{ from: location.pathname }} />
  }

  return children
}
