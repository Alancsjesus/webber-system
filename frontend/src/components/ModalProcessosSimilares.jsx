import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Rascunho:     'bg-gray-100 text-gray-600',
  Submetida:    'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Devolvida:    'bg-orange-100 text-orange-700',
  Aprovada:     'bg-green-100 text-green-700',
  Rejeitada:    'bg-red-100 text-red-700',
}

function fmtData(iso) {
  if (!iso) return '—'
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

export default function ModalProcessosSimilares({ dfdId, tipo = 'dfd', id, onClose }) {
  const navigate = useNavigate()
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // dfdId é o formato original (compatibilidade); tipo+id permite chamar também
  // a partir de ETP/TR — o backend resolve os dois para o DFD de origem.
  const paramKey = dfdId ? 'dfd' : tipo
  const paramValue = dfdId || id

  useEffect(() => {
    api.get('/base-conhecimento/similares/', { params: { [paramKey]: paramValue } })
      .then(({ data }) => setDados(data))
      .catch(() => setError('Não foi possível buscar processos semelhantes.'))
      .finally(() => setLoading(false))
  }, [paramKey, paramValue])

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[85vh] overflow-y-auto">
        <div className="p-5 border-b border-gray-100 flex items-start justify-between">
          <div>
            <h3 className="font-bold text-gray-800">Processos Semelhantes</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Outros DFDs que já demandaram os mesmos itens do catálogo — o que aconteceu com eles pode
              indicar o que esperar deste processo.
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="p-5">
          {loading && <LoadingSpinner />}
          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">{error}</p>}

          {!loading && dados && (
            <>
              {dados.itens_compartilhados.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-500 mb-1.5">Itens usados na comparação</p>
                  <div className="flex flex-wrap gap-1.5">
                    {dados.itens_compartilhados.map((i) => (
                      <span key={i.item_catalogo_id}
                        className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                        {i.nome}{i.familia && <span className="text-gray-400"> · {i.familia}</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {dados.itens_compartilhados.length === 0 ? (
                <p className="text-sm text-gray-400 py-6 text-center">
                  Este DFD não tem itens vinculados ao catálogo — não é possível comparar com outros processos.
                </p>
              ) : dados.similares.length === 0 ? (
                <p className="text-sm text-gray-400 py-6 text-center">
                  Nenhum outro processo do órgão usou os mesmos itens do catálogo até agora.
                </p>
              ) : (
                <div className="border border-gray-200 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-400 bg-gray-50 border-b border-gray-100">
                        <th className="py-2 px-4 font-medium">Processo</th>
                        <th className="py-2 px-4 font-medium">Status</th>
                        <th className="py-2 px-4 font-medium">Etapa atual</th>
                        <th className="py-2 px-4 font-medium">Itens em comum</th>
                        <th className="py-2 px-4 font-medium">Devoluções</th>
                        <th className="py-2 px-4 font-medium">Criado em</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.similares.map((s) => (
                        <tr key={s.dfd_id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                          <td className="py-2 px-4">
                            <button onClick={() => navigate(`/demanda/dfd/${s.dfd_id}`)}
                              className="text-left">
                              <span className="font-mono text-xs text-blue-600 hover:underline block">{s.numero_sei}</span>
                              <span className="text-xs text-gray-500">{s.objeto}</span>
                            </button>
                          </td>
                          <td className="py-2 px-4">
                            <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[s.status] || 'bg-gray-100 text-gray-600'}`}>
                              {s.status}
                            </span>
                          </td>
                          <td className="py-2 px-4 text-gray-600 text-xs">{s.etapa_atual}</td>
                          <td className="py-2 px-4 text-gray-600 text-xs text-center">{s.itens_em_comum}</td>
                          <td className="py-2 px-4 text-xs text-center">
                            {s.total_devolucoes > 0 ? (
                              <span className="font-semibold text-orange-600">{s.total_devolucoes}</span>
                            ) : (
                              <span className="text-gray-400">0</span>
                            )}
                          </td>
                          <td className="py-2 px-4 text-gray-500 text-xs">{fmtData(s.criado_em)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        <div className="p-5 border-t border-gray-100 flex justify-end">
          <button onClick={onClose} className="text-sm text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50">Fechar</button>
        </div>
      </div>
    </div>
  )
}
