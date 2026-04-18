import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const PRIO_CLS = {
  Alta:  'bg-red-100 text-red-700',
  Média: 'bg-yellow-100 text-yellow-700',
  Baixa: 'bg-gray-100 text-gray-500',
}

export default function AceiteNecessidades() {
  const navigate = useNavigate()
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(new Set())
  const [showRecusar, setShowRecusar] = useState(false)
  const [motivo, setMotivo]     = useState('')
  const [saving, setSaving]     = useState(false)
  const [msg, setMsg]           = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/planejamento/necessidade/', {
      params: { tipo_execucao: 'externa', page_size: 200 },
    })
      .then(({ data }) => {
        const all = data.results ?? data
        setList(all.filter(n => n.aceite_pai === 'pendente'))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const toggleAll = () => {
    if (selected.size === list.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(list.map(n => n.id)))
    }
  }

  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const handleAceitar = async () => {
    if (!selected.size) return
    setSaving(true)
    setMsg(null)
    try {
      const { data } = await api.post('/planejamento/necessidade/aceitar_lote/', {
        ids: [...selected],
      })
      setMsg({ type: 'success', text: `${data.aceitas} necessidade(s) aceita(s) com sucesso.` })
      setSelected(new Set())
      load()
    } catch {
      setMsg({ type: 'error', text: 'Erro ao aceitar necessidades.' })
    } finally {
      setSaving(false)
    }
  }

  const handleRecusar = async () => {
    if (!selected.size || !motivo.trim()) return
    setSaving(true)
    setMsg(null)
    try {
      const { data } = await api.post('/planejamento/necessidade/recusar_lote/', {
        ids: [...selected],
        motivo,
      })
      setMsg({ type: 'success', text: `${data.recusadas} necessidade(s) recusada(s).` })
      setSelected(new Set())
      setMotivo('')
      setShowRecusar(false)
      load()
    } catch {
      setMsg({ type: 'error', text: 'Erro ao recusar necessidades.' })
    } finally {
      setSaving(false)
    }
  }

  // Agrupar por órgão de origem
  const grupos = list.reduce((acc, n) => {
    const sigla = n.org_sigla || 'Desconhecido'
    if (!acc[sigla]) acc[sigla] = []
    acc[sigla].push(n)
    return acc
  }, {})

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Aceite de Necessidades</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Necessidades dos órgãos filhos aguardando aceite para execução pelo órgão pai
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
                                 : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {msg.text}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-gray-400">Carregando...</p>
      ) : list.length === 0 ? (
        <div className="text-center py-16 text-gray-400 text-sm">
          Nenhuma necessidade aguardando aceite.
        </div>
      ) : (
        <>
          {/* Barra de ações */}
          <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-xl border border-gray-200">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-600">
              <input type="checkbox"
                checked={selected.size === list.length && list.length > 0}
                onChange={toggleAll}
                className="accent-blue-600 w-4 h-4" />
              Selecionar todas ({list.length})
            </label>
            <span className="text-gray-300">|</span>
            <span className="text-sm text-gray-500">{selected.size} selecionada(s)</span>
            <div className="ml-auto flex gap-2">
              <button
                onClick={handleAceitar}
                disabled={selected.size === 0 || saving}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-40 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors">
                Aceitar selecionadas
              </button>
              <button
                onClick={() => setShowRecusar(true)}
                disabled={selected.size === 0 || saving}
                className="border border-red-300 text-red-600 hover:bg-red-50 disabled:opacity-40 text-sm font-medium px-4 py-1.5 rounded-lg transition-colors">
                Recusar selecionadas
              </button>
            </div>
          </div>

          {/* Lista por órgão */}
          {Object.entries(grupos).map(([orgSigla, items]) => (
            <div key={orgSigla} className="mb-6">
              <div className="flex items-center gap-2 mb-2 px-2 py-1.5 bg-indigo-50 border border-indigo-200 rounded-lg">
                <span className="font-mono font-bold text-indigo-800">{orgSigla}</span>
                <span className="text-xs text-indigo-600">{items.length} necessidade(s) pendente(s)</span>
              </div>
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-4 py-2 w-10"></th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Título</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Unid. Dem.</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Área</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Valor</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Prioridade</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-400">Prazo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {items.map(n => (
                      <tr key={n.id}
                        className={`transition-colors ${selected.has(n.id) ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
                        <td className="px-4 py-2 text-center">
                          <input type="checkbox"
                            checked={selected.has(n.id)}
                            onChange={() => toggle(n.id)}
                            className="accent-blue-600 w-4 h-4" />
                        </td>
                        <td className="px-4 py-2">
                          <button
                            onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}
                            className="font-medium text-gray-800 hover:text-blue-600 text-left">
                            {n.titulo}
                          </button>
                        </td>
                        <td className="px-4 py-2 text-gray-500 text-xs">
                          {n.unidade_demandante || '—'}
                        </td>
                        <td className="px-4 py-2 text-xs text-gray-500">
                          {(n.area_aplicacao || []).join(', ')}
                        </td>
                        <td className="px-4 py-2 text-gray-700 font-mono text-xs">
                          {Number(n.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </td>
                        <td className="px-4 py-2">
                          <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${PRIO_CLS[n.prioridade] || ''}`}>
                            {n.prioridade}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-xs text-gray-500">
                          {n.prazo_desejado
                            ? new Date(n.prazo_desejado).toLocaleDateString('pt-BR')
                            : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}

      {/* Modal recusa em lote */}
      {showRecusar && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">Recusar necessidades</h3>
            <p className="text-sm text-gray-500 mb-4">{selected.size} necessidade(s) serão recusadas.</p>
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo da recusa *</label>
            <textarea rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button onClick={handleRecusar} disabled={!motivo.trim() || saving}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? 'Processando...' : 'Confirmar recusa'}
              </button>
              <button onClick={() => { setShowRecusar(false); setMotivo('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
