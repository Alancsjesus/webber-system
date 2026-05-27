import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useDFDStore from '../stores/dfdStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_LABEL = {
  Rascunho:    { cls: 'bg-gray-100 text-gray-600' },
  Submetida:   { cls: 'bg-blue-100 text-blue-700' },
  'Em Análise':{ cls: 'bg-yellow-100 text-yellow-700' },
  Devolvida:   { cls: 'bg-orange-100 text-orange-700' },
  Aprovada:    { cls: 'bg-green-100 text-green-700' },
  Rejeitada:   { cls: 'bg-red-100 text-red-700' },
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'DFDs — Documentos de Formalização de Demanda',
  descricao: 'Lista de todos os DFDs da unidade. O DFD formaliza a necessidade de contratação e precede o ETP e o Termo de Referência.',
  acoes: [
    { label: '+ Novo DFD',    texto: 'Cria um DFD vinculado a uma necessidade aprovada. Preencha número SEI, descrição, valor estimado e prazo.' },
    { label: 'Filtro Status', texto: 'Filtra por: Rascunho, Submetida, Em Análise, Devolvida, Aprovada ou Rejeitada.' },
    { label: 'Buscar',        texto: 'Busca pelo número SEI ou descrição do objeto da demanda.' },
  ],
  dica: 'Um DFD aprovado permite criar o ETP. Se devolvido, verifique o motivo no detalhe.',
  baseLegal: 'Lei 14.133/2021 — Art. 12, § 1º.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function DFDList() {
  const navigate = useNavigate()
  const { dfds, total, loading, error, fetchDFDs } = useDFDStore()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    const params = {}
    if (search) params.search = search
    if (status) params.status = status
    fetchDFDs(params)
  }, [search, status])

  return (
    <div className="p-6 lg:p-8">
      {/* Cabeçalho */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">DFDs</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Documentos de Formalização de Demanda
          </p>
        </div>
        <button
          onClick={() => navigate('/demanda/dfd/novo')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Novo DFD
        </button>
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por número SEI ou descrição..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos os status</option>
          <option value="Rascunho">Rascunho</option>
          <option value="Submetida">Submetida</option>
          <option value="Em Análise">Em Análise</option>
          <option value="Devolvida">Devolvida</option>
          <option value="Aprovada">Aprovada</option>
          <option value="Rejeitada">Rejeitada</option>
        </select>
      </div>

      {/* Estado */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {loading && <LoadingSpinner />}

      {!loading && (
        <>
          {dfds.length === 0 ? (
            <EmptyState
              icon="document"
              title="Nenhum DFD encontrado"
              description={
                search || status
                  ? 'Tente ajustar os filtros para encontrar o que procura.'
                  : 'Os DFDs são criados a partir de necessidades aprovadas. Aprove uma necessidade primeiro.'
              }
              actionLabel={!search && !status ? '+ Novo DFD' : undefined}
              onAction={!search && !status ? () => navigate('/demanda/dfd/novo') : undefined}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[640px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Nº SEI</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Descrição</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Valor</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Prazo</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {dfds.map((dfd) => {
                    const st = STATUS_LABEL[dfd.status] || { cls: 'bg-gray-100 text-gray-600' }
                    return (
                      <tr
                        key={dfd.id}
                        onClick={() => navigate(`/demanda/dfd/${dfd.id}`)}
                        className="hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <td className="px-5 py-3 font-mono text-blue-600">{dfd.numero_sei}</td>
                        <td className="px-5 py-3 text-gray-700 max-w-xs truncate">{dfd.descricao}</td>
                        <td className="px-5 py-3 text-gray-700">
                          {Number(dfd.valor_estimado).toLocaleString('pt-BR', {
                            style: 'currency',
                            currency: 'BRL',
                          })}
                        </td>
                        <td className="px-5 py-3 text-gray-500">
                          {new Date(dfd.prazo_necessidade).toLocaleDateString('pt-BR')}
                        </td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${st.cls}`}>
                            {dfd.status}
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
