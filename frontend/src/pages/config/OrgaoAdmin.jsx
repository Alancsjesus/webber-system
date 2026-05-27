import { useEffect, useState } from 'react'
import api from '../../services/api'

const empty = () => ({ sigla: '', nome: '', parent: '', ativa: true })

export default function OrgaoAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm]       = useState(null)
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  const load = () => {
    setLoading(true)
    api.get('/core/orgaos/', { params: { ativa: 'all', page_size: 200 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = { sigla: form.sigla, nome: form.nome, ativa: form.ativa }
      if (form.parent) payload.parent = Number(form.parent)
      if (form.id) await api.patch(`/core/orgaos/${form.id}/`, payload)
      else          await api.post('/core/orgaos/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Desativar este órgão?')) return
    await api.delete(`/core/orgaos/${id}/`)
    load()
  }

  const raizes = list.filter(o => !o.parent)
  const filhos = list.filter(o => o.parent)

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Órgãos</h1>
          <p className="text-sm text-gray-500 mt-0.5">Gestão de órgãos e hierarquia</p>
        </div>
        <button onClick={() => setForm(empty())}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Novo órgão
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-blue-200 bg-blue-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">{form.id ? 'Editar órgão' : 'Novo órgão'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <F label="Sigla *" error={errors.sigla}>
              <input value={form.sigla} onChange={e => set('sigla', e.target.value.toUpperCase())}
                className={inp(errors.sigla)} placeholder="Ex: SSP" />
            </F>
            <F label="Nome *" error={errors.nome}>
              <input value={form.nome} onChange={e => set('nome', e.target.value)}
                className={inp(errors.nome)} placeholder="Nome completo do órgão" />
            </F>
            <F label="Órgão pai (se filho)">
              <select value={form.parent || ''} onChange={e => set('parent', e.target.value)}
                className={inp()}>
                <option value="">— sem pai (órgão raiz) —</option>
                {raizes.map(o => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
              </select>
            </F>
            <F label="Situação">
              <select value={form.ativa ? 'true' : 'false'} onChange={e => set('ativa', e.target.value === 'true')}
                className={inp()}>
                <option value="true">Ativo</option>
                <option value="false">Inativo</option>
              </select>
            </F>
          </div>
          {errors.non_field_errors && <p className="text-xs text-red-600 mt-2">{errors.non_field_errors}</p>}
          <div className="flex gap-2 mt-4">
            <button onClick={handleSave} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button onClick={() => setForm(null)}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg hover:bg-white">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {loading ? <p className="text-sm text-gray-400">Carregando...</p> : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Sigla</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão Pai</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Situação</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(o => (
                <tr key={o.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{o.sigla}</td>
                  <td className="px-5 py-3 text-gray-700">{o.nome}</td>
                  <td className="px-5 py-3 text-gray-500">{o.parent_sigla || <span className="italic text-gray-300">—</span>}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${o.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {o.ativa ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => setForm({ ...o })}
                      className="text-xs text-blue-600 hover:underline">Editar</button>
                    {o.ativa && (
                      <button onClick={() => handleDelete(o.id)}
                        className="text-xs text-red-500 hover:underline">Desativar</button>
                    )}
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

function F({ label, error, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-0.5">{error}</p>}
    </div>
  )
}
const inp = (err) => `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400' : 'border-gray-300'}`
