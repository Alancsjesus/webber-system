import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanejamentoStore from '../stores/planejamentoStore'
import useAuthStore from '../stores/authStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Identificada:  'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'DFD Criado':  'bg-blue-100 text-blue-700',
  Cancelada:     'bg-red-100 text-red-700',
}

const PRIO_CLS = {
  Alta:   'bg-red-100 text-red-700',
  Média:  'bg-yellow-100 text-yellow-700',
  Baixa:  'bg-gray-100 text-gray-500',
}

export default function NecessidadeList() {
  const navigate  = useNavigate()
  const orgSigla  = useAuthStore((s) => s.orgaoSigla)
  const { necessidades, total, loading, error, fetchNecessidades } = usePlanejamentoStore()
  const [search, setSearch]   = useState('')
  const [status, setStatus]   = useState('')
  const [prioridade, setPrio] = useState('')
  const [origem, setOrigem]   = useState('')

  useEffect(() => {
    const params = {}
    if (search)    params.search    = search
    if (status)    params.status    = status
    if (prioridade) params.prioridade = prioridade
    fetchNecessidades(params)
  }, [search, status, prioridade])

  const necFiltradas = origem
    ? necessidades.filter((n) => n.origem === origem)
    : necessidades

  return (
    <div className="p-8">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Necessidades de Planejamento</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Demandas identificadas que originam DFDs
          </p>
        </div>
        <button
          onClick={() => navigate('/planejamento/necessidades/nova')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Nova necessidade
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por título, descrição ou departamento..."
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
          <option value="Identificada">Identificada</option>
          <option value="Em Análise">Em Análise</option>
          <option value="Aprovada">Aprovada</option>
          <option value="DFD Criado">DFD Criado</option>
          <option value="Cancelada">Cancelada</option>
        </select>
        <select
          value={prioridade}
          onChange={(e) => setPrio(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Toda prioridade</option>
          <option value="Alta">Alta</option>
          <option value="Média">Média</option>
          <option value="Baixa">Baixa</option>
        </select>
        <select
          value={origem}
          onChange={(e) => setOrigem(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Toda origem</option>
          <option value="propria">Próprias ({orgSigla})</option>
          <option value="herdada">Herdadas (órgãos filhos)</option>
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
          {necFiltradas.length === 0 ? (
            <EmptyState
              icon="clipboard"
              title="Nenhuma necessidade encontrada"
              description={
                search || status || prioridade || origem
                  ? 'Tente ajustar os filtros para encontrar o que procura.'
                  : 'Crie a primeira necessidade para dar início ao fluxo de planejamento e contratação.'
              }
              actionLabel={!search && !status && !prioridade && !origem ? '+ Nova necessidade' : undefined}
              onAction={!search && !status && !prioridade && !origem ? () => navigate('/planejamento/necessidades/nova') : undefined}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Título</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Valor</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Prioridade</th>
                    <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {necFiltradas.map((n) => (
                    <tr
                      key={n.id}
                      onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}
                      className={`cursor-pointer transition-colors ${n.origem === 'herdada' ? 'bg-indigo-50 hover:bg-indigo-100' : 'hover:bg-gray-50'}`}
                    >
                      <td className="px-5 py-3 font-medium text-gray-800 max-w-xs">
                        <div className="flex items-center gap-2 truncate">
                          <span className="truncate">{n.titulo}</span>
                          {n.origem === 'herdada' && (
                            <span className="shrink-0 text-xs px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700 font-medium">
                              Herdada
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 truncate mt-0.5">{n.departamento_solicitante}</p>
                      </td>
                      <td className="px-5 py-3 text-gray-500">
                        {n.org_sigla || '—'}
                      </td>
                      <td className="px-5 py-3 text-gray-700">
                        {Number(n.valor_estimado).toLocaleString('pt-BR', {
                          style: 'currency', currency: 'BRL',
                        })}
                      </td>
                      <td className="px-5 py-3 text-gray-500">{n.exercicio_fiscal}</td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${PRIO_CLS[n.prioridade] || ''}`}>
                          {n.prioridade}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[n.status] || ''}`}>
                          {n.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="text-xs text-gray-400 mt-3">{total} registro(s) · {necFiltradas.length} exibido(s)</p>
        </>
      )}
    </div>
  )
}
