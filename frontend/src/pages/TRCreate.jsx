import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useTrStore from '../stores/trStore'
import FormErrors from '../components/FormErrors'

// ── Prazo de Vigência ─────────────────────────────────────────────────────────

const TIPO_PRAZO_OPTS = [
  { value: '',           label: '— Selecione o tipo de vigência —' },
  { value: 'escopo',     label: 'Por Escopo — Aquisição/entrega única (Art. 105)' },
  { value: 'continuo',   label: 'Contínuo — Serviço continuado (Art. 106/107)' },
  { value: 'emergencial',label: 'Emergencial — Contratação direta emergência (Art. 75, VIII)' },
  { value: 'direta_108', label: 'Contratação Direta Art. 108' },
]
const INSTRUMENTO_OPTS = [
  { value: '',        label: '— Selecione —' },
  { value: 'contrato',label: 'Assinatura do Contrato' },
  { value: 'afm',     label: 'AFM — Autorização de Fornecimento de Material' },
  { value: 'aps',     label: 'APS — Autorização de Prestação de Serviços' },
]

function gerarRedacao(tipo, meses, instrumento) {
  const inst = INSTRUMENTO_OPTS.find(i => i.value === instrumento)?.label || instrumento || 'assinatura do Contrato'
  if (tipo === 'escopo')
    return `O prazo de vigência do Contrato é de 30 dias, a contar da data da ${inst}, observado o artigo 105 da Lei Federal n° 14.133/2021.`
  if (tipo === 'continuo')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 5 anos), a contar da data da ${inst}, prorrogável até atingir o limite de 10 anos, na forma dos artigos 106 e 107 da Lei Federal n° 14.133/2021.`
  if (tipo === 'emergencial')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses, podendo ser prorrogado, desde que o prazo total não ultrapasse 1 (um) ano, observado o art. 75, inc. VIII, da Lei Federal n° 14.133/2021.`
  if (tipo === 'direta_108')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 10 anos), a contar da data da ${inst}, nos termos do artigo 108 da Lei Federal n° 14.133/2021.`
  return ''
}

function PrazoVigenciaEditor({ form, set }) {
  const tipo = form.tipo_prazo_vigencia || ''
  const meses = form.prazo_meses || ''
  const instrumento = form.instrumento_inicio || ''
  const precisaMeses = ['continuo', 'emergencial', 'direta_108'].includes(tipo)
  const precisaInstrumento = ['escopo', 'continuo', 'direta_108'].includes(tipo)

  const atualizar = (novoTipo, novosMeses, novoInstrumento) => {
    set('tipo_prazo_vigencia', novoTipo)
    set('prazo_observacao', gerarRedacao(novoTipo, novosMeses, novoInstrumento))
  }

  const redacao = tipo ? gerarRedacao(tipo, meses, instrumento) : ''

  return (
    <div className="space-y-3">
      <div>
        <select
          value={tipo}
          onChange={e => { set('tipo_prazo_vigencia', e.target.value); atualizar(e.target.value, meses, instrumento) }}
          className={inp()}
        >
          {TIPO_PRAZO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {precisaMeses && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            Prazo em meses{tipo === 'continuo' ? ' (máx. 60)' : tipo === 'emergencial' ? ' (máx. 12)' : ' (máx. 120)'}
          </label>
          <input
            type="number" min="1"
            max={tipo === 'continuo' ? 60 : tipo === 'emergencial' ? 12 : 120}
            value={meses}
            onChange={e => { set('prazo_meses', e.target.value); atualizar(tipo, e.target.value, instrumento) }}
            className={inp()}
          />
        </div>
      )}
      {precisaInstrumento && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Instrumento de início da vigência</label>
          <select
            value={instrumento}
            onChange={e => { set('instrumento_inicio', e.target.value); atualizar(tipo, meses, e.target.value) }}
            className={inp()}
          >
            {INSTRUMENTO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      )}
      {redacao && (
        <div className="bg-teal-50 border border-teal-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-teal-700 mb-1">Redação gerada (Lei 14.133/2021):</p>
          <p className="text-xs text-teal-800 leading-relaxed">{redacao}</p>
        </div>
      )}
    </div>
  )
}

// ── Formulário principal ──────────────────────────────────────────────────────

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
    tipo_prazo_vigencia:    '',
    prazo_meses:            '',
    instrumento_inicio:     '',
    prazo_observacao:       '',
    local_entrega:          etp?.dfd_local_entrega ?? '',
    garantia_contrato:      '',
    estimativa_valor:       etp?.estimativa_valor ?? '',
    observacoes:            '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  if (!etp) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          Nenhum ETP selecionado. Acesse esta página a partir de um ETP aprovado.
        </p>
        <button onClick={() => navigate(-1)} className="mt-4 text-sm text-blue-600 hover:underline">← Voltar</button>
      </div>
    )
  }

  const set = (field, value) => {
    setForm(p => ({ ...p, [field]: value }))
    setErrors(p => ({ ...p, [field]: undefined }))
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
        objeto_contratacao:     form.objeto_contratacao,
        justificativa:          form.justificativa,
        requisitos_contratacao: form.requisitos_contratacao,
        obrigacoes_contratada:  form.obrigacoes_contratada,
        obrigacoes_contratante: form.obrigacoes_contratante,
        criterios_selecao:      form.criterios_selecao,
        criterios_medicao:      form.criterios_medicao,
        tipo_prazo_vigencia:    form.tipo_prazo_vigencia || '',
        prazo_meses:            form.prazo_meses ? Number(form.prazo_meses) : null,
        instrumento_inicio:     form.instrumento_inicio || '',
        prazo_observacao:       form.prazo_observacao,
        local_entrega:          form.local_entrega,
        garantia_contrato:      form.garantia_contrato,
        estimativa_valor:       form.estimativa_valor ? Number(form.estimativa_valor) : null,
        observacoes:            form.observacoes,
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
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      <h1 className="text-xl font-bold text-gray-800 mb-1">Nova Minuta do Termo de Referência</h1>
      <div className="flex items-center gap-3 text-sm text-gray-500 mb-6">
        <span>ETP: <span className="font-mono font-semibold text-teal-700">{etp.numero_sei}</span></span>
        <span>·</span>
        <span>DFD: <span className="font-mono font-semibold">{etp.dfd_numero_sei}</span></span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <F label="Objeto da contratação *" error={errors.objeto_contratacao}>
          <textarea rows={3} value={form.objeto_contratacao}
            onChange={e => set('objeto_contratacao', e.target.value)}
            placeholder="Descreva o objeto a ser contratado..."
            className={inp(errors.objeto_contratacao)} />
        </F>

        <F label="Justificativa da contratação">
          <textarea rows={3} value={form.justificativa}
            onChange={e => set('justificativa', e.target.value)}
            className={inp()} />
        </F>

        <F label="Requisitos da contratação">
          <textarea rows={3} value={form.requisitos_contratacao}
            onChange={e => set('requisitos_contratacao', e.target.value)}
            className={inp()} />
        </F>

        <div className="grid grid-cols-2 gap-4">
          <F label="Obrigações da contratada">
            <textarea rows={3} value={form.obrigacoes_contratada}
              onChange={e => set('obrigacoes_contratada', e.target.value)}
              className={inp()} />
          </F>
          <F label="Obrigações da contratante">
            <textarea rows={3} value={form.obrigacoes_contratante}
              onChange={e => set('obrigacoes_contratante', e.target.value)}
              className={inp()} />
          </F>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <F label="Critérios de seleção do fornecedor">
            <textarea rows={2} value={form.criterios_selecao}
              onChange={e => set('criterios_selecao', e.target.value)}
              className={inp()} />
          </F>
          <F label="Critérios de medição e pagamento">
            <textarea rows={2} value={form.criterios_medicao}
              onChange={e => set('criterios_medicao', e.target.value)}
              className={inp()} />
          </F>
        </div>

        {/* Prazo de Vigência — estruturado */}
        <F label="Prazo de Vigência do Contrato">
          <PrazoVigenciaEditor form={form} set={set} />
        </F>

        <div className="grid grid-cols-2 gap-4">
          <F label="Estimativa de valor (R$)" error={errors.estimativa_valor}>
            <input type="number" min="0" step="0.01" value={form.estimativa_valor}
              onChange={e => set('estimativa_valor', e.target.value)}
              className={inp(errors.estimativa_valor)} />
          </F>
          <F label="Local de entrega">
            <input type="text" value={form.local_entrega}
              onChange={e => set('local_entrega', e.target.value)}
              className={inp()} />
          </F>
        </div>

        <F label="Garantia contratual">
          <textarea rows={2} value={form.garantia_contrato}
            onChange={e => set('garantia_contrato', e.target.value)}
            className={inp()} />
        </F>

        <F label="Observações">
          <textarea rows={2} value={form.observacoes}
            onChange={e => set('observacoes', e.target.value)}
            className={inp()} />
        </F>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Criando...' : 'Criar Minuta TR'}
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
