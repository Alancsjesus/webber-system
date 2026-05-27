import { useEffect, useState } from 'react'
import api from '../../services/api'

const PAPEIS = [
  { value: 'admin',               label: 'Administrador' },
  { value: 'analista',            label: 'Analista de Contratações' },
  { value: 'gestor_planejamento', label: 'Gestor de Planejamento' },
  { value: 'gestor_contrato',     label: 'Gestor de Contrato' },
  { value: 'fiscal_contrato',     label: 'Fiscal de Contrato' },
  { value: 'ordenador',           label: 'Ordenador de Despesas' },
  { value: 'solicitante',         label: 'Solicitante' },
  { value: 'responsavel_tecnico', label: 'Responsável Técnico' },
]

const empty = () => ({
  username: '', first_name: '', last_name: '', email: '',
  password: '', papel: 'solicitante', org_id: '', unidade: '',
})

export default function UsuarioAdmin() {
  const [list, setList]       = useState([])
  const [orgaos, setOrgaos]   = useState([])
  const [unidades, setUnidades] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm]       = useState(null)
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  const load = () => {
    setLoading(true)
    api.get('/core/usuarios/', { params: { page_size: 300 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])
  useEffect(() => {
    api.get('/core/orgaos/', { params: { page_size: 100 } }).then(({ data }) => setOrgaos(data.results ?? data))
  }, [])

  const loadUnidades = (orgId) => {
    if (!orgId) { setUnidades([]); return }
    api.get('/core/unidades/', { params: { orgao: orgId, page_size: 100 } })
      .then(({ data }) => setUnidades(data.results ?? data))
  }

  const set = (k, v) => {
    setForm(p => ({ ...p, [k]: v }))
    setErrors(p => ({ ...p, [k]: undefined }))
    if (k === 'org_id') { loadUnidades(v); setForm(p => ({ ...p, org_id: v, unidade: '' })) }
  }

  const openForm = (u = null) => {
    if (u) {
      setForm({ ...u, password: '' })
      loadUnidades(u.org_id)
    } else {
      setForm(empty())
      setUnidades([])
    }
  }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = {
        username: form.username,
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        papel: form.papel,
        org_id: form.org_id ? Number(form.org_id) : null,
        unidade: form.unidade ? Number(form.unidade) : null,
      }
      if (form.password) payload.password = form.password
      if (form.id) await api.patch(`/core/usuarios/${form.id}/`, payload)
      else          await api.post('/core/usuarios/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDeactivate = async (id) => {
    if (!confirm('Desativar este usuário?')) return
    await api.delete(`/core/usuarios/${id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Usuários</h1>
          <p className="text-sm text-gray-500 mt-0.5">Cadastro de usuários, perfis e vínculos</p>
        </div>
        <button onClick={() => openForm()}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Novo usuário
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-blue-200 bg-blue-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">{form.id ? 'Editar usuário' : 'Novo usuário'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <F label="Username *" error={errors.username}>
              <input value={form.username} onChange={e => set('username', e.target.value)}
                disabled={!!form.id} className={inp(errors.username)} placeholder="login" />
            </F>
            <F label="Senha" error={errors.password}>
              <input type="password" value={form.password} onChange={e => set('password', e.target.value)}
                className={inp(errors.password)}
                placeholder={form.id ? 'Deixe em branco para não alterar' : 'Mínimo 8 caracteres'} />
            </F>
            <F label="Nome" error={errors.first_name}>
              <input value={form.first_name} onChange={e => set('first_name', e.target.value)}
                className={inp(errors.first_name)} placeholder="Primeiro nome" />
            </F>
            <F label="Sobrenome" error={errors.last_name}>
              <input value={form.last_name} onChange={e => set('last_name', e.target.value)}
                className={inp(errors.last_name)} placeholder="Sobrenome" />
            </F>
            <F label="E-mail" error={errors.email}>
              <input type="email" value={form.email} onChange={e => set('email', e.target.value)}
                className={inp(errors.email)} placeholder="email@orgao.gov.br" />
            </F>
            <F label="Papel *" error={errors.papel}>
              <select value={form.papel} onChange={e => set('papel', e.target.value)} className={inp(errors.papel)}>
                {PAPEIS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </F>
            <F label="Órgão *" error={errors.org_id}>
              <select value={form.org_id || ''} onChange={e => set('org_id', e.target.value)} className={inp(errors.org_id)}>
                <option value="">— selecione —</option>
                {orgaos.map(o => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
              </select>
            </F>
            <F label="Unidade" error={errors.unidade}>
              <select value={form.unidade || ''} onChange={e => set('unidade', e.target.value)} className={inp(errors.unidade)}
                disabled={!form.org_id}>
                <option value="">— selecione —</option>
                {unidades.map(u => <option key={u.id} value={u.id}>{u.sigla} — {u.nome} ({u.tipo})</option>)}
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
                <th className="text-left px-4 py-3 font-medium text-gray-500">Usuário</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Papel</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Órgão</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Unidade</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(u => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-gray-800 font-semibold">{u.username}</td>
                  <td className="px-4 py-3 text-gray-700">{[u.first_name, u.last_name].filter(Boolean).join(' ') || '—'}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium">
                      {PAPEIS.find(p => p.value === u.papel)?.label || u.papel}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 font-mono text-xs">{u.org_sigla || '—'}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{u.unidade_sigla ? `${u.unidade_sigla} (${u.unidade_tipo})` : '—'}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    <button onClick={() => openForm(u)} className="text-xs text-blue-600 hover:underline">Editar</button>
                    <button onClick={() => handleDeactivate(u.id)} className="text-xs text-red-500 hover:underline">Desativar</button>
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
const inp = (err) => `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400' : 'border-gray-300'} disabled:bg-gray-50 disabled:text-gray-400`
