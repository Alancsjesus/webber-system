import { useEffect, useState } from 'react'
import api from '../../services/api'

const TIPOS = [
  'Obra / Equipamento', 'Funcionamento / Operação', 'Capacitação', 'Equipamento',
  'Publicidade', 'Estudo / Projeto Obra', 'Outras Atividades', 'Serviço',
  'Outros Projetos', 'Outras Operações Especiais', 'Reserva de Contingência',
]
const empty = () => ({ codigo: '', nome: '', tipo: TIPOS[0], descricao: '', ativa: true })

export default function AcaoAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState('')
  const [form, setForm]       = useState(null)
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  const load = () => {
    setLoading(true)
    api.get('/orcamento/acao/', { params: { search, page_size: 300 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [search])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = { codigo: form.codigo, nome: form.nome, tipo: form.tipo, descricao: form.descricao, ativa: form.ativa }
      if (form.id) await api.patch(`/orcamento/acao/${form.id}/`, payload)
      else          await api.post('/orcamento/acao/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Excluir esta ação?')) return
    await api.delete(`/orcamento/acao/${id}/`)
    load()
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Ações Orçamentárias</h1>
          <p className="text-sm text-gray-500 mt-0.5">Ações do orçamento por órgão</p>
        </div>
        <button onClick={() => setForm(empty())}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Nova ação
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-blue-200 bg-blue-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">{form.id ? 'Editar ação' : 'Nova ação'}</h2>
          <div className="grid grid-cols-2 gap-3">
            <F label="Código *" error={errors.codigo}>
              <input value={form.codigo} onChange={e => set('codigo', e.target.value)}
                className={inp(errors.codigo)} placeholder="Ex: 2024.001" />
            </F>
            <F label="Tipo *" error={errors.tipo}>
              <select value={form.tipo} onChange={e => set('tipo', e.target.value)} className={inp(errors.tipo)}>
                {TIPOS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </F>
            <F label="Nome *" error={errors.nome}>
              <input value={form.nome} onChange={e => set('nome', e.target.value)}
                className={`${inp(errors.nome)} col-span-2`} placeholder="Nome da ação orçamentária" />
            </F>
            <F label="Descrição" error={errors.descricao}>
              <textarea rows={2} value={form.descricao} onChange={e => set('descricao', e.target.value)}
                className={inp()} />
            </F>
            <F label="Situação">
              <select value={form.ativa ? 'true' : 'false'} onChange={e => set('ativa', e.target.value === 'true')} className={inp()}>
                <option value="true">Ativa</option>
                <option value="false">Inativa</option>
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

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por código ou nome..."
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500" />

      {loading ? <p className="text-sm text-gray-400">Carregando...</p> : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Sit.</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(a => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-mono text-gray-800 font-semibold">{a.codigo}</td>
                  <td className="px-5 py-3 text-gray-700 max-w-xs truncate">{a.nome}</td>
                  <td className="px-5 py-3 text-gray-500 text-xs">{a.tipo}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${a.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {a.ativa ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => setForm({ ...a })} className="text-xs text-blue-600 hover:underline">Editar</button>
                    <button onClick={() => handleDelete(a.id)} className="text-xs text-red-500 hover:underline">Excluir</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {list.length === 0 && <p className="text-center py-8 text-sm text-gray-400">Nenhuma ação cadastrada.</p>}
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
