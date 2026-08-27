import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_OPTS = [
  { value: 'andamento', label: 'Em Andamento' },
  { value: 'cpa',       label: 'Em CPA' },
  { value: 'concluido', label: 'Concluído' },
]
const ACAO_OPTS = [
  { value: 'notificacao', label: 'Notificação' },
  { value: 'rescisao',    label: 'Rescisão' },
]
const STATUS_CLS = {
  andamento: 'bg-blue-100 text-blue-700',
  cpa:       'bg-amber-100 text-amber-700',
  concluido: 'bg-green-100 text-green-700',
}
const ACAO_CLS = {
  notificacao: 'bg-gray-100 text-gray-600',
  rescisao:    'bg-red-100 text-red-600',
}
const fmtDate = (v) => v ? new Date(v + 'T00:00').toLocaleDateString('pt-BR') : '—'

function CountCard({ label, value, sub, color }) {
  const bg = { blue: 'bg-blue-600', green: 'bg-green-600', amber: 'bg-amber-500', red: 'bg-red-500', gray: 'bg-gray-600' }
  return (
    <div className={`rounded-xl p-5 text-white ${bg[color]}`}>
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Notificações',
  descricao: 'Visão gerencial das Notificações Contratuais: quantas cada contrato acumulou, o balanço geral por status/ação e um apanhado histórico cronológico de todos os lançamentos.',
  acoes: [
    { label: 'Filtros',              texto: 'Combine Exercício, Status e Ação (Notificação/Rescisão) para restringir tanto a tabela por contrato quanto a linha do tempo.' },
    { label: 'Tabela por Contrato',  texto: 'Um contrato com muitas notificações — especialmente em CPA — merece atenção prioritária. Clique no contrato para abrir o detalhe.' },
    { label: 'Linha do Tempo',       texto: 'Todos os lançamentos ordenados do mais recente para o mais antigo, cruzando todos os contratos.' },
  ],
  dica: 'A ordenação da linha do tempo usa a Data da Notificação quando preenchida; senão usa a data de registro do lançamento.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PainelNotificacoes() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filtros, setFiltros] = useState({ exercicio: '', status: '', tipo_acao: '' })

  const load = () => {
    setLoading(true); setError(null)
    const params = {}
    for (const [k, v] of Object.entries(filtros)) if (v !== '') params[k] = v
    api.get('/contratos/notificacao-painel/', { params })
      .then(({ data }) => setDados(data))
      .catch(() => setError('Erro ao carregar o painel de notificações.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const totais = dados?.totais
  const porContrato = dados?.por_contrato ?? []
  const timeline = dados?.timeline ?? []

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Painel de Notificações</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Quantas notificações/rescisões cada contrato acumulou, e o histórico cronológico de todos os lançamentos.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" value={filtros.exercicio} onChange={(e) => setFiltros((p) => ({ ...p, exercicio: e.target.value }))}
            className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <select value={filtros.status} onChange={(e) => setFiltros((p) => ({ ...p, status: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos</option>
            {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Ação</label>
          <select value={filtros.tipo_acao} onChange={(e) => setFiltros((p) => ({ ...p, tipo_acao: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todas</option>
            {ACAO_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button onClick={load}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Atualizar
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && totais && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <CountCard label="Total" value={totais.total} color="gray" />
            <CountCard label="Em Andamento" value={totais.andamento} color="blue" />
            <CountCard label="Em CPA" value={totais.cpa} color="amber" />
            <CountCard label="Concluído" value={totais.concluido} color="green" />
            <CountCard label="Rescisões" value={totais.rescisoes} sub={`${totais.notificacoes} notificações`} color="red" />
            <CountCard label="Contratos Afetados" value={totais.contratos_afetados} color="gray" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Tabela por Contrato */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Por Contrato</h2>
              {porContrato.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhuma notificação encontrada para os filtros selecionados.</p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs min-w-[560px]">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Contrato</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Fornecedor</th>
                          <th className="text-right px-3 py-2 font-medium text-gray-500">Total</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Por Status</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Última</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {porContrato.map((g) => (
                          <tr key={g.contrato_id} className="hover:bg-gray-50">
                            <td className="px-3 py-2">
                              <Link to={`/contratos/${g.contrato_id}`} className="font-mono text-blue-600 hover:underline" title={g.contrato_objeto}>
                                {g.contrato_numero}
                              </Link>
                            </td>
                            <td className="px-3 py-2 text-gray-600 max-w-[140px] truncate" title={g.fornecedor_nome || ''}>
                              {g.fornecedor_nome || <span className="text-gray-300">—</span>}
                            </td>
                            <td className="px-3 py-2 text-right font-semibold text-gray-800">{g.total}</td>
                            <td className="px-3 py-2">
                              <div className="flex gap-1 flex-wrap">
                                {g.andamento > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CLS.andamento}`}>{g.andamento} andamento</span>}
                                {g.cpa > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CLS.cpa}`}>{g.cpa} CPA</span>}
                                {g.concluido > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CLS.concluido}`}>{g.concluido} concluído</span>}
                              </div>
                            </td>
                            <td className="px-3 py-2 text-gray-500 whitespace-nowrap">{fmtDate(g.ultima_data)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Linha do Tempo */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Linha do Tempo</h2>
              {timeline.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhuma notificação encontrada para os filtros selecionados.</p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-4 max-h-[600px] overflow-y-auto">
                  <ol className="relative border-l-2 border-gray-100 space-y-4 pl-4">
                    {timeline.map((t) => (
                      <li key={t.id} className="relative">
                        <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-blue-500 ring-4 ring-white" />
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-gray-500">{fmtDate(t.data)}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${ACAO_CLS[t.tipo_acao] || 'bg-gray-100 text-gray-600'}`}>{t.tipo_acao_display}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CLS[t.status] || 'bg-gray-100 text-gray-600'}`}>{t.status_display}</span>
                          <Link to={`/contratos/${t.contrato_id}`} className="text-xs font-mono text-blue-600 hover:underline">{t.contrato_numero}</Link>
                        </div>
                        <p className="text-sm text-gray-800 mt-0.5">{t.resumo_fato}</p>
                        {t.fornecedor_nome && <p className="text-xs text-gray-400 mt-0.5">{t.fornecedor_nome}</p>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
