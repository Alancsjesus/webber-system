import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

const NAV_BASE = [
  {
    section: 'Geral',
    items: [
      { to: '/',       label: 'Dashboard', end: true },
      { to: '/painel', label: 'Painel de Demandas' },
    ],
  },
  {
    section: 'Planejamento',
    items: [
      { to: '/planejamento/necessidades', label: 'Necessidades' },
    ],
  },
  {
    section: 'Orçamento',
    items: [
      { to: '/orcamento/dotacoes',   label: 'Dotações' },
      { to: '/orcamento/indicacoes', label: 'Indicações / DOD' },
    ],
  },
  {
    section: 'Pesquisa de Preços',
    items: [
      { to: '/pesquisa/mapa', label: 'Mapa Comparativo' },
    ],
  },
  {
    section: 'Demanda',
    items: [
      { to: '/demanda/dfd', label: 'DFDs' },
    ],
  },
  {
    section: 'Análise Técnica',
    items: [
      { to: '/etp/etps',            label: 'ETPs' },
      { to: '/analise-tecnica/trs', label: 'Minutas TR' },
    ],
  },
]

// Seção de aceite apenas para perfis de planejamento do órgão pai
const NAV_ACEITE = {
  section: 'Aceite',
  items: [
    { to: '/planejamento/aceite', label: 'Aceite de Necessidades' },
  ],
}

// Configurações subdivididas por perfil
const NAV_CONFIG_ADMIN = {
  section: 'Configurações',
  items: [
    { to: '/config/perfis',    label: 'Perfis e Permissões' },
    { to: '/config/orgaos',    label: 'Órgãos' },
    { to: '/config/unidades',  label: 'Unidades' },
    { to: '/config/usuarios',  label: 'Usuários' },
    { to: '/config/parametros',label: 'Parâmetros do Sistema' },
    { to: '/config/acoes',     label: 'Ações Orçamentárias' },
    { to: '/config/elementos', label: 'Elementos de Despesa' },
    { to: '/config/naturezas', label: 'Naturezas de Despesa' },
    { to: '/config/fontes',    label: 'Fontes de Recurso' },
  ],
}

// Planejamento vê tabelas orçamentárias e parâmetros
const NAV_CONFIG_PLANEJAMENTO = {
  section: 'Configurações',
  items: [
    { to: '/config/parametros',label: 'Parâmetros do Sistema' },
    { to: '/config/acoes',     label: 'Ações Orçamentárias' },
    { to: '/config/elementos', label: 'Elementos de Despesa' },
    { to: '/config/naturezas', label: 'Naturezas de Despesa' },
    { to: '/config/fontes',    label: 'Fontes de Recurso' },
  ],
}

// Licitante vê parâmetros de licitação (ex: limite dispensa ETP)
const NAV_CONFIG_LICITANTE = {
  section: 'Configurações',
  items: [
    { to: '/config/parametros', label: 'Parâmetros do Sistema' },
  ],
}

const TIPO_UNIDADE_BADGE = {
  demandante:   { label: 'Demandante',   cls: 'bg-purple-800 text-purple-200' },
  licitante:    { label: 'Licitante',    cls: 'bg-blue-800 text-blue-200' },
  contratante:  { label: 'Contratante',  cls: 'bg-green-800 text-green-200' },
  planejamento: { label: 'Planejamento', cls: 'bg-orange-800 text-orange-200' },
}

function buildSections(papel, tipoUnidade) {
  const sections = [...NAV_BASE]

  // Adicionar seção de aceite para planejamento (órgão pai aceita demandas externas)
  if (tipoUnidade === 'planejamento' || ['gestor_planejamento', 'admin'].includes(papel)) {
    sections.splice(2, 0, NAV_ACEITE) // insere após Planejamento
  }

  // Configurações por perfil
  if (papel === 'admin') {
    sections.push(NAV_CONFIG_ADMIN)
  } else if (papel === 'gestor_planejamento' || tipoUnidade === 'planejamento') {
    sections.push(NAV_CONFIG_PLANEJAMENTO)
  } else if (tipoUnidade === 'licitante') {
    sections.push(NAV_CONFIG_LICITANTE)
  }

  return sections
}

export default function Layout() {
  const logout      = useAuthStore((s) => s.logout)
  const tipoUnidade = useAuthStore((s) => s.tipoUnidade)
  const papel       = useAuthStore((s) => s.papel)
  const orgaoSigla  = useAuthStore((s) => s.orgaoSigla)
  const orgaoNome   = useAuthStore((s) => s.orgaoNome)
  const unidadeNome = useAuthStore((s) => s.unidadeNome)
  const navigate    = useNavigate()

  const allSections = buildSections(papel, tipoUnidade)

  const [open, setOpen] = useState(() =>
    Object.fromEntries(allSections.map(({ section }) => [section, true]))
  )
  const toggle = (section) => setOpen((prev) => ({ ...prev, [section]: !prev[section] }))

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-700">
          <span className="text-lg font-bold text-white">Webber</span>
          <p className="text-xs text-gray-300 mt-0.5">Gestão de Contratações</p>

          {orgaoSigla && (
            <div className="mt-2">
              <p className="text-xs font-bold text-white leading-tight">{orgaoSigla}</p>
              {orgaoNome && (
                <p className="text-xs text-gray-400 leading-tight truncate" title={orgaoNome}>
                  {orgaoNome}
                </p>
              )}
            </div>
          )}

          {unidadeNome && (
            <div className="mt-1.5 flex items-start gap-1.5">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-300 truncate leading-tight" title={unidadeNome}>
                  {unidadeNome}
                </p>
              </div>
              {tipoUnidade && (
                <span className={`shrink-0 px-1.5 py-0.5 rounded text-xs font-medium ${TIPO_UNIDADE_BADGE[tipoUnidade]?.cls || 'bg-gray-700 text-gray-300'}`}>
                  {TIPO_UNIDADE_BADGE[tipoUnidade]?.label || tipoUnidade}
                </span>
              )}
            </div>
          )}

          {papel && (
            <p className="text-xs text-gray-500 mt-1 capitalize">{papel.replace(/_/g, ' ')}</p>
          )}
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {allSections.map(({ section, items }) => (
            <div key={section}>
              <button
                onClick={() => toggle(section)}
                className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg text-xs font-semibold text-gray-200 uppercase tracking-wider hover:text-white transition-colors"
              >
                <span>{section}</span>
                <span className={`transition-transform duration-200 ${open[section] ? 'rotate-90' : ''}`}>›</span>
              </button>

              {open[section] && (
                <div className="mt-0.5 ml-2 space-y-0.5">
                  {items.map(({ to, label, end }) => (
                    <NavLink
                      key={to}
                      to={to}
                      end={end}
                      className={({ isActive }) =>
                        `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-blue-600 text-white'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }`
                      }
                    >
                      {label}
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        <div className="px-3 py-3 border-t border-gray-700 space-y-1">
          <NavLink to="/ajuda"
            className={({ isActive }) =>
              `block px-3 py-2 text-sm rounded-lg transition-colors ${isActive ? 'text-white bg-gray-700' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`
            }>
            Ajuda
          </NavLink>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="w-full text-left px-3 py-2 text-sm text-gray-200 hover:text-red-300 hover:bg-gray-800 rounded-lg transition-colors"
          >
            Sair
          </button>
        </div>
      </aside>

      {/* Conteúdo */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
