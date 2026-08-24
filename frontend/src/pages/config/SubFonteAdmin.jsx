import { useEffect, useState } from 'react'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

export default function SubFonteAdmin() {
  const [list, setList]         = useState([])
  const [fontes, setFontes]     = useState([])
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [form, setForm]         = useState({ codigo: '', nome: '', fonte_recurso: '' })
  const [editId, setEditId]     = useState(null)
  const [errors, setErrors]     = useState({})
  const [msg, setMsg]           = useState(null)
  const [filtroFonte, setFiltroFonte] = useState('')

  const load = () => {
    setLoading(true)
    const params = { inativas: true, page_size: 200 }
    if (filtroFonte) params.fonte_recurso = filtroFonte
    api.get('/orcamento/subfonte-recurso/', { params })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/orcamento/fonte-recurso/', { params: { page_size: 200 } })
      .then(({ data }) => setFontes(data.results ?? data))
  }, [])

  useEffect(() => { load() }, [filtroFonte])

  const reset = () => { setForm({ codigo: '', nome: '', fonte_recurso: '' }); setEditId(null); setErrors({}) }

  const startEdit = (s) => {
    setForm({ codigo: s.codigo, nome: s.nome, fonte_recurso: String(s.fonte_recurso) })
    setEditId(s.id); setErrors({})
  }

  const validate = () => {
    const e = {}
    if (!form.codigo.trim()) e.codigo = 'Código obrigatório'
    if (!form.nome.trim()) e.nome = 'Nome obrigatório'
    if (!form.fonte_recurso) e.fonte_recurso = 'Fonte obrigatória'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true); setMsg(null)
    try {
      const payload = { codigo: form.codigo, nome: form.nome, fonte_recurso: Number(form.fonte_recurso), ativa: true }
      if (editId) {
        await api.patch(`/orcamento/subfonte-recurso/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Subfonte atualizada.' })
      } else {
        await api.post('/orcamento/subfonte-recurso/', payload)
        setMsg({ type: 'success', text: 'Subfonte criada.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleInativar = async (s) => {
    if (!confirm(`Inativar subfonte "${s.fonte_codigo}.${s.codigo} — ${s.nome}"?`)) return
    await api.delete(`/orcamento/subfonte-recurso/${s.id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Subfontes de Recurso</h1>
        <p className="text-sm text-gray-500 mt-0.5">Detalhamento opcional de uma Fonte de Recurso (ex: Tesouro Livre / Tesouro Vinculado)</p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">{editId ? 'Editar subfonte' : 'Nova subfonte de recurso'}</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fonte de recurso *</label>
            <select value={form.fonte_recurso}
              onChange={e => { setForm(p => ({ ...p, fonte_recurso: e.target.value })); setErrors(p => ({ ...p, fonte_recurso: undefined })) }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.fonte_recurso ? 'border-red-400' : 'border-gray-300'}`}>
              <option value="">Selecione...</option>
              {fontes.map(f => (
                <option key={f.id} value={f.id}>{f.codigo} — {f.nome}</option>
              ))}
            </select>
            {errors.fonte_recurso && <p className="text-xs text-red-600 mt-1">{errors.fonte_recurso}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código *</label>
            <input type="text" value={form.codigo}
              onChange={e => { setForm(p => ({ ...p, codigo: e.target.value })); setErrors(p => ({ ...p, codigo: undefined })) }}
              placeholder="Ex: 01"
              className={`w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.codigo ? 'border-red-400' : 'border-gray-300'}`} />
            {errors.codigo && <p className="text-xs text-red-600 mt-1">{errors.codigo}</p>}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Nome *</label>
          <input type="text" value={form.nome}
            onChange={e => { setForm(p => ({ ...p, nome: e.target.value })); setErrors(p => ({ ...p, nome: undefined })) }}
            placeholder="Ex: Tesouro Livre"
            className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.nome ? 'border-red-400' : 'border-gray-300'}`} />
          {errors.nome && <p className="text-xs text-red-600 mt-1">{errors.nome}</p>}
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar alterações' : 'Criar subfonte'}
          </button>
          {editId && <button type="button" onClick={reset} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>}
        </div>
      </form>

      <div className="mb-4">
        <select value={filtroFonte} onChange={e => setFiltroFonte(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todas as fontes</option>
          {fontes.map(f => <option key={f.id} value={f.id}>{f.codigo} — {f.nome}</option>)}
        </select>
      </div>

      {loading ? <LoadingSpinner /> : list.length === 0 ? (
        <EmptyState icon="currency" title="Nenhuma subfonte cadastrada"
          description="Cadastre subfontes para detalhar a origem de recursos dentro de uma Fonte (ex: Tesouro Livre, Tesouro Vinculado)." />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Fonte</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(s => (
                <tr key={s.id} className={`hover:bg-gray-50 ${!s.ativa ? 'opacity-40' : ''}`}>
                  <td className="px-5 py-3 text-gray-500 text-xs">{s.fonte_codigo} — {s.fonte_nome}</td>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{s.codigo}</td>
                  <td className="px-5 py-3 text-gray-700">{s.nome}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {s.ativa ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => startEdit(s)} className="text-xs text-blue-600 hover:underline">Editar</button>
                    {s.ativa && <button onClick={() => handleInativar(s)} className="text-xs text-red-500 hover:underline">Inativar</button>}
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
