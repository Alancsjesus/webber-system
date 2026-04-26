import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useIndicacaoStore from '../stores/indicacaoStore'
import api from '../services/api'

const ANO_ATUAL = new Date().getFullYear()

export default function IndicacaoCreate() {
  const navigate = useNavigate()
  const { createIndicacao } = useIndicacaoStore()

  const [form, setForm] = useState({
    exercicio_fiscal: ANO_ATUAL,
    tipo_vinculo: 'dfd',   // 'dfd' | 'necessidade' | 'nenhum'
    dfd: '',
    necessidade: '',
    observacoes: '',
  })
  const [dfds, setDfds]   = useState([])
  const [necs, setNecs]   = useState([])
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    api.get('/demanda/dfd/', { params: { status: 'Aprovada', page_size: 100 } })
      .then(({ data }) => setDfds(data.results ?? data))
      .catch(() => {})
    api.get('/planejamento/necessidade/', { params: { status: 'Aprovada', page_size: 100 } })
      .then(({ data }) => setNecs(data.results ?? data))
      .catch(() => {})
  }, [])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.exercicio_fiscal) errs.exercicio_fiscal = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const payload = {
        exercicio_fiscal: Number(form.exercicio_fiscal),
        observacoes: form.observacoes,
      }
      if (form.tipo_vinculo === 'dfd' && form.dfd)
        payload.dfd = Number(form.dfd)
      if (form.tipo_vinculo === 'necessidade' && form.necessidade)
        payload.necessidade = Number(form.necessidade)

      const ind = await createIndicacao(payload)
      navigate(`/orcamento/indicacoes/${ind.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d))
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8 max-w-xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Nova Indicação Orçamentária</h1>
      <p className="text-sm text-gray-500 mb-6">
        Após criar, vincule as dotações e os valores indicados antes de submeter ao Ordenador.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Field label="Exercício fiscal *" error={errors.exercicio_fiscal}>
          <input
            type="number" min="2020" max="2050"
            value={form.exercicio_fiscal}
            onChange={(e) => set('exercicio_fiscal', e.target.value)}
            className={inp(errors.exercicio_fiscal)}
          />
        </Field>

        <Field label="Vincular a" error={errors.tipo_vinculo}>
          <div className="flex gap-4 mt-1">
            {[
              { val: 'dfd',        label: 'DFD' },
              { val: 'necessidade', label: 'Necessidade' },
              { val: 'nenhum',     label: 'Sem vínculo' },
            ].map(({ val, label }) => (
              <label key={val} className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
                <input
                  type="radio" name="tipo_vinculo" value={val}
                  checked={form.tipo_vinculo === val}
                  onChange={() => set('tipo_vinculo', val)}
                  className="accent-blue-600"
                />
                {label}
              </label>
            ))}
          </div>
        </Field>

        {form.tipo_vinculo === 'dfd' && (
          <Field label="DFD aprovado" error={errors.dfd}>
            <select value={form.dfd} onChange={(e) => set('dfd', e.target.value)} className={inp(errors.dfd)}>
              <option value="">Selecione um DFD...</option>
              {dfds.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.numero_sei} — {d.descricao?.slice(0, 50)}
                </option>
              ))}
            </select>
          </Field>
        )}

        {form.tipo_vinculo === 'necessidade' && (
          <Field label="Necessidade aprovada" error={errors.necessidade}>
            <select value={form.necessidade} onChange={(e) => set('necessidade', e.target.value)} className={inp(errors.necessidade)}>
              <option value="">Selecione uma necessidade...</option>
              {necs.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.titulo} ({n.exercicio_fiscal})
                </option>
              ))}
            </select>
          </Field>
        )}

        <Field label="Observações">
          <textarea
            rows={3} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            placeholder="Justificativa ou observações adicionais..."
            className={inp()}
          />
        </Field>

        <div className="flex gap-3 pt-2">
          <button
            type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm"
          >
            {saving ? 'Criando...' : 'Criar indicação'}
          </button>
          <button
            type="button" onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm"
          >
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
