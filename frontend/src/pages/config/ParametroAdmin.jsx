import { useEffect, useState } from 'react'
import api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'

const VAZIO = { chave: '', valor: '', descricao: '', norma_base: '', data_vigencia: '' }

export default function ParametroAdmin() {
  const [list, setList]         = useState([])
  const [loading, setLoading]   = useState(true)
  const [editId, setEditId]     = useState(null)
  const [editForm, setEditForm] = useState({})
  const [novoForm, setNovoForm] = useState(VAZIO)
  const [showNovo, setShowNovo] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [msg, setMsg]           = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/core/parametros/', { params: { page_size: 100 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const startEdit = (p) => {
    setEditId(p.id)
    setEditForm({ valor: p.valor, descricao: p.descricao, norma_base: p.norma_base || '', data_vigencia: p.data_vigencia || '' })
    setMsg(null)
  }
  const cancelEdit = () => { setEditId(null); setEditForm({}) }

  const handleSave = async (p) => {
    setSaving(true); setMsg(null)
    try {
      await api.patch(`/core/parametros/${p.id}/`, editForm)
      setMsg({ type: 'success', text: `"${p.chave}" atualizado.` })
      setEditId(null)
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao salvar.' })
    } finally { setSaving(false) }
  }

  const handleCreate = async () => {
    if (!novoForm.chave.trim() || !novoForm.valor.trim()) return
    setSaving(true); setMsg(null)
    try {
      await api.post('/core/parametros/', novoForm)
      setMsg({ type: 'success', text: `Parâmetro "${novoForm.chave}" criado.` })
      setNovoForm(VAZIO)
      setShowNovo(false)
      load()
    } catch (err) {
      const d = err.response?.data || {}
      const txt = d.chave ? `Chave: ${d.chave}` : (d.detail || 'Erro ao criar.')
      setMsg({ type: 'error', text: txt })
    } finally { setSaving(false) }
  }

  const setE = (k, v) => setEditForm(p => ({ ...p, [k]: v }))
  const setN = (k, v) => setNovoForm(p => ({ ...p, [k]: v }))

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Parâmetros do Sistema</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Valores e prazos configuráveis — cada parâmetro registra a norma que o fundamenta.
          </p>
        </div>
        <button onClick={() => { setShowNovo(v => !v); setMsg(null) }}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {showNovo ? 'Cancelar' : '+ Novo parâmetro'}
        </button>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
                                 : 'bg-red-50 text-red-700 border border-red-200'
        }`}>{msg.text}</div>
      )}

      {/* Formulário novo parâmetro */}
      {showNovo && (
        <div className="mb-6 bg-blue-50 border border-blue-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">Novo parâmetro</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Chave (identificador único) *</label>
              <input value={novoForm.chave} onChange={e => setN('chave', e.target.value)}
                placeholder="Ex: prazo_validade_parametro_vi_meses"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Valor *</label>
              <input value={novoForm.valor} onChange={e => setN('valor', e.target.value)}
                placeholder="Ex: 6"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Descrição</label>
              <input value={novoForm.descricao} onChange={e => setN('descricao', e.target.value)}
                placeholder="Explique o que este parâmetro controla..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Norma / Legislação base</label>
              <input value={novoForm.norma_base} onChange={e => setN('norma_base', e.target.value)}
                placeholder="Ex: Decreto Estadual 22.886/2024, Art. 5º, VI"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Data de vigência da norma</label>
              <input type="date" value={novoForm.data_vigencia} onChange={e => setN('data_vigencia', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <button onClick={handleCreate} disabled={saving || !novoForm.chave.trim() || !novoForm.valor.trim()}
            className="mt-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
            {saving ? 'Criando...' : 'Criar parâmetro'}
          </button>
        </div>
      )}

      {loading ? <LoadingSpinner /> : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Parâmetro</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500 w-36">Valor</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Norma / Vigência</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500 w-32">Atualizado por</th>
                <th className="px-5 py-3 w-28"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 align-top">
                  <td className="px-5 py-4">
                    <p className="font-mono text-xs font-semibold text-blue-700">{p.chave}</p>
                    <p className="text-xs text-gray-400 mt-0.5 leading-snug">{p.descricao}</p>
                  </td>
                  <td className="px-5 py-4">
                    {editId === p.id ? (
                      <input value={editForm.valor}
                        onChange={e => setE('valor', e.target.value)}
                        className="border border-blue-400 rounded-lg px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full"
                        autoFocus />
                    ) : (
                      <span className="font-semibold text-gray-800">{p.valor}</span>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    {editId === p.id ? (
                      <div className="space-y-2">
                        <input value={editForm.norma_base}
                          onChange={e => setE('norma_base', e.target.value)}
                          placeholder="Norma / Legislação"
                          className="border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 w-full" />
                        <input type="date" value={editForm.data_vigencia}
                          onChange={e => setE('data_vigencia', e.target.value)}
                          className="border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 w-full" />
                        <input value={editForm.descricao}
                          onChange={e => setE('descricao', e.target.value)}
                          placeholder="Descrição"
                          className="border border-gray-300 rounded-lg px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 w-full" />
                      </div>
                    ) : (
                      <div>
                        {p.norma_base
                          ? <p className="text-xs text-indigo-700 font-medium">{p.norma_base}</p>
                          : <p className="text-xs text-gray-300">—</p>}
                        {p.data_vigencia && (
                          <p className="text-xs text-gray-400 mt-0.5">
                            Vigência: {new Date(p.data_vigencia).toLocaleDateString('pt-BR')}
                          </p>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-5 py-4 text-xs text-gray-400">
                    {p.atualizado_por_username || '—'}
                  </td>
                  <td className="px-5 py-4 text-right">
                    {editId === p.id ? (
                      <div className="flex flex-col gap-1">
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
                  <td colSpan={5} className="px-5 py-10 text-center text-gray-400 text-sm">
                    Nenhum parâmetro. Execute <code className="bg-gray-100 px-1 rounded">python manage.py setup_dev</code>.
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
