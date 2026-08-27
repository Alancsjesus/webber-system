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

const AREA_OPTS = [
  { value: 'TI',        label: 'Tecnologia da Informação' },
  { value: 'Formação',  label: 'Formação' },
  { value: 'Ops',       label: 'Operações' },
  { value: 'Rede',      label: 'Rede' },
  { value: 'Frota',     label: 'Frota' },
  { value: 'Derivados', label: 'Derivados' },
]

const BENEFICIADA_OPTS = [
  { value: '', label: 'Todas' },
  { value: 'Sim', label: 'Sim' },
  { value: 'Não', label: 'Não' },
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
  descricao: 'Cruza todas as Indicações Orçamentárias do órgão numa única lista de itens/dotações, independente de a qual indicação cada linha pertence — útil para ver, por Fonte de Recurso, tudo que já foi indicado, empenhado, liquidado e pago, com o contexto completo (objeto, itens do DFD, área de atuação) de cada demanda.',
  acoes: [
    { label: 'Filtros clássicos', texto: 'Fonte, Subfonte, Ação, Natureza e Elemento de Despesa filtram diretamente a dotação; Exercício e Processo SEI filtram a Indicação.' },
    { label: 'Filtros de negócio', texto: 'Área de Aplicação, Órgão Executor, Beneficiada e Instrumento Financeiro (FESP) filtram pela Necessidade/demanda de origem — vazio quando a indicação não tem demanda vinculada.' },
    { label: 'Status',           texto: 'Filtra pelo estágio de execução atual de cada linha (Pago, Liquidado, Empenhado, Em Diligência, Indicado ou Sem Execução).' },
  ],
  dica: 'As colunas "Objeto" e "Itens" mostram sempre a demanda (DFD) como um todo, não só o item eventualmente rateado na linha — a coluna "Item Planejado" continua mostrando o item específico dessa dotação, e valores marcados com "≈" são rateados proporcionalmente, já que empenho/liquidação/pagamento são sempre registrados por dotação, não por item.',
  baseLegal: 'Lei 14.133/2021 — Art. 7º (indicação orçamentária) e Lei 4.320/1964, arts. 58-64 (estágios da despesa: empenho, liquidação, pagamento).',
}
// ──────────────────────────────────────────────────────────────────────────────

const FILTERS_INICIAIS = {
  fonte_recurso: '', subfonte_recurso: '', acao: '', elemento_despesa: '', natureza_despesa: '',
  exercicio_fiscal: '', numero_sei: '',
  area_aplicacao: '', orgao_executor: '', beneficiada: '', instrumento_financeiro: '',
  status_execucao: '',
}

export default function RelatorioIndicacoes() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fontes, setFontes] = useState([])
  const [subfontes, setSubfontes] = useState([])
  const [acoes, setAcoes] = useState([])
  const [elementos, setElementos] = useState([])
  const [naturezas, setNaturezas] = useState([])
  const [orgaos, setOrgaos] = useState([])
  const [instrumentos, setInstrumentos] = useState([])
  const [filters, setFilters] = useState(FILTERS_INICIAIS)

  useEffect(() => {
    api.get('/orcamento/fonte-recurso/', { params: { page_size: 200 } })
      .then(({ data }) => setFontes(data.results ?? data)).catch(() => {})
    api.get('/orcamento/subfonte-recurso/', { params: { page_size: 200 } })
      .then(({ data }) => setSubfontes(data.results ?? data)).catch(() => {})
    api.get('/orcamento/acao/', { params: { page_size: 200 } })
      .then(({ data }) => setAcoes(data.results ?? data)).catch(() => {})
    api.get('/orcamento/elemento-despesa/', { params: { page_size: 200 } })
      .then(({ data }) => setElementos(data.results ?? data)).catch(() => {})
    api.get('/orcamento/natureza-despesa/', { params: { page_size: 200 } })
      .then(({ data }) => setNaturezas(data.results ?? data)).catch(() => {})
    api.get('/core/orgaos/', { params: { page_size: 200 } })
      .then(({ data }) => setOrgaos(data.results ?? data)).catch(() => {})
    api.get('/fesp/instrumento/', { params: { page_size: 200 } })
      .then(({ data }) => setInstrumentos(data.results ?? data)).catch(() => {})
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
          Itens de todas as Indicações Orçamentárias, cruzados numa única lista — filtre por fonte, dotação, demanda de origem ou estágio de execução.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 space-y-3">
        <div className="flex flex-wrap gap-3 items-end">
          <Select label="Fonte de Recurso" value={filters.fonte_recurso} onChange={(v) => set('fonte_recurso', v)}
            options={[{ value: '', label: 'Todas as fontes' }, ...fontes.map((f) => ({ value: f.id, label: `${f.codigo} — ${f.nome}` }))]} />
          <Select label="Subfonte" value={filters.subfonte_recurso} onChange={(v) => set('subfonte_recurso', v)}
            options={[{ value: '', label: 'Todas' }, ...subfontes.map((f) => ({ value: f.id, label: `${f.codigo} — ${f.nome}` }))]} />
          <Select label="Ação Orçamentária" value={filters.acao} onChange={(v) => set('acao', v)}
            options={[{ value: '', label: 'Todas' }, ...acoes.map((a) => ({ value: a.id, label: `${a.codigo} — ${a.nome}` }))]} />
          <Select label="Natureza de Despesa" value={filters.natureza_despesa} onChange={(v) => set('natureza_despesa', v)}
            options={[{ value: '', label: 'Todas' }, ...naturezas.map((n) => ({ value: n.id, label: n.descricao }))]} />
          <Select label="Elemento de Despesa" value={filters.elemento_despesa} onChange={(v) => set('elemento_despesa', v)}
            options={[{ value: '', label: 'Todos' }, ...elementos.map((e) => ({ value: e.id, label: `${e.codigo} — ${e.descricao}` }))]} />
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
            <input type="number" value={filters.exercicio_fiscal} onChange={(e) => set('exercicio_fiscal', e.target.value)}
              className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Processo SEI</label>
            <input type="text" value={filters.numero_sei} onChange={(e) => set('numero_sei', e.target.value)}
              placeholder="busca parcial"
              className="w-36 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div className="flex flex-wrap gap-3 items-end pt-3 border-t border-gray-100">
          <Select label="Área de Aplicação" value={filters.area_aplicacao} onChange={(v) => set('area_aplicacao', v)}
            options={[{ value: '', label: 'Todas' }, ...AREA_OPTS]} />
          <Select label="Órgão Executor" value={filters.orgao_executor} onChange={(v) => set('orgao_executor', v)}
            options={[{ value: '', label: 'Todos' }, ...orgaos.map((o) => ({ value: o.id, label: o.sigla }))]} />
          <Select label="Beneficiada" value={filters.beneficiada} onChange={(v) => set('beneficiada', v)}
            options={BENEFICIADA_OPTS} />
          <Select label="Instrumento (FESP)" value={filters.instrumento_financeiro} onChange={(v) => set('instrumento_financeiro', v)}
            options={[{ value: '', label: 'Todos' }, ...instrumentos.map((i) => ({ value: i.id, label: `${i.tipo_instrumento_display || i.tipo_instrumento} — ${i.numero_instrumento}` }))]} />
          <Select label="Status" value={filters.status_execucao} onChange={(v) => set('status_execucao', v)}
            options={STATUS_OPTS} />
          <button onClick={load}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
            Atualizar
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && dados && (
        dados.itens.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhum item encontrado para os filtros selecionados.</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs min-w-[1900px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Objeto</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Itens</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Área</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Órgão Executor</th>
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
                  {dados.itens.map((it, i) => {
                    const rateioTitle = it.rateio
                      ? 'Valor rateado proporcionalmente à fatia do item na dotação — a execução (empenho/liquidação/pagamento) é sempre registrada por dotação, não por item.'
                      : undefined
                    const prefixo = it.rateio ? '≈ ' : ''
                    const itensDfd = it.itens_dfd || []
                    const itensTitle = itensDfd.map((id) => `${id.objeto} (${id.quantidade} ${id.unidade_medida})`).join('\n')
                    return (
                    <tr key={`${it.id}-${i}`} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-gray-700 max-w-[220px] truncate" title={it.objeto || ''}>
                        {it.objeto || <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-3 py-2 text-gray-600" title={itensTitle}>
                        {itensDfd.length > 0 ? `${itensDfd.length} ${itensDfd.length === 1 ? 'item' : 'itens'}` : <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-3 py-2 text-gray-600">
                        {(it.area_aplicacao || []).length > 0
                          ? it.area_aplicacao.join(', ')
                          : <span className="text-gray-300">—</span>}
                      </td>
                      <td className="px-3 py-2 text-gray-600">{it.orgao_executor_sigla || <span className="text-gray-300">—</span>}</td>
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
                        {it.em_diligencia ? fmt(it.valor_indicado_item) : '—'}
                      </td>
                      <td className="px-3 py-2 text-right font-semibold text-gray-800">
                        {it.em_diligencia ? '—' : fmt(it.valor_indicado_item)}
                      </td>
                      <td className="px-3 py-2 text-right font-semibold text-blue-700" title={rateioTitle}>{prefixo}{fmt(it.valor_empenhado)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-purple-700" title={rateioTitle}>{prefixo}{fmt(it.valor_liquidado)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-teal-700" title={rateioTitle}>{prefixo}{fmt(it.valor_pago)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-gray-500" title={rateioTitle}>{prefixo}{fmt(it.saldo)}</td>
                    </tr>
                  )})}
                </tbody>
              </table>
            </div>
          </div>
        )
      )}
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[180px]">
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  )
}
