import { useState, useEffect, useMemo } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useDFDStore from '../stores/dfdStore'
import usePlanejamentoStore from '../stores/planejamentoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'

const MODALIDADES = [
  { value: 'licitacao',           label: 'Licitação' },
  { value: 'dispensa_valor',      label: 'Dispensa por Valor (Art. 75, II)' },
  { value: 'dispensa_emergencia', label: 'Dispensa por Emergência (Art. 75, VIII)' },
  { value: 'inexigibilidade',     label: 'Inexigibilidade (Art. 74)' },
  { value: 'arp_saque',           label: 'Saque de ATA de Registro de Preços' },
]

const AREAS = [
  { value: 'TI',        label: 'Tecnologia da Informação' },
  { value: 'Formação',  label: 'Formação' },
  { value: 'Ops',       label: 'Operações' },
  { value: 'Rede',      label: 'Rede' },
  { value: 'Frota',     label: 'Frota' },
  { value: 'Derivados', label: 'Derivados' },
]

const PRIORIDADE_CLS = {
  Alta:  'bg-red-100 text-red-700',
  Média: 'bg-yellow-100 text-yellow-700',
  Baixa: 'bg-gray-100 text-gray-600',
}

function novoItem() {
  return { objeto: '', unidade_medida: '', quantidade: '', valor_unitario_estimado: '' }
}

function calcularTotal(itens) {
  return itens.reduce((acc, i) => {
    return acc + (parseFloat(i.quantidade) || 0) * (parseFloat(i.valor_unitario_estimado) || 0)
  }, 0)
}

export default function DFDCreate() {
  const navigate   = useNavigate()
  const location   = useLocation()
  const { createDFD } = useDFDStore()
  const { updateNecessidade } = usePlanejamentoStore()
  const orgId = useAuthStore((s) => s.orgId)

  // necessidade passada via navigate state (vindo da tela de Necessidades)
  const necessidadePreSelecionada = location.state?.necessidade ?? null

  // --- necessidades disponíveis ---
  const [disponíveis, setDisponíveis] = useState([])
  const [loadingNec, setLoadingNec]   = useState(true)
  const [selecionada, setSelecionada] = useState(necessidadePreSelecionada)
  const [busca, setBusca]             = useState('')

  useEffect(() => {
    api.get('/planejamento/necessidade/', { params: { status: 'Aprovada', sem_dfd: true, page_size: 200 } })
      .then(({ data }) => {
        const lista = data.results ?? data
        setDisponíveis(lista)
        // Se veio pré-selecionada mas não está na lista (já tem DFD), mantém mesmo assim
        if (necessidadePreSelecionada && !lista.find(n => n.id === necessidadePreSelecionada.id)) {
          setDisponíveis(prev => [necessidadePreSelecionada, ...prev])
        }
      })
      .catch(() => setDisponíveis([]))
      .finally(() => setLoadingNec(false))
  }, [])

  // Preencher formulário quando necessidade é selecionada
  useEffect(() => {
    if (necReal) {
      setForm(prev => ({
        ...prev,
        descricao:         necReal.descricao,
        area_aplicacao:    necReal.area_aplicacao ?? [],
        prazo_necessidade: necReal.prazo_desejado ?? prev.prazo_necessidade,
      }))
      setItens([novoItem()])
    }
  }, [necReal?.id])

  // --- formulário ---
  const [form, setFormState] = useState({
    numero_sei:                    '',
    descricao:                     selecionada?.descricao ?? '',
    modalidade_aquisicao:          'licitacao',
    area_aplicacao:                selecionada?.area_aplicacao ?? [],
    prazo_necessidade:             selecionada?.prazo_desejado ?? '',
    observacoes:                   '',
    local_entrega:                 '',
    justificativa_sem_planejamento: '',
  })
  const [itens,  setItens]   = useState([novoItem()])
  const [saving, setSaving]  = useState(false)
  const [errors, setErrors]  = useState({})

  // Unidades licitante / contratante
  const [unidLicitante,   setUnidLicitante]   = useState('')
  const [unidContratante, setUnidContratante] = useState('')
  const [unidsLicitante,  setUnidsLicitante]  = useState([])
  const [unidsContratante,setUnidsContratante]= useState([])

  useEffect(() => {
    api.get('/core/unidades/', { params: { tipo: 'licitante' } })
      .then(({ data }) => setUnidsLicitante(data.results ?? data))
      .catch(() => {})
    api.get('/core/unidades/', { params: { tipo: 'contratante' } })
      .then(({ data }) => setUnidsContratante(data.results ?? data))
      .catch(() => {})
  }, [])

  const set = (field, value) => {
    setFormState(prev => ({ ...prev, [field]: value }))
    setErrors(prev => ({ ...prev, [field]: undefined }))
  }

  const toggleArea = (area) => {
    setFormState(prev => {
      const next = prev.area_aplicacao.includes(area)
        ? prev.area_aplicacao.filter(a => a !== area)
        : [...prev.area_aplicacao, area]
      return { ...prev, area_aplicacao: next }
    })
    setErrors(prev => ({ ...prev, area_aplicacao: undefined }))
  }

  const setItem = (idx, field, value) =>
    setItens(prev => { const n = [...prev]; n[idx] = { ...n[idx], [field]: value }; return n })

  // --- extrapolação ---
  const totalItens = calcularTotal(itens)

  const necReal = selecionada && selecionada !== 'sem' ? selecionada : null

  const extrapolacao = useMemo(() => {
    if (!necReal) return { valor: false, area: false, extras: [] }
    const extraValue = necReal.valor_estimado && totalItens > necReal.valor_estimado * 1.10
    const areasPlano = new Set(necReal.area_aplicacao ?? [])
    const extrasArea = form.area_aplicacao.filter(a => !areasPlano.has(a))
    return { valor: !!extraValue, area: extrasArea.length > 0, extras: extrasArea }
  }, [necReal, totalItens, form.area_aplicacao])

  // Justificativa: obrigatória quando não há necessidade planejada selecionada ou quando extrapola
  const precisaJustificativa = !necReal || extrapolacao.valor || extrapolacao.area

  // --- validação ---
  const validate = () => {
    const errs = {}
    if (!form.numero_sei.trim())    errs.numero_sei = 'Campo obrigatório'
    if (!form.descricao.trim())     errs.descricao  = 'Campo obrigatório'
    if (form.area_aplicacao.length === 0) errs.area_aplicacao = 'Selecione ao menos uma área'
    if (!form.prazo_necessidade)    errs.prazo_necessidade = 'Campo obrigatório'
    if (precisaJustificativa && !form.justificativa_sem_planejamento.trim())
      errs.justificativa_sem_planejamento = 'Justificativa obrigatória'

    const itensValidos = itens.filter(
      i => i.objeto.trim() && i.unidade_medida.trim() &&
           parseFloat(i.quantidade) > 0 && parseFloat(i.valor_unitario_estimado) > 0
    )
    if (itensValidos.length === 0)
      errs.itens = 'Adicione ao menos um item com objeto, unidade, quantidade e valor'

    return { errs, itensValidos }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const { errs, itensValidos } = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const dfd = await createDFD({
        numero_sei:                    form.numero_sei,
        descricao:                     form.descricao,
        modalidade_aquisicao:          form.modalidade_aquisicao,
        area_aplicacao:                form.area_aplicacao,
        prazo_necessidade:             form.prazo_necessidade,
        observacoes:                   form.observacoes,
        local_entrega:                 form.local_entrega,
        valor_estimado:                totalItens || 0,
        justificativa_sem_planejamento: precisaJustificativa
          ? form.justificativa_sem_planejamento
          : null,
        ...(unidLicitante   && { unidade_licitante:   parseInt(unidLicitante)   }),
        ...(unidContratante && { unidade_contratante: parseInt(unidContratante) }),
      })

      // Salva itens
      await Promise.all(
        itensValidos.map(item =>
          api.post(`/demanda/dfd/${dfd.id}/itens/`, {
            objeto:                  item.objeto,
            unidade_medida:          item.unidade_medida,
            quantidade:              parseFloat(item.quantidade),
            valor_unitario_estimado: parseFloat(item.valor_unitario_estimado),
            observacao:              item.observacao || '',
          })
        )
      )

      // Vincula DFD à necessidade selecionada
      if (necReal?.id) {
        await updateNecessidade(necReal.id, { dfd: dfd.id, status: 'DFD Criado' })
      }

      navigate(`/demanda/dfd/${dfd.id}`)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data))
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const necFiltradas = disponíveis.filter(n =>
    !busca || n.titulo.toLowerCase().includes(busca.toLowerCase()) ||
    (n.departamento_solicitante ?? '').toLowerCase().includes(busca.toLowerCase())
  )

  return (
    <div className="p-8 max-w-3xl">
      <button onClick={() => navigate(-1)}
        className="text-sm text-gray-400 hover:text-gray-600 mb-4 inline-flex items-center gap-1">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Novo DFD</h1>

      {/* ── PASSO 1: Selecionar necessidade planejada ── */}
      <section className="mb-6 border border-gray-200 rounded-xl p-4 bg-white">
        <p className="text-sm font-semibold text-gray-700 mb-1">
          Necessidade de planejamento
        </p>
        <p className="text-xs text-gray-400 mb-3">
          Selecione a necessidade aprovada que origina este DFD. Se não houver, uma justificativa será exigida.
        </p>

        {loadingNec ? (
          <p className="text-xs text-gray-400">Carregando necessidades...</p>
        ) : disponíveis.length === 0 ? (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700">
            Nenhuma necessidade aprovada disponível. O DFD será criado fora do planejamento — justificativa obrigatória.
          </div>
        ) : (
          <>
            {necReal ? (
              <div className="flex items-start justify-between bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-green-800">{necReal.titulo}</p>
                  <p className="text-xs text-green-600 mt-0.5">
                    {necReal.departamento_solicitante} · Exercício {necReal.exercicio_fiscal} ·{' '}
                    {Number(necReal.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                </div>
                <button type="button" onClick={() => setSelecionada(null)}
                  className="text-xs text-green-600 hover:text-red-500 ml-3 shrink-0">
                  Alterar
                </button>
              </div>
            ) : selecionada === 'sem' ? (
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700 flex items-center justify-between">
                <span>DFD fora do planejamento — justificativa obrigatória.</span>
                <button type="button" onClick={() => setSelecionada(null)} className="text-amber-600 hover:underline ml-2">Cancelar</button>
              </div>
            ) : (
              <>
                <input type="text" value={busca} onChange={e => setBusca(e.target.value)}
                  placeholder="Buscar por título ou departamento..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <div className="max-h-52 overflow-y-auto space-y-1">
                  {necFiltradas.length === 0 ? (
                    <p className="text-xs text-gray-400 px-1">Nenhum resultado.</p>
                  ) : necFiltradas.map(n => (
                    <button key={n.id} type="button" onClick={() => setSelecionada(n)}
                      className="w-full text-left px-3 py-2 rounded-lg border border-gray-100 hover:border-blue-300 hover:bg-blue-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-800">{n.titulo}</p>
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${PRIORIDADE_CLS[n.prioridade] ?? ''}`}>
                          {n.prioridade}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {n.departamento_solicitante} · Ex. {n.exercicio_fiscal} ·{' '}
                        {Number(n.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </p>
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-2">
                  Ou{' '}
                  <button type="button" onClick={() => setSelecionada('sem')}
                    className="text-amber-600 hover:underline">
                    prosseguir sem necessidade planejada
                  </button>
                  {' '}(justificativa obrigatória).
                </p>
              </>
            )}
          </>
        )}
      </section>

      {/* Formulário aparece assim que o carregamento termina */}
      {!loadingNec && (
        <form onSubmit={handleSubmit} className="space-y-5">

          {/* Avisos de extrapolação */}
          {necReal && (extrapolacao.valor || extrapolacao.area) && (
            <div className="bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 text-sm text-amber-800">
              <p className="font-semibold mb-1">Atenção: DFD extrapola o planejamento</p>
              {extrapolacao.valor && (
                <p>• Valor estimado dos itens ({totalItens.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}) supera em mais de 10% o valor planejado ({Number(necReal.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}).</p>
              )}
              {extrapolacao.area && (
                <p>• Áreas não previstas no planejamento: <strong>{extrapolacao.extras.join(', ')}</strong>.</p>
              )}
              <p className="mt-1 text-amber-700">Preencha a justificativa abaixo.</p>
            </div>
          )}

          <Field label="Modalidade de aquisição">
            <select value={form.modalidade_aquisicao}
              onChange={e => set('modalidade_aquisicao', e.target.value)}
              className={inputCls()}>
              {MODALIDADES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
            {['dispensa_valor', 'dispensa_emergencia', 'arp_saque'].includes(form.modalidade_aquisicao) && (
              <p className="text-xs text-amber-600 mt-1">
                Esta modalidade pode dispensar a elaboração do ETP. A dispensa será avaliada após aprovação do DFD.
              </p>
            )}
          </Field>

          <Field label="Número SEI" error={errors.numero_sei}>
            <input type="text" value={form.numero_sei}
              onChange={e => set('numero_sei', e.target.value)}
              placeholder="Ex: 00060.000123/2025-00"
              className={inputCls(errors.numero_sei)} />
          </Field>

          <Field label="Descrição" error={errors.descricao}>
            <textarea rows={3} value={form.descricao}
              onChange={e => set('descricao', e.target.value)}
              className={inputCls(errors.descricao)} />
          </Field>

          <Field label="Áreas de aplicação" error={errors.area_aplicacao}>
            <div className="flex flex-wrap gap-2">
              {AREAS.map(({ value, label }) => {
                const selected = form.area_aplicacao.includes(value)
                const foraDoPlan = necReal &&
                  !(necReal.area_aplicacao ?? []).includes(value)
                return (
                  <button key={value} type="button" onClick={() => toggleArea(value)}
                    className={`px-3 py-1.5 rounded-lg text-sm border font-medium transition-colors ${
                      selected
                        ? foraDoPlan
                          ? 'bg-amber-500 border-amber-500 text-white'
                          : 'bg-blue-600 border-blue-600 text-white'
                        : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                    }`}>
                    {label}{selected && foraDoPlan ? ' ⚠' : ''}
                  </button>
                )
              })}
            </div>
            {necReal && (
              <p className="text-xs text-gray-400 mt-1">
                Áreas planejadas: {(necReal.area_aplicacao ?? []).join(', ') || '—'}
              </p>
            )}
          </Field>

          <Field label="Prazo de necessidade" error={errors.prazo_necessidade}>
            <input type="date" value={form.prazo_necessidade}
              onChange={e => set('prazo_necessidade', e.target.value)}
              className={inputCls(errors.prazo_necessidade)} />
          </Field>

          <Field label="Observações (opcional)">
            <textarea rows={2} value={form.observacoes}
              onChange={e => set('observacoes', e.target.value)}
              className={inputCls()} />
          </Field>

          <Field label="Local de entrega (opcional)">
            <textarea rows={2} value={form.local_entrega}
              onChange={e => set('local_entrega', e.target.value)}
              placeholder="Ex: Almoxarifado Central, Rua X n° 123, Sala 10..."
              className={inputCls()} />
          </Field>

          {/* Justificativa — só quando necessário */}
          {precisaJustificativa && (
            <Field label={
              !selecionada || selecionada === 'sem'
                ? 'Justificativa (DFD fora do planejamento)'
                : 'Justificativa (extrapolação do planejamento)'
            } error={errors.justificativa_sem_planejamento}>
              <textarea rows={3} value={form.justificativa_sem_planejamento}
                onChange={e => set('justificativa_sem_planejamento', e.target.value)}
                placeholder={
                  !selecionada || selecionada === 'sem'
                    ? 'Explique por que esta demanda não está prevista no planejamento...'
                    : 'Explique por que o DFD excede o escopo ou valor do planejamento...'
                }
                className={inputCls(errors.justificativa_sem_planejamento)} />
            </Field>
          )}

          {/* Itens */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">
                Itens da demanda
                {necReal && (
                  <span className="ml-2 text-xs text-gray-400 font-normal">
                    planejado: {Number(necReal.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </span>
                )}
              </p>
              <button type="button" onClick={() => setItens(p => [...p, novoItem()])}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                + Adicionar item
              </button>
            </div>
            {errors.itens && <p className="text-xs text-red-600 mb-2">{errors.itens}</p>}

            <div className="space-y-3">
              {itens.map((item, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-3 bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-gray-400 uppercase">Item {idx + 1}</span>
                    {itens.length > 1 && (
                      <button type="button" onClick={() => setItens(p => p.filter((_, i) => i !== idx))}
                        className="text-xs text-red-400 hover:text-red-600">Remover</button>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                      <label className="block text-xs text-gray-500 mb-0.5">Objeto / Descrição</label>
                      <input type="text" value={item.objeto}
                        onChange={e => setItem(idx, 'objeto', e.target.value)}
                        placeholder="Ex: Notebook Dell Latitude"
                        className={inputCls()} />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Unidade</label>
                      <input type="text" value={item.unidade_medida}
                        onChange={e => setItem(idx, 'unidade_medida', e.target.value)}
                        placeholder="UN, M², HR..."
                        className={inputCls()} />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Quantidade</label>
                      <input type="number" min="0" step="0.0001" value={item.quantidade}
                        onChange={e => setItem(idx, 'quantidade', e.target.value)}
                        className={inputCls()} />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 mb-0.5">Valor unitário (R$)</label>
                      <input type="number" min="0" step="0.01" value={item.valor_unitario_estimado}
                        onChange={e => setItem(idx, 'valor_unitario_estimado', e.target.value)}
                        className={inputCls()} />
                    </div>
                    <div className="flex items-end">
                      <p className="text-sm text-gray-600">
                        Total:{' '}
                        <span className="font-semibold text-gray-800">
                          {((parseFloat(item.quantidade) || 0) * (parseFloat(item.valor_unitario_estimado) || 0))
                            .toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </span>
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {totalItens > 0 && (
              <div className="mt-3 flex items-center justify-end gap-3">
                {necReal && (
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    extrapolacao.valor
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {extrapolacao.valor ? '⚠ Acima do planejado' : '✓ Dentro do planejado'}
                  </span>
                )}
                <span className="text-sm text-gray-500">Total estimado:</span>
                <span className="text-base font-bold text-gray-800">
                  {totalItens.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
          </div>

          {/* Unidades responsáveis */}
          <div className="border border-gray-200 rounded-xl p-4 bg-gray-50">
            <p className="text-sm font-medium text-gray-700 mb-3">Unidades responsáveis</p>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Unidade licitante (opcional)">
                <select value={unidLicitante} onChange={e => setUnidLicitante(e.target.value)}
                  className={inputCls()}>
                  <option value="">— selecione —</option>
                  {unidsLicitante.map(u => (
                    <option key={u.id} value={u.id}>{u.orgao_sigla}/{u.sigla} — {u.nome}</option>
                  ))}
                </select>
              </Field>
              <Field label="Unidade contratante (opcional)">
                <select value={unidContratante} onChange={e => setUnidContratante(e.target.value)}
                  className={inputCls()}>
                  <option value="">— selecione —</option>
                  {unidsContratante.map(u => (
                    <option key={u.id} value={u.id}>{u.orgao_sigla}/{u.sigla} — {u.nome}</option>
                  ))}
                </select>
              </Field>
            </div>
            <p className="text-xs text-gray-400 mt-2">
              Podem ser definidas ou alteradas depois da criação.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors">
              {saving ? 'Salvando...' : 'Criar DFD'}
            </button>
            <button type="button" onClick={() => navigate(-1)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm transition-colors">
              Cancelar
            </button>
          </div>
        </form>
      )}
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

function inputCls(error) {
  return `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
}
