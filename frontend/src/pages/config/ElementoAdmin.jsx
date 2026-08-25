import { useEffect, useState } from 'react'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Elementos de Despesa',
  descricao: 'Catálogo de Elementos de Despesa (ex: 30 — Material de Consumo, 52 — Material Permanente), derivado automaticamente ao escolher uma Natureza de Despesa em uma dotação.',
  acoes: [
    { label: 'Código',   texto: 'Código numérico do elemento, conforme classificação orçamentária padrão.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ElementoAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [form, setForm]       = useState({ codigo: '', descricao: '' })
  const [editId, setEditId]   = useState(null)
  const [errors, setErrors]   = useState({})
  const [msg, setMsg]         = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/orcamento/elemento-despesa/', { params: { inativos: true, page_size: 200 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const reset = () => { setForm({ codigo: '', descricao: '' }); setEditId(null); setErrors({}) }

  const startEdit = (el) => {
    setForm({ codigo: el.codigo, descricao: el.descricao })
    setEditId(el.id)
    setErrors({})
  }

  const validate = () => {
    const e = {}
    if (!form.codigo || isNaN(Number(form.codigo))) e.codigo = 'Código numérico obrigatório'
    if (!form.descricao.trim()) e.descricao = 'Descrição obrigatória'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true); setMsg(null)
    try {
      const payload = { codigo: Number(form.codigo), descricao: form.descricao, ativo: true }
      if (editId) {
        await api.patch(`/orcamento/elemento-despesa/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Elemento atualizado.' })
      } else {
        await api.post('/orcamento/elemento-despesa/', payload)
        setMsg({ type: 'success', text: 'Elemento criado.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleInativar = async (el) => {
    if (!confirm(`Inativar elemento "${el.codigo} — ${el.descricao}"?`)) return
    await api.delete(`/orcamento/elemento-despesa/${el.id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Elementos de Despesa</h1>
        <p className="text-sm text-gray-500 mt-0.5">Código de 2 dígitos (ex: 30, 39, 52)</p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">{editId ? 'Editar elemento' : 'Novo elemento'}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código *</label>
            <input type="number" value={form.codigo} onChange={e => { setForm(p => ({ ...p, codigo: e.target.value })); setErrors(p => ({ ...p, codigo: undefined })) }}
              placeholder="Ex: 30" className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.codigo ? 'border-red-400' : 'border-gray-300'}`} />
            {errors.codigo && <p className="text-xs text-red-600 mt-1">{errors.codigo}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Descrição *</label>
            <input type="text" value={form.descricao} onChange={e => { setForm(p => ({ ...p, descricao: e.target.value })); setErrors(p => ({ ...p, descricao: undefined })) }}
              placeholder="Ex: Material de Consumo" className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.descricao ? 'border-red-400' : 'border-gray-300'}`} />
            {errors.descricao && <p className="text-xs text-red-600 mt-1">{errors.descricao}</p>}
          </div>
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar alterações' : 'Criar elemento'}
          </button>
          {editId && <button type="button" onClick={reset} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>}
        </div>
      </form>

      {loading ? <LoadingSpinner /> : list.length === 0 ? (
        <EmptyState icon="document" title="Nenhum elemento cadastrado" description="Cadastre os elementos de despesa (30, 39, 52...)" />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Descrição</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(el => (
                <tr key={el.id} className={`hover:bg-gray-50 ${!el.ativo ? 'opacity-40' : ''}`}>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{String(el.codigo).padStart(2, '0')}</td>
                  <td className="px-5 py-3 text-gray-700">{el.descricao}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${el.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {el.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => startEdit(el)} className="text-xs text-blue-600 hover:underline">Editar</button>
                    {el.ativo && <button onClick={() => handleInativar(el)} className="text-xs text-red-500 hover:underline">Inativar</button>}
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
