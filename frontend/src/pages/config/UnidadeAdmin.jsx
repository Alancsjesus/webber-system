import { useEffect, useState } from 'react'
import api from '../../services/api'

const TIPOS = [
  { value: 'demandante',   label: 'Demandante' },
  { value: 'licitante',    label: 'Licitante' },
  { value: 'contratante',  label: 'Contratante' },
  { value: 'planejamento', label: 'Planejamento' },
]

const empty = () => ({ sigla: '', nome: '', orgao: '', tipo: 'demandante', ativa: true })

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Unidades',
  descricao: 'Cadastro das unidades organizacionais dentro de cada órgão (ex: Coordenadoria de Licitações). O tipo da unidade amplia o acesso a módulos além do papel do usuário — ex: usuário em unidade "licitante" ganha acesso a Licitação mesmo sem esse papel individual.',
  acoes: [
    { label: 'Tipo',   texto: 'Demandante, Licitante, Contratante ou Planejamento — controla quais seções do menu ficam visíveis para usuários vinculados a essa unidade, independente do papel individual de cada um.' },
    { label: 'Órgão',  texto: 'Toda unidade pertence a exatamente um órgão — filtros e listagens usam esse vínculo.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function UnidadeAdmin() {
  const [list, setList]       = useState([])
  const [orgaos, setOrgaos]   = useState([])
  const [loading, setLoading] = useState(true)
  const [filterOrg, setFilterOrg] = useState('')
  const [filterTipo, setFilterTipo] = useState('')
  const [form, setForm]       = useState(null)
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  const load = () => {
    setLoading(true)
    const params = { page_size: 300 }
    if (filterOrg)  params.orgao = filterOrg
    if (filterTipo) params.tipo  = filterTipo
    api.get('/core/unidades/', { params: { ...params, ativa: 'all' } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }
  useEffect(load, [filterOrg, filterTipo])
  useEffect(() => {
    api.get('/core/orgaos/', { params: { page_size: 100 } })
      .then(({ data }) => setOrgaos(data.results ?? data))
  }, [])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true); setErrors({})
    try {
      const payload = {
        sigla: form.sigla,
        nome: form.nome,
        orgao: Number(form.orgao),
        tipo: form.tipo,
        ativa: form.ativa,
      }
      if (form.id) await api.patch(`/core/unidades/${form.id}/`, payload)
      else          await api.post('/core/unidades/', payload)
      setForm(null); load()
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Desativar esta unidade?')) return
    await api.delete(`/core/unidades/${id}/`)
    load()
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Unidades Organizacionais</h1>
          <p className="text-sm text-gray-500 mt-0.5">Demandante, Licitante, Contratante, Planejamento</p>
        </div>
        <button onClick={() => setForm(empty())}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Nova unidade
        </button>
      </div>

      {form && (
        <div className="mb-6 border border-blue-200 bg-blue-50 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-blue-800 mb-4">{form.id ? 'Editar unidade' : 'Nova unidade'}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <F label="Órgão *" error={errors.orgao}>
              <select value={form.orgao || ''} onChange={e => set('orgao', e.target.value)} className={inp(errors.orgao)}>
                <option value="">— selecione —</option>
                {orgaos.map(o => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
              </select>
            </F>
            <F label="Tipo *" error={errors.tipo}>
              <select value={form.tipo} onChange={e => set('tipo', e.target.value)} className={inp(errors.tipo)}>
                {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </F>
            <F label="Sigla *" error={errors.sigla}>
              <input value={form.sigla} onChange={e => set('sigla', e.target.value.toUpperCase())}
                className={inp(errors.sigla)} placeholder="Ex: CLIC" />
            </F>
            <F label="Nome *" error={errors.nome}>
              <input value={form.nome} onChange={e => set('nome', e.target.value)}
                className={inp(errors.nome)} placeholder="Nome completo da unidade" />
            </F>
            <F label="Situação">
              <select value={form.ativa ? 'true' : 'false'} onChange={e => set('ativa', e.target.value === 'true')} className={inp()}>
                <option value="true">Ativa</option>
                <option value="false">Inativa</option>
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

      <div className="flex flex-wrap gap-3 mb-4">
        <select value={filterOrg} onChange={e => setFilterOrg(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os órgãos</option>
          {orgaos.map(o => <option key={o.id} value={o.id}>{o.sigla}</option>)}
        </select>
        <select value={filterTipo} onChange={e => setFilterTipo(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os tipos</option>
          {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
      </div>

      {loading ? <p className="text-sm text-gray-400">Carregando...</p> : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Sigla</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Nome</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Sit.</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(u => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-mono text-xs text-gray-500">{u.orgao_sigla}</td>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{u.sigla}</td>
                  <td className="px-5 py-3 text-gray-700">{u.nome}</td>
                  <td className="px-5 py-3">
                    <TipoBadge tipo={u.tipo} />
                  </td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${u.ativa ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {u.ativa ? 'Ativa' : 'Inativa'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right space-x-2">
                    <button onClick={() => setForm({ ...u })} className="text-xs text-blue-600 hover:underline">Editar</button>
                    {u.ativa && <button onClick={() => handleDelete(u.id)} className="text-xs text-red-500 hover:underline">Desativar</button>}
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

const TIPO_CLS = {
  demandante:   'bg-purple-100 text-purple-700',
  licitante:    'bg-blue-100 text-blue-700',
  contratante:  'bg-green-100 text-green-700',
  planejamento: 'bg-orange-100 text-orange-700',
}
const TIPO_LABEL = { demandante: 'Demandante', licitante: 'Licitante', contratante: 'Contratante', planejamento: 'Planejamento' }

function TipoBadge({ tipo }) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${TIPO_CLS[tipo] || 'bg-gray-100 text-gray-500'}`}>
      {TIPO_LABEL[tipo] || tipo}
    </span>
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
