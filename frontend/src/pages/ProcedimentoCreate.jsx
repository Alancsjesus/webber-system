import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useLicitacaoStore from '../stores/licitacaoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import CampoSei from '../components/CampoSei'

const ANO = new Date().getFullYear()

const FUNDAMENTOS_DISPENSA = [
  { value: 'art75_i',   label: 'Art. 75, I — Bens/serviços (até R$ 57.277,08)' },
  { value: 'art75_ii',  label: 'Art. 75, II — Obras/engenharia (até R$ 114.554,16)' },
  { value: 'art75_iii', label: 'Art. 75, III — Licitação deserta' },
  { value: 'art75_iv',  label: 'Art. 75, IV — Licitação fracassada' },
  { value: 'art75_v',   label: 'Art. 75, V — Emergência/calamidade' },
  { value: 'outro',     label: 'Outro fundamento' },
]

const FUNDAMENTOS_INEXIG = [
  { value: 'art74_i',   label: 'Art. 74, I — Fornecedor exclusivo' },
  { value: 'art74_ii',  label: 'Art. 74, II — Serviço técnico especializado singular' },
  { value: 'art74_iii', label: 'Art. 74, III — Profissional do setor artístico' },
  { value: 'art74_iv',  label: 'Art. 74, IV — Credenciamento' },
  { value: 'outro',     label: 'Outro fundamento' },
]

const inp = (err) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400' : 'border-gray-300'}`

function Field({ label, error, children, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

export default function ProcedimentoCreate() {
  const navigate = useNavigate()
  const { createProcedimento } = useLicitacaoStore()
  const seiBaseUrl = useAuthStore((s) => s.seiBaseUrl)
  const [dfds, setDfds]           = useState([])
  const [trs, setTrs]             = useState([])
  const [unidades, setUnidades]   = useState([])
  const [saving, setSaving]       = useState(false)
  const [errors, setErrors]       = useState({})

  const [form, setForm] = useState({
    exercicio:                  ANO,
    modalidade:                 'pregao_eletronico',
    unidade_gestora:            '',
    dfd:                        '',
    tr:                         '',
    objeto:                     '',
    valor_estimado:             '',
    numero_sei:                 '',
    data_publicacao:            '',
    data_abertura:              '',
    fundamento_dispensa:        '',
    fundamento_inexigibilidade: '',
    justificativa:              '',
    observacoes:                '',
  })

  const set = (k, v) => {
    setForm(p => ({ ...p, [k]: v }))
    setErrors(p => ({ ...p, [k]: undefined }))
  }

  useEffect(() => {
    api.get('/demanda/dfd/', { params: { status: 'Aprovada', page_size: 100 } })
       .then(({ data }) => setDfds(data.results ?? data))
       .catch(() => {})
    api.get('/core/unidades/', { params: { page_size: 200 } })
       .then(({ data }) => setUnidades(data.results ?? data))
       .catch(() => {})
  }, [])

  useEffect(() => {
    if (!form.dfd) { setTrs([]); set('tr', ''); return }
    api.get('/tr/tr/', { params: { page_size: 100 } })
       .then(({ data }) => {
         const lista = (data.results ?? data).filter(t => String(t.etp_dfd_id) === String(form.dfd))
         setTrs(lista)
       })
       .catch(() => {})
  }, [form.dfd])

  // Preencher objeto automaticamente ao selecionar DFD
  useEffect(() => {
    if (!form.dfd) return
    const dfd = dfds.find(d => String(d.id) === String(form.dfd))
    if (dfd && !form.objeto) set('objeto', dfd.descricao?.slice(0, 300) || '')
  }, [form.dfd])

  const ehDispensa    = ['dispensa_eletronica', 'dispensa_tradicional'].includes(form.modalidade)
  const ehInexig      = form.modalidade === 'inexigibilidade'
  const ehLicitacao   = ['pregao_eletronico', 'concorrencia'].includes(form.modalidade)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.modalidade)         errs.modalidade = 'Selecione a modalidade'
    if (!form.objeto.trim())      errs.objeto = 'Objeto é obrigatório'
    if (!form.exercicio)          errs.exercicio = 'Informe o exercício'
    if (!form.unidade_gestora)    errs.unidade_gestora = 'Informe a unidade gestora (compõe o número do procedimento)'
    if (ehDispensa && !form.fundamento_dispensa) errs.fundamento_dispensa = 'Selecione o fundamento legal'
    if (ehInexig && !form.fundamento_inexigibilidade) errs.fundamento_inexigibilidade = 'Selecione o fundamento legal'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const payload = {
        exercicio:       Number(form.exercicio),
        modalidade:      form.modalidade,
        unidade_gestora: Number(form.unidade_gestora),
        objeto:          form.objeto,
        numero_sei:      form.numero_sei || '',
        observacoes:     form.observacoes || '',
      }
      if (form.dfd)   payload.dfd = Number(form.dfd)
      if (form.tr)    payload.tr  = Number(form.tr)
      if (form.valor_estimado) payload.valor_estimado = Number(form.valor_estimado)
      if (form.data_publicacao) payload.data_publicacao = form.data_publicacao
      if (form.data_abertura)   payload.data_abertura   = form.data_abertura
      if (ehDispensa)  payload.fundamento_dispensa       = form.fundamento_dispensa
      if (ehInexig)    payload.fundamento_inexigibilidade = form.fundamento_inexigibilidade
      if (form.justificativa) payload.justificativa = form.justificativa

      const proc = await createProcedimento(payload)
      navigate(`/licitacao/${proc.id}`)
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
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-1">Novo Procedimento</h1>
      <p className="text-sm text-gray-500 mb-6">
        Licitação, Dispensa ou Inexigibilidade — Lei 14.133/2021
      </p>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Modalidade + Exercício */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Modalidade *" error={errors.modalidade}>
            <select value={form.modalidade} onChange={e => set('modalidade', e.target.value)} className={inp(errors.modalidade)}>
              <optgroup label="Licitações">
                <option value="pregao_eletronico">Pregão Eletrônico</option>
                <option value="concorrencia">Concorrência</option>
              </optgroup>
              <optgroup label="Contratações Diretas">
                <option value="dispensa_eletronica">Dispensa Eletrônica (por Valor — Art. 75 I/II)</option>
                <option value="dispensa_tradicional">Dispensa Tradicional</option>
                <option value="inexigibilidade">Inexigibilidade</option>
              </optgroup>
            </select>
          </Field>
          <Field label="Exercício *" error={errors.exercicio}>
            <input type="number" min="2020" max="2099" value={form.exercicio}
              onChange={e => set('exercicio', e.target.value)} className={inp(errors.exercicio)} />
          </Field>
        </div>

        {/* Unidade gestora */}
        <Field label="Unidade gestora *" error={errors.unidade_gestora}
          hint="A sigla desta unidade compõe o número do procedimento (ex: INEX-DG-001/2026)">
          <select value={form.unidade_gestora} onChange={e => set('unidade_gestora', e.target.value)}
            className={inp(errors.unidade_gestora)}>
            <option value="">— Selecione a unidade —</option>
            {unidades.map(u => (
              <option key={u.id} value={u.id}>
                {u.sigla} — {u.nome} ({u.tipo})
              </option>
            ))}
          </select>
        </Field>

        {/* Pré-visualização do número */}
        {form.unidade_gestora && form.modalidade && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-sm text-blue-700">
            Número gerado automaticamente:&nbsp;
            <strong>
              {{ pregao_eletronico: 'PE', concorrencia: 'CC', dispensa_eletronica: 'DE', dispensa_tradicional: 'DT', inexigibilidade: 'INEX' }[form.modalidade]}
              -{unidades.find(u => String(u.id) === String(form.unidade_gestora))?.sigla ?? '???'}-
              NNN/{form.exercicio}
            </strong>
          </div>
        )}

        {/* DFD e TR */}
        <Field label="DFD de origem" error={errors.dfd}>
          <select value={form.dfd} onChange={e => set('dfd', e.target.value)} className={inp(errors.dfd)}>
            <option value="">— Selecione um DFD aprovado —</option>
            {dfds.map(d => (
              <option key={d.id} value={d.id}>{d.numero_sei} — {d.descricao?.slice(0, 60)}</option>
            ))}
          </select>
        </Field>

        {form.dfd && (
          <Field label="TR de origem" error={errors.tr}
            hint={trs.length === 0 ? 'Nenhum TR aprovado encontrado para este DFD' : ''}>
            <select value={form.tr} onChange={e => set('tr', e.target.value)} className={inp(errors.tr)}>
              <option value="">— Selecione (opcional) —</option>
              {trs.map(t => (
                <option key={t.id} value={t.id}>{t.numero_sei} [{t.status}]</option>
              ))}
            </select>
          </Field>
        )}

        {/* Objeto */}
        <Field label="Objeto do procedimento *" error={errors.objeto}>
          <textarea rows={3} value={form.objeto} onChange={e => set('objeto', e.target.value)}
            placeholder="Descreva o objeto da contratação..."
            className={inp(errors.objeto)} />
        </Field>

        {/* Valor e SEI */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Valor estimado (R$)" error={errors.valor_estimado}>
            <input type="number" min="0" step="0.01" value={form.valor_estimado}
              onChange={e => set('valor_estimado', e.target.value)} className={inp(errors.valor_estimado)}
              placeholder="0,00" />
          </Field>
          <Field label="Número do processo SEI" error={errors.numero_sei}>
            <CampoSei value={form.numero_sei}
              onChange={v => set('numero_sei', v)} className={inp(errors.numero_sei)}
              seiBaseUrl={seiBaseUrl}
              placeholder="099.8188.2025.0027815-30" />
          </Field>
        </div>

        {/* Datas (licitações) */}
        {ehLicitacao && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Data de publicação" error={errors.data_publicacao}>
              <input type="date" value={form.data_publicacao}
                onChange={e => set('data_publicacao', e.target.value)} className={inp(errors.data_publicacao)} />
            </Field>
            <Field label="Data de abertura" error={errors.data_abertura}
              hint={form.modalidade === 'pregao_eletronico' ? 'Mínimo 8 dias úteis após publicação' : 'Mínimo 25 dias úteis após publicação'}>
              <input type="date" value={form.data_abertura}
                onChange={e => set('data_abertura', e.target.value)} className={inp(errors.data_abertura)} />
            </Field>
          </div>
        )}

        {/* Fundamento legal — Dispensa */}
        {ehDispensa && (
          <div className="border border-amber-200 bg-amber-50 rounded-xl p-4 space-y-3">
            <p className="text-sm font-semibold text-amber-800">Fundamento da Dispensa</p>
            <Field label="Fundamento legal *" error={errors.fundamento_dispensa}>
              <select value={form.fundamento_dispensa}
                onChange={e => set('fundamento_dispensa', e.target.value)}
                className={inp(errors.fundamento_dispensa)}>
                <option value="">— Selecione —</option>
                {FUNDAMENTOS_DISPENSA.map(f => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Justificativa da contratação direta *" error={errors.justificativa}>
              <textarea rows={3} value={form.justificativa}
                onChange={e => set('justificativa', e.target.value)}
                placeholder="Justifique a dispensa nos termos do Art. 75 da Lei 14.133/2021..."
                className={inp(errors.justificativa)} />
            </Field>
          </div>
        )}

        {/* Fundamento legal — Inexigibilidade */}
        {ehInexig && (
          <div className="border border-purple-200 bg-purple-50 rounded-xl p-4 space-y-3">
            <p className="text-sm font-semibold text-purple-800">Fundamento da Inexigibilidade</p>
            <Field label="Fundamento legal *" error={errors.fundamento_inexigibilidade}>
              <select value={form.fundamento_inexigibilidade}
                onChange={e => set('fundamento_inexigibilidade', e.target.value)}
                className={inp(errors.fundamento_inexigibilidade)}>
                <option value="">— Selecione —</option>
                {FUNDAMENTOS_INEXIG.map(f => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Justificativa da inexigibilidade *" error={errors.justificativa}>
              <textarea rows={3} value={form.justificativa}
                onChange={e => set('justificativa', e.target.value)}
                placeholder="Demonstre a inviabilidade de competição nos termos do Art. 74 da Lei 14.133/2021..."
                className={inp(errors.justificativa)} />
            </Field>
          </div>
        )}

        <Field label="Observações">
          <textarea rows={2} value={form.observacoes}
            onChange={e => set('observacoes', e.target.value)}
            className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Criando...' : 'Criar procedimento'}
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
