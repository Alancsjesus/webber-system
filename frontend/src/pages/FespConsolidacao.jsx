import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import usePlanoAplicacaoStore from '../stores/planoAplicacaoStore'
import LoadingSpinner from '../components/LoadingSpinner'
import { formatarMoeda } from '../utils/currencyMask'

export default function FespConsolidacao() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    current, fetchPlano,
    fetchSugestoesConsolidacao, confirmarConsolidacao, fetchGrupos,
    gerarNecessidadesGrupo, desfazerConsolidacao,
  } = usePlanoAplicacaoStore()

  const [sugestoes, setSugestoes] = useState(null)
  const [grupos, setGrupos] = useState([])
  const [loading, setLoading] = useState(true)
  const [selecionados, setSelecionados] = useState({}) // { [chave]: Set(itemIds) }
  const [modalChave, setModalChave] = useState(null)
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)

  const carregar = async () => {
    setLoading(true)
    try {
      const [sug, gru] = await Promise.all([fetchSugestoesConsolidacao(id), fetchGrupos(id)])
      setSugestoes(sug)
      setGrupos(gru)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPlano(id); carregar() }, [id])

  const toggleItem = (chave, itemId) => {
    setSelecionados((prev) => {
      const atual = new Set(prev[chave] || [])
      atual.has(itemId) ? atual.delete(itemId) : atual.add(itemId)
      return { ...prev, [chave]: atual }
    })
  }

  const toggleTodos = (chave, itens) => {
    setSelecionados((prev) => {
      const atual = new Set(prev[chave] || [])
      const todosMarcados = itens.every((i) => atual.has(i.id))
      const novo = todosMarcados ? new Set() : new Set(itens.map((i) => i.id))
      return { ...prev, [chave]: novo }
    })
  }

  const handleConsolidar = async (chave, titulo, descricao) => {
    const itemIds = Array.from(selecionados[chave] || [])
    if (!itemIds.length || !titulo.trim()) return
    setBusy(true)
    try {
      await confirmarConsolidacao(id, { chave_agrupamento: chave, item_ids: itemIds, titulo, descricao })
      setModalChave(null)
      setSelecionados((p) => ({ ...p, [chave]: new Set() }))
      setMsg({ type: 'success', text: 'Itens consolidados com sucesso.' })
      await carregar()
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao consolidar.' })
    } finally {
      setBusy(false)
    }
  }

  const handleGerarNecessidades = async (grupoId) => {
    setBusy(true)
    try {
      const r = await gerarNecessidadesGrupo(grupoId)
      setMsg({ type: 'success', text: r.detail })
      await carregar()
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao gerar necessidades.' })
    } finally {
      setBusy(false)
    }
  }

  const handleDesfazer = async (grupoId) => {
    if (!confirm('Desfazer esta consolidação? Os itens voltam a ficar pendentes.')) return
    setBusy(true)
    try {
      await desfazerConsolidacao(grupoId)
      await carregar()
    } finally {
      setBusy(false)
    }
  }

  if (loading || !current) return <div className="p-8"><LoadingSpinner message="Carregando consolidação..." /></div>

  return (
    <div className="p-6 lg:p-8 max-w-5xl">
      <button onClick={() => navigate(`/fesp/planos/${id}`)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar ao plano</button>
      <h1 className="text-xl font-bold text-gray-800">Consolidação de Itens</h1>
      <p className="text-sm text-gray-500 mt-0.5 mb-6">
        {current.numero} — itens pendentes agrupados por família SIMPAS ou código SENASP. Itens destacados aparecem em mais de uma instituição beneficiária.
      </p>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {msg.text}
        </div>
      )}

      {grupos.length > 0 && (
        <div className="mb-8">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Grupos Consolidados</p>
          <div className="space-y-2">
            {grupos.map((g) => (
              <div key={g.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center justify-between flex-wrap gap-2">
                <div>
                  <p className="text-sm font-medium text-gray-800">{g.titulo}</p>
                  <p className="text-xs text-gray-400">{g.status_display}{g.chave_agrupamento && ` · ${g.chave_agrupamento}`}</p>
                </div>
                <div className="flex gap-2">
                  {g.status === 'confirmado' && (
                    <>
                      <button onClick={() => handleGerarNecessidades(g.id)} disabled={busy}
                        className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg">
                        Gerar Necessidades
                      </button>
                      <button onClick={() => handleDesfazer(g.id)} disabled={busy}
                        className="border border-red-300 text-red-500 hover:bg-red-50 text-xs px-3 py-1.5 rounded-lg">
                        Desfazer
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Sugestões de Agrupamento</p>
      {(!sugestoes || sugestoes.length === 0) ? (
        <p className="text-sm text-gray-400">Nenhum item pendente disponível para consolidação.</p>
      ) : (
        <div className="space-y-4">
          {sugestoes.map((g) => {
            const marcados = selecionados[g.chave_agrupamento] || new Set()
            return (
              <div key={g.chave_agrupamento} className={`bg-white border rounded-xl overflow-hidden ${g.multi_orgao ? 'border-yellow-300' : 'border-gray-200'}`}>
                <div className={`px-4 py-3 flex items-center justify-between flex-wrap gap-2 ${g.multi_orgao ? 'bg-yellow-50' : 'bg-gray-50'}`}>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono font-semibold text-gray-800">{g.chave_agrupamento || 'Sem código'}</span>
                      {g.multi_orgao && (
                        <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded-full font-medium">
                          {g.total_orgaos} instituições diferentes
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {g.total_itens} item(ns) · {formatarMoeda(g.valor_total)} ·{' '}
                      {g.orgaos.map((o) => o.sigla).join(', ')}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => toggleTodos(g.chave_agrupamento, g.itens)}
                      className="text-xs text-gray-500 hover:text-gray-700 underline">
                      {g.itens.every((i) => marcados.has(i.id)) ? 'Desmarcar todos' : 'Selecionar todos'}
                    </button>
                    <button onClick={() => setModalChave(g.chave_agrupamento)} disabled={marcados.size === 0}
                      className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-40 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                      Consolidar Selecionados ({marcados.size})
                    </button>
                  </div>
                </div>
                <table className="w-full text-xs">
                  <tbody className="divide-y divide-gray-50">
                    {g.itens.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-2 w-8">
                          <input type="checkbox" checked={marcados.has(item.id)} onChange={() => toggleItem(g.chave_agrupamento, item.id)} />
                        </td>
                        <td className="px-2 py-2 text-gray-700">{item.bem_servico}</td>
                        <td className="px-2 py-2 text-gray-500">{item.org_beneficiaria_sigla}</td>
                        <td className="px-2 py-2 text-right text-gray-500">{item.quantidade} {item.unidade_medida}</td>
                        <td className="px-4 py-2 text-right text-gray-700 font-medium">{formatarMoeda(item.valor_total_estimado)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {modalChave === g.chave_agrupamento && (
                  <ConsolidarModal
                    onConfirm={(titulo, descricao) => handleConsolidar(g.chave_agrupamento, titulo, descricao)}
                    onClose={() => setModalChave(null)}
                    busy={busy}
                  />
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function ConsolidarModal({ onConfirm, onClose, busy }) {
  const [titulo, setTitulo] = useState('')
  const [descricao, setDescricao] = useState('')
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <p className="text-sm font-semibold text-gray-800 mb-3">Confirmar Consolidação</p>
        <input type="text" placeholder="Título do grupo (ex: Viaturas — Interior)" value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-2" />
        <textarea rows={2} placeholder="Descrição (opcional)" value={descricao}
          onChange={(e) => setDescricao(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3" />
        <div className="flex gap-2">
          <button onClick={() => onConfirm(titulo, descricao)} disabled={!titulo.trim() || busy}
            className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
            {busy ? 'Salvando...' : 'Confirmar'}
          </button>
          <button onClick={onClose} className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}
