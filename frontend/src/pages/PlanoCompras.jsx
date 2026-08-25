import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const fmt  = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtQ = (v) => Number(v ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: 4 })

const SUGESTAO_CLS = {
  pregao_eletronico: { badge: 'bg-blue-100 text-blue-800',  dot: 'bg-blue-500',   border: 'border-blue-200' },
  dispensa_agrupada: { badge: 'bg-amber-100 text-amber-800', dot: 'bg-amber-500',  border: 'border-amber-200' },
  dispensa_valor:    { badge: 'bg-green-100 text-green-800', dot: 'bg-green-500',  border: 'border-green-200' },
}

const STATUS_OPTS = ['Rascunho', 'Submetida', 'Em Análise', 'Devolvida', 'Aprovada']

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Plano de Contratações Anual (PCA)',
  descricao: 'Visão consolidada do planejamento anual de contratações do órgão. Agrupa necessidades aprovadas por exercício fiscal para compor o PCA exigido pelo Decreto 10.947/2022.',
  acoes: [
    { label: 'Iniciar Aquisição', texto: 'Transforma uma necessidade aprovada no PCA em um processo de contratação, criando DFD e demais peças automaticamente.' },
    { label: 'Exportar',          texto: 'Exporta o PCA em formato Excel ou PDF para encaminhamento ao órgão central.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 12, IV e Decreto 10.947/2022 (PCA).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PlanoCompras() {
  const navigate = useNavigate()
  const [dados,    setDados]    = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [expanded, setExpanded] = useState({})
  const [filters,  setFilters]  = useState({
    exercicio: new Date().getFullYear(),
    status: '',
    familia: '',
  })
  const [exportLoading, setExportLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.exercicio) params.exercicio = filters.exercicio
      if (filters.status)    params.status    = filters.status
      if (filters.familia)   params.familia   = filters.familia
      const { data } = await api.get('/indicadores/plano-compras/', { params })
      setDados(data)
      // Expandir todas por padrão
      const exp = {}
      ;(data.familias || []).forEach(f => { exp[f.familia] = true })
      setExpanded(exp)
    } catch { setDados(null) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const handleExport = async () => {
    setExportLoading(true)
    try {
      const params = new URLSearchParams({ export: 'pdf' })
      if (filters.exercicio) params.append('exercicio', filters.exercicio)
      if (filters.status)    params.append('status',    filters.status)
      if (filters.familia)   params.append('familia',   filters.familia)
      const resp = await api.get(`/indicadores/plano-compras/?${params}`, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url; a.download = `PlanoCompras-${filters.exercicio || ''}.pdf`; a.click()
      URL.revokeObjectURL(url)
    } finally { setExportLoading(false) }
  }

  return (
    <div className="p-6 lg:p-8">
      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Plano de Compras</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Itens agrupados por família SIMPAS com sugestão de modalidade de aquisição.
          </p>
        </div>
        <button onClick={handleExport} disabled={exportLoading || !dados}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {exportLoading ? 'Gerando PDF...' : '↓ Exportar PDF'}
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" min="2020" max="2050" value={filters.exercicio}
            onChange={e => setFilters(p => ({ ...p, exercicio: e.target.value }))}
            className="w-24 border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status DFD</label>
          <select value={filters.status}
            onChange={e => setFilters(p => ({ ...p, status: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
            <option value="">Todos (exceto Cancelado)</option>
            {STATUS_OPTS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Família SIMPAS</label>
          <input type="text" value={filters.familia} placeholder="Ex: 42.40"
            onChange={e => setFilters(p => ({ ...p, familia: e.target.value }))}
            className="w-28 border border-gray-300 rounded-lg px-3 py-1.5 text-sm font-mono" />
        </div>
        <button onClick={load}
          className="bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
          Atualizar
        </button>
      </div>

      {loading ? <LoadingSpinner /> : !dados ? (
        <p className="text-sm text-gray-400">Nenhum dado disponível. Verifique os filtros.</p>
      ) : (
        <>
          {/* Cards de resumo */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Famílias',        value: dados.total_familias,              cls: 'text-gray-800' },
              { label: 'Valor Total',      value: fmt(dados.valor_total),           cls: 'text-blue-700' },
              { label: 'Limite Dispensa',  value: fmt(dados.limite_dispensa),       cls: 'text-amber-700' },
              { label: 'Pregões sugeridos', value: dados.familias?.filter(f => f.sugestao === 'pregao_eletronico').length, cls: 'text-blue-700' },
            ].map(({ label, value, cls }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
                <p className={`text-xl font-bold ${cls}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Legenda */}
          <div className="flex gap-3 mb-4 text-xs text-gray-500">
            {[
              { sugestao: 'pregao_eletronico', label: 'Pregão Eletrônico' },
              { sugestao: 'dispensa_agrupada', label: 'Dispensa Agrupada' },
              { sugestao: 'dispensa_valor',    label: 'Dispensa por Valor' },
            ].map(({ sugestao, label }) => (
              <span key={sugestao} className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${SUGESTAO_CLS[sugestao]?.dot}`} />
                {label}
              </span>
            ))}
          </div>

          {/* Lista de famílias */}
          {dados.familias.length === 0 ? (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-center">
              <p className="text-sm font-semibold text-amber-800">Nenhum item com código SIMPAS encontrado</p>
              <p className="text-xs text-amber-600 mt-1">
                Vincule itens do catálogo SIMPAS ao criar DFDs para que apareçam aqui.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {dados.familias.map(fam => {
                const cls = SUGESTAO_CLS[fam.sugestao] || SUGESTAO_CLS.dispensa_valor
                const aberta = expanded[fam.familia] !== false
                return (
                  <div key={fam.familia} className={`bg-white border rounded-xl overflow-hidden ${cls.border}`}>
                    {/* Cabeçalho da família */}
                    <button
                      className="w-full flex items-center justify-between px-5 py-3 hover:bg-gray-50 transition-colors"
                      onClick={() => setExpanded(p => ({ ...p, [fam.familia]: !aberta }))}>
                      <div className="flex items-center gap-3">
                        <span className={`w-3 h-3 rounded-full shrink-0 ${cls.dot}`} />
                        <span className="font-mono text-base font-bold text-gray-800">{fam.familia}</span>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls.badge}`}>
                          {fam.sugestao_label}
                        </span>
                        <span className="text-xs text-gray-400">
                          {fam.total_dfds} DFD{fam.total_dfds !== 1 ? 's' : ''} ·
                          {Object.entries(fam.status_counts || {}).map(([s, n]) => ` ${n} ${s}`).join(' ·')}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-sm font-bold text-gray-700">{fmt(fam.valor_total)}</span>
                        <button
                          type="button"
                          onClick={e => {
                            e.stopPropagation()
                            navigate('/aquisicao/preparar', {
                              state: {
                                origem:             'familia',
                                familia:            fam.familia,
                                exercicio:          filters.exercicio,
                                itens_consolidados: fam.itens_consolidados,
                                sugestao:           fam.sugestao,
                                sugestao_label:     fam.sugestao_label,
                                valor_total:        fam.valor_total,
                              },
                            })
                          }}
                          className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg font-medium whitespace-nowrap">
                          Iniciar Aquisição →
                        </button>
                        <span className="text-gray-400 text-xs">{aberta ? '▲' : '▼'}</span>
                      </div>
                    </button>

                    {/* Tabela de itens consolidados */}
                    {aberta && (
                      <div className="border-t border-gray-100 overflow-x-auto">
                        <table className="w-full text-xs">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="text-left px-4 py-2 font-medium text-gray-500">Código</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-500">Descrição</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-500">SIMPAS</th>
                              <th className="text-center px-4 py-2 font-medium text-gray-500">Unid.</th>
                              <th className="text-right px-4 py-2 font-medium text-gray-500">Qtd. Total</th>
                              <th className="text-right px-4 py-2 font-medium text-gray-500">Vl. Unit.</th>
                              <th className="text-right px-4 py-2 font-medium text-gray-500">Vl. Total</th>
                              <th className="text-left px-4 py-2 font-medium text-gray-500">DFDs</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-50">
                            {(fam.itens_consolidados || []).map((it, i) => (
                              <tr key={i} className="hover:bg-gray-50">
                                <td className="px-4 py-2 font-mono text-blue-700 font-semibold">{it.catalogo_codigo}</td>
                                <td className="px-4 py-2 text-gray-800 max-w-xs">{it.catalogo_nome}</td>
                                <td className="px-4 py-2 font-mono text-gray-500 text-[10px]">{it.catalogo_simpas || '—'}</td>
                                <td className="px-4 py-2 text-center text-gray-500">{it.unidade_medida}</td>
                                <td className="px-4 py-2 text-right font-semibold text-gray-800">{fmtQ(it.quantidade_total)}</td>
                                <td className="px-4 py-2 text-right text-gray-600">{fmt(it.valor_unitario)}</td>
                                <td className="px-4 py-2 text-right font-bold text-gray-800">{fmt(it.valor_total_consolidado)}</td>
                                <td className="px-4 py-2 text-gray-500">
                                  {(it.dfds || []).map(d => (
                                    <span key={d} className="inline-block bg-gray-100 font-mono text-[10px] px-1 py-0.5 rounded mr-1">{d}</span>
                                  ))}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                          <tfoot className="border-t border-gray-200 bg-blue-50/40">
                            <tr>
                              <td colSpan={6} className="px-4 py-2 text-right text-xs font-semibold text-gray-500 uppercase">Total da família</td>
                              <td className="px-4 py-2 text-right font-bold text-gray-800">{fmt(fam.valor_total)}</td>
                              <td />
                            </tr>
                          </tfoot>
                        </table>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}
    </div>
  )
}
