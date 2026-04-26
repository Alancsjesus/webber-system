import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_DFD = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetida:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvida:   'bg-orange-100 text-orange-700',
  Aprovada:    'bg-green-100 text-green-700',
  Rejeitada:   'bg-red-100 text-red-700',
}
const STATUS_NEC = {
  Identificada: 'bg-gray-100 text-gray-600',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  'DFD Criado': 'bg-blue-100 text-blue-700',
  Cancelada:    'bg-red-100 text-red-700',
}
const STATUS_ETP = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
}

export default function Painel() {
  const navigate = useNavigate()
  const [data, setData]       = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    api.get('/painel/')
      .then(({ data }) => { setData(data); setLoading(false) })
      .catch(() => { setError('Erro ao carregar painel.'); setLoading(false) })
  }, [])

  const toggle = (key) => setExpanded(p => ({ ...p, [key]: !p[key] }))

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando painel..." /></div>
  if (error)   return <p className="p-8 text-sm text-red-600">{error}</p>

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Painel de Demandas</h1>
        <p className="text-sm text-gray-500 mt-0.5">Visão consolidada por órgão e unidade demandante</p>
      </div>

      {data.map((orgBlock) => (
        <div key={orgBlock.orgao_id} className="mb-8">
          {/* Órgão header */}
          <div className={`flex items-center gap-3 mb-4 px-4 py-3 rounded-xl border ${
            orgBlock.eh_filho
              ? 'border-indigo-200 bg-indigo-50'
              : 'border-blue-200 bg-blue-50'
          }`}>
            <span className={`font-mono font-bold text-lg ${orgBlock.eh_filho ? 'text-indigo-800' : 'text-blue-800'}`}>
              {orgBlock.orgao_sigla}
            </span>
            <span className={`text-sm ${orgBlock.eh_filho ? 'text-indigo-600' : 'text-blue-600'}`}>
              {orgBlock.orgao_nome}
            </span>
            {orgBlock.eh_filho && (
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                Órgão Filho
              </span>
            )}
            <span className="ml-auto text-xs text-gray-500">
              {orgBlock.necessidades.length} necessidade(s) · {orgBlock.dfds.length} DFD(s)
            </span>
          </div>

          {/* Necessidades */}
          {orgBlock.necessidades.length > 0 && (
            <div className="mb-5">
              <button
                onClick={() => toggle(`nec-${orgBlock.orgao_id}`)}
                className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 hover:text-gray-700"
              >
                <span className={`transition-transform ${expanded[`nec-${orgBlock.orgao_id}`] !== false ? 'rotate-90' : ''}`}>›</span>
                Necessidades de Planejamento ({orgBlock.necessidades.length})
              </button>
              {expanded[`nec-${orgBlock.orgao_id}`] !== false && (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 border-b border-gray-100">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Título</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Unid. Dem.</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Execução</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Valor</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Status</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">DFD</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {orgBlock.necessidades.map((n) => (
                        <tr key={n.id}
                          onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}
                          className="hover:bg-gray-50 cursor-pointer">
                          <td className="px-4 py-2 font-medium text-gray-800 max-w-xs truncate">{n.titulo}</td>
                          <td className="px-4 py-2 text-gray-500">{n['unidade_demandante__sigla'] || '—'}</td>
                          <td className="px-4 py-2">
                            <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${
                              n.tipo_execucao === 'externa'
                                ? 'bg-indigo-100 text-indigo-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}>
                              {n.tipo_execucao === 'externa' ? 'Externa' : 'Interna'}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-gray-700">
                            {Number(n.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                          </td>
                          <td className="px-4 py-2">
                            <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${STATUS_NEC[n.status] || ''}`}>
                              {n.status}
                            </span>
                          </td>
                          <td className="px-4 py-2 font-mono text-gray-500">
                            {n['dfd__numero_sei'] || '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* DFDs + ETPs */}
          {orgBlock.dfds.length > 0 && (
            <div>
              <button
                onClick={() => toggle(`dfd-${orgBlock.orgao_id}`)}
                className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 hover:text-gray-700"
              >
                <span className={`transition-transform ${expanded[`dfd-${orgBlock.orgao_id}`] !== false ? 'rotate-90' : ''}`}>›</span>
                DFDs e ETPs ({orgBlock.dfds.length})
              </button>
              {expanded[`dfd-${orgBlock.orgao_id}`] !== false && (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 border-b border-gray-100">
                      <tr>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Nº SEI (DFD)</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Unid. Dem.</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Valor</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Status DFD</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">ETP</th>
                        <th className="text-left px-4 py-2 font-medium text-gray-400">Status ETP</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {orgBlock.dfds.map((d) => (
                        <tr key={d.id} className="hover:bg-gray-50">
                          <td className="px-4 py-2 font-mono text-gray-800 cursor-pointer hover:text-blue-600"
                            onClick={() => navigate(`/demanda/dfd/${d.id}`)}>
                            {d.numero_sei}
                          </td>
                          <td className="px-4 py-2 text-gray-500">{d.unidade_demandante || '—'}</td>
                          <td className="px-4 py-2 text-gray-700">
                            {d.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                          </td>
                          <td className="px-4 py-2">
                            <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${STATUS_DFD[d.status] || ''}`}>
                              {d.status}
                            </span>
                          </td>
                          <td className="px-4 py-2 font-mono text-gray-600">
                            {d.etp ? (
                              <button onClick={() => navigate(`/etp/etps/${d.etp.id}`)}
                                className="hover:text-purple-600 hover:underline">
                                {d.etp.numero_sei}
                              </button>
                            ) : (
                              <span className="text-gray-300">—</span>
                            )}
                          </td>
                          <td className="px-4 py-2">
                            {d.etp ? (
                              <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${STATUS_ETP[d.etp.status] || ''}`}>
                                {d.etp.status}
                              </span>
                            ) : (
                              d.status === 'Aprovada' && (
                                <button onClick={() => navigate('/etp/etps/novo', { state: { dfd: d } })}
                                  className="text-xs text-purple-600 hover:underline font-medium">
                                  + Criar ETP
                                </button>
                              )
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {orgBlock.necessidades.length === 0 && orgBlock.dfds.length === 0 && (
            <p className="text-xs text-gray-400 italic px-2">Nenhum documento registrado para este órgão.</p>
          )}
        </div>
      ))}

      {data.length === 0 && (
        <EmptyState
          icon="clipboard"
          title="Nenhum documento encontrado"
          description="O painel consolida necessidades e DFDs do seu órgão e de órgãos filhos. Crie necessidades para visualizá-las aqui."
          actionLabel="Criar necessidade"
          onAction={() => navigate('/planejamento/necessidades/nova')}
        />
      )}
    </div>
  )
}
