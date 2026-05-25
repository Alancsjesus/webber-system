import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useLicitacaoStore from '../stores/licitacaoStore'
import LoadingSpinner from '../components/LoadingSpinner'
import api from '../services/api'

const MODALIDADE_LABEL = {
  pregao_eletronico:    'Pregão Eletrônico',
  concorrencia:         'Concorrência',
  dispensa_eletronica:  'Dispensa Eletrônica',
  dispensa_tradicional: 'Dispensa Tradicional',
  inexigibilidade:      'Inexigibilidade',
}

const MODALIDADE_CLS = {
  pregao_eletronico:    'bg-blue-100 text-blue-800',
  concorrencia:         'bg-indigo-100 text-indigo-800',
  dispensa_eletronica:  'bg-amber-100 text-amber-800',
  dispensa_tradicional: 'bg-orange-100 text-orange-800',
  inexigibilidade:      'bg-purple-100 text-purple-800',
}

const MODALIDADE_BAR = {
  pregao_eletronico:    'bg-blue-500',
  concorrencia:         'bg-indigo-500',
  dispensa_eletronica:  'bg-amber-500',
  dispensa_tradicional: 'bg-orange-500',
  inexigibilidade:      'bg-purple-500',
}

const STATUS_CLS = {
  'Em Instrução':         'bg-gray-100 text-gray-600',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-700',
  'Aprovado':             'bg-teal-100 text-teal-700',
  'Publicado':            'bg-blue-100 text-blue-700',
  'Em Sessão':            'bg-indigo-100 text-indigo-700',
  'Homologado':           'bg-green-100 text-green-700',
  'Contratado':           'bg-green-200 text-green-800',
  'Deserto':              'bg-red-100 text-red-600',
  'Fracassado':           'bg-red-100 text-red-700',
  'Revogado':             'bg-gray-200 text-gray-500',
  'Anulado':              'bg-gray-200 text-gray-500',
}

const STATUS_BAR = {
  'Em Instrução':         'bg-gray-400',
  'Aguardando Aprovação': 'bg-yellow-400',
  'Aprovado':             'bg-teal-400',
  'Publicado':            'bg-blue-400',
  'Em Sessão':            'bg-indigo-400',
  'Homologado':           'bg-green-400',
  'Contratado':           'bg-green-600',
  'Deserto':              'bg-red-300',
  'Fracassado':           'bg-red-400',
  'Revogado':             'bg-gray-300',
  'Anulado':              'bg-gray-300',
}

const fmt = v => Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtK = v => {
  const n = Number(v || 0)
  if (n >= 1_000_000) return `R$ ${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000)     return `R$ ${(n / 1_000).toFixed(0)}K`
  return fmt(n)
}

// ── Gráfico de barras horizontais simples ─────────────────────────────────────

function BarChart({ rows, keyField, labelField, valueField, barCls, maxValue }) {
  const max = maxValue ?? Math.max(...rows.map(r => r[valueField]), 1)
  return (
    <div className="space-y-2">
      {rows.map(r => {
        const pct = Math.round((r[valueField] / max) * 100)
        const cls = typeof barCls === 'function' ? barCls(r[keyField]) : barCls
        return (
          <div key={r[keyField]}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-xs text-gray-600 truncate max-w-[60%]">{r[labelField]}</span>
              <span className="text-xs font-semibold text-gray-700 ml-2">{r[valueField]}</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${cls || 'bg-blue-400'}`}
                style={{ width: `${Math.max(pct, 2)}%` }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Painel de dashboard ───────────────────────────────────────────────────────

function Dashboard({ exercicio }) {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = exercicio ? { exercicio } : {}
    api.get('/licitacao/procedimento/dashboard/', { params })
      .then(({ data }) => setDados(data))
      .catch(() => setDados(null))
      .finally(() => setLoading(false))
  }, [exercicio])

  if (loading) return <div className="py-6 text-center text-sm text-gray-400">Carregando painel...</div>
  if (!dados)  return null

  const kpis = [
    { label: 'Total',        value: dados.total,        cls: 'text-gray-800' },
    { label: 'Em Andamento', value: dados.em_andamento, cls: 'text-blue-700' },
    { label: 'Concluídos',   value: dados.concluidos,   cls: 'text-green-700' },
    { label: 'Valor Est.',   value: fmtK(dados.valor_total), cls: 'text-indigo-700' },
  ]

  return (
    <div className="space-y-5 mb-6">
      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4">
        {kpis.map(k => (
          <div key={k.label} className="bg-white border border-gray-200 rounded-xl p-4">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{k.label}</p>
            <p className={`text-2xl font-bold ${k.cls}`}>{k.value}</p>
          </div>
        ))}
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-4">Por Modalidade</p>
          {dados.por_modalidade.length === 0
            ? <p className="text-xs text-gray-400 italic">Sem dados.</p>
            : <BarChart
                rows={dados.por_modalidade}
                keyField="modalidade"
                labelField="label"
                valueField="count"
                barCls={k => MODALIDADE_BAR[k] || 'bg-gray-400'}
              />}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-4">Por Status</p>
          {dados.por_status.length === 0
            ? <p className="text-xs text-gray-400 italic">Sem dados.</p>
            : <BarChart
                rows={dados.por_status}
                keyField="status"
                labelField="status"
                valueField="count"
                barCls={k => STATUS_BAR[k] || 'bg-gray-400'}
              />}
        </div>
      </div>

      {/* Valores por modalidade */}
      {dados.por_modalidade.some(r => r.valor > 0) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-4">Valor Estimado por Modalidade</p>
          <BarChart
            rows={dados.por_modalidade.filter(r => r.valor > 0)}
            keyField="modalidade"
            labelField="label"
            valueField="valor"
            barCls={k => MODALIDADE_BAR[k] || 'bg-blue-400'}
            maxValue={Math.max(...dados.por_modalidade.map(r => r.valor), 1)}
          />
          <div className="mt-3 flex flex-wrap gap-3">
            {dados.por_modalidade.filter(r => r.valor > 0).map(r => (
              <div key={r.modalidade} className="text-xs text-gray-500">
                <span className={`inline-block w-2 h-2 rounded-full mr-1 ${MODALIDADE_BAR[r.modalidade] || 'bg-gray-400'}`} />
                {r.label}: <strong>{fmt(r.valor)}</strong>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Página principal ──────────────────────────────────────────────────────────

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Procedimentos Licitatórios',
  descricao: 'Lista de todas as licitações e contratações diretas. Cada procedimento segue o fluxo de instrução, aprovação, publicação, sessão pública e homologação.',
  acoes: [
    { label: '+ Novo Procedimento', texto: 'Cria um novo procedimento. Informe a modalidade (Pregão, Concorrência, Dispensa, Inexigibilidade), objeto, valor estimado e datas.' },
    { label: 'Painel',              texto: 'Abre o dashboard com KPIs: total de procedimentos, valores, distribuição por modalidade e status. Útil para gestão e relatórios.' },
    { label: 'Filtro Modalidade',   texto: 'Filtra por Pregão Eletrônico, Concorrência, Dispensa Eletrônica, Dispensa Tradicional ou Inexigibilidade.' },
    { label: 'Filtro Status',       texto: 'Filtra por fase atual do procedimento: Em Instrução, Aguardando Aprovação, Publicado, Em Sessão, Homologado, etc.' },
    { label: 'Filtro Exercício',    texto: 'Filtra os procedimentos pelo ano de exercício fiscal.' },
  ],
  dica: 'Clique em um procedimento para ver as peças instrutórias, tramitações externas e registrar resultados de lotes.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ProcedimentoList() {
  const navigate  = useNavigate()
  const { procedimentos, total, loading, error, fetchProcedimentos } = useLicitacaoStore()
  const [filtros, setFiltros] = useState({ modalidade: '', status: '', exercicio: new Date().getFullYear().toString() })
  const [verPainel, setVerPainel] = useState(false)

  useEffect(() => {
    const p = {}
    if (filtros.modalidade) p.modalidade = filtros.modalidade
    if (filtros.status)     p.status     = filtros.status
    if (filtros.exercicio)  p.exercicio  = filtros.exercicio
    fetchProcedimentos(p)
  }, [filtros])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando procedimentos..." /></div>

  return (
    <div className="p-8">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Licitações e Contratações Diretas</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} procedimento(s) encontrado(s)</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setVerPainel(v => !v)}
            className={`text-sm font-medium px-4 py-2 rounded-lg border transition-colors ${
              verPainel
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'
            }`}>
            {verPainel ? '▲ Ocultar Painel' : '▦ Painel'}
          </button>
          <button onClick={() => navigate('/licitacao/novo')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm">
            + Novo Procedimento
          </button>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <select value={filtros.modalidade}
          onChange={e => setFiltros(p => ({ ...p, modalidade: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todas as modalidades</option>
          {Object.entries(MODALIDADE_LABEL).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>
        <select value={filtros.status}
          onChange={e => setFiltros(p => ({ ...p, status: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os status</option>
          {['Em Instrução','Aguardando Aprovação','Aprovado','Publicado','Em Sessão',
            'Homologado','Contratado','Deserto','Fracassado','Revogado','Anulado'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input type="number" placeholder="Exercício" value={filtros.exercicio}
          onChange={e => setFiltros(p => ({ ...p, exercicio: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>
      )}

      {/* Painel de dashboard */}
      {verPainel && <Dashboard exercicio={filtros.exercicio} />}

      {/* Lista */}
      {procedimentos.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">⚖️</p>
          <p className="font-medium text-gray-600">Nenhum procedimento encontrado</p>
          <p className="text-sm mt-1">Clique em "+ Novo Procedimento" para criar o primeiro.</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Número</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Modalidade</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Objeto</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Valor Est.</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Abertura</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Tram.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {procedimentos.map(p => (
                <tr key={p.id} onClick={() => navigate(`/licitacao/${p.id}`)}
                  className="hover:bg-blue-50 cursor-pointer transition-colors">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">
                    {p.numero}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${MODALIDADE_CLS[p.modalidade] || 'bg-gray-100 text-gray-600'}`}>
                      {MODALIDADE_LABEL[p.modalidade] || p.modalidade}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs truncate" title={p.objeto}>
                    {p.objeto}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700 font-medium">
                    {p.valor_estimado ? fmt(p.valor_estimado) : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {p.data_abertura
                      ? new Date(p.data_abertura + 'T12:00').toLocaleDateString('pt-BR')
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_CLS[p.status] || 'bg-gray-100 text-gray-600'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {p.tramitacoes_pendentes > 0
                      ? <span className="text-xs bg-red-100 text-red-700 font-medium px-1.5 py-0.5 rounded-full">{p.tramitacoes_pendentes}</span>
                      : <span className="text-gray-300 text-xs">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
