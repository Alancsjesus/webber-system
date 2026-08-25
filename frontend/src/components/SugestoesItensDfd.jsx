/**
 * Painel de sugestão de itens do DFD de origem para o Mapa de Preços.
 * Mostra os itens do DFD vinculado ao mapa que ainda não foram inseridos
 * na pesquisa (por código SIMPAS ou descrição), com opção de adicionar
 * um por um ou todos de uma vez — evita redigitar o que já foi levantado
 * no planejamento.
 */
import { useEffect, useState } from 'react'
import api from '../services/api'

export default function SugestoesItensDfd({ dfdId, itensDoMapa = [], onAdicionar }) {
  const [itensDfd, setItensDfd] = useState([])
  const [loading, setLoading]   = useState(false)
  const [adicionando, setAdicionando] = useState(null)
  const [adicionandoTodos, setAdicionandoTodos] = useState(false)

  useEffect(() => {
    if (!dfdId) { setItensDfd([]); return }
    setLoading(true)
    api.get(`/demanda/dfd/${dfdId}/`)
      .then(({ data }) => setItensDfd(data.itens || []))
      .catch(() => setItensDfd([]))
      .finally(() => setLoading(false))
  }, [dfdId])

  if (!dfdId) return null

  const jaNoMapa = new Set(
    itensDoMapa.map(i => (i.codigo_simpas || i.descricao || '').trim().toLowerCase()).filter(Boolean)
  )
  const sugestoes = itensDfd.filter(item => {
    const chave = (item.catalogo_codigo_simpas || item.objeto || '').trim().toLowerCase()
    return chave && !jaNoMapa.has(chave)
  })

  if (loading || sugestoes.length === 0) return null

  const payloadDoItem = (item, ordem) => ({
    ordem,
    descricao: item.objeto,
    codigo_simpas: item.catalogo_codigo_simpas || '',
    unidade_medida: item.unidade_medida,
    quantidade: Number(item.quantidade),
  })

  const adicionarUm = async (item) => {
    setAdicionando(item.id)
    try { await onAdicionar(payloadDoItem(item, itensDoMapa.length + 1)) }
    finally { setAdicionando(null) }
  }

  const adicionarTodos = async () => {
    setAdicionandoTodos(true)
    try {
      let ordem = itensDoMapa.length + 1
      for (const item of sugestoes) {
        await onAdicionar(payloadDoItem(item, ordem))
        ordem += 1
      }
    } finally { setAdicionandoTodos(false) }
  }

  return (
    <div className="bg-violet-50 border border-violet-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="text-sm font-semibold text-violet-800">
          Sugestões do DFD de origem ({sugestoes.length})
        </p>
        <button onClick={adicionarTodos} disabled={adicionandoTodos}
          className="text-xs bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-medium px-3 py-1 rounded-lg">
          {adicionandoTodos ? 'Adicionando...' : '+ Adicionar todos'}
        </button>
      </div>
      <p className="text-xs text-violet-600 mb-3">
        Itens já cadastrados no DFD que ainda não estão nesta pesquisa de preços.
      </p>
      <div className="space-y-1.5">
        {sugestoes.map(item => (
          <div key={item.id} className="flex items-center justify-between bg-white border border-violet-100 rounded-lg px-3 py-2">
            <div className="min-w-0 flex-1">
              <p className="text-sm text-gray-800 truncate">{item.objeto}</p>
              <p className="text-xs text-gray-400">
                {item.quantidade} {item.unidade_medida}
                {item.catalogo_codigo_simpas && <span className="font-mono ml-2 text-violet-500">{item.catalogo_codigo_simpas}</span>}
              </p>
            </div>
            <button onClick={() => adicionarUm(item)} disabled={adicionando === item.id}
              className="text-xs text-violet-700 hover:text-violet-900 font-medium border border-violet-300 hover:border-violet-500 disabled:opacity-50 px-2.5 py-1 rounded-lg ml-3 shrink-0">
              {adicionando === item.id ? '...' : '+ Adicionar'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
