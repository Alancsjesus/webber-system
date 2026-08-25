import { useEffect, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const STATUS_OPTS = [
  { value: '', label: 'Todos os status' },
  { value: 'pendente', label: 'Pendente' },
  { value: 'consolidado', label: 'Consolidado' },
  { value: 'necessidade_gerada', label: 'Necessidade Gerada' },
  { value: 'cancelado', label: 'Cancelado' },
]

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Relatório de Itens — Plano de Aplicação',
  descricao: 'Lista item a item de todos os Planos de Aplicação, cruzando pendentes e executados, com filtros por exercício, órgão beneficiário, natureza, status e situação de execução.',
  acoes: [
    { label: 'Filtros',        texto: 'Combine exercício, órgão beneficiário, natureza (Custeio/Investimento), status do item e se já foi executado (tem Contrato gerado) para refinar a lista.' },
    { label: 'Exportar PDF',   texto: 'Gera o relatório filtrado em PDF.' },
    { label: 'Exportar XLSX',  texto: 'Gera o relatório filtrado em planilha Excel, útil para análises fora do sistema.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FespRelatorioItens() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(false)
  const [exportLoading, setExportLoading] = useState(null) // 'pdf' | 'xlsx' | null
  const [filters, setFilters] = useState({
    exercicio: '', org_beneficiaria: '', natureza: '', status: '', executado: '', eixo: '',
  })

  const buildParams = () => {
    const params = {}
    for (const [k, v] of Object.entries(filters)) if (v !== '') params[k] = v
    return params
  }

  const load = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/fesp/relatorio-itens/', { params: buildParams() })
      setDados(data)
    } catch { setDados(null) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleExport = async (format) => {
    setExportLoading(format)
    try {
      const params = { ...buildParams(), export: format }
      const resp = await api.get('/fesp/relatorio-itens/', { params, responseType: 'blob' })
      const mime = format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      const url = URL.createObjectURL(new Blob([resp.data], { type: mime }))
      const a = document.createElement('a')
      a.href = url
      a.download = `RelatorioItensFESP-${filters.exercicio || ''}.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } finally { setExportLoading(null) }
  }

  const set = (k, v) => setFilters((p) => ({ ...p, [k]: v }))

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Relatório de Itens — Plano de Aplicação</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Itens pendentes de aquisição ou já executados, com filtros e exportação.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => handleExport('pdf')} disabled={!!exportLoading || !dados}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-50 text-sm font-medium px-4 py-2 rounded-lg">
            {exportLoading === 'pdf' ? 'Gerando...' : '↓ Exportar PDF'}
          </button>
          <button onClick={() => handleExport('xlsx')} disabled={!!exportLoading || !dados}
            className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {exportLoading === 'xlsx' ? 'Gerando...' : '↓ Exportar Excel'}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" value={filters.exercicio} onChange={(e) => set('exercicio', e.target.value)}
            className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Natureza</label>
          <select value={filters.natureza} onChange={(e) => set('natureza', e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todas</option>
            <option value="custeio">Custeio</option>
            <option value="investimento">Investimento</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <select value={filters.status} onChange={(e) => set('status', e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Execução</label>
          <select value={filters.executado} onChange={(e) => set('executado', e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos</option>
            <option value="false">Pendentes</option>
            <option value="true">Executados</option>
          </select>
        </div>
        <div className="flex-1 min-w-[160px]">
          <label className="block text-xs font-medium text-gray-600 mb-1">Eixo/Ementa</label>
          <input type="text" value={filters.eixo} onChange={(e) => set('eixo', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
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
              <table className="w-full text-sm min-w-[900px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Plano</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Exercício</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Eixo</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Órgão Benef.</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Meta</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Bem/Serviço</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Status</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dados.itens.map((it) => (
                    <tr key={it.item_id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono text-xs text-gray-700">{it.plano_numero}</td>
                      <td className="px-4 py-2 text-gray-600">{it.exercicio}</td>
                      <td className="px-4 py-2 text-gray-600">{it.eixo}</td>
                      <td className="px-4 py-2 text-gray-600">{it.org_beneficiaria_sigla}</td>
                      <td className="px-4 py-2 text-gray-600">{it.meta_titulo}</td>
                      <td className="px-4 py-2 text-gray-700">{it.bem_servico}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${it.executado ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
                          {it.executado ? 'Executado' : it.status_display}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-right font-semibold text-gray-800">{fmt(it.valor_total_estimado)}</td>
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
