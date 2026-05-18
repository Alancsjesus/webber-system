import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

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
  Rascunho:     'bg-gray-100 text-gray-600',
  Submetido:    'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Devolvido:    'bg-orange-100 text-orange-700',
  Aprovado:     'bg-green-100 text-green-700',
  Cancelado:    'bg-red-100 text-red-700',
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
  Rascunho:           'bg-gray-400',
  Submetida:          'bg-blue-400',
  'Em Análise':       'bg-yellow-400',
  Aprovada:           'bg-green-500',
  'Em Análise (DFD)': 'bg-indigo-400',
  Rejeitada:          'bg-red-400',
}
const BAR_ETP = {
  Rascunho:     'bg-gray-400',
  Submetido:    'bg-blue-400',
  'Em Análise': 'bg-yellow-400',
  Devolvido:    'bg-orange-400',
  Aprovado:     'bg-green-500',
  Cancelado:    'bg-red-400',
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

// ── Sub-componentes internos ───────────────────────────────────────────────────

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

// ── Componente principal ───────────────────────────────────────────────────────

export default function DashboardAnalytics({ stats, indOrc, indDev, indAgrup }) {
  const navigate = useNavigate()
  const [expandedFamilia, setExpandedFamilia] = useState(null)

  if (!stats) return null

  const nec   = stats.necessidades ?? {}
  const dfds  = stats.dfds         ?? {}
  const dot   = stats.dotacoes     ?? {}
  const etps  = stats.etps         ?? {}
  const trs   = stats.trs          ?? {}
  const porOrgao  = stats.por_orgao ?? []
  const temFilhos = porOrgao.length > 0

  const nec_pendentes = (nec.por_status?.Identificada ?? 0) + (nec.por_status?.['Em Análise'] ?? 0)
  const dfd_pendentes = (dfds.por_status?.Rascunho ?? 0) + (dfds.por_status?.Submetida ?? 0)
  const etp_aprovados = etps.por_status?.Aprovado ?? 0
  const tr_aprovados  = trs.por_status?.Aprovado  ?? 0

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="p-6 space-y-6">

        {/* Cards de contagem */}
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
          <ValueCard label="Valor planejado"  value={fmt(nec.valor_total ?? 0)} sub="total de necessidades" />
          <ValueCard label="Valor em demanda" value={fmt(dfds.valor_total ?? 0)} sub="total de DFDs" />
          <ValueCard label="Total dotado"     value={fmt(dot.valor_total ?? 0)} sub="dotações orçamentárias" highlight />
        </div>

        {/* Distribuição por status */}
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

        {/* Breakdown por órgão */}
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
                          {o.eh_filho && <span className="text-gray-300 text-xs">↳</span>}
                          <span className={`font-semibold ${o.eh_filho ? 'text-purple-700' : 'text-gray-800'}`}>{o.orgao_sigla}</span>
                          <span className="text-xs text-gray-400 hidden sm:inline truncate max-w-[160px]">{o.orgao_nome}</span>
                          {o.eh_filho && <span className="text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">filho</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center font-medium text-gray-700">{o.necessidades_total}</td>
                      <td className="px-4 py-3 text-center font-medium text-gray-700">{o.dfds_total}</td>
                      <td className="px-4 py-3 text-center font-medium text-gray-700">{o.etps_total}</td>
                      <td className="px-4 py-3 text-center font-medium text-gray-700">{o.trs_total}</td>
                      <td className="px-4 py-3 text-right text-gray-600 text-xs">{fmt(o.valor_total)}</td>
                      <td className="px-4 py-3 text-center">
                        {o.aceites_pendentes > 0
                          ? <span className="inline-flex items-center gap-1 bg-amber-100 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-full">⚠ {o.aceites_pendentes}</span>
                          : <span className="text-gray-300 text-xs">—</span>}
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

        {/* Indicadores */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

          {indOrc && (
            <section className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-gray-700">Execução Orçamentária</h2>
                  {indOrc.exercicio && <p className="text-xs text-gray-400 mt-0.5">Exercício {indOrc.exercicio}</p>}
                </div>
                <button onClick={() => navigate('/orcamento/dotacoes')} className="text-xs text-blue-600 hover:underline">Ver dotações</button>
              </div>
              <div className="space-y-2 mb-4">
                {[
                  { label: 'Dotado',          value: indOrc.totais.dotado,          pct: 100,                               cor: 'bg-blue-500' },
                  { label: 'Indicado',        value: indOrc.totais.indicado,        pct: indOrc.totais.pct_indicado,        cor: 'bg-yellow-500' },
                  { label: 'Descentralizado', value: indOrc.totais.descentralizado, pct: indOrc.totais.pct_descentralizado, cor: 'bg-orange-500' },
                  { label: 'Concedido',       value: indOrc.totais.concedido,       pct: indOrc.totais.pct_concedido,       cor: 'bg-green-500' },
                ].map(({ label, value, pct, cor }) => (
                  <div key={label}>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-0.5">
                      <span className="font-medium">{label}</span>
                      <span className="font-semibold text-gray-700">{fmt(value)} <span className="text-gray-400 font-normal">({pct}%)</span></span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full ${cor} rounded-full transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              {indOrc.por_elemento.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Por elemento de despesa</p>
                  <div className="space-y-1">
                    {indOrc.por_elemento.slice(0, 5).map(el => (
                      <div key={el.elemento_codigo} className="flex items-center justify-between text-xs">
                        <span className="text-gray-600 truncate flex-1">
                          <span className="font-mono text-gray-400 mr-1">{String(el.elemento_codigo).padStart(2, '0')}</span>
                          {el.elemento_descricao}
                        </span>
                        <div className="flex items-center gap-2 ml-2 shrink-0">
                          <span className="text-gray-400">{fmt(el.dotado)}</span>
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${el.pct_indicado > 0 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-400'}`}>
                            {el.pct_indicado}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {indDev && (
            <section className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-semibold text-gray-700">Qualidade Documental</h2>
                  <p className="text-xs text-gray-400 mt-0.5">Taxa de devoluções por tipo de documento</p>
                </div>
              </div>
              <div className="space-y-3">
                {[
                  { tipo: 'DFD',  cor: 'bg-blue-500',   navTo: '/demanda/dfd' },
                  { tipo: 'ETP',  cor: 'bg-purple-500',  navTo: '/etp/etps' },
                  { tipo: 'TR',   cor: 'bg-teal-500',    navTo: '/analise-tecnica/trs' },
                  { tipo: 'Mapa', cor: 'bg-violet-500',  navTo: '/pesquisa/mapa' },
                ].map(({ tipo, cor, navTo }) => {
                  const d    = indDev[tipo] || { total: 0, devolvidos: 0, taxa_devolucao: 0 }
                  const taxa = d.taxa_devolucao
                  const taxaCor = taxa === 0
                    ? 'text-green-600 bg-green-50'
                    : taxa < 20 ? 'text-yellow-700 bg-yellow-50' : 'text-red-600 bg-red-50'
                  return (
                    <div key={tipo} className="flex items-center gap-3">
                      <button onClick={() => navigate(navTo)}
                        className={`w-12 h-6 rounded text-xs font-bold text-white flex items-center justify-center shrink-0 ${cor} hover:opacity-80`}>
                        {tipo}
                      </button>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-xs text-gray-500">
                            {d.total} doc{d.total !== 1 ? 's' : ''} · {d.devolvidos} devolvido{d.devolvidos !== 1 ? 's' : ''}
                          </span>
                          <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${taxaCor}`}>{taxa}%</span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all ${taxa === 0 ? 'bg-green-400' : taxa < 20 ? 'bg-yellow-400' : 'bg-red-400'}`}
                            style={{ width: `${Math.min(taxa, 100)}%` }} />
                        </div>
                        {d.por_categoria && Object.keys(d.por_categoria).length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {Object.entries(d.por_categoria).map(([cat, count]) => (
                              <span key={cat} className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                                {cat.replace(/_/g, ' ')}: {count}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
              <div className="mt-4 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-400">
                  <span className="text-green-600 font-medium">0%</span> ótimo ·
                  <span className="text-yellow-600 font-medium"> &lt;20%</span> aceitável ·
                  <span className="text-red-600 font-medium"> ≥20%</span> requer atenção
                </p>
              </div>
            </section>
          )}
        </div>

        {/* Sugestão de Agrupamento por Família SIMPAS */}
        {indAgrup && indAgrup.total_familias > 0 && (
          <section className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-sm font-semibold text-gray-700">Sugestão de Agrupamento por Família SIMPAS</h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  Itens de DFDs em aberto agrupados por família — limite de dispensa: {fmt(indAgrup.limite_dispensa)}
                </p>
              </div>
              <button onClick={() => navigate('/config/catalogo')} className="text-xs text-blue-600 hover:underline shrink-0">Ver catálogo</button>
            </div>
            <div className="space-y-3">
              {indAgrup.familias.map(g => {
                const cor = g.sugestao === 'pregao_eletronico'
                  ? { badge: 'bg-blue-100 text-blue-700', border: 'border-blue-200', dot: 'bg-blue-500' }
                  : g.sugestao === 'dispensa_agrupada'
                    ? { badge: 'bg-amber-100 text-amber-700', border: 'border-amber-200', dot: 'bg-amber-500' }
                    : { badge: 'bg-green-100 text-green-700', border: 'border-green-200', dot: 'bg-green-500' }
                const expanded = expandedFamilia === g.familia
                return (
                  <div key={g.familia} className={`border rounded-xl overflow-hidden ${cor.border}`}>
                    <button
                      className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
                      onClick={() => setExpandedFamilia(expanded ? null : g.familia)}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full shrink-0 ${cor.dot}`} />
                        <div className="text-left">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-sm font-semibold text-gray-800">{g.familia}</span>
                            {g.categoria_path && (
                              <span className="text-xs text-purple-600 font-medium">{g.categoria_path}</span>
                            )}
                            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cor.badge}`}>{g.sugestao_label}</span>
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {g.total_itens} item{g.total_itens !== 1 ? 'ns' : ''} em {g.total_dfds} DFD{g.total_dfds !== 1 ? 's' : ''}
                            {' · '}{g.sugestao_motivo}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-sm font-bold text-gray-700">{fmt(g.valor_total)}</span>
                        <span className={`text-gray-400 text-xs transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`}>›</span>
                      </div>
                    </button>
                    {expanded && (
                      <div className="px-4 pb-3 border-t border-gray-100">
                        <table className="w-full text-xs mt-2">
                          <thead>
                            <tr className="text-gray-400 uppercase">
                              <th className="text-left pb-1 font-medium">Item</th>
                              <th className="text-left pb-1 font-medium">DFD</th>
                              <th className="text-left pb-1 font-medium">Status</th>
                              <th className="text-right pb-1 font-medium">Qtd</th>
                              <th className="text-right pb-1 font-medium">Valor Total</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-50">
                            {g.itens.map(item => (
                              <tr key={item.item_id} className="hover:bg-gray-50">
                                <td className="py-1.5 pr-3 max-w-xs">
                                  <span className="font-mono text-blue-700 mr-1">{item.catalogo_codigo}</span>
                                  <span className="text-gray-700 truncate">{item.catalogo_nome}</span>
                                  {item.categoria_path && (
                                    <p className="text-[10px] text-purple-500 mt-0.5 truncate">{item.categoria_path}</p>
                                  )}
                                </td>
                                <td className="py-1.5 font-mono text-gray-600 pr-2">{item.dfd_sei}</td>
                                <td className="py-1.5 pr-2">
                                  <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-600">{item.dfd_status}</span>
                                </td>
                                <td className="py-1.5 text-right text-gray-600">{item.quantidade}</td>
                                <td className="py-1.5 text-right font-semibold text-gray-800">{fmt(item.valor_total)}</td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot>
                            <tr className="border-t border-gray-200">
                              <td colSpan={4} className="pt-2 text-right text-gray-400 font-medium uppercase text-[10px]">Total família</td>
                              <td className="pt-2 text-right font-bold text-gray-800">{fmt(g.valor_total)}</td>
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-400">
              <span className="text-green-600 font-medium">Verde</span> Dispensa por Valor ·
              <span className="text-amber-600 font-medium"> Âmbar</span> Dispensa Agrupada ·
              <span className="text-blue-600 font-medium"> Azul</span> Pregão Eletrônico recomendado
            </div>
          </section>
        )}

      </div>
    </div>
  )
}
