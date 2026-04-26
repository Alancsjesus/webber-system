import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useTrStore from '../stores/trStore'

export default function TRCreate() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const etp       = location.state?.etp
  const { createTr } = useTrStore()

  const [form, setForm] = useState({
    objeto_contratacao:     '',
    justificativa:          '',
    requisitos_contratacao: '',
    obrigacoes_contratada:  '',
    obrigacoes_contratante: '',
    criterios_selecao:      '',
    criterios_medicao:      '',
    prazo_execucao:         '',
    local_entrega:          etp?.dfd_local_entrega ?? '',
    garantia_contrato:      '',
    estimativa_valor:       etp?.estimativa_valor ?? '',
    observacoes:            '',
  })
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  if (!etp) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-600">Nenhum ETP selecionado. Acesse esta página a partir de um ETP aprovado.</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-sm text-blue-600 hover:underline">← Voltar</button>
      </div>
    )
  }

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.objeto_contratacao.trim()) errs.objeto_contratacao = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const tr = await createTr({
        etp: etp.id,
        ...form,
        estimativa_valor: form.estimativa_valor ? Number(form.estimativa_valor) : null,
      })
      navigate(`/analise-tecnica/trs/${tr.id}`)
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
    <div className="p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Nova Minuta do Termo de Referência</h1>
      <p className="text-sm text-gray-500 mb-6">
        ETP: <span className="font-mono font-medium text-teal-700">{etp.numero_sei}</span>
        {' · '}DFD: <span className="font-mono font-medium">{etp.dfd_numero_sei}</span>
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <F label="Objeto da contratação *" error={errors.objeto_contratacao}>
          <textarea rows={3} value={form.objeto_contratacao}
            onChange={(e) => set('objeto_contratacao', e.target.value)}
            className={inp(errors.objeto_contratacao)}
            placeholder="Descreva o objeto a ser contratado..." />
        </F>

        <F label="Justificativa da contratação" error={errors.justificativa}>
          <textarea rows={3} value={form.justificativa}
            onChange={(e) => set('justificativa', e.target.value)}
            className={inp(errors.justificativa)} />
        </F>

        <F label="Requisitos da contratação" error={errors.requisitos_contratacao}>
          <textarea rows={3} value={form.requisitos_contratacao}
            onChange={(e) => set('requisitos_contratacao', e.target.value)}
            className={inp()} />
        </F>

        <div className="grid grid-cols-2 gap-4">
          <F label="Obrigações da contratada">
            <textarea rows={3} value={form.obrigacoes_contratada}
              onChange={(e) => set('obrigacoes_contratada', e.target.value)}
              className={inp()} />
          </F>
          <F label="Obrigações da contratante">
            <textarea rows={3} value={form.obrigacoes_contratante}
              onChange={(e) => set('obrigacoes_contratante', e.target.value)}
              className={inp()} />
          </F>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <F label="Critérios de seleção do fornecedor">
            <textarea rows={2} value={form.criterios_selecao}
              onChange={(e) => set('criterios_selecao', e.target.value)}
              className={inp()} />
          </F>
          <F label="Critérios de medição e pagamento">
            <textarea rows={2} value={form.criterios_medicao}
              onChange={(e) => set('criterios_medicao', e.target.value)}
              className={inp()} />
          </F>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <F label="Prazo de execução">
            <input type="text" value={form.prazo_execucao}
              onChange={(e) => set('prazo_execucao', e.target.value)}
              placeholder="Ex: 12 meses" className={inp()} />
          </F>
          <F label="Estimativa de valor (R$)" error={errors.estimativa_valor}>
            <input type="number" min="0" step="0.01" value={form.estimativa_valor}
              onChange={(e) => set('estimativa_valor', e.target.value)}
              className={inp(errors.estimativa_valor)} />
          </F>
        </div>

        <F label="Local de entrega">
          <input type="text" value={form.local_entrega}
            onChange={(e) => set('local_entrega', e.target.value)}
            className={inp()} />
        </F>

        <F label="Garantia contratual">
          <textarea rows={2} value={form.garantia_contrato}
            onChange={(e) => set('garantia_contrato', e.target.value)}
            className={inp()} />
        </F>

        <F label="Observações">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </F>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Salvando...' : 'Criar TR'}
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

function F({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

const inp = (error) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
