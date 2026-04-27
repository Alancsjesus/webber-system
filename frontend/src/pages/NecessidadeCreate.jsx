import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanejamentoStore from '../stores/planejamentoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import FormErrors from '../components/FormErrors'

const TODAY = new Date().toISOString().split('T')[0]

const AREAS = [
  { value: 'TI',        label: 'Tecnologia da Informação' },
  { value: 'Formação',  label: 'Formação' },
  { value: 'Ops',       label: 'Operações' },
  { value: 'Rede',      label: 'Rede' },
  { value: 'Frota',     label: 'Frota' },
  { value: 'Derivados', label: 'Derivados' },
]

const ANO_ATUAL = new Date().getFullYear()

export default function NecessidadeCreate() {
  const navigate = useNavigate()
  const { createNecessidade } = usePlanejamentoStore()
  const orgaoSigla = useAuthStore((s) => s.orgaoSigla)

  const [form, setForm] = useState({
    titulo: '',
    descricao: '',
    area_aplicacao: [],
    valor_estimado: '',
    departamento_solicitante: '',
    exercicio_fiscal: ANO_ATUAL,
    prioridade: 'Média',
    prazo_desejado: '',
    observacoes: '',
    tipo_execucao: 'interna',
    orgao_executor: '',
  })
  const [orgaosPai, setOrgaosPai] = useState([])
  const [saving, setSaving]   = useState(false)
  const [errors, setErrors]   = useState({})

  // Carregar órgãos disponíveis para execução externa (órgão pai)
  useEffect(() => {
    api.get('/core/orgaos/', { params: { page_size: 50 } })
      .then(({ data }) => {
        const list = data.results ?? data
        setOrgaosPai(list.filter(o => o.parent !== null || o.eh_pai))
      })
      .catch(() => {})
  }, [])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const toggleArea = (area) => {
    setForm((p) => ({
      ...p,
      area_aplicacao: p.area_aplicacao.includes(area)
        ? p.area_aplicacao.filter((a) => a !== area)
        : [...p.area_aplicacao, area],
    }))
    setErrors((p) => ({ ...p, area_aplicacao: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.titulo.trim())                    e.titulo = 'Campo obrigatório'
    if (!form.descricao.trim())                 e.descricao = 'Campo obrigatório'
    if (!form.departamento_solicitante.trim())  e.departamento_solicitante = 'Campo obrigatório'
    if (!form.valor_estimado || isNaN(Number(form.valor_estimado)))
      e.valor_estimado = 'Valor inválido'
    if (form.area_aplicacao.length === 0)
      e.area_aplicacao = 'Selecione ao menos uma área'
    if (!form.exercicio_fiscal)                 e.exercicio_fiscal = 'Campo obrigatório'
    if (form.prazo_desejado && form.prazo_desejado < TODAY)
      e.prazo_desejado = 'O prazo deve ser uma data futura'
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
        valor_estimado: Number(form.valor_estimado),
        exercicio_fiscal: Number(form.exercicio_fiscal),
        prazo_desejado: form.prazo_desejado || null,
        orgao_executor: form.tipo_execucao === 'externa' && form.orgao_executor
          ? Number(form.orgao_executor) : null,
      }
      const nec = await createNecessidade(payload)
      navigate(`/planejamento/necessidades/${nec.id}`)
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
      <h1 className="text-xl font-bold text-gray-800 mb-6">Nova Necessidade</h1>

      <form onSubmit={handleSubmit} className="space-y-5">

        <FormErrors errors={errors} />

        <Field label="Título *" error={errors.titulo}>
          <input type="text" value={form.titulo}
            onChange={(e) => set('titulo', e.target.value)}
            className={inp(errors.titulo)} />
        </Field>

        <Field label="Descrição" error={errors.descricao}>
          <textarea rows={3} value={form.descricao}
            onChange={(e) => set('descricao', e.target.value)}
            className={inp(errors.descricao)} />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Departamento solicitante" error={errors.departamento_solicitante}>
            <input type="text" value={form.departamento_solicitante}
              onChange={(e) => set('departamento_solicitante', e.target.value)}
              className={inp(errors.departamento_solicitante)} />
          </Field>

          <Field label="Exercício fiscal" error={errors.exercicio_fiscal}>
            <input type="number" min="2020" max="2050" value={form.exercicio_fiscal}
              onChange={(e) => set('exercicio_fiscal', e.target.value)}
              className={inp(errors.exercicio_fiscal)} />
          </Field>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Valor estimado (R$)" error={errors.valor_estimado}>
            <input type="number" min="0" step="0.01" value={form.valor_estimado}
              onChange={(e) => set('valor_estimado', e.target.value)}
              className={inp(errors.valor_estimado)} />
          </Field>

          <Field label="Prioridade">
            <select value={form.prioridade}
              onChange={(e) => set('prioridade', e.target.value)}
              className={inp()}>
              <option value="Alta">Alta</option>
              <option value="Média">Média</option>
              <option value="Baixa">Baixa</option>
            </select>
          </Field>
        </div>

        {/* Tipo de execução */}
        <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
          <p className="text-sm font-medium text-gray-700 mb-3">Responsável pela execução</p>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="tipo_execucao" value="interna"
                checked={form.tipo_execucao === 'interna'}
                onChange={() => { set('tipo_execucao', 'interna'); set('orgao_executor', '') }}
                className="accent-blue-600" />
              <span className="text-sm text-gray-700">
                <strong>Execução Interna</strong>
                <span className="block text-xs text-gray-500">Pelo próprio órgão ({orgaoSigla})</span>
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="radio" name="tipo_execucao" value="externa"
                checked={form.tipo_execucao === 'externa'}
                onChange={() => set('tipo_execucao', 'externa')}
                className="accent-blue-600" />
              <span className="text-sm text-gray-700">
                <strong>Execução Externa</strong>
                <span className="block text-xs text-gray-500">Repassada ao órgão superior (pai)</span>
              </span>
            </label>
          </div>

          {form.tipo_execucao === 'externa' && (
            <div className="mt-3">
              <Field label="Órgão executor (pai)" error={errors.orgao_executor}>
                <select value={form.orgao_executor}
                  onChange={(e) => set('orgao_executor', e.target.value)}
                  className={inp(errors.orgao_executor)}>
                  <option value="">— Selecione o órgão superior —</option>
                  {orgaosPai.map(o => (
                    <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>
                  ))}
                </select>
              </Field>
              <p className="text-xs text-amber-600 mt-1.5">
                Esta necessidade aguardará aceite do órgão superior antes de prosseguir.
              </p>
            </div>
          )}
        </div>

        <Field label="Áreas de aplicação" error={errors.area_aplicacao}>
          <div className="flex flex-wrap gap-2">
            {AREAS.map(({ value, label }) => {
              const sel = form.area_aplicacao.includes(value)
              return (
                <button key={value} type="button" onClick={() => toggleArea(value)}
                  className={`px-3 py-1.5 rounded-lg text-sm border font-medium transition-colors ${
                    sel ? 'bg-blue-600 border-blue-600 text-white'
                        : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                  }`}>
                  {label}
                </button>
              )
            })}
          </div>
        </Field>

        <Field label="Prazo desejado (opcional)" error={errors.prazo_desejado}>
          <input type="date" value={form.prazo_desejado} min={TODAY}
            onChange={(e) => set('prazo_desejado', e.target.value)}
            className={inp(errors.prazo_desejado)} />
        </Field>

        <Field label="Observações (opcional)">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
            {saving ? 'Salvando...' : 'Criar necessidade'}
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
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
