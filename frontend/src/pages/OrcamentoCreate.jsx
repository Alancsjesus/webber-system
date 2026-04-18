import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useOrcamentoStore from '../stores/orcamentoStore'

const ANO_ATUAL = new Date().getFullYear()

export default function OrcamentoCreate() {
  const navigate = useNavigate()
  const { createDotacao, fetchAcoes, fetchElementos, fetchFontes, acoes, elementos, fontes } =
    useOrcamentoStore()

  const [form, setForm] = useState({
    exercicio_fiscal: ANO_ATUAL,
    acao: '',
    elemento_despesa: '',
    fonte_recurso: '',
    valor_dotado: '',
    status: 'Proposta',
    eixo: '',
    objetivo_estrategico: '',
    observacoes: '',
  })
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    fetchAcoes()
    fetchElementos()
    fetchFontes()
  }, [])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.exercicio_fiscal)                             e.exercicio_fiscal = 'Campo obrigatório'
    if (!form.acao)                                         e.acao = 'Selecione uma ação'
    if (!form.elemento_despesa)                             e.elemento_despesa = 'Selecione um elemento'
    if (!form.fonte_recurso)                                e.fonte_recurso = 'Selecione uma fonte'
    if (!form.valor_dotado || isNaN(Number(form.valor_dotado))) e.valor_dotado = 'Valor inválido'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const dotacao = await createDotacao({
        ...form,
        exercicio_fiscal: Number(form.exercicio_fiscal),
        acao: Number(form.acao),
        elemento_despesa: Number(form.elemento_despesa),
        fonte_recurso: Number(form.fonte_recurso),
        valor_dotado: Number(form.valor_dotado),
      })
      navigate(`/orcamento/dotacoes/${dotacao.id}`)
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
      <h1 className="text-xl font-bold text-gray-800 mb-6">Nova Dotação Orçamentária</h1>

      <form onSubmit={handleSubmit} className="space-y-5">

        <div className="grid grid-cols-2 gap-4">
          <Field label="Exercício fiscal" error={errors.exercicio_fiscal}>
            <input type="number" min="2020" max="2050" value={form.exercicio_fiscal}
              onChange={(e) => set('exercicio_fiscal', e.target.value)}
              className={inp(errors.exercicio_fiscal)} />
          </Field>

          <Field label="Status">
            <select value={form.status}
              onChange={(e) => set('status', e.target.value)}
              className={inp()}>
              <option value="Proposta">Proposta</option>
              <option value="Em Análise">Em Análise</option>
              <option value="Aprovada">Aprovada</option>
              <option value="Em Execução">Em Execução</option>
              <option value="Concluída">Concluída</option>
              <option value="Cancelada">Cancelada</option>
            </select>
          </Field>
        </div>

        <Field label="Ação orçamentária" error={errors.acao}>
          <select value={form.acao}
            onChange={(e) => set('acao', e.target.value)}
            className={inp(errors.acao)}>
            <option value="">Selecione uma ação...</option>
            {acoes.map((a) => (
              <option key={a.id} value={a.id}>
                {a.codigo} — {a.nome}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Elemento de despesa" error={errors.elemento_despesa}>
          <select value={form.elemento_despesa}
            onChange={(e) => set('elemento_despesa', e.target.value)}
            className={inp(errors.elemento_despesa)}>
            <option value="">Selecione um elemento...</option>
            {elementos.map((el) => (
              <option key={el.id} value={el.id}>
                {el.codigo} — {el.descricao}
              </option>
            ))}
          </select>
        </Field>

        <Field label="Fonte de recurso" error={errors.fonte_recurso}>
          <select value={form.fonte_recurso}
            onChange={(e) => set('fonte_recurso', e.target.value)}
            className={inp(errors.fonte_recurso)}>
            <option value="">Selecione uma fonte...</option>
            {fontes.map((f) => (
              <option key={f.id} value={f.id}>
                {f.codigo} — {f.nome} ({f.tipo})
              </option>
            ))}
          </select>
        </Field>

        <Field label="Valor dotado (R$)" error={errors.valor_dotado}>
          <input type="number" min="0" step="0.01" value={form.valor_dotado}
            onChange={(e) => set('valor_dotado', e.target.value)}
            className={inp(errors.valor_dotado)} />
        </Field>

        <Field label="Eixo (opcional)">
          <input type="text" value={form.eixo}
            onChange={(e) => set('eixo', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Objetivo estratégico (opcional)">
          <input type="text" value={form.objetivo_estrategico}
            onChange={(e) => set('objetivo_estrategico', e.target.value)}
            className={inp()} />
        </Field>

        <Field label="Observações (opcional)">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
            {saving ? 'Salvando...' : 'Criar dotação'}
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
