import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanoAplicacaoStore from '../stores/planoAplicacaoStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'
import { TIPO_INSTRUMENTO_OPTIONS } from './FespInstrumentoList'

const PAGE_SIZE = 20

export { TIPO_INSTRUMENTO_OPTIONS as NATUREZA_PLANO_OPTIONS }

export const NATUREZA_PLANO_CLS = {
  fesp: 'bg-amber-100 text-amber-700',
  emenda_parlamentar: 'bg-sky-100 text-sky-700',
  convenio: 'bg-teal-100 text-teal-700',
  contrato_repasse: 'bg-indigo-100 text-indigo-700',
  transferencia_fundo_a_fundo: 'bg-purple-100 text-purple-700',
  financiamento: 'bg-emerald-100 text-emerald-700',
}

export const STATUS_PLANO_CLS = {
  elaboracao: 'bg-gray-100 text-gray-600',
  submetido_conselho: 'bg-blue-100 text-blue-700',
  devolvido: 'bg-red-100 text-red-600',
  aprovado_conselho: 'bg-emerald-100 text-emerald-700',
  homologado: 'bg-indigo-100 text-indigo-700',
  aprovado: 'bg-emerald-100 text-emerald-700',
  publicado: 'bg-green-100 text-green-700',
  encerrado: 'bg-purple-100 text-purple-700',
  cancelado: 'bg-red-100 text-red-600',
}

export const pageHelp = {
  titulo: 'Planos de Aplicação',
  descricao: 'Plano de Aplicação anual do FESP, emendas e financiamentos — elaborado pela Coordenação, aprovado pelo Conselho Gestor e homologado por ato do Chefe do Poder Executivo (Lei 14.169/2019).',
  acoes: [
    { label: '+ Novo Plano', texto: 'Cria um Plano de Aplicação para um exercício fiscal e uma natureza de recurso (FESP, emenda, convênio, repasse, fundo a fundo ou financiamento), a partir do qual serão organizadas Metas Específicas e itens financiados por Instrumentos Financeiros.' },
    { label: 'Filtro de Natureza', texto: 'Filtra os planos por natureza do recurso — só o FESP segue o rito de Conselho Gestor e homologação; as demais naturezas usam aprovação direta.' },
  ],
  fluxo: [
    { status: 'Em Elaboração', descricao: 'Plano sendo montado — Metas Específicas e itens editáveis.' },
    { status: 'Submetido ao Conselho', descricao: 'Aguardando deliberação do Conselho Gestor.' },
    { status: 'Aprovado pelo Conselho', descricao: 'Aguardando homologação por ato do Chefe do Executivo.' },
    { status: 'Homologado', descricao: 'Ato de homologação registrado.' },
    { status: 'Publicado', descricao: 'Plano vigente — itens podem ser consolidados e gerar necessidades.' },
  ],
  dica: 'A consolidação de itens entre unidades diferentes (ex: PMBA e CBMBA pedindo o mesmo tipo de item) fica disponível a partir da aba "Consolidação" no detalhe do plano.',
  baseLegal: 'Lei Estadual 14.169/2019, arts. 7º a 12.',
}

export default function FespPlanoList() {
  const navigate = useNavigate()
  const { planos, total, loading, error, fetchPlanos } = usePlanoAplicacaoStore()
  const [searchInput, setSearchInput] = useState('')
  const [status, setStatus] = useState('')
  const [natureza, setNatureza] = useState('')
  const [exercicio, setExercicio] = useState('')
  const [page, setPage] = useState(1)
  const search = useDebouncedValue(searchInput)

  useEffect(() => { setPage(1) }, [search, status, natureza, exercicio])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (status) params.status = status
    if (natureza) params.natureza = natureza
    if (exercicio) params.exercicio_fiscal = exercicio
    fetchPlanos(params)
  }, [search, status, natureza, exercicio, page])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Planos de Aplicação</h1>
          <p className="text-sm text-gray-500 mt-0.5">FESP, Emendas e Financiamentos</p>
        </div>
        <button
          onClick={() => navigate('/fesp/planos/novo')}
          className="bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Novo plano
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por número, ementa/eixo..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
        <input
          type="number"
          placeholder="Exercício"
          value={exercicio}
          onChange={(e) => setExercicio(e.target.value)}
          className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
        <select value={natureza} onChange={(e) => setNatureza(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500">
          <option value="">Todas as naturezas</option>
          {TIPO_INSTRUMENTO_OPTIONS.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500">
          <option value="">Todos os status</option>
          <option value="elaboracao">Em Elaboração</option>
          <option value="submetido_conselho">Submetido ao Conselho</option>
          <option value="devolvido">Devolvido</option>
          <option value="aprovado_conselho">Aprovado pelo Conselho</option>
          <option value="homologado">Homologado</option>
          <option value="aprovado">Aprovado</option>
          <option value="publicado">Publicado</option>
          <option value="encerrado">Encerrado</option>
          <option value="cancelado">Cancelado</option>
        </select>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && (
        <>
          {planos.length === 0 ? (
            <EmptyState
              icon="currency"
              title="Nenhum plano de aplicação encontrado"
              description={search || status || natureza || exercicio ? 'Tente ajustar os filtros.' : 'Crie o Plano de Aplicação do exercício para organizar Metas Específicas e itens financiados pelo FESP/emendas/financiamentos.'}
              actionLabel={!search && !status && !natureza && !exercicio ? '+ Novo plano' : undefined}
              onAction={!search && !status && !natureza && !exercicio ? () => navigate('/fesp/planos/novo') : undefined}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[720px]">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Número</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Ementa/Eixo</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Natureza</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {planos.map((p) => (
                      <tr key={p.id} onClick={() => navigate(`/fesp/planos/${p.id}`)}
                        className="hover:bg-gray-50 cursor-pointer transition-colors">
                        <td className="px-5 py-3 font-medium text-gray-800 font-mono">{p.numero}</td>
                        <td className="px-5 py-3 text-gray-500 max-w-sm truncate">{p.ementa}</td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${NATUREZA_PLANO_CLS[p.natureza] || ''}`}>
                            {p.natureza_display}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-gray-500">{p.exercicio_fiscal}</td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_PLANO_CLS[p.status] || ''}`}>
                            {p.status_display}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="plano(s)" onPage={setPage} />
        </>
      )}
    </div>
  )
}
