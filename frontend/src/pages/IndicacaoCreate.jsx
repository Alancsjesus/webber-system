import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useIndicacaoStore from '../stores/indicacaoStore'
import DFDPicker from '../components/DFDPicker'
import NecessidadePicker from '../components/NecessidadePicker'

const ANO_ATUAL = new Date().getFullYear()

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Nova Indicação Orçamentária',
  descricao: 'Cria o "envelope" da indicação — o vínculo com dotações e o detalhamento por item de DFD são feitos depois, na tela de detalhe.',
  acoes: [
    { label: 'Vincular a', texto: 'DFD: a indicação nasce ligada a um DFD específico, habilitando o detalhamento por item depois. Necessidade: liga a uma necessidade de planejamento solta (sem DFD ainda). Sem vínculo: indicação genérica, sem rastreabilidade a um DFD ou necessidade específica.' },
    { label: 'Criar indicação', texto: 'Salva como Rascunho. Depois de criada, é preciso vincular dotações orçamentárias e, se ligada a um DFD, ratear os itens antes de submeter ao Ordenador.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

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
  const [dfdLabel, setDfdLabel] = useState('')
  const [necLabel, setNecLabel] = useState('')
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

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
            <DFDPicker
              value={form.dfd}
              valueLabel={dfdLabel}
              onChange={(id, dfd) => {
                set('dfd', id || '')
                setDfdLabel(dfd ? `${dfd.numero_sei} — ${dfd.descricao?.slice(0, 50) || ''}` : '')
              }}
            />
          </Field>
        )}

        {form.tipo_vinculo === 'necessidade' && (
          <Field label="Necessidade aprovada" error={errors.necessidade}>
            <NecessidadePicker
              value={form.necessidade}
              valueLabel={necLabel}
              onChange={(id, nec) => {
                set('necessidade', id || '')
                setNecLabel(nec ? `${nec.titulo} (${nec.exercicio_fiscal})` : '')
              }}
            />
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
