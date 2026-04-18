import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useEtpStore from '../stores/etpStore'

export default function ETPCreate() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const dfd       = location.state?.dfd
  const { createEtp } = useEtpStore()

  const [form, setForm] = useState({
    numero_sei: dfd?.numero_sei ?? '',
    necessidade_contratacao: '',
    requisitos_contratacao: '',
    levantamento_mercado: '',
    estimativa_valor: '',
    descricao_solucao: '',
    justificativa_solucao: '',
    riscos: '',
    sustentabilidade: '',
    observacoes: '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  if (!dfd) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-600">
          Nenhum DFD selecionado. Acesse esta página a partir de um DFD aprovado.
        </p>
        <button onClick={() => navigate(-1)} className="mt-3 text-sm text-blue-600 hover:underline">
          Voltar
        </button>
      </div>
    )
  }

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.numero_sei.trim())                e.numero_sei = 'Campo obrigatório'
    if (!form.necessidade_contratacao.trim())   e.necessidade_contratacao = 'Campo obrigatório'
    return e
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const etp = await createEtp({
        dfd: dfd.id,
        ...form,
        estimativa_valor: form.estimativa_valor ? Number(form.estimativa_valor) : null,
      })
      navigate(`/etp/etps/${etp.id}`)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      }
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8 max-w-2xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Novo ETP</h1>
      <p className="text-sm text-gray-500 mb-6">
        DFD de origem: <span className="font-medium text-gray-700">{dfd.numero_sei}</span>
      </p>

      {errors.non_field_errors && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {errors.non_field_errors}
        </div>
      )}
      {errors.dfd && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
          {errors.dfd}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">

        <Field label="Número SEI do ETP" error={errors.numero_sei}>
          <input type="text" value={form.numero_sei}
            onChange={(e) => set('numero_sei', e.target.value)}
            className={inp(errors.numero_sei)} />
        </Field>

        <Field label="Necessidade da contratação *" error={errors.necessidade_contratacao}>
          <textarea rows={4} value={form.necessidade_contratacao}
            onChange={(e) => set('necessidade_contratacao', e.target.value)}
            placeholder="Descreva a necessidade que justifica a contratação..."
            className={inp(errors.necessidade_contratacao)} />
        </Field>

        <Field label="Requisitos da contratação">
          <textarea rows={3} value={form.requisitos_contratacao}
            onChange={(e) => set('requisitos_contratacao', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Levantamento de mercado">
          <textarea rows={3} value={form.levantamento_mercado}
            onChange={(e) => set('levantamento_mercado', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Estimativa de valor (R$)">
          <input type="number" min="0" step="0.01" value={form.estimativa_valor}
            onChange={(e) => set('estimativa_valor', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Descrição da solução escolhida">
          <textarea rows={3} value={form.descricao_solucao}
            onChange={(e) => set('descricao_solucao', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Justificativa da solução">
          <textarea rows={2} value={form.justificativa_solucao}
            onChange={(e) => set('justificativa_solucao', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Mapa de riscos">
          <textarea rows={2} value={form.riscos}
            onChange={(e) => set('riscos', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Critérios de sustentabilidade">
          <textarea rows={2} value={form.sustentabilidade}
            onChange={(e) => set('sustentabilidade', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Observações">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
            {saving ? 'Salvando...' : 'Criar ETP'}
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
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
