import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useOrcamentoStore from '../stores/orcamentoStore'
import FormErrors from '../components/FormErrors'
import CampoMoeda from '../components/CampoMoeda'

const ANO_ATUAL = new Date().getFullYear()

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Nova Dotação Orçamentária',
  descricao: 'Registra a disponibilidade de recurso orçamentário (ação + natureza/elemento + fonte) que depois será indicada para necessidades e itens de DFD específicos.',
  acoes: [
    { label: 'Natureza de despesa', texto: 'Caminho recomendado: selecione a natureza — o elemento de despesa é derivado automaticamente dela. O guia de classificação SIMPAS ajuda a escolher a natureza certa (Material de Consumo, Material Permanente, Serviço).' },
    { label: 'Elemento de despesa',  texto: 'Alternativa avulsa, só aparece se nenhuma natureza for selecionada — use apenas quando a natureza específica ainda não estiver cadastrada.' },
    { label: 'Fonte de recurso',     texto: 'Ao selecionar, carrega as subfontes específicas dessa fonte (se houver) para detalhamento opcional.' },
    { label: 'Criar dotação',        texto: 'Salva como "Proposta" (ou o status escolhido). O valor dotado é o teto que poderá ser indicado para necessidades depois, em Orçamento → Indicações.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function OrcamentoCreate() {
  const navigate = useNavigate()
  const { createDotacao, fetchAcoes, fetchElementos, fetchNaturezas, fetchFontes, fetchSubfontes, acoes, elementos, naturezas, fontes, subfontes } =
    useOrcamentoStore()

  const [form, setForm] = useState({
    exercicio_fiscal: ANO_ATUAL,
    acao: '',
    natureza_despesa: '',   // campo primário — elemento é derivado da natureza
    elemento_despesa: '',   // preenchido automaticamente quando natureza é selecionada
    fonte_recurso: '',
    subfonte_recurso: '',   // opcional — detalhamento da fonte selecionada
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
    fetchNaturezas()   // carrega todas as naturezas (elemento é derivado delas)
    fetchFontes()
  }, [])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const validate = () => {
    const e = {}
    if (!form.exercicio_fiscal)                              e.exercicio_fiscal = 'Campo obrigatório'
    if (!form.acao)                                          e.acao = 'Selecione uma ação'
    if (!form.natureza_despesa && !form.elemento_despesa)    e.natureza_despesa = 'Selecione uma natureza ou um elemento'
    if (!form.fonte_recurso)                                 e.fonte_recurso = 'Selecione uma fonte'
    if (!form.valor_dotado || isNaN(Number(form.valor_dotado))) e.valor_dotado = 'Valor inválido'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      // Natureza contém o elemento — backend auto-preenche elemento a partir da natureza
      const payload = {
        exercicio_fiscal: Number(form.exercicio_fiscal),
        acao:             Number(form.acao),
        fonte_recurso:    Number(form.fonte_recurso),
        valor_dotado:     Number(form.valor_dotado),
        status:           form.status,
        eixo:             form.eixo,
        objetivo_estrategico: form.objetivo_estrategico,
        observacoes:      form.observacoes,
      }
      if (form.natureza_despesa) {
        payload.natureza_despesa = Number(form.natureza_despesa)
        // elemento_despesa será auto-preenchido pelo backend via natureza
      } else {
        payload.elemento_despesa = Number(form.elemento_despesa)
      }
      if (form.subfonte_recurso) payload.subfonte_recurso = Number(form.subfonte_recurso)
      const dotacao = await createDotacao(payload)
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
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Nova Dotação Orçamentária</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

        <Field label="Natureza de despesa" error={errors.natureza_despesa}>
          <select value={form.natureza_despesa}
            onChange={(e) => {
              set('natureza_despesa', e.target.value)
              set('elemento_despesa', '') // limpa seleção avulsa
            }}
            className={inp(errors.natureza_despesa)}>
            <option value="">Selecione uma natureza...</option>
            {naturezas.map((n) => (
              <option key={n.id} value={n.id}>
                {n.formato} — {n.descricao} (El. {String(n.elemento_codigo).padStart(2,'0')})
              </option>
            ))}
          </select>
          {form.natureza_despesa && (() => {
            const nat = naturezas.find(n => String(n.id) === String(form.natureza_despesa))
            return nat
              ? <p className="text-xs text-blue-600 mt-1">Elemento derivado: {String(nat.elemento_codigo).padStart(2,'0')} — {nat.elemento_descricao}</p>
              : null
          })()}
          {/* Guia rápido de correspondência classificação SIMPAS → natureza */}
          {!form.natureza_despesa && (
            <div className="mt-2 bg-blue-50 border border-blue-100 rounded-lg p-3 text-xs text-blue-700 space-y-1">
              <p className="font-semibold text-blue-800">Guia — Classificação SIMPAS × Natureza de Despesa:</p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-blue-600">
                <span>Material de Consumo</span><span className="font-mono">→ 3.3.90.30 (El. 30)</span>
                <span>Material Permanente</span><span className="font-mono">→ 4.4.90.52 (El. 52)</span>
                <span>Serviço</span>             <span className="font-mono">→ 3.3.90.39 (El. 39)</span>
              </div>
            </div>
          )}
        </Field>

        {/* Elemento avulso — só aparece se não houver natureza selecionada */}
        {!form.natureza_despesa && (
          <Field label="Elemento de despesa *" error={errors.elemento_despesa}>
            <select value={form.elemento_despesa}
              onChange={(e) => set('elemento_despesa', e.target.value)}
              className={inp(errors.elemento_despesa)}>
              <option value="">Selecione um elemento...</option>
              {elementos.map((el) => (
                <option key={el.id} value={el.id}>
                  {String(el.codigo).padStart(2,'0')} — {el.descricao}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">Ou selecione uma natureza acima (recomendado — o elemento será derivado automaticamente)</p>
          </Field>
        )}

        <Field label="Fonte de recurso" error={errors.fonte_recurso}>
          <select value={form.fonte_recurso}
            onChange={(e) => {
              set('fonte_recurso', e.target.value)
              set('subfonte_recurso', '') // limpa subfonte ao trocar de fonte
              if (e.target.value) fetchSubfontes(e.target.value)
            }}
            className={inp(errors.fonte_recurso)}>
            <option value="">Selecione uma fonte...</option>
            {fontes.map((f) => (
              <option key={f.id} value={f.id}>
                {f.codigo} — {f.nome} ({f.tipo})
              </option>
            ))}
          </select>
        </Field>

        {form.fonte_recurso && subfontes.length > 0 && (
          <Field label="Subfonte de recurso (opcional)" error={errors.subfonte_recurso}>
            <select value={form.subfonte_recurso}
              onChange={(e) => set('subfonte_recurso', e.target.value)}
              className={inp(errors.subfonte_recurso)}>
              <option value="">Sem subfonte específica</option>
              {subfontes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.codigo} — {s.nome}
                </option>
              ))}
            </select>
          </Field>
        )}

        <Field label="Valor dotado (R$)" error={errors.valor_dotado}>
          <CampoMoeda value={form.valor_dotado}
            onChange={(v) => set('valor_dotado', v)}
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
