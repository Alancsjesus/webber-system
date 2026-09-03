import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../services/api'
import CampoMoeda from '../components/CampoMoeda'

// ── Constantes ────────────────────────────────────────────────────────────────

const AREAS = [
  { value: 'TI',        label: 'Tecnologia da Informação' },
  { value: 'Formação',  label: 'Formação e Capacitação' },
  { value: 'Ops',       label: 'Operações' },
  { value: 'Rede',      label: 'Rede Física' },
  { value: 'Frota',     label: 'Frota' },
  { value: 'Derivados', label: 'Derivados' },
]

const MODALIDADES = [
  { value: 'licitacao',           label: 'Licitação' },
  { value: 'dispensa_valor',      label: 'Dispensa por Valor' },
  { value: 'dispensa_emergencia', label: 'Dispensa por Emergência' },
  { value: 'inexigibilidade',     label: 'Inexigibilidade' },
  { value: 'arp_saque',           label: 'Saque de ATA de Registro de Preços' },
]

const SUGESTAO_PARA_MODALIDADE = {
  pregao_eletronico: 'licitacao',
  dispensa_agrupada: 'dispensa_valor',
  dispensa_valor:    'dispensa_valor',
}

const SUGESTAO_LABELS = {
  pregao_eletronico: { label: 'Pregão Eletrônico recomendado', cls: 'bg-blue-100 text-blue-800' },
  dispensa_agrupada: { label: 'Dispensa Agrupada recomendada', cls: 'bg-amber-100 text-amber-800' },
  dispensa_valor:    { label: 'Dispensa por Valor',            cls: 'bg-green-100 text-green-800' },
}

const STATUS_DFD_CLS = {
  Rascunho:     'bg-gray-100 text-gray-600',
  Submetida:    'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  Devolvida:    'bg-orange-100 text-orange-700',
}

const fmt  = v => Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const inp = (err) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400 bg-red-50' : 'border-gray-300'}`

function Field({ label, error, children, hint }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {hint  && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

let _keySeq = 2000
const nextKey = () => _keySeq++

// ── Componente principal ──────────────────────────────────────────────────────

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Preparar Aquisição',
  descricao: 'Ponte entre o planejamento e o DFD — acessada a partir de uma Necessidade aprovada ou de uma família do Plano de Compras. Reúne os itens e gera o DFD com um clique.',
  acoes: [
    { label: 'Aviso de aquisições existentes', texto: 'Só aparece na origem "Plano de Compras": lista DFDs já existentes para a mesma família SIMPAS, para evitar duplicidade de pedido de compra.' },
    { label: 'Novo DFD independente vs. Consolidar DFDs aprovados', texto: 'Consolidar soma os itens de vários DFDs aprovados (sem ETP ainda) da mesma família em um único DFD — reduz fragmentação de processos.' },
    { label: '+ Adicionar item',    texto: 'Busca no catálogo SIMPAS (pré-preenche código e unidade) ou permite inserir um item livre quando não encontrado.' },
    { label: 'Classificação preliminar (triagem)', texto: 'Define elegibilidade de dispensa do ETP e as seções de checklist aplicáveis — não é a modalidade de licitação, decidida depois no Procedimento.' },
    { label: 'Confirmar e Gerar DFD →', texto: 'Cria o DFD com os itens revisados, já vinculado à necessidade ou aos DFDs consolidados de origem.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PrepararAquisicao() {
  const navigate = useNavigate()
  const { state } = useLocation()

  useEffect(() => { if (!state?.origem) navigate('/', { replace: true }) }, [])
  if (!state?.origem) return null

  const { origem, necessidade, familia, exercicio,
          itens_consolidados, sugestao, valor_total: valorTotalFamilia } = state

  // ── Detecção de aquisições existentes (somente família) ───────────────────
  const [statusFamilia, setStatusFamilia] = useState(null)   // { dfds, resumo }
  const [loadingStatus, setLoadingStatus] = useState(false)

  // modo: 'novo' | 'consolidar'
  const [modo, setModo] = useState('novo')
  const [dfdsSelec, setDfdsSelec] = useState([])  // IDs selecionados para consolidar

  useEffect(() => {
    if (origem !== 'familia' || !familia) return
    setLoadingStatus(true)
    api.get('/demanda/dfd/status-familia/', { params: { familia, exercicio } })
      .then(({ data }) => {
        setStatusFamilia(data)
        // pré-selecionar todos aprovados sem ETP
        setDfdsSelec(
          data.dfds
            .filter(d => d.status === 'Aprovada' && !d.tem_etp)
            .map(d => d.id),
        )
      })
      .catch(() => {})
      .finally(() => setLoadingStatus(false))
  }, [familia, exercicio, origem])

  // ── Itens editáveis ───────────────────────────────────────────────────────
  const [itens, setItens] = useState(() => {
    if (origem === 'familia' && itens_consolidados?.length) {
      return itens_consolidados.map(it => ({
        _key:                 nextKey(),
        item_catalogo_id:     null,
        objeto:               it.catalogo_nome || '',
        catalogo_codigo:      it.catalogo_codigo || '',
        catalogo_simpas:      it.catalogo_simpas || '',
        unidade_medida:       it.unidade_medida  || 'un',
        quantidade:           Number(it.quantidade_total) || 1,
        valor_unitario_estimado: Number(it.valor_unitario) || 0,
        // ItemDFD de origem consolidados nesta linha — mantém a rastreabilidade
        // do agrupamento (ver core.VinculoRastreabilidade / iniciar_de_familia)
        item_dfd_ids:         it.item_ids || [],
      }))
    }
    return []
  })

  // Quando o modo muda para "consolidar" ou a seleção muda, recarregar itens
  useEffect(() => {
    if (modo !== 'consolidar' || !statusFamilia) return
    const dfdsEscolhidos = statusFamilia.dfds.filter(d => dfdsSelec.includes(d.id))
    const mapa = new Map()  // chave: codigo ou objeto → item
    for (const dfd of dfdsEscolhidos) {
      for (const it of (dfd.itens_familia || [])) {
        const chave = it.catalogo_simpas || it.catalogo_codigo || it.objeto
        if (mapa.has(chave)) {
          const ex = mapa.get(chave)
          ex.quantidade += it.quantidade
          if (it.id != null) ex.item_dfd_ids.push(it.id)
        } else {
          mapa.set(chave, {
            _key:                 nextKey(),
            item_catalogo_id:     it.item_catalogo_id || null,
            objeto:               it.objeto,
            catalogo_codigo:      it.catalogo_codigo || '',
            catalogo_simpas:      it.catalogo_simpas || '',
            unidade_medida:       it.unidade_medida,
            quantidade:           it.quantidade,
            valor_unitario_estimado: it.valor_unitario_estimado,
            // ItemDFD de origem consolidados nesta linha — ver comentário
            // equivalente acima, no bloco origem === 'familia'.
            item_dfd_ids:         it.id != null ? [it.id] : [],
          })
        }
      }
    }
    setItens([...mapa.values()])
  }, [modo, dfdsSelec, statusFamilia])

  // ── Formulário de metadados ───────────────────────────────────────────────
  const [form, setForm] = useState({
    numero_sei:           '',
    prazo_necessidade:    '',
    area_aplicacao:       origem === 'necessidade' && necessidade?.area_aplicacao
                            ? (Array.isArray(necessidade.area_aplicacao)
                                ? necessidade.area_aplicacao
                                : [necessidade.area_aplicacao])
                            : [],
    modalidade_aquisicao: SUGESTAO_PARA_MODALIDADE[sugestao] || 'licitacao',
    observacoes:          '',
  })
  const [errors, setErrors]       = useState({})
  const [saving, setSaving]       = useState(false)
  const [saveError, setSaveError] = useState(null)

  // ── Busca de catálogo ─────────────────────────────────────────────────────
  const [showCatalogo, setShowCatalogo]     = useState(false)
  const [catalogoQuery, setCatalogoQuery]   = useState('')
  const [catalogoRes, setCatalogoRes]       = useState([])
  const [catalogoLoad, setCatalogoLoad]     = useState(false)

  const buscarCatalogo = useCallback(async (q) => {
    if (!q || q.length < 2) { setCatalogoRes([]); return }
    setCatalogoLoad(true)
    try {
      const { data } = await api.get('/core/catalogo/', { params: { search: q, page_size: 20 } })
      setCatalogoRes(data.results ?? data)
    } catch { setCatalogoRes([]) }
    finally { setCatalogoLoad(false) }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => buscarCatalogo(catalogoQuery), 300)
    return () => clearTimeout(t)
  }, [catalogoQuery])

  // ── Helpers de itens ──────────────────────────────────────────────────────
  const addFromCatalogo = (cat) => {
    setItens(p => [...p, {
      _key: nextKey(), item_catalogo_id: cat.id,
      objeto: cat.nome, catalogo_codigo: cat.codigo_interno,
      catalogo_simpas: cat.codigo_simpas || '', unidade_medida: cat.unidade_medida || 'un',
      quantidade: 1, valor_unitario_estimado: 0,
    }])
    setErrors(p => ({ ...p, itens: undefined }))
    setShowCatalogo(false); setCatalogoQuery(''); setCatalogoRes([])
  }
  const addItemLivre = () => {
    setItens(p => [...p, {
      _key: nextKey(), item_catalogo_id: null, objeto: '', catalogo_codigo: '',
      catalogo_simpas: '', unidade_medida: 'un', quantidade: 1, valor_unitario_estimado: 0,
    }])
    setErrors(p => ({ ...p, itens: undefined }))
    setShowCatalogo(false)
  }
  const updateItem = (key, field, value) =>
    setItens(p => p.map(it => it._key === key ? { ...it, [field]: value } : it))
  const removeItem = (key) => setItens(p => p.filter(it => it._key !== key))

  const setF = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }
  const toggleArea = (a) => setForm(p => ({
    ...p,
    area_aplicacao: p.area_aplicacao.includes(a)
      ? p.area_aplicacao.filter(x => x !== a)
      : [...p.area_aplicacao, a],
  }))

  const totalEstimado = itens.reduce(
    (acc, it) => acc + (Number(it.quantidade) || 0) * (Number(it.valor_unitario_estimado) || 0), 0,
  )

  // ── Submissão ─────────────────────────────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.numero_sei.trim())     errs.numero_sei = 'Obrigatório'
    if (!form.prazo_necessidade)     errs.prazo_necessidade = 'Obrigatório'
    if (!form.area_aplicacao.length) errs.area_aplicacao = 'Selecione ao menos uma área'
    if (!itens.length)               errs.itens = 'Adicione pelo menos 1 item ao DFD'
    if (Object.keys(errs).length)    { setErrors(errs); return }

    const itensPayload = itens.map(it => ({
      item_catalogo_id:        it.item_catalogo_id || null,
      objeto:                  it.objeto,
      unidade_medida:          it.unidade_medida,
      quantidade:              Number(it.quantidade),
      valor_unitario_estimado: Number(it.valor_unitario_estimado),
      // Só relevante para o endpoint de agrupamento (iniciar-de-familia) —
      // ignorado pelo endpoint de necessidade, que não conhece este campo.
      ...(it.item_dfd_ids?.length ? { item_dfd_ids: it.item_dfd_ids } : {}),
    }))

    // Observações automáticas ao consolidar DFDs
    let observacoes = form.observacoes
    if (modo === 'consolidar' && dfdsSelec.length) {
      const seis = statusFamilia.dfds
        .filter(d => dfdsSelec.includes(d.id))
        .map(d => d.numero_sei).join(', ')
      const auto = `DFD consolidado a partir dos DFDs: ${seis}.`
      observacoes = observacoes ? `${auto}\n${observacoes}` : auto
    }

    setSaving(true); setSaveError(null)
    try {
      let dfd
      if (origem === 'necessidade') {
        const { data } = await api.post(
          `/planejamento/necessidade/${necessidade.id}/iniciar_dfd/`,
          { ...form, observacoes, itens: itensPayload },
        )
        dfd = data
      } else {
        const { data } = await api.post('/demanda/dfd/iniciar-de-familia/', {
          ...form, observacoes, familia, exercicio, itens: itensPayload,
        })
        dfd = data
      }
      navigate(`/demanda/dfd/${dfd.id}`, {
        state: { mensagem: 'DFD criado a partir do plano de compras.' },
      })
    } catch (err) {
      const d = err.response?.data || {}
      if (typeof d === 'object' && !d.detail) {
        const mapped = {}
        for (const [k, v] of Object.entries(d))
          mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
        setErrors(mapped)
      } else {
        setSaveError(d.detail || 'Erro ao criar DFD. Tente novamente.')
      }
    } finally { setSaving(false) }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  const resumo = statusFamilia?.resumo
  const temAndamento = resumo?.em_andamento > 0
  const temDisponiveis = resumo?.aprovados_sem_etp > 0

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>
      <h1 className="text-xl font-bold text-gray-800 mb-0.5">Preparar Aquisição</h1>
      <p className="text-sm text-gray-500 mb-6">Revise os itens e preencha os dados para gerar o DFD.</p>

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* ── SEÇÃO A — Origem ──────────────────────────────────────── */}
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">Origem</p>
          {origem === 'necessidade' ? (
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-100 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-emerald-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25Z" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-gray-800">{necessidade?.titulo || '—'}</p>
                <p className="text-sm text-gray-500 mt-0.5">
                  Necessidade aprovada · Exercício {necessidade?.exercicio_fiscal}
                  {necessidade?.valor_estimado > 0 && ` · ${fmt(necessidade.valor_estimado)}`}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-start gap-3">
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5 text-blue-700" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
                </svg>
              </div>
              <div>
                <p className="font-semibold text-gray-800">
                  Plano de Compras — Família SIMPAS <span className="font-mono">{familia}</span>
                </p>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  <p className="text-sm text-gray-500">Exercício {exercicio} · {fmt(valorTotalFamilia)}</p>
                  {sugestao && SUGESTAO_LABELS[sugestao] && (
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${SUGESTAO_LABELS[sugestao].cls}`}>
                      {SUGESTAO_LABELS[sugestao].label}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ── SEÇÃO: Aquisições existentes (somente família) ────────── */}
        {origem === 'familia' && (
          <>
            {loadingStatus && (
              <div className="text-sm text-gray-400 text-center py-3">Verificando aquisições existentes...</div>
            )}

            {!loadingStatus && statusFamilia && (statusFamilia.dfds.length > 0) && (
              <div className={`rounded-xl border p-5 ${temAndamento ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'}`}>
                <div className="flex items-start gap-3 mb-4">
                  <span className="text-xl mt-0.5">{temAndamento ? '⚠' : 'ℹ'}</span>
                  <div>
                    <p className={`text-sm font-semibold ${temAndamento ? 'text-amber-800' : 'text-blue-800'}`}>
                      {temAndamento
                        ? `Atenção: ${resumo.em_andamento} DFD${resumo.em_andamento > 1 ? 's' : ''} com aquisição em andamento para esta família`
                        : `${resumo.total} DFD${resumo.total > 1 ? 's' : ''} existente${resumo.total > 1 ? 's' : ''} para esta família`}
                    </p>
                    <p className={`text-xs mt-0.5 ${temAndamento ? 'text-amber-600' : 'text-blue-600'}`}>
                      {temAndamento
                        ? 'Verifique se uma nova aquisição não gerará duplicidade. É possível consolidar DFDs aprovados ou prosseguir com novo DFD.'
                        : `${resumo.aprovados_sem_etp} aprovado${resumo.aprovados_sem_etp !== 1 ? 's' : ''} disponível${resumo.aprovados_sem_etp !== 1 ? 'is' : ''} para consolidar.`}
                    </p>
                  </div>
                </div>

                {/* Lista de DFDs existentes */}
                <div className="space-y-2 mb-4">
                  {statusFamilia.dfds.map(dfd => (
                    <div key={dfd.id} className="bg-white rounded-lg border border-gray-200 px-4 py-2.5 flex items-center justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-sm font-semibold text-gray-800">{dfd.numero_sei}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_DFD_CLS[dfd.status] || 'bg-gray-100 text-gray-600'}`}>
                            {dfd.status}
                          </span>
                          {dfd.tem_procedimento && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-medium">
                              Proc. licitatório
                            </span>
                          )}
                          {dfd.tem_etp && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-medium">
                              ETP {dfd.etp_status}
                            </span>
                          )}
                          {dfd.tem_tr && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 font-medium">
                              TR {dfd.tr_status}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5 truncate">{dfd.descricao}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs text-gray-500">{fmt(dfd.valor_estimado)}</span>
                        <button type="button"
                          onClick={() => navigate(`/demanda/dfd/${dfd.id}`)}
                          className="text-xs text-blue-600 hover:underline">
                          Ver →
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Seletor de modo */}
                <div className="flex gap-2 flex-wrap">
                  <button type="button"
                    onClick={() => setModo('novo')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                      modo === 'novo'
                        ? 'bg-gray-800 text-white border-gray-800'
                        : 'bg-white text-gray-600 border-gray-300 hover:border-gray-500'
                    }`}>
                    Novo DFD independente
                  </button>
                  {temDisponiveis && (
                    <button type="button"
                      onClick={() => setModo('consolidar')}
                      className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors ${
                        modo === 'consolidar'
                          ? 'bg-blue-700 text-white border-blue-700'
                          : 'bg-white text-blue-700 border-blue-300 hover:border-blue-500'
                      }`}>
                      Consolidar DFDs aprovados ({resumo.aprovados_sem_etp})
                    </button>
                  )}
                </div>

                {/* Seleção de DFDs para consolidar */}
                {modo === 'consolidar' && (
                  <div className="mt-4 space-y-2">
                    <p className="text-xs font-semibold text-gray-500 uppercase">Selecione os DFDs a consolidar:</p>
                    {statusFamilia.dfds
                      .filter(d => d.status === 'Aprovada' && !d.tem_etp)
                      .map(dfd => (
                        <label key={dfd.id} className="flex items-center gap-3 cursor-pointer bg-white border border-gray-200 rounded-lg px-4 py-2.5 hover:border-blue-400 transition-colors">
                          <input type="checkbox"
                            checked={dfdsSelec.includes(dfd.id)}
                            onChange={e => setDfdsSelec(p =>
                              e.target.checked ? [...p, dfd.id] : p.filter(x => x !== dfd.id)
                            )}
                            className="w-4 h-4 accent-blue-600 shrink-0"
                          />
                          <div className="min-w-0 flex-1">
                            <span className="font-mono text-sm font-semibold text-gray-800">{dfd.numero_sei}</span>
                            <span className="text-xs text-gray-500 ml-2 truncate">{dfd.descricao}</span>
                          </div>
                          <span className="text-xs text-gray-500 shrink-0">{fmt(dfd.valor_estimado)}</span>
                        </label>
                      ))}
                    {dfdsSelec.length === 0 && (
                      <p className="text-xs text-amber-600">Selecione ao menos 1 DFD para consolidar.</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ── SEÇÃO B — Itens ──────────────────────────────────────── */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
            <div>
              <p className="text-sm font-semibold text-gray-700">Itens do DFD</p>
              <p className="text-xs text-gray-400">
                {itens.length} {itens.length === 1 ? 'item' : 'itens'} · Total estimado:{' '}
                <strong className="text-gray-700">{fmt(totalEstimado)}</strong>
              </p>
            </div>
            <button type="button" onClick={() => setShowCatalogo(p => !p)}
              className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg font-medium">
              + Adicionar item
            </button>
          </div>

          {/* Painel de busca */}
          {showCatalogo && (
            <div className="px-5 py-4 bg-blue-50 border-b border-blue-100">
              <div className="flex gap-2 mb-3">
                <input autoFocus type="text" value={catalogoQuery}
                  onChange={e => setCatalogoQuery(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') e.preventDefault() }}
                  placeholder="Buscar no catálogo SIMPAS (mín. 2 caracteres)..."
                  className="flex-1 border border-blue-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                <button type="button"
                  onClick={() => { setShowCatalogo(false); setCatalogoQuery(''); setCatalogoRes([]) }}
                  className="px-3 py-2 text-sm text-gray-500 hover:text-gray-700">✕</button>
              </div>
              {catalogoLoad && <p className="text-xs text-blue-600 text-center py-2">Buscando...</p>}
              {!catalogoLoad && catalogoRes.length > 0 && (
                <div className="max-h-48 overflow-y-auto divide-y divide-blue-100 rounded-lg border border-blue-200 bg-white">
                  {catalogoRes.map(cat => (
                    <button key={cat.id} type="button" onClick={() => addFromCatalogo(cat)}
                      className="w-full text-left px-4 py-2.5 hover:bg-blue-50 transition-colors">
                      <p className="text-sm font-medium text-gray-800 leading-tight">{cat.nome}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        <span className="font-mono mr-2">{cat.codigo_interno}</span>
                        {cat.codigo_simpas && <span className="font-mono text-blue-600">{cat.codigo_simpas}</span>}
                        <span className="ml-2">{cat.unidade_medida}</span>
                      </p>
                    </button>
                  ))}
                </div>
              )}
              {!catalogoLoad && catalogoQuery.length >= 2 && catalogoRes.length === 0 && (
                <p className="text-xs text-gray-500 text-center py-2">
                  Nenhum item encontrado.{' '}
                  <button type="button" onClick={addItemLivre} className="text-blue-600 hover:underline font-medium">
                    Inserir item livre →
                  </button>
                </p>
              )}
            </div>
          )}

          {/* Tabela de itens */}
          {itens.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="px-4 py-2.5 text-left">Objeto / Descrição</th>
                    <th className="px-3 py-2.5 text-center w-20">Unid.</th>
                    <th className="px-3 py-2.5 text-right w-24">Qtd.</th>
                    <th className="px-3 py-2.5 text-right w-32">Vl. Unit.</th>
                    <th className="px-3 py-2.5 text-right w-32">Vl. Total</th>
                    <th className="w-8" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {itens.map(it => (
                    <tr key={it._key} className="hover:bg-gray-50">
                      <td className="px-4 py-2">
                        <input type="text" value={it.objeto}
                          onChange={e => updateItem(it._key, 'objeto', e.target.value)}
                          placeholder="Descrição do item"
                          className="w-full text-sm border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1" />
                        {(it.catalogo_codigo || it.catalogo_simpas) && (
                          <p className="text-[10px] text-gray-400 font-mono mt-0.5">
                            {it.catalogo_codigo && <span className="mr-2">{it.catalogo_codigo}</span>}
                            {it.catalogo_simpas && <span className="text-blue-500">{it.catalogo_simpas}</span>}
                          </p>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <input type="text" value={it.unidade_medida}
                          onChange={e => updateItem(it._key, 'unidade_medida', e.target.value)}
                          className="w-full text-sm text-center border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1" />
                      </td>
                      <td className="px-3 py-2">
                        <input type="number" min="0" step="0.0001" value={it.quantidade}
                          onChange={e => updateItem(it._key, 'quantidade', e.target.value)}
                          className="w-full text-sm text-right border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1" />
                      </td>
                      <td className="px-3 py-2">
                        <CampoMoeda value={it.valor_unitario_estimado}
                          onChange={v => updateItem(it._key, 'valor_unitario_estimado', v)}
                          className="w-full text-sm text-right border-0 bg-transparent focus:outline-none focus:ring-1 focus:ring-blue-400 rounded px-1" />
                      </td>
                      <td className="px-3 py-2 text-right font-medium text-gray-700 whitespace-nowrap">
                        {fmt((Number(it.quantidade) || 0) * (Number(it.valor_unitario_estimado) || 0))}
                      </td>
                      <td className="px-2 py-2">
                        <button type="button" onClick={() => removeItem(it._key)} title="Remover"
                          className="w-6 h-6 flex items-center justify-center text-gray-300 hover:text-red-500 rounded transition-colors">
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="border-t border-gray-200 bg-gray-50">
                  <tr>
                    <td colSpan={4} className="px-4 py-2.5 text-right text-xs font-semibold text-gray-500 uppercase">Total estimado</td>
                    <td className="px-3 py-2.5 text-right font-bold text-gray-800">{fmt(totalEstimado)}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          ) : (
            <div className="py-10 text-center text-gray-400">
              <p className="text-sm">Nenhum item adicionado.</p>
              <p className="text-xs mt-1">Clique em "+ Adicionar item" para buscar no catálogo SIMPAS.</p>
            </div>
          )}

          {errors.itens && (
            <p className="px-5 py-2 text-xs text-red-600 border-t border-red-100 bg-red-50">{errors.itens}</p>
          )}
        </div>

        {/* ── SEÇÃO C — Metadados do DFD ───────────────────────────── */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 space-y-5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">Dados do DFD</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <Field label="Número SEI *" error={errors.numero_sei}>
              <input type="text" value={form.numero_sei}
                onChange={e => setF('numero_sei', e.target.value)}
                placeholder="020.16859.2026.0000000-00"
                className={inp(errors.numero_sei)} />
            </Field>
            <Field label="Prazo da necessidade *" error={errors.prazo_necessidade}>
              <input type="date" value={form.prazo_necessidade}
                onChange={e => setF('prazo_necessidade', e.target.value)}
                className={inp(errors.prazo_necessidade)} />
            </Field>
          </div>
          <Field label="Classificação preliminar (triagem)"
            hint="Define elegibilidade de dispensa do ETP e as seções de checklist aplicáveis. Não é a modalidade de licitação — ela é decidida depois, no Procedimento, com base na Pesquisa de Preços.">
            <select value={form.modalidade_aquisicao}
              onChange={e => setF('modalidade_aquisicao', e.target.value)}
              className={inp(false)}>
              {MODALIDADES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </Field>
          <Field label="Área de aplicação *" error={errors.area_aplicacao}>
            <div className="flex flex-wrap gap-2 mt-1">
              {AREAS.map(a => (
                <button key={a.value} type="button" onClick={() => toggleArea(a.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                    form.area_aplicacao.includes(a.value)
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                  }`}>
                  {a.label}
                </button>
              ))}
            </div>
          </Field>
          <Field label="Observações">
            <textarea rows={3} value={form.observacoes}
              onChange={e => setF('observacoes', e.target.value)}
              placeholder="Informações adicionais..."
              className={inp(false)} />
          </Field>
        </div>

        {saveError && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            {saveError}
          </div>
        )}

        {/* ── Ações ────────────────────────────────────────────────── */}
        <div className="flex items-center justify-between pt-2">
          <button type="button" onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm">
            ← Voltar
          </button>
          <div className="flex items-center gap-3">
            {totalEstimado > 0 && (
              <span className="text-sm text-gray-500">
                Total: <strong className="text-gray-800">{fmt(totalEstimado)}</strong>
              </span>
            )}
            <button type="submit"
              disabled={saving || (modo === 'consolidar' && dfdsSelec.length === 0)}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-6 py-2 rounded-lg text-sm">
              {saving ? 'Criando DFD...' : 'Confirmar e Gerar DFD →'}
            </button>
          </div>
        </div>

      </form>
    </div>
  )
}
