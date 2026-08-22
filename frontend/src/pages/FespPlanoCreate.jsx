import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanoAplicacaoStore from '../stores/planoAplicacaoStore'
import FormErrors from '../components/FormErrors'

const ANO_ATUAL = new Date().getFullYear()

export default function FespPlanoCreate() {
  const navigate = useNavigate()
  const { createPlano } = usePlanoAplicacaoStore()

  const [form, setForm] = useState({
    exercicio_fiscal: ANO_ATUAL,
    ementa: '',
    descricao: '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.exercicio_fiscal) e.exercicio_fiscal = 'Campo obrigatório'
    if (!form.ementa.trim()) e.ementa = 'Campo obrigatório'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const plano = await createPlano({
        exercicio_fiscal: Number(form.exercicio_fiscal),
        ementa: form.ementa,
        descricao: form.descricao,
      })
      navigate(`/fesp/planos/${plano.id}`)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Novo Plano de Aplicação</h1>
      <p className="text-sm text-gray-500 mb-6">O número do plano é gerado automaticamente ao salvar.</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <Field label="Exercício fiscal" error={errors.exercicio_fiscal}>
          <input type="number" min="2020" max="2050" value={form.exercicio_fiscal}
            onChange={(e) => set('exercicio_fiscal', e.target.value)}
            className={inp(errors.exercicio_fiscal)} />
        </Field>

        <Field label="Ementa" error={errors.ementa}>
          <input type="text" value={form.ementa}
            onChange={(e) => set('ementa', e.target.value)}
            placeholder="Ex: Plano de Aplicação FESP — Enfrentamento à Violência contra a Mulher"
            className={inp(errors.ementa)} />
        </Field>

        <Field label="Descrição (opcional)">
          <textarea rows={3} value={form.descricao}
            onChange={(e) => set('descricao', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
            {saving ? 'Salvando...' : 'Criar plano'}
          </button>
          <button type="button" onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm transition-colors">
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
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
