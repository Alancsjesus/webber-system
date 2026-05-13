import { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

// ── Paleta de cores por seção ─────────────────────────────────────────────────
const SECTION_ACCENT = {
  'Geral':              { dot: 'bg-slate-400',   ring: 'bg-slate-500/20',   text: 'text-slate-300'  },
  'Planejamento':       { dot: 'bg-emerald-400',  ring: 'bg-emerald-500/15', text: 'text-emerald-300'},
  'Aceite':             { dot: 'bg-amber-400',    ring: 'bg-amber-500/15',   text: 'text-amber-300'  },
  'Orçamento':          { dot: 'bg-yellow-400',   ring: 'bg-yellow-500/15',  text: 'text-yellow-300' },
  'Demanda':            { dot: 'bg-blue-400',     ring: 'bg-blue-500/15',    text: 'text-blue-300'   },
  'Pesquisa de Preços': { dot: 'bg-violet-400',   ring: 'bg-violet-500/15',  text: 'text-violet-300' },
  'Análise Técnica':    { dot: 'bg-indigo-400',   ring: 'bg-indigo-500/15',  text: 'text-indigo-300' },
  'Licitação':          { dot: 'bg-orange-400',   ring: 'bg-orange-500/15',  text: 'text-orange-300' },
  'Contratos':          { dot: 'bg-teal-400',     ring: 'bg-teal-500/15',    text: 'text-teal-300'   },
  'Configurações':      { dot: 'bg-gray-400',     ring: 'bg-gray-500/10',    text: 'text-gray-300'   },
}

const ACTIVE_CLS = {
  'Geral':              'bg-gray-800/70 text-white',
  'Planejamento':       'bg-gray-800/70 text-white',
  'Aceite':             'bg-gray-800/70 text-white',
  'Orçamento':          'bg-gray-800/70 text-white',
  'Demanda':            'bg-gray-800/70 text-white',
  'Pesquisa de Preços': 'bg-gray-800/70 text-white',
  'Análise Técnica':    'bg-gray-800/70 text-white',
  'Licitação':          'bg-gray-800/70 text-white',
  'Contratos':          'bg-gray-800/70 text-white',
  'Configurações':      'bg-gray-800/70 text-white',
}

// borda esquerda colorida por seção (indicador de item ativo)
const ACTIVE_BORDER = {
  'Geral':              'border-l-2 border-slate-500',
  'Planejamento':       'border-l-2 border-emerald-500',
  'Aceite':             'border-l-2 border-amber-500',
  'Orçamento':          'border-l-2 border-yellow-500',
  'Demanda':            'border-l-2 border-blue-500',
  'Pesquisa de Preços': 'border-l-2 border-violet-500',
  'Análise Técnica':    'border-l-2 border-indigo-500',
  'Licitação':          'border-l-2 border-orange-500',
  'Contratos':          'border-l-2 border-teal-500',
  'Configurações':      'border-l-2 border-gray-500',
}

// ── Dados de navegação ────────────────────────────────────────────────────────

const NAV_BASE = [
  {
    section: 'Geral',
    items: [
      { to: '/',               label: 'Dashboard',       end: true },
      { to: '/painel',         label: 'Painel de Demandas' },
      { to: '/plano-compras',  label: 'Plano de Compras' },
    ],
  },
  {
    section: 'Planejamento',
    items: [{ to: '/planejamento/necessidades', label: 'Necessidades' }],
  },
  {
    section: 'Orçamento',
    items: [
      { to: '/orcamento/dotacoes',   label: 'Dotações' },
      { to: '/orcamento/indicacoes', label: 'Indicações / DOD' },
    ],
  },
  {
    section: 'Demanda',
    items: [{ to: '/demanda/dfd', label: 'DFDs' }],
  },
  {
    section: 'Pesquisa de Preços',
    items: [{ to: '/pesquisa/mapa', label: 'Mapa Comparativo' }],
  },
  {
    section: 'Análise Técnica',
    items: [
      { to: '/etp/etps',            label: 'ETPs' },
      { to: '/analise-tecnica/trs', label: 'Minutas TR' },
    ],
  },
  {
    section: 'Licitação',
    items: [{ to: '/licitacao', label: 'Procedimentos' }],
  },
  {
    section: 'Contratos',
    items: [{ to: '/contratos', label: 'Contratos' }],
  },
]

const NAV_ACEITE = {
  section: 'Aceite',
  items: [{ to: '/planejamento/aceite', label: 'Aceite de Necessidades' }],
}

// Configurações como seção agrupada (type: 'grouped')
const CONFIG_GROUPS_ADMIN = [
  {
    label: 'Acesso',
    items: [
      { to: '/config/perfis',   label: 'Perfis e Permissões' },
      { to: '/config/orgaos',   label: 'Órgãos' },
      { to: '/config/unidades', label: 'Unidades' },
      { to: '/config/usuarios', label: 'Usuários' },
    ],
  },
  {
    label: 'Parâmetros',
    items: [
      { to: '/config/parametros', label: 'Parâmetros do Sistema' },
      { to: '/config/areas',      label: 'Áreas de Atuação' },
    ],
  },
  {
    label: 'Orçamento',
    items: [
      { to: '/config/acoes',     label: 'Ações Orçamentárias' },
      { to: '/config/naturezas', label: 'Naturezas de Despesa' },
      { to: '/config/elementos', label: 'Elementos de Despesa' },
      { to: '/config/fontes',    label: 'Fontes de Recurso' },
    ],
  },
  {
    label: 'Catálogo',
    items: [
      { to: '/config/catalogo',  label: 'Itens e Famílias SIMPAS' },
    ],
  },
  {
    label: 'Documentos',
    items: [
      { to: '/config/artefatos', label: 'Seções de Artefatos' },
    ],
  },
]

const CONFIG_GROUPS_PLANEJAMENTO = [
  {
    label: 'Parâmetros',
    items: [
      { to: '/config/parametros', label: 'Parâmetros do Sistema' },
      { to: '/config/areas',      label: 'Áreas de Atuação' },
    ],
  },
  {
    label: 'Orçamento',
    items: [
      { to: '/config/acoes',     label: 'Ações Orçamentárias' },
      { to: '/config/naturezas', label: 'Naturezas de Despesa' },
      { to: '/config/elementos', label: 'Elementos de Despesa' },
      { to: '/config/fontes',    label: 'Fontes de Recurso' },
    ],
  },
]

const CONFIG_GROUPS_LICITANTE = [
  {
    label: 'Parâmetros',
    items: [
      { to: '/config/parametros', label: 'Parâmetros do Sistema' },
    ],
  },
]

const TIPO_UNIDADE_BADGE = {
  demandante:   { label: 'Demandante',   cls: 'bg-purple-800 text-purple-200' },
  licitante:    { label: 'Licitante',    cls: 'bg-blue-800 text-blue-200' },
  contratante:  { label: 'Contratante',  cls: 'bg-green-800 text-green-200' },
  planejamento: { label: 'Planejamento', cls: 'bg-orange-800 text-orange-200' },
}

// ── Matriz de acesso (espelha RequireRole.jsx) ────────────────────────────────

const ACESSO_PAPEL = {
  admin:               ['*'],
  analista:            ['/', '/painel', '/ajuda', '/plano-compras', '/planejamento', '/demanda', '/pesquisa', '/etp', '/analise-tecnica', '/orcamento', '/licitacao', '/contratos'],
  gestor_planejamento: ['/', '/painel', '/ajuda', '/plano-compras', '/planejamento', '/demanda', '/pesquisa', '/orcamento'],
  gestor_contrato:     ['/', '/painel', '/ajuda', '/demanda', '/analise-tecnica', '/licitacao', '/contratos'],
  fiscal_contrato:     ['/', '/painel', '/ajuda', '/demanda', '/contratos'],
  ordenador:           ['/', '/painel', '/ajuda', '/plano-compras', '/orcamento', '/contratos', '/licitacao'],
  responsavel_tecnico: ['/', '/painel', '/ajuda', '/demanda', '/pesquisa', '/etp', '/analise-tecnica'],
  solicitante:         ['/', '/painel', '/ajuda', '/demanda', '/planejamento', '/pesquisa', '/etp', '/analise-tecnica'],
}
const ACESSO_UNIDADE = {
  licitante:    ['/licitacao', '/etp', '/analise-tecnica', '/pesquisa', '/contratos', '/plano-compras'],
  planejamento: ['/orcamento', '/planejamento', '/plano-compras'],
  contratante:  ['/contratos', '/licitacao'],
  demandante:   ['/demanda', '/pesquisa'],
}

function podeAcessar(to, papel, tipoUnidade) {
  if (papel === 'admin') return true
  const rotas  = ACESSO_PAPEL[papel] || []
  const extras = ACESSO_UNIDADE[tipoUnidade] || []
  const todas  = [...new Set([...rotas, ...extras])]
  if (todas.includes('*')) return true
  const prefixo = '/' + (to.split('/')[1] || '')
  return todas.some(r => to === r || to.startsWith(r + '/') || prefixo === r)
}

// ── buildSections ─────────────────────────────────────────────────────────────

function buildSections(papel, tipoUnidade, flags) {
  const f = flags || {}
  let sections = [...NAV_BASE]

  if (!f.modulo_planejamento_ativo) sections = sections.filter(s => s.section !== 'Planejamento')
  if (!f.modulo_orcamento_ativo)    sections = sections.filter(s => s.section !== 'Orçamento')
  if (!f.modulo_mapa_ativo)         sections = sections.filter(s => s.section !== 'Pesquisa de Preços')
  if (!f.modulo_etp_ativo) {
    sections = sections
      .map(s => s.section === 'Análise Técnica' ? { ...s, items: s.items.filter(i => !i.to.startsWith('/etp')) } : s)
      .filter(s => s.items?.length !== 0)
  }

  if (f.modulo_planejamento_ativo !== false &&
      (tipoUnidade === 'planejamento' || ['gestor_planejamento', 'admin'].includes(papel))) {
    const idx = sections.findIndex(s => s.section === 'Planejamento')
    if (idx >= 0) sections.splice(idx + 1, 0, NAV_ACEITE)
  }

  // Filtrar itens e seções baseado na matriz de permissões
  sections = sections
    .map(s => ({
      ...s,
      items: (s.items || []).filter(item => podeAcessar(item.to, papel, tipoUnidade)),
    }))
    .filter(s => (s.items || []).length > 0)

  // Seção de configurações agrupada
  let configGroups = null
  if (papel === 'admin') configGroups = CONFIG_GROUPS_ADMIN
  else if (papel === 'gestor_planejamento' || tipoUnidade === 'planejamento') configGroups = CONFIG_GROUPS_PLANEJAMENTO
  else if (tipoUnidade === 'licitante') configGroups = CONFIG_GROUPS_LICITANTE

  if (configGroups) sections.push({ section: 'Configurações', type: 'grouped', groups: configGroups })

  return sections
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function Layout() {
  const logout      = useAuthStore((s) => s.logout)
  const tipoUnidade = useAuthStore((s) => s.tipoUnidade)
  const papel       = useAuthStore((s) => s.papel)
  const orgaoSigla  = useAuthStore((s) => s.orgaoSigla)
  const orgaoNome   = useAuthStore((s) => s.orgaoNome)
  const unidadeNome = useAuthStore((s) => s.unidadeNome)
  const flags       = useAuthStore((s) => s.flags)
  const navigate    = useNavigate()
  const location    = useLocation()

  const allSections = buildSections(papel, tipoUnidade, flags)

  const [open, setOpen] = useState(() =>
    Object.fromEntries(allSections.map(({ section }) => [section, true]))
  )
  const toggle = (section) => setOpen(p => ({ ...p, [section]: !p[section] }))

  const [sidebarOpen, setSidebarOpen] = useState(true)

  const isHome = location.pathname === '/'

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-60' : 'w-14'} relative bg-gray-950 flex flex-col shrink-0 shadow-xl transition-[width] duration-200 ease-in-out`}>

        {/* Botão flutuante de recolhimento — posicionado na borda direita */}
        <button
          onClick={() => setSidebarOpen(p => !p)}
          title={sidebarOpen ? 'Recolher menu' : 'Expandir menu'}
          className="absolute -right-3 top-1/2 -translate-y-1/2 z-20 w-6 h-6 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center shadow-lg hover:bg-gray-600 transition-colors"
        >
          <svg className={`w-3 h-3 text-gray-300 transition-transform duration-200 ${sidebarOpen ? '' : 'rotate-180'}`} fill="currentColor" viewBox="0 0 20 20">
            <path d="M12.707 4.293a1 1 0 010 1.414L8.414 10l4.293 4.293a1 1 0 01-1.414 1.414l-5-5a1 1 0 010-1.414l5-5a1 1 0 011.414 0z"/>
          </svg>
        </button>

        {/* Bloco 1 — identidade do sistema */}
        <div className={`${sidebarOpen ? 'px-4' : 'px-2'} pt-4 pb-3 border-b border-gray-800/60 flex items-center ${sidebarOpen ? 'gap-2.5' : 'justify-center'}`}>
          {orgaoSigla === 'SSP' ? (
            <img src="/logos/sspba_brasao.png" alt="SSP-BA"
              className="w-10 h-10 object-contain shrink-0 drop-shadow" />
          ) : (
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center shrink-0">
              <span className="text-white text-sm font-black">W</span>
            </div>
          )}
          {sidebarOpen && (
            <div className="overflow-hidden">
              <span className="text-base font-black text-white tracking-tight whitespace-nowrap">Webber</span>
              <p className="text-[10px] text-gray-500 leading-none mt-0.5">Lei 14.133/2021</p>
            </div>
          )}
        </div>

        {/* Bloco 2 — contexto do usuário */}
        {orgaoSigla && (
          <div className={`${sidebarOpen ? 'px-3' : 'px-2'} py-3 border-b border-gray-800/60`}>
            {sidebarOpen ? (
              <div className="rounded-xl bg-gray-900 ring-1 ring-gray-800 px-3 py-2.5 space-y-1">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-sm font-black text-white">{orgaoSigla}</span>
                  {tipoUnidade && (
                    <span className={`shrink-0 px-2 py-0.5 rounded-md text-[10px] font-semibold ${TIPO_UNIDADE_BADGE[tipoUnidade]?.cls || 'bg-gray-700 text-gray-300'}`}>
                      {TIPO_UNIDADE_BADGE[tipoUnidade]?.label || tipoUnidade}
                    </span>
                  )}
                </div>
                {orgaoNome && (
                  <p className="text-[11px] text-gray-400 leading-tight line-clamp-1">{orgaoNome}</p>
                )}
                {unidadeNome && (
                  <p className="text-[10px] text-gray-600 truncate" title={unidadeNome}>{unidadeNome}</p>
                )}
                {papel && (
                  <p className="text-[10px] text-gray-600 capitalize">{papel.replace(/_/g, ' ')}</p>
                )}
              </div>
            ) : (
              /* Modo recolhido: apenas badge de tipo centrado */
              <div className="flex justify-center">
                <span className={`w-9 h-9 rounded-lg flex items-center justify-center text-[11px] font-black ${TIPO_UNIDADE_BADGE[tipoUnidade]?.cls || 'bg-gray-700 text-gray-300'}`}
                  title={orgaoSigla}>
                  {orgaoSigla?.slice(0, 2)}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Nav */}
        <nav className={`flex-1 ${sidebarOpen ? 'px-2' : 'px-1.5'} py-3 space-y-0.5 overflow-y-auto scrollbar-thin`}>
          {allSections.map((sec) => {
            const accent = SECTION_ACCENT[sec.section] || SECTION_ACCENT['Geral']
            const activeCls = ACTIVE_CLS[sec.section] || ACTIVE_CLS['Geral']
            const isConfigPath = location.pathname.startsWith('/config')

            const activeBorder = ACTIVE_BORDER[sec.section] || 'border-l-2 border-gray-500'

            /* Modo recolhido: apenas dot colorido da seção, clicável p/ expandir */
            if (!sidebarOpen) {
              return (
                <button
                  key={sec.section}
                  onClick={() => setSidebarOpen(true)}
                  title={sec.section}
                  className={`w-full flex items-center justify-center py-2 rounded-lg group transition-colors hover:bg-gray-800/60`}
                >
                  <span className={`w-2.5 h-2.5 rounded-full ${accent.dot}`} />
                </button>
              )
            }

            return (
              <div key={sec.section}>
                {/* Cabeçalho da seção */}
                <button
                  onClick={() => toggle(sec.section)}
                  className={`w-full flex items-center justify-between px-2 py-1.5 rounded-lg group transition-colors ${open[sec.section] ? accent.ring : 'hover:bg-gray-800/60'}`}
                >
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${accent.dot}`} />
                    <span className={`text-[11px] font-semibold uppercase tracking-widest ${accent.text}`}>
                      {sec.section}
                    </span>
                  </div>
                  <svg
                    className={`w-3 h-3 text-gray-600 transition-transform duration-200 group-hover:text-gray-400 ${open[sec.section] ? 'rotate-90' : ''}`}
                    fill="currentColor" viewBox="0 0 20 20"
                  >
                    <path d="M7.293 4.293a1 1 0 011.414 0L14 9.586l-5.293 5.293a1 1 0 01-1.414-1.414L11.586 9 6.293 4.707a1 1 0 010-1.414z"/>
                  </svg>
                </button>

                {open[sec.section] && (
                  <div className="mt-0.5 mb-1">
                    {/* Seção simples */}
                    {sec.type !== 'grouped' && (
                      <div className="ml-3 pl-2 border-l border-gray-800 space-y-0.5">
                        {sec.items.map(({ to, label, end }) => (
                          <NavLink key={to} to={to} end={end}
                            className={({ isActive }) =>
                              `block px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                                isActive
                                  ? `${activeCls} ${activeBorder} pl-2.5 shadow-sm`
                                  : 'text-gray-400 hover:text-white hover:bg-gray-800 border-l-2 border-transparent pl-2.5'
                              }`
                            }>
                            {label}
                          </NavLink>
                        ))}
                      </div>
                    )}

                    {/* Seção agrupada (Configurações) */}
                    {sec.type === 'grouped' && (
                      <div className="ml-3 pl-2 border-l border-gray-800 space-y-2">
                        {sec.groups.map((group) => (
                          <div key={group.label}>
                            <p className="px-3 py-1 text-[10px] font-semibold text-gray-600 uppercase tracking-widest">
                              {group.label}
                            </p>
                            <div className="space-y-0.5">
                              {group.items.map(({ to, label }) => (
                                <NavLink key={to} to={to}
                                  className={({ isActive }) =>
                                    `block px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                                      isActive
                                        ? `${activeCls} ${activeBorder} pl-2.5 shadow-sm`
                                        : 'text-gray-400 hover:text-white hover:bg-gray-800 border-l-2 border-transparent pl-2.5'
                                    }`
                                  }>
                                  {label}
                                </NavLink>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* Rodapé */}
        <div className="px-2 py-2 border-t border-gray-800 space-y-0.5">
          {sidebarOpen ? (
            <>
              {/* Avatar + papel */}
              {papel && (
                <div className="flex items-center gap-2 px-3 py-1.5 mb-1">
                  <div className="w-7 h-7 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center shrink-0">
                    <span className="text-[11px] font-bold text-gray-300 select-none">
                      {papel[0].toUpperCase()}
                    </span>
                  </div>
                  <span className="text-[11px] text-gray-500 capitalize truncate">
                    {papel.replace(/_/g, ' ')}
                  </span>
                </div>
              )}
              <NavLink to="/ajuda"
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 py-2 text-[13px] rounded-lg transition-colors ${isActive ? 'text-white bg-gray-700' : 'text-gray-500 hover:text-white hover:bg-gray-800'}`
                }>
                <span className="text-gray-600 text-xs">?</span>
                Ajuda
              </NavLink>
              <button
                onClick={() => { logout(); navigate('/login') }}
                className="w-full flex items-center gap-2 px-3 py-2 text-[13px] text-gray-500 hover:text-red-400 hover:bg-gray-800/60 rounded-lg transition-colors"
              >
                <span>↩</span>
                Sair
              </button>
            </>
          ) : (
            /* Modo recolhido: apenas avatar e ícone de sair centralizados */
            <div className="flex flex-col items-center gap-1">
              {papel && (
                <div className="w-8 h-8 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center" title={papel.replace(/_/g, ' ')}>
                  <span className="text-[11px] font-bold text-gray-300 select-none">{papel[0].toUpperCase()}</span>
                </div>
              )}
              <button
                onClick={() => { logout(); navigate('/login') }}
                title="Sair"
                className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-red-400 hover:bg-gray-800/60 rounded-lg transition-colors"
              >
                <span className="text-base">↩</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Conteúdo principal */}
      <main className="flex-1 overflow-y-auto bg-gray-50 relative">
        <Outlet />

        {/* Botão Home flutuante — visível quando não está na página inicial */}
        {!isHome && (
          <button
            onClick={() => navigate('/')}
            title="Página inicial"
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-gray-300 hover:text-white text-sm font-medium rounded-full shadow-lg border border-gray-700 transition-all hover:shadow-xl hover:-translate-y-0.5"
          >
            <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
            Início
          </button>
        )}
      </main>
    </div>
  )
}
