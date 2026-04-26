import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

// ── Status color maps ──────────────────────────────────────────────────────────
const CLS_NEC = {
  Identificada: 'bg-gray-100 text-gray-600',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  'DFD Criado': 'bg-blue-100 text-blue-700',
  Cancelada:    'bg-red-100 text-red-700',
}
const CLS_DFD = {
  Rascunho:  'bg-gray-100 text-gray-600',
  Submetida: 'bg-blue-100 text-blue-700',
  Aprovada:  'bg-green-100 text-green-700',
  Rejeitada: 'bg-red-100 text-red-700',
}
const CLS_ETP = {
  Rascunho:   'bg-gray-100 text-gray-600',
  Submetido:  'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Devolvido:  'bg-orange-100 text-orange-700',
  Aprovado:   'bg-green-100 text-green-700',
  Cancelado:  'bg-red-100 text-red-700',
}
const CLS_DOT = {
  Proposta:      'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'Em Execução': 'bg-blue-100 text-blue-700',
  Concluída:     'bg-purple-100 text-purple-700',
  Cancelada:     'bg-red-100 text-red-700',
}

const BAR_NEC = {
  Identificada: 'bg-gray-400',
  'Em Análise': 'bg-yellow-400',
  Aprovada:     'bg-green-500',
  'DFD Criado': 'bg-blue-500',
  Cancelada:    'bg-red-400',
}
const BAR_DFD = {
  Rascunho:            'bg-gray-400',
  Submetida:           'bg-blue-400',
  'Em Análise':        'bg-yellow-400',
  Aprovada:            'bg-green-500',
  'Em Análise (DFD)':  'bg-indigo-400',
  Rejeitada:           'bg-red-400',
}
const BAR_ETP = {
  Rascunho:   'bg-gray-400',
  Submetido:  'bg-blue-400',
  'Em Análise': 'bg-yellow-400',
  Devolvido:  'bg-orange-400',
  Aprovado:   'bg-green-500',
  Cancelado:  'bg-red-400',
}
const BAR_DOT = {
  Proposta:      'bg-gray-400',
  'Em Análise':  'bg-yellow-400',
  Aprovada:      'bg-green-500',
  'Em Execução': 'bg-blue-500',
  Concluída:     'bg-purple-500',
  Cancelada:     'bg-red-400',
}

function fmt(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function StatusBar({ porStatus, colorMap }) {
  const total = Object.values(porStatus).reduce((a, b) => a + b, 0)
  if (total === 0) return <p className="text-xs text-gray-400 mt-2">Sem dados.</p>
  return (
    <div className="mt-2">
      <div className="flex h-2 rounded-full overflow-hidden gap-px">
        {Object.entries(porStatus).map(([s, c]) => (
          <div key={s} title={`${s}: ${c}`}
            style={{ width: `${(c / total) * 100}%` }}
            className={`${colorMap[s] || 'bg-gray-300'} transition-all`} />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
        {Object.entries(porStatus).map(([s, c]) => (
          <span key={s} className="flex items-center gap-1 text-xs text-gray-500">
            <span className={`inline-block w-2 h-2 rounded-full ${colorMap[s] || 'bg-gray-300'}`} />
            {s}: {c}
          </span>
        ))}
      </div>
    </div>
  )
}

function CountCard({ label, value, sub, color, onClick }) {
  const bg = { blue: 'bg-blue-600', green: 'bg-green-600', amber: 'bg-amber-500', indigo: 'bg-indigo-600', purple: 'bg-purple-600' }
  return (
    <div onClick={onClick}
      className={`rounded-xl p-5 text-white ${bg[color]} ${onClick ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''}`}>
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

function ValueCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl p-5 border ${highlight ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200'}`}>
      <p className="text-xs font-semibold uppercase text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${highlight ? 'text-purple-700' : 'text-gray-800'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  )
}

function RecentTable({ title, onVerTodas, empty, footerLabel, onFooter, children }) {
  const hasItems = Array.isArray(children) ? children.length > 0 : !!children
  return (
    <section className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        <button onClick={onVerTodas} className="text-xs text-blue-600 hover:underline">Ver todos</button>
      </div>
      {!hasItems
        ? <p className="text-sm text-gray-400 text-center py-8">{empty}</p>
        : <ul className="divide-y divide-gray-50">{children}</ul>}
      <div className="px-4 py-3 border-t border-gray-50">
        <button onClick={onFooter} className="text-sm text-blue-600 hover:underline">{footerLabel}</button>
      </div>
    </section>
  )
}

function OrgaoTag({ sigla, isFilho }) {
  if (!sigla) return null
  return (
    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${isFilho ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600'}`}>
      {sigla}
    </span>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/dashboard/stats/')
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando dashboard..." /></div>
  if (!stats)  return <div className="p-8 text-sm text-red-400">Erro ao carregar dados.</div>

  const nec   = stats.necessidades ?? {}
  const dfds  = stats.dfds         ?? {}
  const dot   = stats.dotacoes     ?? {}
  const etps  = stats.etps         ?? {}
  const trs   = stats.trs          ?? {}
  const aceitesPendentes = stats.aceites_pendentes ?? 0
  const porOrgao         = stats.por_orgao         ?? []
  const temFilhos        = porOrgao.length > 0

  // Sub-totals for cards
  const nec_pendentes = (nec.por_status?.Identificada ?? 0) + (nec.por_status?.['Em Análise'] ?? 0)
  const dfd_pendentes = (dfds.por_status?.Rascunho ?? 0) + (dfds.por_status?.Submetida ?? 0)
  const etp_aprovados = etps.por_status?.Aprovado ?? 0
  const tr_aprovados  = trs.por_status?.Aprovado  ?? 0

  return (
    <div className="p-8 space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">Visão geral do sistema</p>
      </div>

      {/* Banner: onboarding quando sistema está vazio */}
      {(nec.total ?? 0) === 0 && (dfds.total ?? 0) === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
          <div className="flex items-start gap-3">
            <span className="text-blue-500 text-xl mt-0.5">🚀</span>
            <div>
              <p className="text-sm font-semibold text-blue-800 mb-2">Bem-vindo ao WEBBER System!</p>
              <p className="text-xs text-blue-600 mb-3">O sistema está pronto. Siga os passos abaixo para começar:</p>
              <ol className="space-y-1.5">
                {[
                  { step: '1', label: 'Configure os órgãos e unidades', path: '/config/orgaos', cta: 'Ir para Configurações' },
                  { step: '2', label: 'Cadastre as ações orçamentárias', path: '/config/acoes', cta: 'Ir para Ações' },
                  { step: '3', label: 'Crie a primeira necessidade de planejamento', path: '/planejamento/necessidades/nova', cta: 'Nova Necessidade' },
                ].map(({ step, label, path, cta }) => (
                  <li key={step} className="flex items-center gap-2 text-xs text-blue-700">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-200 text-blue-800 font-bold flex items-center justify-center text-[10px]">{step}</span>
                    <span className="flex-1">{label}</span>
                    <button onClick={() => navigate(path)}
                      className="text-blue-600 hover:text-blue-800 font-medium hover:underline">{cta} →</button>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* Banner: aceites pendentes */}
      {aceitesPendentes > 0 && (
        <button
          onClick={() => navigate('/planejamento/aceite')}
          className="w-full flex items-center gap-3 bg-amber-50 border border-amber-300 rounded-xl px-5 py-3 text-left hover:bg-amber-100 transition-colors"
        >
          <span className="text-amber-500 text-xl">⚠</span>
          <div>
            <p className="text-sm font-semibold text-amber-800">
              {aceitesPendentes} necessidade{aceitesPendentes > 1 ? 's' : ''} de órgão{aceitesPendentes > 1 ? 's' : ''} filho{aceitesPendentes > 1 ? 's' : ''} aguardando aceite
            </p>
            <p className="text-xs text-amber-600">Clique para revisar e aceitar/recusar</p>
          </div>
          <span className="ml-auto text-amber-500 text-lg">›</span>
        </button>
      )}

      {/* Cards de contagem — 5 colunas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
        <CountCard label="Necessidades" value={nec.total ?? 0}
          sub={`${nec_pendentes} pendente(s)`} color="blue"
          onClick={() => navigate('/planejamento/necessidades')} />
        <CountCard label="DFDs" value={dfds.total ?? 0}
          sub={`${dfd_pendentes} pendente(s)`} color="green"
          onClick={() => navigate('/demanda/dfd')} />
        <CountCard label="ETPs" value={etps.total ?? 0}
          sub={`${etp_aprovados} aprovado(s)`} color="amber"
          onClick={() => navigate('/etp/etps')} />
        <CountCard label="Termos de Ref." value={trs.total ?? 0}
          sub={`${tr_aprovados} aprovado(s)`} color="indigo"
          onClick={() => navigate('/analise-tecnica/trs')} />
        <CountCard label="Dotações" value={dot.total ?? 0}
          sub={`${dot.por_status?.['Em Execução'] ?? 0} em execução`} color="purple"
          onClick={() => navigate('/orcamento/dotacoes')} />
      </div>

      {/* Cards de valor */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <ValueCard label="Valor planejado" value={fmt(nec.valor_total ?? 0)} sub="total de necessidades" />
        <ValueCard label="Valor em demanda" value={fmt(dfds.valor_total ?? 0)} sub="total de DFDs" />
        <ValueCard label="Total dotado" value={fmt(dot.valor_total ?? 0)} sub="dotações orçamentárias" highlight />
      </div>

      {/* Distribuição por status — 2×2 grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700">Necessidades por status</h2>
          <StatusBar porStatus={nec.por_status ?? {}} colorMap={BAR_NEC} />
        </section>
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700">DFDs por status</h2>
          <StatusBar porStatus={dfds.por_status ?? {}} colorMap={BAR_DFD} />
        </section>
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700">ETPs por status</h2>
          <StatusBar porStatus={etps.por_status ?? {}} colorMap={BAR_ETP} />
        </section>
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700">Dotações por status</h2>
          <StatusBar porStatus={dot.por_status ?? {}} colorMap={BAR_DOT} />
        </section>
      </div>

      {/* Breakdown por órgão — apenas para órgãos pai */}
      {temFilhos && (
        <section className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100">
            <h2 className="text-sm font-semibold text-gray-700">Demandas por órgão</h2>
            <p className="text-xs text-gray-400 mt-0.5">Órgãos filhos exibem apenas necessidades de execução externa repassadas ao órgão pai</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-5 py-2.5 text-left">Órgão</th>
                  <th className="px-4 py-2.5 text-center">Necessidades</th>
                  <th className="px-4 py-2.5 text-center">DFDs</th>
                  <th className="px-4 py-2.5 text-center">ETPs</th>
                  <th className="px-4 py-2.5 text-center">TRs</th>
                  <th className="px-4 py-2.5 text-right">Valor estimado</th>
                  <th className="px-4 py-2.5 text-center">Aceites pendentes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {porOrgao.map((o) => (
                  <tr key={o.orgao_id} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        {o.eh_filho && (
                          <span className="text-gray-300 text-xs">↳</span>
                        )}
                        <span className={`font-semibold ${o.eh_filho ? 'text-purple-700' : 'text-gray-800'}`}>
                          {o.orgao_sigla}
                        </span>
                        <span className="text-xs text-gray-400 hidden sm:inline truncate max-w-[160px]">{o.orgao_nome}</span>
                        {o.eh_filho && (
                          <span className="text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">filho</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{o.necessidades_total}</td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{o.dfds_total}</td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{o.etps_total}</td>
                    <td className="px-4 py-3 text-center font-medium text-gray-700">{o.trs_total}</td>
                    <td className="px-4 py-3 text-right text-gray-600 text-xs">{fmt(o.valor_total)}</td>
                    <td className="px-4 py-3 text-center">
                      {o.aceites_pendentes > 0
                        ? <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-full">
                            ⚠ {o.aceites_pendentes}
                          </span>
                        : <span className="text-gray-300 text-xs">—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Tabelas de itens recentes */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

        <RecentTable title="Necessidades recentes"
          onVerTodas={() => navigate('/planejamento/necessidades')}
          empty="Nenhuma necessidade ainda."
          footerLabel="+ Nova necessidade"
          onFooter={() => navigate('/planejamento/necessidades/nova')}>
          {(nec.recentes ?? []).map((n) => (
            <li key={n.id} onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-gray-800 truncate">{n.titulo}</p>
                  {temFilhos && <OrgaoTag sigla={n['org_id__sigla']} isFilho={n['org_id__sigla'] !== (porOrgao[0]?.orgao_sigla)} />}
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{fmt(n.valor_estimado)}</p>
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${CLS_NEC[n.status] || 'bg-gray-100 text-gray-600'}`}>
                {n.status}
              </span>
            </li>
          ))}
        </RecentTable>

        <RecentTable title="DFDs recentes"
          onVerTodas={() => navigate('/demanda/dfd')}
          empty="Nenhum DFD ainda."
          footerLabel="+ Novo DFD"
          onFooter={() => navigate('/demanda/dfd/novo')}>
          {(dfds.recentes ?? []).map((d) => (
            <li key={d.id} onClick={() => navigate(`/demanda/dfd/${d.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-mono text-blue-600 truncate">{d.numero_sei}</p>
                  {temFilhos && <OrgaoTag sigla={d['org_id__sigla']} isFilho={d['org_id__sigla'] !== (porOrgao[0]?.orgao_sigla)} />}
                </div>
                <p className="text-xs text-gray-400 mt-0.5 truncate">{d.descricao}</p>
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${CLS_DFD[d.status] || 'bg-gray-100 text-gray-600'}`}>
                {d.status}
              </span>
            </li>
          ))}
        </RecentTable>

        <RecentTable title="ETPs recentes"
          onVerTodas={() => navigate('/etp/etps')}
          empty="Nenhum ETP ainda."
          footerLabel="Ver todos ETPs"
          onFooter={() => navigate('/etp/etps')}>
          {(etps.recentes ?? []).map((e) => (
            <li key={e.id} onClick={() => navigate(`/etp/etps/${e.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-mono text-amber-600 truncate">{e.numero_sei}</p>
                  {temFilhos && <OrgaoTag sigla={e['dfd__org_id__sigla']} isFilho={e['dfd__org_id__sigla'] !== (porOrgao[0]?.orgao_sigla)} />}
                </div>
                {e.estimativa_valor && (
                  <p className="text-xs text-gray-400 mt-0.5">{fmt(e.estimativa_valor)}</p>
                )}
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${CLS_ETP[e.status] || 'bg-gray-100 text-gray-600'}`}>
                {e.status}
              </span>
            </li>
          ))}
        </RecentTable>

      </div>
    </div>
  )
}
