import { useEffect, useState } from 'react'
import api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'

export default function ParametroAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [editId, setEditId]   = useState(null)
  const [editValor, setEditValor] = useState('')
  const [saving, setSaving]   = useState(false)
  const [msg, setMsg]         = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/core/parametros/', { params: { page_size: 50 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const startEdit = (p) => {
    setEditId(p.id)
    setEditValor(p.valor)
    setMsg(null)
  }

  const cancelEdit = () => { setEditId(null); setEditValor('') }

  const handleSave = async (p) => {
    setSaving(true)
    setMsg(null)
    try {
      await api.patch(`/core/parametros/${p.id}/`, { valor: editValor })
      setMsg({ type: 'success', text: `Parâmetro "${p.chave}" atualizado.` })
      setEditId(null)
      load()
    } catch (err) {
      const detail = err.response?.data?.detail || 'Erro ao salvar.'
      setMsg({ type: 'error', text: detail })
    } finally {
      setSaving(false) }
  }

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Parâmetros do Sistema</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Valores configuráveis que controlam regras de negócio do sistema.
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${
          msg.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {msg.text}
        </div>
      )}

      {loading ? <LoadingSpinner /> : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Parâmetro</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Valor</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Atualizado por</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 align-top">
                  <td className="px-5 py-4 max-w-xs">
                    <p className="font-mono text-xs font-semibold text-blue-700">{p.chave}</p>
                    <p className="text-xs text-gray-400 mt-0.5 leading-snug">{p.descricao}</p>
                  </td>
                  <td className="px-5 py-4">
                    {editId === p.id ? (
                      <input
                        value={editValor}
                        onChange={(e) => setEditValor(e.target.value)}
                        className="border border-blue-400 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-40"
                        autoFocus
                      />
                    ) : (
                      <span className="font-semibold text-gray-800">{p.valor}</span>
                    )}
                  </td>
                  <td className="px-5 py-4 text-xs text-gray-400">
                    {p.atualizado_por_username || '—'}
                  </td>
                  <td className="px-5 py-4 text-right">
                    {editId === p.id ? (
                      <div className="flex gap-2 justify-end">
                        <button onClick={() => handleSave(p)} disabled={saving}
                          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                          {saving ? '...' : 'Salvar'}
                        </button>
                        <button onClick={cancelEdit}
                          className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg hover:bg-gray-50">
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <button onClick={() => startEdit(p)}
                        className="text-xs text-blue-600 hover:underline">
                        Editar
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {list.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-5 py-10 text-center text-gray-400 text-sm">
                    Nenhum parâmetro cadastrado. Execute <code className="bg-gray-100 px-1 rounded">python manage.py setup_dev</code> para criar os parâmetros iniciais.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
