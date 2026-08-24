import { useEffect, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const STATUS_OPTS = [
  { value: '', label: 'Todos os status' },
  { value: 'Pago', label: 'Pago' },
  { value: 'Liquidado', label: 'Liquidado' },
  { value: 'Empenhado', label: 'Empenhado' },
  { value: 'Em Diligência', label: 'Em Diligência' },
  { value: 'Indicado', label: 'Indicado' },
  { value: 'Sem Execução', label: 'Sem Execução' },
]

const STATUS_EXECUCAO_CLS = {
  'Pago':          'bg-teal-100 text-teal-700',
  'Liquidado':     'bg-purple-100 text-purple-700',
  'Empenhado':     'bg-blue-100 text-blue-700',
  'Em Diligência': 'bg-amber-100 text-amber-700',
  'Indicado':      'bg-gray-100 text-gray-600',
  'Sem Execução':  'bg-gray-50 text-gray-400',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Relatório de Indicações por Fonte',
  descricao: 'Cruza todas as Indicações Orçamentárias do órgão numa única lista de itens/dotações, independente de a qual indicação cada linha pertence — útil para ver, por Fonte de Recurso, tudo que já foi indicado, empenhado, liquidado e pago.',
  acoes: [
    { label: 'Filtro Fonte de Recurso', texto: 'Restringe a lista às dotações de uma fonte específica (ex: uma emenda parlamentar, um fundo).' },
    { label: 'Filtro Exercício',        texto: 'Filtra pelo ano fiscal da indicação de origem.' },
    { label: 'Filtro Status',           texto: 'Filtra pelo estágio de execução atual de cada linha (Pago, Liquidado, Empenhado, Em Diligência, Indicado ou Sem Execução).' },
  ],
  dica: 'A coluna "Beneficiada" mostra Sim quando a demanda de origem (DFD ou Necessidade) é execução externa (para outro órgão); fica em branco quando não há como determinar.',
  baseLegal: 'Lei 14.133/2021 — Art. 7º (indicação orçamentária) e Lei 4.320/1964, arts. 58-64 (estágios da despesa: empenho, liquidação, pagamento).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function RelatorioIndicacoes() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fontes, setFontes] = useState([])
  const [filters, setFilters] = useState({ fonte_recurso: '', exercicio_fiscal: '', status_execucao: '' })

  useEffect(() => {
    api.get('/orcamento/fonte-recurso/', { params: { page_size: 200 } })
      .then(({ data }) => setFontes(data.results ?? data))
      .catch(() => {})
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      for (const [k, v] of Object.entries(filters)) if (v !== '') params[k] = v
      const { data } = await api.get('/orcamento/relatorio-indicacoes/', { params })
      setDados(data)
    } catch { setDados(null) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const set = (k, v) => setFilters((p) => ({ ...p, [k]: v }))

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Relatório de Indicações por Fonte</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Itens de todas as Indicações Orçamentárias, cruzados numa única lista — filtre por fonte de recurso, exercício ou estágio de execução.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Fonte de Recurso</label>
          <select value={filters.fonte_recurso} onChange={(e) => set('fonte_recurso', e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[220px]">
            <option value="">Todas as fontes</option>
            {fontes.map((f) => <option key={f.id} value={f.id}>{f.codigo} — {f.nome}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" value={filters.exercicio_fiscal} onChange={(e) => set('exercicio_fiscal', e.target.value)}
            className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <select value={filters.status_execucao} onChange={(e) => set('status_execucao', e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button onClick={load}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Atualizar
        </button>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && dados && (
        dados.itens.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum item encontrado para os filtros selecionados.</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs min-w-[1200px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Fonte</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Beneficiada</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Item Planejado</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Indicação</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Status</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Diligência</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Indicado</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Empenhado</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Liquidado</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Pago</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Saldo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dados.itens.map((it) => (
                    <tr key={it.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-700">{it.fonte_codigo} — {it.fonte_nome}</td>
                      <td className="px-3 py-2 text-gray-600">{it.beneficiada || '—'}</td>
                      <td className="px-3 py-2 text-gray-700">{it.item_dfd_objeto || <span className="text-gray-300">—</span>}</td>
                      <td className="px-3 py-2 font-mono text-xs text-gray-500">{it.indicacao_numero} <span className="text-gray-400">({it.exercicio_fiscal})</span></td>
                      <td className="px-3 py-2">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium whitespace-nowrap ${STATUS_EXECUCAO_CLS[it.status_execucao] || 'bg-gray-100 text-gray-600'}`}>
                          {it.status_execucao}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-right text-amber-700 font-semibold">
                        {it.em_diligencia ? fmt(it.valor_indicado) : '—'}
                      </td>
                      <td className="px-3 py-2 text-right font-semibold text-gray-800">
                        {it.em_diligencia ? '—' : fmt(it.valor_indicado)}
                      </td>
                      <td className="px-3 py-2 text-right font-semibold text-blue-700">{fmt(it.valor_empenhado)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-purple-700">{fmt(it.valor_liquidado)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-teal-700">{fmt(it.valor_pago)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-gray-500">{fmt(it.saldo)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  )
}
