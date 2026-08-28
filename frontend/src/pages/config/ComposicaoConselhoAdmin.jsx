import { useEffect, useState } from 'react'
import api from '../../services/api'

const CARGO_OPTIONS = [
  { value: 'presidente', label: 'Presidente (Secretário de Segurança Pública)' },
  { value: 'assessor_planejamento', label: 'Assessor de Planejamento' },
  { value: 'diretor_geral', label: 'Diretor-Geral' },
  { value: 'representante_casa_civil', label: 'Representante da Casa Civil' },
  { value: 'representante_fazenda', label: 'Representante da Secretaria da Fazenda' },
  { value: 'representante_planejamento', label: 'Representante da Secretaria de Planejamento' },
  { value: 'membro_convidado', label: 'Membro Convidado' },
]

const TODAY = new Date().toISOString().split('T')[0]

const empty = () => ({
  usuario: '', cargo: 'membro_convidado', orgao_representado: '', nome_orgao_externo: '',
  portaria_nomeacao: '', data_inicio_mandato: TODAY, data_fim_mandato: '', ativo: true,
})

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Composição do Conselho Gestor',
  descricao: 'Cadastro dos membros do Conselho Gestor do FESP, que delibera sobre a aprovação dos Planos de Aplicação de natureza FESP (Lei 14.169/2019).',
  acoes: [
    { label: 'Usuário / Órgão externo', texto: 'Um membro pode ser um usuário interno do sistema ou representar um órgão externo sem cadastro de usuário (preenchido por nome livre).' },
    { label: 'Mandato',                 texto: 'Data de início obrigatória; fim do mandato opcional — membro sem data de fim é considerado vigente indefinidamente enquanto "Ativo".' },
  ],
  baseLegal: 'Lei Estadual 14.169/2019, Art. 9º.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ComposicaoConselhoAdmin() {
  const [list, setList] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [orgaos, setOrgaos] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const load = () => {
    setLoading(true)
    api.get('/fesp/composicao-conselho/', { params: { page_size: 100 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [])

  useEffect(() => {
    api.get('/core/users-list/').then(({ data }) => setUsuarios(data.results ?? data)).catch(() => {})
    api.get('/core/orgaos/', { params: { page_size: 50 } }).then(({ data }) => setOrgaos(data.results ?? data)).catch(() => {})
  }, [])

  const set = (k, v) => { setForm((p) => ({ ...p, [k]: v })); setErrors((p) => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = {
        usuario: form.usuario || null,
        cargo: form.cargo,
        orgao_representado: form.orgao_representado || null,
        nome_orgao_externo: form.nome_orgao_externo,
        portaria_nomeacao: form.portaria_nomeacao,
        data_inicio_mandato: form.data_inicio_mandato,
        data_fim_mandato: form.data_fim_mandato || null,
        ativo: form.ativo,
      }
      if (form.id) await api.patch(`/fesp/composicao-conselho/${form.id}/`, payload)
      else await api.post('/fesp/composicao-conselho/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Inativar este membro do Conselho Gestor?')) return
    try {
      await api.delete(`/fesp/composicao-conselho/${id}/`)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Erro ao inativar o membro.')
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Conselho Gestor FESP</h1>
          <p className="text-sm text-gray-500 mt-0.5">Composição do Conselho Gestor (Lei 14.169/2019, arts. 7º-12)</p>
        </div>
        <button onClick={() => setForm(empty())}
          className="bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Novo membro
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-yellow-200 bg-yellow-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-yellow-800 mb-4">{form.id ? 'Editar membro' : 'Novo membro'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <F label="Cargo *" error={errors.cargo}>
              <select value={form.cargo} onChange={(e) => set('cargo', e.target.value)} className={inp(errors.cargo)}>
                {CARGO_OPTIONS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </F>
            <F label="Usuário do sistema (opcional)" error={errors.usuario}>
              <select value={form.usuario} onChange={(e) => set('usuario', e.target.value)} className={inp(errors.usuario)}>
                <option value="">Não vinculado a um usuário</option>
                {usuarios.map((u) => <option key={u.id} value={u.id}>{u.first_name || u.username} ({u.username})</option>)}
              </select>
            </F>
            <F label="Órgão representado (tenant Weber-e)">
              <select value={form.orgao_representado} onChange={(e) => set('orgao_representado', e.target.value)} className={inp()}>
                <option value="">—</option>
                {orgaos.map((o) => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
              </select>
            </F>
            <F label="Órgão/ente externo (ex: Casa Civil, SEFAZ)">
              <input type="text" value={form.nome_orgao_externo} onChange={(e) => set('nome_orgao_externo', e.target.value)} className={inp()} />
            </F>
            <F label="Portaria de nomeação">
              <input type="text" value={form.portaria_nomeacao} onChange={(e) => set('portaria_nomeacao', e.target.value)} className={inp()} />
            </F>
            <F label="Início do mandato *" error={errors.data_inicio_mandato}>
              <input type="date" value={form.data_inicio_mandato} onChange={(e) => set('data_inicio_mandato', e.target.value)} className={inp(errors.data_inicio_mandato)} />
            </F>
            <F label="Fim do mandato (opcional)">
              <input type="date" value={form.data_fim_mandato} onChange={(e) => set('data_fim_mandato', e.target.value)} className={inp()} />
            </F>
            <F label="Ativo?">
              <select value={form.ativo ? 'true' : 'false'} onChange={(e) => set('ativo', e.target.value === 'true')} className={inp()}>
                <option value="true">Sim</option>
                <option value="false">Não</option>
              </select>
            </F>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={handleSave} disabled={saving}
              className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button onClick={() => setForm(null)} className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg hover:bg-white">
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
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Cargo</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Usuário / Órgão</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Mandato</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {list.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3 text-gray-700">{m.cargo_display}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{m.usuario_nome || m.nome_orgao_externo || '—'}</td>
                    <td className="px-5 py-3 text-xs text-gray-500">
                      {new Date(m.data_inicio_mandato + 'T00:00').toLocaleDateString('pt-BR')}
                      {m.data_fim_mandato && ` — ${new Date(m.data_fim_mandato + 'T00:00').toLocaleDateString('pt-BR')}`}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${m.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {m.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right space-x-2">
                      <button onClick={() => setForm({ ...m, usuario: m.usuario || '', orgao_representado: m.orgao_representado || '' })} className="text-xs text-blue-600 hover:underline">Editar</button>
                      <button onClick={() => handleDelete(m.id)} className="text-xs text-red-500 hover:underline">Inativar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {list.length === 0 && <p className="text-center py-8 text-sm text-gray-400">Nenhum membro cadastrado.</p>}
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
const inp = (err) => `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 ${err ? 'border-red-400' : 'border-gray-300'}`
