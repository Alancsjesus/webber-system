import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useContratoStore from '../stores/contratoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import FormErrors from '../components/FormErrors'

const TIPOS_ORIGEM = [
  { value: 'licitacao',       label: 'Licitação' },
  { value: 'dispensa',        label: 'Dispensa de Licitação' },
  { value: 'inexigibilidade', label: 'Inexigibilidade' },
  { value: 'saque_arp',       label: 'Saque de ATA de Registro de Preços' },
  { value: 'adesao_arp',      label: 'Adesão a ATA de Registro de Preços' },
]

export default function ContratoCreate() {
  const navigate = useNavigate()
  const { createContrato } = useContratoStore()
  const orgId = useAuthStore((s) => s.orgId)

  const [form, setForm] = useState({
    exercicio: new Date().getFullYear(),
    orgao_executor: '',
    objeto: '',
    tipo_origem: 'licitacao',
    dfd: '',
    valor_contrato: '',
    data_assinatura: '',
    data_vigencia_inicio: '',
    data_vigencia_fim: '',
    observacoes: '',
  })
  const [orgaos, setOrgaos]   = useState([])
  const [dfds, setDfds]       = useState([])
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  useEffect(() => {
    api.get('/core/orgaos/').then(({ data }) => setOrgaos(data.results ?? data))
    api.get('/demanda/dfd/', { params: { status: 'Aprovada', page_size: 200 } })
      .then(({ data }) => setDfds(data.results ?? data))
  }, [])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const validate = () => {
    const e = {}
    if (!form.orgao_executor) e.orgao_executor = 'Selecione o órgão executor'
    if (!form.objeto.trim())  e.objeto = 'Campo obrigatório'
    if (!form.tipo_origem)    e.tipo_origem = 'Selecione a origem'
    if (!form.valor_contrato || isNaN(Number(form.valor_contrato))) e.valor_contrato = 'Valor inválido'
    if (!form.exercicio)      e.exercicio = 'Campo obrigatório'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      const payload = {
        ...form,
        exercicio: Number(form.exercicio),
        orgao_executor: Number(form.orgao_executor),
        valor_contrato: Number(form.valor_contrato),
        dfd: form.dfd ? Number(form.dfd) : null,
        data_assinatura: form.data_assinatura || null,
        data_vigencia_inicio: form.data_vigencia_inicio || null,
        data_vigencia_fim: form.data_vigencia_fim || null,
      }
      const contrato = await createContrato(payload)
      navigate(`/contratos/${contrato.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  return (
    <div className="p-8 max-w-2xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Novo Contrato</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <div className="grid grid-cols-2 gap-4">
          <Field label="Exercício fiscal *" error={errors.exercicio}>
            <input type="number" min="2020" max="2050" value={form.exercicio}
              onChange={e => set('exercicio', e.target.value)} className={inp(errors.exercicio)} />
          </Field>
          <Field label="Tipo de origem *" error={errors.tipo_origem}>
            <select value={form.tipo_origem} onChange={e => set('tipo_origem', e.target.value)} className={inp(errors.tipo_origem)}>
              {TIPOS_ORIGEM.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </Field>
        </div>

        <Field label="Órgão executor *" error={errors.orgao_executor}>
          <select value={form.orgao_executor} onChange={e => set('orgao_executor', e.target.value)} className={inp(errors.orgao_executor)}>
            <option value="">Selecione...</option>
            {orgaos.map(o => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
          </select>
        </Field>

        <Field label="DFD de origem (opcional)">
          <select value={form.dfd} onChange={e => set('dfd', e.target.value)} className={inp()}>
            <option value="">Sem DFD vinculado</option>
            {dfds.map(d => <option key={d.id} value={d.id}>{d.numero_sei} — {d.descricao?.slice(0,50)}</option>)}
          </select>
        </Field>

        <Field label="Objeto *" error={errors.objeto}>
          <textarea rows={3} value={form.objeto} onChange={e => set('objeto', e.target.value)}
            placeholder="Descrição do objeto contratado..." className={inp(errors.objeto)} />
        </Field>

        <Field label="Valor do contrato (R$) *" error={errors.valor_contrato}>
          <input type="number" min="0" step="0.01" value={form.valor_contrato}
            onChange={e => set('valor_contrato', e.target.value)} className={inp(errors.valor_contrato)} />
        </Field>

        <div className="grid grid-cols-3 gap-4">
          <Field label="Data de assinatura">
            <input type="date" value={form.data_assinatura} onChange={e => set('data_assinatura', e.target.value)} className={inp()} />
          </Field>
          <Field label="Início da vigência">
            <input type="date" value={form.data_vigencia_inicio} onChange={e => set('data_vigencia_inicio', e.target.value)} className={inp()} />
          </Field>
          <Field label="Fim da vigência">
            <input type="date" value={form.data_vigencia_fim} onChange={e => set('data_vigencia_fim', e.target.value)} className={inp()} />
          </Field>
        </div>

        <Field label="Observações (opcional)">
          <textarea rows={2} value={form.observacoes} onChange={e => set('observacoes', e.target.value)} className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Salvando...' : 'Criar contrato'}
          </button>
          <button type="button" onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

const inp = (error) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${error ? 'border-red-400' : 'border-gray-300'}`
