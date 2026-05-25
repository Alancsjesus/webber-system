import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useEtpStore from '../stores/etpStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
  Cancelado:   'bg-red-100 text-red-700',
  Dispensado:  'bg-purple-100 text-purple-700',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'ETPs — Estudos Técnicos Preliminares',
  descricao: 'Lista os ETPs da unidade. O ETP documenta a análise técnica da contratação: descrição da solução, estimativas e riscos. É elaborado após aprovação do DFD.',
  acoes: [
    { label: 'Filtro Status', texto: 'Filtra por: Rascunho, Submetido, Em Análise, Devolvido, Aprovado, Dispensado ou Cancelado.' },
    { label: 'Buscar',        texto: 'Busca por número SEI do ETP ou da necessidade vinculada.' },
  ],
  dica: 'ETPs dispensados (art. 18, § 3º, Lei 14.133/2021) permitem prosseguir diretamente para o TR sem análise técnica prévia.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ETPList() {
  const navigate = useNavigate()
  const { etps, total, loading, error, fetchEtps } = useEtpStore()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    const params = {}
    if (search) params.search = search
    if (status) params.status = status
    fetchEtps(params)
  }, [search, status])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Estudos Técnicos Preliminares</h1>
          <p className="text-sm text-gray-500 mt-0.5">ETPs gerados a partir de DFDs aprovados</p>
        </div>
      </div>

      <div className="flex gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por SEI ou necessidade..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        >
          <option value="">Todos os status</option>
          <option value="Rascunho">Rascunho</option>
          <option value="Submetido">Submetido</option>
          <option value="Em Análise">Em Análise</option>
          <option value="Devolvido">Devolvido</option>
          <option value="Aprovado">Aprovado</option>
          <option value="Dispensado">Dispensado</option>
          <option value="Cancelado">Cancelado</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {error}
        </div>
      )}

      {loading && <LoadingSpinner />}

      {!loading && (
        <>
          {etps.length === 0 ? (
            <EmptyState
              icon="search"
              title="Nenhum ETP encontrado"
              description={
                search || status
                  ? 'Tente ajustar os filtros para encontrar o que procura.'
                  : 'Os ETPs são gerados a partir de DFDs aprovados. Aprove um DFD para criar o primeiro ETP.'
              }
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Nº SEI ETP</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">DFD</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Estimado</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {etps.map((e) => (
                    <tr
                      key={e.id}
                      onClick={() => navigate(`/etp/etps/${e.id}`)}
                      className="hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3 font-medium text-gray-800">{e.numero_sei}</td>
                      <td className="px-5 py-3 text-gray-500">{e.dfd_numero_sei}</td>
                      <td className="px-5 py-3 text-gray-500">{e.org_sigla}</td>
                      <td className="px-5 py-3 text-gray-700">
                        {e.estimativa_valor
                          ? Number(e.estimativa_valor).toLocaleString('pt-BR', {
                              style: 'currency', currency: 'BRL',
                            })
                          : '—'}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[e.status] || ''}`}>
                          {e.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
