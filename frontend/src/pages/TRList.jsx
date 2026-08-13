import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useTrStore from '../stores/trStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'

const PAGE_SIZE = 20

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
  Cancelado:   'bg-red-100 text-red-700',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'TRs — Termos de Referência',
  descricao: 'Lista os Termos de Referência da unidade. O TR define o objeto da contratação, especificações técnicas, critérios de habilitação e modelo de execução.',
  acoes: [
    { label: 'Filtro Status', texto: 'Filtra por: Rascunho, Submetido, Em Análise, Devolvido, Aprovado ou Cancelado.' },
    { label: 'Buscar',        texto: 'Busca pelo número SEI ou objeto do TR.' },
  ],
  dica: 'O TR aprovado é a principal peça instrutória do procedimento licitatório. Verifique especificações antes de submeter.',
  baseLegal: 'Lei 14.133/2021 — Art. 6º, XXIII (Termo de Referência).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function TRList() {
  const navigate = useNavigate()
  const { trs, total, loading, error, fetchTrs } = useTrStore()
  const [searchInput, setSearchInput] = useState('')
  const [statusFiltro, setStatusFiltro] = useState('')
  const [page, setPage] = useState(1)
  const search = useDebouncedValue(searchInput)

  useEffect(() => { setPage(1) }, [search, statusFiltro])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (statusFiltro) params.status = statusFiltro
    fetchTrs(params)
  }, [search, statusFiltro, page])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Minutas do Termo de Referência</h1>
          <p className="text-sm text-gray-500 mt-0.5">Minutas geradas a partir de ETPs aprovados</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-5">
        <input type="text" placeholder="Buscar por SEI ou objeto..."
          value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
        <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500">
          <option value="">Todos os status</option>
          {Object.keys(STATUS_CLS).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : trs.length === 0 ? (
        <EmptyState
          icon="fileText"
          title="Nenhum TR encontrado"
          description={
            search || statusFiltro
              ? 'Tente ajustar os filtros para encontrar o que procura.'
              : 'Os TRs são gerados a partir de ETPs aprovados. Conclua o fluxo de análise técnica primeiro.'
          }
        />
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[640px]">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Nº SEI TR</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">ETP</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">DFD</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Est.</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {trs.map((t) => (
                  <tr key={t.id} onClick={() => navigate(`/analise-tecnica/trs/${t.id}`)}
                    className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-5 py-3 font-medium text-gray-800">{t.numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.etp_numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.dfd_numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.org_sigla}</td>
                    <td className="px-5 py-3 text-gray-700">
                      {t.estimativa_valor
                        ? Number(t.estimativa_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                        : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[t.status] || ''}`}>
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
          <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="registro(s)" onPage={setPage} />
        </>
      )}
    </div>
  )
}
