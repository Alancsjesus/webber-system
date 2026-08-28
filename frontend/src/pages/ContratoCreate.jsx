import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useContratoStore from '../stores/contratoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import FormErrors from '../components/FormErrors'
import FornecedorPicker from '../components/FornecedorPicker'
import CampoMoeda from '../components/CampoMoeda'
import CampoSei from '../components/CampoSei'

const TIPOS_ORIGEM = [
  { value: 'licitacao',       label: 'Licitação' },
  { value: 'dispensa',        label: 'Dispensa de Licitação' },
  { value: 'inexigibilidade', label: 'Inexigibilidade' },
  { value: 'saque_arp',       label: 'Saque de ATA de Registro de Preços' },
  { value: 'adesao_arp',      label: 'Adesão a ATA de Registro de Preços' },
]

const TIPOS_INSTRUMENTO = [
  { value: 'contrato', label: 'Contrato' },
  { value: 'afm',      label: 'AFM — Autorização de Fornecimento de Material' },
]

const GARANTIA_TIPOS = [
  { value: 'caucao_dinheiro', label: 'Caução em Dinheiro' },
  { value: 'caucao_titulos',  label: 'Caução em Títulos da Dívida Pública' },
  { value: 'seguro_garantia', label: 'Seguro-Garantia' },
  { value: 'fianca_bancaria', label: 'Fiança Bancária' },
]

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Novo Contrato',
  descricao: 'Registra um contrato firmado com um fornecedor, geralmente após conclusão de um Procedimento — mas pode ser criado independentemente (ex: Saque/Adesão a ATA de Registro de Preços).',
  acoes: [
    { label: 'Tipo de origem',       texto: 'Classifica como o contrato foi originado: licitação, dispensa, inexigibilidade, ou saque/adesão a Ata de Registro de Preços.' },
    { label: 'Tipo de instrumento',  texto: 'Contrato: instrumento formal gerado pelo próprio Weber-e. AFM: Autorização de Fornecimento de Material recebida do SIMPAS — nesse caso, informe o número da AFM.' },
    { label: 'Processo SEI',         texto: 'Processo SEI da contratação em si. Cada fase posterior (apostila, aditivo, cronograma, medição, pagamento, notificação) pode ter seu próprio processo SEI, registrado na aba correspondente.' },
    { label: 'Fornecedor contratado', texto: 'Busca por CNPJ/CPF ou razão social no cadastro de fornecedores — histórico de relações anteriores fica disponível na tela de detalhe do fornecedor.' },
    { label: 'Exigir garantia contratual', texto: 'Percentual limitado a 5% do valor — acima disso exige justificativa obrigatória para contrato de grande vulto ou risco elevado (Art. 96, §3º).' },
    { label: 'Criar contrato',       texto: 'Salva o contrato. A execução (medições, pagamentos, cronograma de entrega) é registrada depois, na aba "Execução Contratual" do detalhe.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 92 (cláusulas necessárias) e Art. 96 (garantia).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ContratoCreate() {
  const navigate = useNavigate()
  const { createContrato } = useContratoStore()
  const orgId = useAuthStore((s) => s.orgId)

  const [form, setForm] = useState({
    exercicio: new Date().getFullYear(),
    orgao_executor: '',
    fornecedor: '',
    objeto: '',
    tipo_origem: 'licitacao',
    tipo_instrumento: 'contrato',
    numero_afm: '',
    numero_processo_sei: '',
    dfd: '',
    valor_contrato: '',
    data_assinatura: '',
    data_vigencia_inicio: '',
    data_vigencia_fim: '',
    observacoes: '',
    garantia_exigida: false,
    garantia_tipo: '',
    garantia_percentual: '',
    garantia_apolice: '',
    garantia_vigencia_inicio: '',
    garantia_vigencia_fim: '',
    garantia_justificativa_acima_5: '',
  })
  const [fornecedorLabel, setFornecedorLabel] = useState('')
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
    if (form.tipo_instrumento === 'afm' && !form.numero_afm.trim())
      e.numero_afm = 'Informe o número da AFM recebido do SIMPAS'
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
        fornecedor: form.fornecedor ? Number(form.fornecedor) : null,
        valor_contrato: Number(form.valor_contrato),
        dfd: form.dfd ? Number(form.dfd) : null,
        data_assinatura: form.data_assinatura || null,
        data_vigencia_inicio: form.data_vigencia_inicio || null,
        data_vigencia_fim: form.data_vigencia_fim || null,
        garantia_percentual: form.garantia_percentual !== '' ? Number(form.garantia_percentual) : null,
        garantia_vigencia_inicio: form.garantia_vigencia_inicio || null,
        garantia_vigencia_fim: form.garantia_vigencia_fim || null,
      }
      const contrato = await createContrato(payload)
      navigate(`/contratos/${contrato.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Novo Contrato</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Tipo de instrumento *" error={errors.tipo_instrumento}>
            <select value={form.tipo_instrumento} onChange={e => set('tipo_instrumento', e.target.value)} className={inp(errors.tipo_instrumento)}>
              {TIPOS_INSTRUMENTO.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </Field>
          {form.tipo_instrumento === 'afm' && (
            <Field label="Nº da AFM (SIMPAS) *" error={errors.numero_afm}>
              <input type="text" value={form.numero_afm} onChange={e => set('numero_afm', e.target.value)}
                placeholder="Ex: 20.003.00049/2026" className={inp(errors.numero_afm)} />
            </Field>
          )}
        </div>

        <Field label="Processo SEI (opcional)" error={errors.numero_processo_sei}>
          <CampoSei value={form.numero_processo_sei} onChange={v => set('numero_processo_sei', v)} />
        </Field>

        <Field label="Órgão executor *" error={errors.orgao_executor}>
          <select value={form.orgao_executor} onChange={e => set('orgao_executor', e.target.value)} className={inp(errors.orgao_executor)}>
            <option value="">Selecione...</option>
            {orgaos.map(o => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
          </select>
        </Field>

        <Field label="Fornecedor contratado (opcional)">
          <FornecedorPicker
            value={form.fornecedor}
            valueLabel={fornecedorLabel}
            onChange={(id, fornecedor) => {
              set('fornecedor', id)
              setFornecedorLabel(fornecedor ? `${fornecedor.documento} — ${fornecedor.nome_razao_social}` : '')
            }}
          />
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
          <CampoMoeda value={form.valor_contrato}
            onChange={v => set('valor_contrato', v)} className={inp(errors.valor_contrato)} />
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

        {/* Garantia contratual */}
        <div className="border border-gray-200 rounded-xl p-4 space-y-4">
          <div className="flex items-center gap-3">
            <input type="checkbox" id="garantia_exigida" checked={form.garantia_exigida}
              onChange={e => set('garantia_exigida', e.target.checked)}
              className="w-4 h-4 accent-blue-600" />
            <label htmlFor="garantia_exigida" className="text-sm font-medium text-gray-700 cursor-pointer">
              Exigir garantia contratual (art. 96, Lei 14.133/2021)
            </label>
          </div>

          {form.garantia_exigida && (
            <div className="space-y-4 pt-2 border-t border-gray-100">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Tipo de garantia *">
                  <select value={form.garantia_tipo} onChange={e => set('garantia_tipo', e.target.value)} className={inp()}>
                    <option value="">Selecione...</option>
                    {GARANTIA_TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </Field>
                <Field label="Percentual (%) *" error={errors.garantia_percentual}>
                  <input type="number" min="0" max="10" step="0.01"
                    value={form.garantia_percentual}
                    onChange={e => set('garantia_percentual', e.target.value)}
                    placeholder="Ex: 5.00"
                    className={inp(errors.garantia_percentual)} />
                </Field>
              </div>

              {Number(form.garantia_percentual) > 5 && (
                <Field label="Justificativa para percentual acima de 5% *" error={errors.garantia_justificativa_acima_5}>
                  <textarea rows={2} value={form.garantia_justificativa_acima_5}
                    onChange={e => set('garantia_justificativa_acima_5', e.target.value)}
                    placeholder="Contrato de grande vulto ou risco elevado conforme art. 96, §3º..."
                    className={inp(errors.garantia_justificativa_acima_5)} />
                </Field>
              )}

              <Field label="Nº da apólice / título (opcional)">
                <input type="text" value={form.garantia_apolice}
                  onChange={e => set('garantia_apolice', e.target.value)}
                  placeholder="Número do documento de garantia"
                  className={inp()} />
              </Field>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Field label="Início da vigência da garantia">
                  <input type="date" value={form.garantia_vigencia_inicio}
                    onChange={e => set('garantia_vigencia_inicio', e.target.value)} className={inp()} />
                </Field>
                <Field label="Fim da vigência da garantia">
                  <input type="date" value={form.garantia_vigencia_fim}
                    onChange={e => set('garantia_vigencia_fim', e.target.value)} className={inp()} />
                </Field>
              </div>
            </div>
          )}
        </div>

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
