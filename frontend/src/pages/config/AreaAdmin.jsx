import { useEffect, useState } from 'react'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

export default function AreaAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [form, setForm]       = useState({ codigo: '', nome: '' })
  const [editId, setEditId]   = useState(null)
  const [errors, setErrors]   = useState({})
  const [msg, setMsg]         = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/core/areas/', { params: { inativas: true, page_size: 100 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const reset = () => { setForm({ codigo: '', nome: '' }); setEditId(null); setErrors({}) }

  const startEdit = (a) => { setForm({ codigo: a.codigo, nome: a.nome }); setEditId(a.id); setErrors({}) }

  const validate = () => {
    const e = {}
    if (!form.codigo.trim()) e.codigo = 'Código obrigatório'
    if (!form.nome.trim())   e.nome   = 'Nome obrigatório'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true); setMsg(null)
    try {
      const payload = { codigo: form.codigo.trim(), nome: form.nome.trim(), ativa: true }
      if (editId) {
        await api.patch(`/core/areas/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Área atualizada.' })
      } else {
        await api.post('/core/areas/', payload)
        setMsg({ type: 'success', text: 'Área criada.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleInativar = async (a) => {
    if (!confirm(`Inativar área "${a.nome}"?`)) return
    await api.delete(`/core/areas/${a.id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Áreas de Atuação</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Categorias utilizadas em Necessidades e DFDs para classificar o tipo de demanda.
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">{editId ? 'Editar área' : 'Nova área de atuação'}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código *</label>
            <input value={form.codigo} onChange={e => { setForm(p => ({ ...p, codigo: e.target.value })); setErrors(p => ({ ...p, codigo: undefined })) }}
              placeholder="Ex: TI, Formação, Saúde"
              disabled={!!editId}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.codigo ? 'border-red-400' : 'border-gray-300'} ${editId ? 'bg-gray-50' : ''}`} />
            {errors.codigo && <p className="text-xs text-red-600 mt-1">{errors.codigo}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Nome *</label>
            <input value={form.nome} onChange={e => { setForm(p => ({ ...p, nome: e.target.value })); setErrors(p => ({ ...p, nome: undefined })) }}
              placeholder="Ex: Tecnologia da Informação"
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.nome ? 'border-red-400' : 'border-gray-300'}`} />
            {errors.nome && <p className="text-xs text-red-600 mt-1">{errors.nome}</p>}
          </div>
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar' : 'Criar área'}
          </button>
          {editId && <button type="button" onClick={reset} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>}
        </div>
      </form>

      {loading ? <LoadingSpinner /> : list.length === 0 ? (
        <EmptyState icon="clipboard" title="Nenhuma área cadastrada" description="Cadastre as áreas de atuação utilizadas no planejamento de contratações." />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(a => (
                <tr key={a.id} className={`hover:bg-gray-50 ${!a.ativa ? 'opacity-40' : ''}`}>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{a.codigo}</td>
                  <td className="px-5 py-3 text-gray-700">{a.nome}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${a.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {a.ativa ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    {a.ativa && <button onClick={() => startEdit(a)} className="text-xs text-blue-600 hover:underline">Editar</button>}
                    {a.ativa && <button onClick={() => handleInativar(a)} className="text-xs text-red-500 hover:underline">Inativar</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  )
}
