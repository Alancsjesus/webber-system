import { useEffect, useState } from 'react'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'

export default function NaturezaAdmin() {
  const [list, setList]         = useState([])
  const [elementos, setElementos] = useState([])
  const [loading, setLoading]   = useState(true)
  const [saving, setSaving]     = useState(false)
  const [form, setForm]         = useState({ codigo: '', descricao: '', elemento_despesa: '' })
  const [editId, setEditId]     = useState(null)
  const [errors, setErrors]     = useState({})
  const [msg, setMsg]           = useState(null)
  const [filtroEl, setFiltroEl] = useState('')

  const load = () => {
    setLoading(true)
    const params = { inativas: true, page_size: 200 }
    if (filtroEl) params.elemento_despesa = filtroEl
    api.get('/orcamento/natureza-despesa/', { params })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/orcamento/elemento-despesa/', { params: { page_size: 200 } })
      .then(({ data }) => setElementos(data.results ?? data))
  }, [])

  useEffect(() => { load() }, [filtroEl])

  const reset = () => { setForm({ codigo: '', descricao: '', elemento_despesa: '' }); setEditId(null); setErrors({}) }

  const startEdit = (n) => {
    setForm({ codigo: n.codigo, descricao: n.descricao, elemento_despesa: String(n.elemento_despesa) })
    setEditId(n.id); setErrors({})
  }

  const validate = () => {
    const e = {}
    if (!form.codigo.trim() || form.codigo.length !== 6 || isNaN(Number(form.codigo))) e.codigo = 'Código deve ter exatamente 6 dígitos (ex: 339030)'
    if (!form.descricao.trim()) e.descricao = 'Descrição obrigatória'
    if (!form.elemento_despesa) e.elemento_despesa = 'Elemento obrigatório'
    return e
  }

  const formatarCodigo = (codigo) => {
    const c = String(codigo).padStart(6, '0')
    return `${c[0]}.${c[1]}.${c[2]}${c[3]}.${c[4]}${c[5]}`
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true); setMsg(null)
    try {
      const payload = { codigo: form.codigo, descricao: form.descricao, elemento_despesa: Number(form.elemento_despesa), ativa: true }
      if (editId) {
        await api.patch(`/orcamento/natureza-despesa/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Natureza atualizada.' })
      } else {
        await api.post('/orcamento/natureza-despesa/', payload)
        setMsg({ type: 'success', text: 'Natureza criada.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleInativar = async (n) => {
    if (!confirm(`Inativar natureza "${n.formato} — ${n.descricao}"?`)) return
    await api.delete(`/orcamento/natureza-despesa/${n.id}/`)
    load()
  }

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Naturezas de Despesa</h1>
        <p className="text-sm text-gray-500 mt-0.5">Formato 3.3.90.30 — ex: 339030 (Material de Consumo), 449052 (Equipamentos)</p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {msg.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">{editId ? 'Editar natureza' : 'Nova natureza de despesa'}</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código (6 dígitos) *</label>
            <input type="text" maxLength={6} value={form.codigo}
              onChange={e => { setForm(p => ({ ...p, codigo: e.target.value.replace(/\D/g, '') })); setErrors(p => ({ ...p, codigo: undefined })) }}
              placeholder="Ex: 339030"
              className={`w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.codigo ? 'border-red-400' : 'border-gray-300'}`} />
            {form.codigo.length === 6 && (
              <p className="text-xs text-blue-600 mt-1">Formato: {formatarCodigo(form.codigo)}</p>
            )}
            {errors.codigo && <p className="text-xs text-red-600 mt-1">{errors.codigo}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Elemento de despesa *</label>
            <select value={form.elemento_despesa}
              onChange={e => { setForm(p => ({ ...p, elemento_despesa: e.target.value })); setErrors(p => ({ ...p, elemento_despesa: undefined })) }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.elemento_despesa ? 'border-red-400' : 'border-gray-300'}`}>
              <option value="">Selecione...</option>
              {elementos.map(el => (
                <option key={el.id} value={el.id}>{String(el.codigo).padStart(2,'0')} — {el.descricao}</option>
              ))}
            </select>
            {errors.elemento_despesa && <p className="text-xs text-red-600 mt-1">{errors.elemento_despesa}</p>}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Descrição *</label>
          <input type="text" value={form.descricao}
            onChange={e => { setForm(p => ({ ...p, descricao: e.target.value })); setErrors(p => ({ ...p, descricao: undefined })) }}
            placeholder="Ex: Material de Consumo"
            className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.descricao ? 'border-red-400' : 'border-gray-300'}`} />
          {errors.descricao && <p className="text-xs text-red-600 mt-1">{errors.descricao}</p>}
        </div>
        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar alterações' : 'Criar natureza'}
          </button>
          {editId && <button type="button" onClick={reset} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>}
        </div>
      </form>

      <div className="mb-4">
        <select value={filtroEl} onChange={e => setFiltroEl(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os elementos</option>
          {elementos.map(el => <option key={el.id} value={el.id}>{el.codigo} — {el.descricao}</option>)}
        </select>
      </div>

      {loading ? <LoadingSpinner /> : list.length === 0 ? (
        <EmptyState icon="currency" title="Nenhuma natureza cadastrada"
          description="Cadastre as naturezas de despesa no formato 3.3.90.30 (ex: 339030, 339039, 449052)" />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Formato</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Descrição</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Elemento</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(n => (
                <tr key={n.id} className={`hover:bg-gray-50 ${!n.ativa ? 'opacity-40' : ''}`}>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{n.codigo}</td>
                  <td className="px-5 py-3 font-mono text-blue-700 text-xs">{n.formato}</td>
                  <td className="px-5 py-3 text-gray-700">{n.descricao}</td>
                  <td className="px-5 py-3 text-gray-500 text-xs">{n.elemento_codigo} — {n.elemento_descricao}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${n.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {n.ativa ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => startEdit(n)} className="text-xs text-blue-600 hover:underline">Editar</button>
                    {n.ativa && <button onClick={() => handleInativar(n)} className="text-xs text-red-500 hover:underline">Inativar</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
