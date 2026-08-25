import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useInstrumentoFinanceiroStore from '../stores/instrumentoFinanceiroStore'
import useOrcamentoStore from '../stores/orcamentoStore'
import FormErrors from '../components/FormErrors'
import CampoMoeda from '../components/CampoMoeda'
import CampoSei from '../components/CampoSei'
import { TIPO_INSTRUMENTO_OPTIONS } from './FespInstrumentoList'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Novo Instrumento Financeiro',
  descricao: 'Registra o instrumento externo (FESP, emenda parlamentar, convênio, repasse, fundo a fundo ou financiamento) que dá origem ao recurso de um ou mais Planos de Aplicação.',
  acoes: [
    { label: 'Tipo de instrumento',      texto: 'Classifica a origem do recurso — usado em relatórios e para orientar qual prestação de contas externa se aplica.' },
    { label: 'Número do instrumento',    texto: 'Número externo do instrumento (ex: número do convênio no SICONV), não gerado pelo sistema.' },
    { label: 'Fonte de recurso — Orçamento', texto: 'Vínculo opcional com uma fonte de recurso já cadastrada em Orçamento, para rastreabilidade cruzada.' },
    { label: 'Criar instrumento',        texto: 'Salva o instrumento, que pode então ser vinculado a itens de Planos de Aplicação.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FespInstrumentoCreate() {
  const navigate = useNavigate()
  const { createInstrumento } = useInstrumentoFinanceiroStore()
  const { fontes, fetchFontes } = useOrcamentoStore()

  const [form, setForm] = useState({
    tipo_instrumento: 'fesp',
    numero_instrumento: '',
    objeto: '',
    orgao_concedente_nome: '',
    fonte_recurso: '',
    valor_total_pactuado: '',
    valor_contrapartida: '',
    data_assinatura: '',
    vigencia_inicio: '',
    vigencia_fim: '',
    numero_processo_sei: '',
    observacoes: '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => { fetchFontes() }, [])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.tipo_instrumento) e.tipo_instrumento = 'Campo obrigatório'
    if (!form.numero_instrumento.trim()) e.numero_instrumento = 'Campo obrigatório'
    if (!form.objeto.trim()) e.objeto = 'Campo obrigatório'
    if (!form.valor_total_pactuado || isNaN(Number(form.valor_total_pactuado)))
      e.valor_total_pactuado = 'Valor inválido'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const payload = {
        tipo_instrumento: form.tipo_instrumento,
        numero_instrumento: form.numero_instrumento,
        objeto: form.objeto,
        orgao_concedente_nome: form.orgao_concedente_nome,
        fonte_recurso: form.fonte_recurso || null,
        valor_total_pactuado: Number(form.valor_total_pactuado),
        valor_contrapartida: Number(form.valor_contrapartida || 0),
        data_assinatura: form.data_assinatura || null,
        vigencia_inicio: form.vigencia_inicio || null,
        vigencia_fim: form.vigencia_fim || null,
        numero_processo_sei: form.numero_processo_sei,
        observacoes: form.observacoes,
      }
      const instrumento = await createInstrumento(payload)
      navigate(`/fesp/instrumentos/${instrumento.id}`)
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
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Novo Instrumento Financeiro</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Tipo de instrumento" error={errors.tipo_instrumento}>
            <select value={form.tipo_instrumento}
              onChange={(e) => set('tipo_instrumento', e.target.value)}
              className={inp(errors.tipo_instrumento)}>
              {TIPO_INSTRUMENTO_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </Field>

          <Field label="Número do instrumento (externo)" error={errors.numero_instrumento}>
            <input type="text" value={form.numero_instrumento}
              onChange={(e) => set('numero_instrumento', e.target.value)}
              placeholder="Ex: FESP-2026, nº do convênio no SICONV..."
              className={inp(errors.numero_instrumento)} />
          </Field>
        </div>

        <Field label="Objeto" error={errors.objeto}>
          <textarea rows={3} value={form.objeto}
            onChange={(e) => set('objeto', e.target.value)}
            className={inp(errors.objeto)} />
        </Field>

        <Field label="Órgão/ente concedente (opcional)" error={errors.orgao_concedente_nome}>
          <input type="text" value={form.orgao_concedente_nome}
            onChange={(e) => set('orgao_concedente_nome', e.target.value)}
            placeholder="Ex: União, Ministério da Justiça e Segurança Pública..."
            className={inp()} />
        </Field>

        <Field label="Fonte de recurso — Orçamento (opcional)" error={errors.fonte_recurso}>
          <select value={form.fonte_recurso}
            onChange={(e) => set('fonte_recurso', e.target.value)}
            className={inp(errors.fonte_recurso)}>
            <option value="">Sem vínculo direto</option>
            {fontes.map((f) => <option key={f.id} value={f.id}>{f.codigo} — {f.nome}</option>)}
          </select>
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Valor total pactuado (R$)" error={errors.valor_total_pactuado}>
            <CampoMoeda value={form.valor_total_pactuado}
              onChange={(v) => set('valor_total_pactuado', v)}
              className={inp(errors.valor_total_pactuado)} />
          </Field>
          <Field label="Valor de contrapartida (R$)" error={errors.valor_contrapartida}>
            <CampoMoeda value={form.valor_contrapartida}
              onChange={(v) => set('valor_contrapartida', v)}
              className={inp(errors.valor_contrapartida)} />
          </Field>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Data de assinatura">
            <input type="date" value={form.data_assinatura}
              onChange={(e) => set('data_assinatura', e.target.value)} className={inp()} />
          </Field>
          <Field label="Início da vigência">
            <input type="date" value={form.vigencia_inicio}
              onChange={(e) => set('vigencia_inicio', e.target.value)} className={inp()} />
          </Field>
          <Field label="Fim da vigência">
            <input type="date" value={form.vigencia_fim}
              onChange={(e) => set('vigencia_fim', e.target.value)} className={inp()} />
          </Field>
        </div>

        <Field label="Número do processo SEI (opcional)">
          <CampoSei value={form.numero_processo_sei} onChange={(v) => set('numero_processo_sei', v)} className={inp()} />
        </Field>

        <Field label="Observações (opcional)">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
            {saving ? 'Salvando...' : 'Criar instrumento'}
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
