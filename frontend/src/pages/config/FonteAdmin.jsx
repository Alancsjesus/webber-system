import { useEffect, useState } from 'react'
import api from '../../services/api'

const TIPOS = ['Tesouro', 'FESP', 'FUNEBOM']
const empty = () => ({ codigo: '', nome: '', tipo: 'Tesouro', exercicio_anterior: false })

export default function FonteAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm]       = useState(null)
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  const load = () => {
    setLoading(true)
    api.get('/orcamento/fonte-recurso/', { params: { page_size: 300 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = {
        codigo: Number(form.codigo),
        nome: form.nome,
        tipo: form.tipo,
        exercicio_anterior: form.exercicio_anterior,
      }
      if (form.id) await api.patch(`/orcamento/fonte-recurso/${form.id}/`, payload)
      else          await api.post('/orcamento/fonte-recurso/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Excluir esta fonte?')) return
    await api.delete(`/orcamento/fonte-recurso/${id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Fontes de Recurso</h1>
          <p className="text-sm text-gray-500 mt-0.5">Fontes orçamentárias por órgão</p>
        </div>
        <button onClick={() => setForm(empty())}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Nova fonte
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-blue-200 bg-blue-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">{form.id ? 'Editar fonte' : 'Nova fonte'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <F label="Código *" error={errors.codigo}>
              <input type="number" value={form.codigo} onChange={e => set('codigo', e.target.value)}
                className={inp(errors.codigo)} placeholder="Ex: 100" />
            </F>
            <F label="Tipo *" error={errors.tipo}>
              <select value={form.tipo} onChange={e => set('tipo', e.target.value)} className={inp(errors.tipo)}>
                {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </F>
            <F label="Nome *" error={errors.nome}>
              <input value={form.nome} onChange={e => set('nome', e.target.value)}
                className={inp(errors.nome)} placeholder="Ex: Recursos Ordinários" />
            </F>
            <F label="Exercício anterior?">
              <select value={form.exercicio_anterior ? 'true' : 'false'}
                onChange={e => set('exercicio_anterior', e.target.value === 'true')} className={inp()}>
                <option value="false">Não</option>
                <option value="true">Sim (restos a pagar)</option>
              </select>
            </F>
          </div>
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
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Ex. Ant.</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(f => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{f.codigo}</td>
                  <td className="px-5 py-3 text-gray-700">{f.nome}</td>
                  <td className="px-5 py-3 text-gray-500 text-xs">{f.tipo}</td>
                  <td className="px-5 py-3 text-xs text-gray-500">{f.exercicio_anterior ? 'Sim' : 'Não'}</td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => setForm({ ...f })} className="text-xs text-blue-600 hover:underline">Editar</button>
                    <button onClick={() => handleDelete(f.id)} className="text-xs text-red-500 hover:underline">Excluir</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {list.length === 0 && <p className="text-center py-8 text-sm text-gray-400">Nenhuma fonte cadastrada.</p>}
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
