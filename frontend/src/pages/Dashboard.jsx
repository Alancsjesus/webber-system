import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const STATUS_DFD_CLS = {
  Rascunho:  'bg-gray-100 text-gray-600',
  Submetida: 'bg-blue-100 text-blue-700',
  Aprovada:  'bg-green-100 text-green-700',
  Rejeitada: 'bg-red-100 text-red-700',
}

const STATUS_NEC_CLS = {
  Identificada: 'bg-gray-100 text-gray-600',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  'DFD Criado': 'bg-blue-100 text-blue-700',
  Cancelada:    'bg-red-100 text-red-700',
}

const STATUS_DOT_CLS = {
  Proposta:      'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'Em Execução': 'bg-blue-100 text-blue-700',
  Concluída:     'bg-purple-100 text-purple-700',
  Cancelada:     'bg-red-100 text-red-700',
}

const STATUS_DOT_BAR = {
  Proposta:      'bg-gray-400',
  'Em Análise':  'bg-yellow-400',
  Aprovada:      'bg-green-500',
  'Em Execução': 'bg-blue-500',
  Concluída:     'bg-purple-500',
  Cancelada:     'bg-red-400',
}

const STATUS_NEC_BAR = {
  Identificada: 'bg-gray-400',
  'Em Análise': 'bg-yellow-400',
  Aprovada:     'bg-green-500',
  'DFD Criado': 'bg-blue-500',
  Cancelada:    'bg-red-400',
}

function fmt(valor) {
  return Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function StatusBar({ porStatus, colorMap }) {
  const total = Object.values(porStatus).reduce((a, b) => a + b, 0)
  if (total === 0) return null
  return (
    <div className="mt-3">
      <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
        {Object.entries(porStatus).map(([status, count]) => (
          <div
            key={status}
            title={`${status}: ${count}`}
            style={{ width: `${(count / total) * 100}%` }}
            className={`${colorMap[status] || 'bg-gray-300'} transition-all`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5">
        {Object.entries(porStatus).map(([status, count]) => (
          <span key={status} className="flex items-center gap-1 text-xs text-gray-500">
            <span className={`inline-block w-2 h-2 rounded-full ${colorMap[status] || 'bg-gray-300'}`} />
            {status}: {count}
          </span>
        ))}
      </div>
    </div>
  )
}

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

  if (loading) {
    return <div className="p-8 text-sm text-gray-400">Carregando...</div>
  }

  const nec = stats?.necessidades ?? {}
  const dfds = stats?.dfds ?? {}
  const dot = stats?.dotacoes ?? {}

  const aprovadas = nec.por_status?.Aprovada ?? 0
  const pendentes = (dfds.por_status?.Rascunho ?? 0) + (dfds.por_status?.Submetida ?? 0)
  const emExecucao = dot.por_status?.['Em Execução'] ?? 0

  return (
    <div className="p-8">
      <div className="mb-7">
        <h1 className="text-xl font-bold text-gray-800">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-0.5">Visão geral do sistema</p>
      </div>

      {/* Cards — 3 colunas */}
      <div className="grid grid-cols-1 gap-4 mb-4 sm:grid-cols-3">
        <Card
          label="Necessidades"
          value={nec.total ?? 0}
          sub={`${aprovadas} aprovada(s)`}
          color="blue"
          onClick={() => navigate('/planejamento/necessidades')}
        />
        <Card
          label="DFDs"
          value={dfds.total ?? 0}
          sub={`${pendentes} pendente(s)`}
          color="green"
          onClick={() => navigate('/demanda/dfd')}
        />
        <Card
          label="Dotações"
          value={dot.total ?? 0}
          sub={`${emExecucao} em execução`}
          color="purple"
          onClick={() => navigate('/orcamento/dotacoes')}
        />
      </div>

      {/* Cards de valor */}
      <div className="grid grid-cols-1 gap-4 mb-8 sm:grid-cols-3">
        <ValueCard
          label="Valor planejado"
          value={fmt(nec.valor_total ?? 0)}
          sub="total de necessidades"
        />
        <ValueCard
          label="Valor em demanda"
          value={fmt(dfds.valor_total ?? 0)}
          sub="total de DFDs"
        />
        <ValueCard
          label="Total dotado"
          value={fmt(dot.valor_total ?? 0)}
          sub="dotações orçamentárias"
          highlight
        />
      </div>

      {/* Distribuição por status */}
      <div className="grid grid-cols-1 gap-4 mb-8 sm:grid-cols-2">
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Necessidades por status</h2>
          {Object.keys(nec.por_status ?? {}).length === 0
            ? <p className="text-xs text-gray-400 mt-2">Sem dados.</p>
            : <StatusBar porStatus={nec.por_status} colorMap={STATUS_NEC_BAR} />
          }
        </section>
        <section className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Dotações por status</h2>
          {Object.keys(dot.por_status ?? {}).length === 0
            ? <p className="text-xs text-gray-400 mt-2">Sem dados.</p>
            : <StatusBar porStatus={dot.por_status} colorMap={STATUS_DOT_BAR} />
          }
        </section>
      </div>

      {/* Tabelas recentes — 3 colunas */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

        {/* Necessidades recentes */}
        <RecentTable
          title="Necessidades recentes"
          onVerTodas={() => navigate('/planejamento/necessidades')}
          empty="Nenhuma necessidade ainda."
          footerLabel="+ Nova necessidade"
          onFooter={() => navigate('/planejamento/necessidades/nova')}
        >
          {(nec.recentes ?? []).map((n) => (
            <li
              key={n.id}
              onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{n.titulo}</p>
                <p className="text-xs text-gray-400 mt-0.5">{fmt(n.valor_estimado)}</p>
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_NEC_CLS[n.status] || ''}`}>
                {n.status}
              </span>
            </li>
          ))}
        </RecentTable>

        {/* DFDs recentes */}
        <RecentTable
          title="DFDs recentes"
          onVerTodas={() => navigate('/demanda/dfd')}
          empty="Nenhum DFD ainda."
          footerLabel="+ Novo DFD"
          onFooter={() => navigate('/demanda/dfd/novo')}
        >
          {(dfds.recentes ?? []).map((d) => (
            <li
              key={d.id}
              onClick={() => navigate(`/demanda/dfd/${d.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <p className="text-sm font-mono text-blue-600 truncate">{d.numero_sei}</p>
                <p className="text-xs text-gray-400 mt-0.5 truncate">{d.descricao}</p>
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_DFD_CLS[d.status] || ''}`}>
                {d.status}
              </span>
            </li>
          ))}
        </RecentTable>

        {/* Dotações recentes */}
        <RecentTable
          title="Dotações recentes"
          onVerTodas={() => navigate('/orcamento/dotacoes')}
          empty="Nenhuma dotação ainda."
          footerLabel="+ Nova dotação"
          onFooter={() => navigate('/orcamento/dotacoes/nova')}
        >
          {(dot.recentes ?? []).map((d) => (
            <li
              key={d.id}
              onClick={() => navigate(`/orcamento/dotacoes/${d.id}`)}
              className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between gap-3"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {d['acao__codigo']} — {d['acao__nome']}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">{fmt(d.valor_dotado)} · {d.exercicio_fiscal}</p>
              </div>
              <span className={`shrink-0 px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_DOT_CLS[d.status] || ''}`}>
                {d.status}
              </span>
            </li>
          ))}
        </RecentTable>

      </div>
    </div>
  )
}

function Card({ label, value, sub, color, onClick }) {
  const colors = {
    blue:   'bg-blue-600',
    green:  'bg-green-600',
    purple: 'bg-purple-600',
  }
  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-5 text-white ${colors[color]} ${onClick ? 'cursor-pointer hover:opacity-90 transition-opacity' : ''}`}
    >
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-xs opacity-70 mt-1">{sub}</p>
    </div>
  )
}

function ValueCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl p-5 border ${highlight ? 'bg-purple-50 border-purple-200' : 'bg-gray-50 border-gray-200'}`}>
      <p className="text-xs font-semibold uppercase text-gray-500 mb-1">{label}</p>
      <p className={`text-xl font-bold ${highlight ? 'text-purple-700' : 'text-gray-800'}`}>{value}</p>
      <p className="text-xs text-gray-400 mt-1">{sub}</p>
    </div>
  )
}

function RecentTable({ title, onVerTodas, empty, footerLabel, onFooter, children }) {
  const hasItems = Array.isArray(children) ? children.length > 0 : !!children
  return (
    <section className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        <button onClick={onVerTodas} className="text-xs text-blue-600 hover:underline">
          Ver todos
        </button>
      </div>
      {!hasItems
        ? <p className="text-sm text-gray-400 text-center py-8">{empty}</p>
        : <ul className="divide-y divide-gray-50">{children}</ul>
      }
      <div className="px-4 py-3 border-t border-gray-50">
        <button onClick={onFooter} className="text-sm text-blue-600 hover:underline">
          {footerLabel}
        </button>
      </div>
    </section>
  )
}
