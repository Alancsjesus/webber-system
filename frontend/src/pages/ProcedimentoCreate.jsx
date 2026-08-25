import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useLicitacaoStore from '../stores/licitacaoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import CampoSei from '../components/CampoSei'
import CampoMoeda from '../components/CampoMoeda'

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

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Novo Procedimento',
  descricao: 'Formaliza a modalidade de contratação (licitação, dispensa ou inexigibilidade) que efetivamente será usada — decisão distinta da classificação preliminar feita no DFD.',
  acoes: [
    { label: 'Unidade gestora',   texto: 'A sigla da unidade compõe o número automático do procedimento (ex: PE-CLIC-001/2026, INEX-DG-003/2026) — mostrado em pré-visualização assim que unidade e modalidade forem escolhidas.' },
    { label: 'DFD / TR de origem', texto: 'Vincula o procedimento ao DFD aprovado e, opcionalmente, ao TR correspondente — o TR só aparece se houver algum TR aprovado ligado ao DFD selecionado. Ao selecionar o TR, o Valor estimado é preenchido automaticamente com o valor final do TR (ainda editável). Exige que o DFD já tenha uma Indicação Orçamentária aprovada (DOD) — exceto quando o TR é de Sistema de Registro de Preços, já que a Ata em si não compromete orçamento.' },
    { label: 'Data de abertura',  texto: 'Prazo mínimo após a publicação varia por modalidade: 8 dias úteis para Pregão Eletrônico, 25 dias úteis para os demais tipos de licitação.' },
    { label: 'Fundamento da Dispensa/Inexigibilidade', texto: 'Só aparece para essas modalidades — exige selecionar o inciso legal (Art. 75 ou Art. 74) e justificativa obrigatória.' },
    { label: 'Teto de dispensa por família', texto: 'Para dispensa por valor, o sistema soma todas as dispensas já aprovadas/homologadas/contratadas no mesmo exercício que compartilham alguma família SIMPAS com este procedimento. Se ultrapassar o teto legal (R$ 57.277,08 para bens/serviços, R$ 114.554,16 para obras — Art. 75), bloqueia a criação e exige confirmação explícita antes de prosseguir (evita fracionamento de despesa).' },
    { label: 'Criar procedimento', texto: 'Salva o procedimento com número sequencial definitivo já atribuído.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Arts. 28 (modalidades), 74 (inexigibilidade) e 75 (dispensa).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ProcedimentoCreate() {
  const navigate = useNavigate()
  const { createProcedimento } = useLicitacaoStore()
  const seiBaseUrl = useAuthStore((s) => s.seiBaseUrl)
  const [dfds, setDfds]           = useState([])
  const [trs, setTrs]             = useState([])
  const [unidades, setUnidades]   = useState([])
  const [saving, setSaving]       = useState(false)
  const [errors, setErrors]       = useState({})
  const [alertaTeto, setAlertaTeto] = useState(null)

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

  // Preencher valor estimado automaticamente com o valor final do TR selecionado
  useEffect(() => {
    if (!form.tr) return
    const tr = trs.find(t => String(t.id) === String(form.tr))
    if (tr && tr.estimativa_valor != null) set('valor_estimado', String(tr.estimativa_valor))
  }, [form.tr])

  // Preencher objeto automaticamente ao selecionar DFD
  useEffect(() => {
    if (!form.dfd) return
    const dfd = dfds.find(d => String(d.id) === String(form.dfd))
    if (dfd && !form.objeto) set('objeto', dfd.descricao?.slice(0, 300) || '')
  }, [form.dfd])

  const ehDispensa    = ['dispensa_eletronica', 'dispensa_tradicional'].includes(form.modalidade)
  const ehInexig      = form.modalidade === 'inexigibilidade'
  const ehLicitacao   = ['pregao_eletronico', 'concorrencia'].includes(form.modalidade)

  const submeter = async (confirmarTetoExcedido = false) => {
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
      if (confirmarTetoExcedido) payload.confirmar_teto_excedido = true

      const proc = await createProcedimento(payload)
      navigate(`/licitacao/${proc.id}`)
    } catch (err) {
      const d = err.response?.data || {}
      if (d.codigo === 'teto_dispensa_excedido') {
        setAlertaTeto(d.valor_estimado)
      } else {
        const mapped = {}
        for (const [k, v] of Object.entries(d))
          mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
        setErrors(mapped)
      }
    } finally {
      setSaving(false)
    }
  }

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
    setAlertaTeto(null)
    await submeter(false)
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
          <Field label="Valor estimado (R$)" error={errors.valor_estimado}
            hint={form.tr ? 'Pré-preenchido com o valor estimado do TR selecionado — pode ser ajustado.' : ''}>
            <CampoMoeda value={form.valor_estimado}
              onChange={v => set('valor_estimado', v)} className={inp(errors.valor_estimado)} />
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

        {alertaTeto && (
          <div className="bg-red-50 border border-red-300 rounded-xl px-4 py-3 text-sm text-red-800">
            <p className="font-semibold mb-1">⚠ Teto de dispensa excedido</p>
            <p className="mb-3">{alertaTeto}</p>
            <p className="mb-3 text-red-700">
              Confirme apenas se este caso já foi analisado e o fracionamento de despesa não se aplica.
            </p>
            <div className="flex gap-2">
              <button type="button" disabled={saving}
                onClick={() => submeter(true)}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                Confirmar e prosseguir mesmo assim
              </button>
              <button type="button" onClick={() => setAlertaTeto(null)}
                className="border border-red-300 text-red-600 hover:bg-red-100 text-xs font-medium px-3 py-1.5 rounded-lg">
                Cancelar
              </button>
            </div>
          </div>
        )}

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
