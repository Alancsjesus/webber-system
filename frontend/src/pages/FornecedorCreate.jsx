import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useFornecedorStore from '../stores/fornecedorStore'
import { mascararDocumento, validarDocumento } from '../utils/documentoValidator'

const PORTES = [
  { value: '',       label: 'Não informado' },
  { value: 'MEI',    label: 'MEI' },
  { value: 'ME',     label: 'Microempresa' },
  { value: 'EPP',    label: 'Empresa de Pequeno Porte' },
  { value: 'DEMAIS', label: 'Demais' },
]

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Novo Fornecedor',
  descricao: 'Cadastro global — não pertence a um órgão específico, fica disponível para toda a plataforma ao vincular cotações, licitações e contratos.',
  acoes: [
    { label: 'Tipo de pessoa',   texto: 'Pessoa Jurídica (CNPJ) ou Física (CPF) — muda a máscara e a validação do documento, e habilita os campos de Nome Fantasia/Porte só para PJ.' },
    { label: 'CNPJ/CPF',         texto: 'Validado por dígito verificador antes de salvar — não é só formatação.' },
    { label: 'Cadastrar fornecedor', texto: 'Salva o fornecedor, que passa a poder ser buscado nos formulários de cotação, licitação e contrato.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FornecedorCreate() {
  const navigate = useNavigate()
  const { createFornecedor } = useFornecedorStore()

  const [form, setForm] = useState({
    tipo_pessoa: 'PJ',
    documento: '',
    nome_razao_social: '',
    nome_fantasia: '',
    porte_empresa: '',
    email: '',
    telefone: '',
    municipio: '',
    uf: '',
    observacoes: '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const setTipoPessoa = (tipo) => {
    setForm(p => ({ ...p, tipo_pessoa: tipo, documento: mascararDocumento(p.documento, tipo) }))
  }

  const setDocumento = (valor) => {
    setForm(p => ({ ...p, documento: mascararDocumento(valor, p.tipo_pessoa) }))
    setErrors(p => ({ ...p, documento: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!validarDocumento(form.documento, form.tipo_pessoa)) {
      e.documento = form.tipo_pessoa === 'PF' ? 'CPF inválido' : 'CNPJ inválido'
    }
    if (!form.nome_razao_social.trim()) e.nome_razao_social = 'Campo obrigatório'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      const fornecedor = await createFornecedor(form)
      navigate(`/fornecedores/${fornecedor.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Novo Fornecedor</h1>
        <p className="text-sm text-gray-500 mt-0.5">Cadastro válido para todos os órgãos do sistema</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <Field label="Tipo de pessoa *">
          <div className="flex gap-2">
            {[['PJ', 'Pessoa Jurídica (CNPJ)'], ['PF', 'Pessoa Física (CPF)']].map(([value, label]) => (
              <button key={value} type="button" onClick={() => setTipoPessoa(value)}
                className={`flex-1 border rounded-lg px-3 py-2 text-sm ${form.tipo_pessoa === value ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium' : 'border-gray-300 text-gray-600'}`}>
                {label}
              </button>
            ))}
          </div>
        </Field>

        <Field label={form.tipo_pessoa === 'PF' ? 'CPF *' : 'CNPJ *'} error={errors.documento}>
          <input value={form.documento} onChange={e => setDocumento(e.target.value)}
            placeholder={form.tipo_pessoa === 'PF' ? '000.000.000-00' : '00.000.000/0000-00'}
            className={inp(errors.documento)} />
        </Field>

        <Field label={form.tipo_pessoa === 'PF' ? 'Nome completo *' : 'Razão social *'} error={errors.nome_razao_social}>
          <input value={form.nome_razao_social} onChange={e => set('nome_razao_social', e.target.value)}
            className={inp(errors.nome_razao_social)} />
        </Field>

        {form.tipo_pessoa === 'PJ' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Nome fantasia">
              <input value={form.nome_fantasia} onChange={e => set('nome_fantasia', e.target.value)} className={inp()} />
            </Field>
            <Field label="Porte">
              <select value={form.porte_empresa} onChange={e => set('porte_empresa', e.target.value)} className={inp()}>
                {PORTES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
              </select>
            </Field>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="E-mail">
            <input type="email" value={form.email} onChange={e => set('email', e.target.value)} className={inp()} />
          </Field>
          <Field label="Telefone">
            <input value={form.telefone} onChange={e => set('telefone', e.target.value)} className={inp()} />
          </Field>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-4">
          <Field label="Município">
            <input value={form.municipio} onChange={e => set('municipio', e.target.value)} className={inp()} />
          </Field>
          <Field label="UF">
            <input value={form.uf} onChange={e => set('uf', e.target.value.toUpperCase().slice(0, 2))}
              className={`${inp()} w-20`} maxLength={2} />
          </Field>
        </div>

        <Field label="Observações">
          <textarea rows={3} value={form.observacoes} onChange={e => set('observacoes', e.target.value)} className={inp()} />
        </Field>

        <div className="flex gap-2 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : 'Cadastrar fornecedor'}
          </button>
          <button type="button" onClick={() => navigate('/fornecedores')}
            className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
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
const inp = (err) => `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400' : 'border-gray-300'}`
