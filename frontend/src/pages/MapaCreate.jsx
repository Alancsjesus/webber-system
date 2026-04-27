import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useMapaStore from '../stores/mapaStore'
import api from '../services/api'

const ANO = new Date().getFullYear()

export default function MapaCreate() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const dfd       = location.state?.dfd
  const { createMapa } = useMapaStore()

  const [form, setForm] = useState({
    objeto:           dfd?.descricao ?? '',
    exercicio_fiscal: ANO,
    dfd:              dfd?.id ?? '',
    observacoes:      '',
  })
  const [dfds, setDfds]   = useState([])
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    api.get('/demanda/dfd/', { params: { status: 'Aprovada', page_size: 100 } })
      .then(({ data }) => setDfds(data.results ?? data))
      .catch(() => {})
  }, [])

  const set = (k, v) => { setForm((p) => ({ ...p, [k]: v })); setErrors((p) => ({ ...p, [k]: undefined })) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.objeto.trim())    errs.objeto = 'Campo obrigatório'
    if (!form.exercicio_fiscal) errs.exercicio_fiscal = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      const payload = { ...form, exercicio_fiscal: Number(form.exercicio_fiscal), metodo_calculo: 'media' }
      if (!form.dfd) delete payload.dfd
      const mapa = await createMapa(payload)
      navigate(`/pesquisa/mapa/${mapa.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  return (
    <div className="p-8 max-w-2xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Novo Mapa Comparativo de Preços</h1>
      <p className="text-sm text-gray-500 mb-2">Decreto Estadual 22.886/2024 — Art. 3º e Art. 8º</p>
      <div className="bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 mb-6 text-sm text-blue-800">
        <strong>Fluxo:</strong> Crie o mapa → adicione as fontes e cotações →
        o sistema analisará a variação dos preços e sugerirá o método de cálculo mais adequado.
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <Field label="Objeto da pesquisa *" error={errors.objeto}>
          <textarea rows={3} value={form.objeto}
            onChange={(e) => set('objeto', e.target.value)}
            placeholder="Descreva o objeto da contratação que subsidiará esta pesquisa de preços..."
            className={inp(errors.objeto)} />
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="Exercício fiscal *" error={errors.exercicio_fiscal}>
            <input type="number" min="2020" max="2050" value={form.exercicio_fiscal}
              onChange={(e) => set('exercicio_fiscal', e.target.value)}
              className={inp(errors.exercicio_fiscal)} />
          </Field>
          <Field label="DFD vinculado (opcional)">
            <select value={form.dfd} onChange={(e) => set('dfd', e.target.value)} className={inp()}>
              <option value="">Sem DFD vinculado</option>
              {dfds.map((d) => (
                <option key={d.id} value={d.id}>{d.numero_sei} — {d.descricao?.slice(0,40)}</option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="Observações iniciais (opcional)">
          <textarea rows={2} value={form.observacoes}
            onChange={(e) => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Criando...' : 'Criar mapa'}
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
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
