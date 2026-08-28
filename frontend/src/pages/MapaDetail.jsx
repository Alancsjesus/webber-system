import { useEffect, useState } from 'react'
import api, { downloadFile } from '../services/api'
import ModalDevolver, { MOTIVOS_MAPA } from '../components/ModalDevolver'
import { useNavigate, useParams } from 'react-router-dom'
import useMapaStore from '../stores/mapaStore'
import useAuthStore from '../stores/authStore'
import LoadingSpinner from '../components/LoadingSpinner'
import PNCPImport from '../components/PNCPImport'
import SugestoesItensDfd from '../components/SugestoesItensDfd'
import FornecedorPicker from '../components/FornecedorPicker'
import CampoMoeda from '../components/CampoMoeda'

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const TIPO_FONTE_LABELS = {
  'I':    'I — SIMPAS / Comprasnet.BA',
  'II':   'II — Contratações similares',
  'III':  'III — Mídia especializada',
  'IV':   'IV — Notas fiscais',
  'V':    'V — Pesquisa direta',
  'HIST': 'Histórico Weber-e',
}

const MOTIVOS_EXCLUSAO = [
  { value: 'excessivo',    label: 'Excessivamente elevado (+30%)' },
  { value: 'inexequivel',  label: 'Inexequível (−30%)' },
  { value: 'inconsistente',label: 'Inconsistente / Especificação diferente' },
  { value: 'desatualizado',label: 'Desatualizado / Prazo vencido' },
  { value: 'manual',       label: 'Excluído manualmente' },
]

const METODOS = [
  { value: 'media',        label: 'Média aritmética',  desc: 'Indicada quando preços são homogêneos (variação ≤10%).' },
  { value: 'mediana',      label: 'Mediana',           desc: 'Indicada quando há variação alta ou valores extremos (outliers).' },
  { value: 'menor_valido', label: 'Menor preço válido', desc: 'Permite adotar o menor preço após exclusão de inexequíveis.' },
]

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Mapa de Preços — Pesquisa de Mercado',
  descricao: 'Instrumento para levantamento e sistematização de preços de mercado visando estimar o valor da contratação. Deve conter ao menos 3 fontes válidas para cada item.',
  acoes: [
    { label: '+ Item',            texto: 'Adiciona um item ao mapa com descrição, unidade e quantidade.' },
    { label: 'Sugestões do DFD de origem', texto: 'Lista os itens já cadastrados no DFD vinculado que ainda não estão nesta pesquisa — adicione um por um ou todos de uma vez, sem redigitar. Só aparece quando o mapa está vinculado a um DFD.' },
    { label: '+ Preço',           texto: 'Registra um preço para o item com fonte, tipo (I a V ou HIST), data e valor unitário.' },
    { label: 'Excluir preço',     texto: 'Remove um preço por motivo de excessivo, inexequível, inconsistente, desatualizado ou manual. O motivo é registrado.' },
    { label: 'Método',            texto: 'Seleciona o método de apuração: Média (preços homogêneos), Mediana (com outliers) ou Menor Preço Válido.' },
    { label: 'Recalcular',        texto: 'Atualiza o valor estimado com base nos preços válidos e no método selecionado.' },
    { label: 'Validar Prazos',    texto: 'Verifica se os preços coletados estão dentro do prazo de validade (180 dias para PNCP, 1 ano para outros).' },
    { label: 'Importar PNCP',     texto: 'Busca preços de contratações similares no Portal Nacional de Compras Públicas (PNCP) para subsidiar a pesquisa.' },
    { label: '+ Solicitação de Cotação', texto: 'Registra o disparo formal de uma solicitação de cotação a TODOS os fornecedores cadastrados numa família SIMPAS (Parâmetro V, Art. 5º, IV). Não envia e-mail automaticamente — mostra os destinatários para copiar em BCC no seu cliente de e-mail, e depois anexe o comprovante do envio (obrigatório pelo Art. 7º, IV).' },
    { label: '+ Resposta',        texto: 'Registra a resposta de um fornecedor específico ao disparo — valor cotado ou recusa, com upload da proposta recebida. Marque "Usar como referência" na resposta escolhida para justificar a seleção (Art. 3º, VII).' },
    { label: 'Submeter',          texto: 'Envia o mapa para aprovação. Todos os itens devem ter pelo menos 3 preços válidos.' },
    { label: 'Aprovar',           texto: 'Homologa o mapa de preços. O valor resultante é usado como referência no procedimento licitatório.' },
    { label: 'Download PDF',      texto: 'Exporta o mapa completo em PDF para compor o processo SEI.' },
  ],
  dica: 'Use preços do PNCP (Tipo I — SIMPAS/Comprasnet.BA) como primeira fonte — são os mais aceitos pelos órgãos de controle.',
  baseLegal: 'Lei 14.133/2021 — Art. 23 e IN SEGES nº 65/2021 (pesquisa de preços).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function MapaDetail() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const papel      = useAuthStore((s) => s.papel)
  const tipoUnidade = useAuthStore((s) => s.tipoUnidade)
  const isLicitante = tipoUnidade === 'licitante' || papel === 'admin'

  const {
    current, loading, error,
    fetchMapa, fetchMetadados, deleteMapa,
    analisar, salvarMetodo, recalcular, validarPrazos,
    submeter, iniciarAnalise, aprovar, devolver, cancelar,
    fetchHistoricoWebber,
    addFonte, deleteFonte,
    addItem, deleteItem,
    addPreco, updatePreco, deletePreco,
    addSolicitacao, updateSolicitacao, deleteSolicitacao,
    addResposta, updateResposta, deleteResposta,
    metadados,
  } = useMapaStore()

  const [msg, setMsg]             = useState(null)
  const [saving, setSaving]       = useState(false)
  const [activeTab, setActiveTab] = useState('fontes')
  const [historicoWB, setHistoricoWB]   = useState(null)
  const [loadingHist, setLoadingHist]   = useState(false)
  const [analise, setAnalise]           = useState(null)
  const [loadingAnalise, setLoadingAnalise] = useState(false)
  const [metodoForm, setMetodoForm]     = useState({ metodo_calculo: 'media', justificativa_metodologia: '' })
  const [showDevolver, setShowDevolver] = useState(false)
  const [motivoDevolucao, setMotivoDevolucao] = useState('')
  const [showCancelar, setShowCancelar] = useState(false)
  const [motivoCancelar, setMotivoCancelar]   = useState('')

  useEffect(() => { fetchMapa(id); fetchMetadados() }, [id])
  useEffect(() => {
    if (current) {
      setMetodoForm({
        metodo_calculo:           current.metodo_calculo || 'media',
        justificativa_metodologia: current.justificativa_metodologia || '',
      })
    }
  }, [current])

  const act = async (fn, successMsg) => {
    setSaving(true); setMsg(null)
    try {
      const r = await fn()
      setMsg({ type: 'success', text: successMsg || 'Operação concluída.' })
      return r
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao executar operação.' })
    } finally { setSaving(false) }
  }

  const loadAnalise = async () => {
    setLoadingAnalise(true)
    try {
      const data = await analisar(id)
      setAnalise(data)
      if (data.metodo_sugerido_global) {
        setMetodoForm(p => ({ ...p, metodo_calculo: data.metodo_sugerido_global }))
      }
    } finally { setLoadingAnalise(false) }
  }

  const loadHistoricoWB = async () => {
    setLoadingHist(true)
    try { setHistoricoWB(await fetchHistoricoWebber(id)) }
    finally { setLoadingHist(false) }
  }

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando mapa..." /></div>
  if (error)   return <div className="p-8 text-sm text-red-600">{error}</div>
  if (!current) return null

  const isEditavel  = ['Rascunho', 'Submetido', 'Devolvido'].includes(current.status)
  const isAprovado  = current.status === 'Aprovado'
  const isDevolvido = current.status === 'Devolvido'

  return (
    <div className="p-6 lg:p-8 max-w-5xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Mapa Comparativo de Preços #{current.id}</h1>
          <p className="text-sm text-gray-500 mt-0.5 max-w-xl">{current.objeto}</p>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              current.status === 'Finalizado' ? 'bg-green-100 text-green-700'
              : current.status === 'Cancelado' ? 'bg-red-100 text-red-600'
              : 'bg-gray-100 text-gray-600'
            }`}>{current.status}</span>
            <span className="text-xs text-gray-400">Exercício {current.exercicio_fiscal}</span>
            {current.dfd_numero_sei && (
              <span className="text-xs font-mono text-blue-700">DFD: {current.dfd_numero_sei}</span>
            )}
            <span className="text-xs text-gray-400">Método: {current.metodo_display}</span>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {isEditavel && (
            <>
              <button onClick={() => act(() => validarPrazos(id), 'Prazos verificados.')} disabled={saving}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">
                Verificar Prazos
              </button>
              <button onClick={() => act(() => recalcular(id), 'Valores recalculados.')} disabled={saving}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">
                Recalcular
              </button>
            </>
          )}
          {/* Submeter — quem elaborou o mapa */}
          {['Rascunho', 'Devolvido'].includes(current.status) && (
            <button onClick={() => act(() => submeter(id), 'Mapa submetido para a Unidade Licitante.')} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Submeter para Aprovação
            </button>
          )}
          {/* Iniciar análise — licitante */}
          {current.status === 'Submetido' && isLicitante && (
            <button onClick={() => act(() => iniciarAnalise(id), 'Análise iniciada.')} disabled={saving}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Iniciar Análise
            </button>
          )}
          {/* Aprovar / Devolver — licitante */}
          {current.status === 'Em Análise' && isLicitante && (
            <>
              <button onClick={() => act(() => aprovar(id), 'Mapa aprovado pela Unidade Licitante.')} disabled={saving}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
                Aprovar
              </button>
              <button onClick={() => setShowDevolver(true)}
                className="border border-orange-300 text-orange-600 hover:bg-orange-50 text-sm px-4 py-1.5 rounded-lg">
                Devolver
              </button>
            </>
          )}
          {/* PDF — aprovado */}
          {isAprovado && (
            <button
              onClick={() => downloadFile(`/pesquisa/mapa/${id}/export/pdf/`, `Mapa_${id}.pdf`)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg inline-block">
              Baixar PDF
            </button>
          )}
          {/* Histórico de tramitação em PDF */}
          <button
            onClick={() => downloadFile(`/pesquisa/mapa/${id}/export/historico/`, `Historico_Mapa_${id}.pdf`)}
            className="border border-gray-300 text-gray-600 text-sm px-3 py-1.5 rounded-lg hover:bg-gray-50">
            ↓ Histórico PDF
          </button>
          {/* Cancelar */}
          {!['Aprovado', 'Cancelado'].includes(current.status) && (
            <button onClick={() => setShowCancelar(true)}
              className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-3 py-1.5 rounded-lg">
              Cancelar
            </button>
          )}
        </div>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
                                 : 'bg-red-50 text-red-700 border border-red-200'
        }`}>{msg.text}</div>
      )}

      {/* Valor total */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex gap-6">
        <div>
          <p className="text-xs font-semibold text-blue-800 uppercase">Valor Estimado Total</p>
          <p className="text-2xl font-bold text-blue-700">{fmt(current.valor_estimado_total)}</p>
        </div>
        <div className="border-l border-blue-200 pl-6">
          <p className="text-xs text-blue-700">Itens: <strong>{current.qtd_itens}</strong></p>
          <p className="text-xs text-blue-700">Fontes: <strong>{current.qtd_fontes}</strong></p>
          <p className="text-xs text-blue-700">Método: <strong>{current.metodo_display}</strong></p>
        </div>
      </div>

      {/* Devolução / Cancelamento alerts */}
      {isDevolvido && current.motivo_devolucao && (
        <div className="mb-4 bg-orange-50 border border-orange-300 rounded-xl px-5 py-3">
          <p className="text-sm font-semibold text-orange-800">Mapa devolvido pela Unidade Licitante</p>
          <p className="text-sm text-orange-700 mt-1">{current.motivo_devolucao}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5 gap-1 flex-wrap">
        {[
          { key: 'fontes',   label: `Fontes (${current.fontes?.length ?? 0})` },
          { key: 'cotacoes', label: `Solicitações de Cotação (${current.solicitacoes_cotacao?.length ?? 0})` },
          { key: 'itens',    label: `Itens e Preços (${current.itens?.length ?? 0})` },
          { key: 'analise',  label: 'Análise e Método' },
          { key: 'historico_wb', label: 'Histórico Weber-e' },
          { key: 'historico',label: `Tramitação (${current.historico?.length ?? 0})` },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => {
            setActiveTab(key)
            if (key === 'historico_wb' && !historicoWB) loadHistoricoWB()
            if (key === 'analise' && !analise) loadAnalise()
          }}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === key
                ? 'border-b-2 border-blue-600 text-blue-700 bg-blue-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Fontes */}
      {activeTab === 'fontes' && (
        <div>
          {isEditavel && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Adicionar fonte consultada</p>
              <FonteForm
                metadados={metadados}
                onSave={async (payload) => {
                  await act(() => addFonte(id, payload), 'Fonte adicionada.')
                }}
              />
            </div>
          )}
          {(current.fontes || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhuma fonte cadastrada. Adicione as fontes consultadas conforme Art. 5º do Decreto 22.886/2024.</p>
            : (
              <div className="space-y-2">
                {current.fontes.map((f) => (
                  <div key={f.id} className={`flex items-start justify-between p-4 rounded-xl border ${
                    f.infrutífera ? 'border-orange-200 bg-orange-50' : 'border-gray-200 bg-white'
                  }`}>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                          {TIPO_FONTE_LABELS[f.tipo] || f.tipo}
                        </span>
                        {f.infrutífera && <span className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded-full">Infrutífera</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-800">{f.descricao}</p>
                      {f.referencia && <p className="text-xs text-gray-500 mt-0.5">{f.referencia}</p>}
                      <p className="text-xs text-gray-400 mt-0.5">
                        Consulta: {f.data_consulta ? new Date(f.data_consulta).toLocaleDateString('pt-BR') : '—'}
                        {f.documento_sei && ` · SEI: ${f.documento_sei}`}
                      </p>
                      {f.infrutífera && f.justificativa_infrutífera && (
                        <p className="text-xs text-orange-700 mt-1">Justificativa: {f.justificativa_infrutífera}</p>
                      )}
                      {f.tipo === 'V' && (
                        <p className="text-xs text-gray-400 mt-1">
                          {(f.solicitacoes || []).length} solicitação(ões) de cotação vinculada(s)
                          {' — '}
                          <button onClick={() => setActiveTab('cotacoes')} className="text-blue-600 hover:underline">
                            ver aba Solicitações de Cotação
                          </button>
                        </p>
                      )}
                    </div>
                    {isEditavel && (
                      <button onClick={() => act(() => deleteFonte(id, f.id), 'Fonte removida.')}
                        className="text-xs text-red-500 hover:text-red-700 ml-4 shrink-0">Remover</button>
                    )}
                  </div>
                ))}
              </div>
            )}
        </div>
      )}

      {/* Tab: Solicitações de Cotação */}
      {activeTab === 'cotacoes' && (
        <div>
          <p className="text-sm text-gray-600 mb-4">
            Disparo formal de solicitação de cotação a todos os fornecedores cadastrados numa família
            (Parâmetro V, Art. 5º, IV do Decreto 22.886/2024). O envio do e-mail é feito pelo seu próprio
            cliente de e-mail — copie os destinatários para BCC e depois anexe o comprovante do envio,
            conforme exige o Art. 7º, IV. As respostas de cada fornecedor são registradas individualmente
            dentro do disparo.
          </p>
          {isEditavel && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Novo disparo de cotação</p>
              <SolicitacaoForm
                fontes={(current.fontes || []).filter(f => f.tipo === 'V')}
                onSave={async (payload) => {
                  await act(() => addSolicitacao(id, payload), 'Disparo registrado.')
                }}
              />
            </div>
          )}

          {(current.solicitacoes_cotacao || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhum disparo de cotação registrado.</p>
            : (
              <div className="space-y-3">
                {current.solicitacoes_cotacao.map((s) => (
                  <SolicitacaoCard
                    key={s.id}
                    sol={s}
                    isEditavel={isEditavel}
                    onEncerrar={() => act(() => updateSolicitacao(id, s.id, { encerrada: true }), 'Disparo encerrado.')}
                    onDelete={() => act(() => deleteSolicitacao(id, s.id), 'Disparo removido.')}
                    onAddResposta={async (payload) => {
                      await act(() => addResposta(id, s.id, payload), 'Resposta registrada.')
                    }}
                    onUpdateResposta={async (respId, payload) => {
                      await act(() => updateResposta(id, s.id, respId, payload), 'Resposta atualizada.')
                    }}
                    onDeleteResposta={(respId) => act(() => deleteResposta(id, s.id, respId), 'Resposta removida.')}
                  />
                ))}
              </div>
            )}
        </div>
      )}

      {/* Tab: Itens e Preços */}
      {activeTab === 'itens' && (
        <div className="space-y-6">
          {isEditavel && (
            <SugestoesItensDfd
              dfdId={current.dfd}
              itensDoMapa={current.itens || []}
              onAdicionar={(payload) => addItem(id, payload)}
            />
          )}
          {isEditavel && (
            <PNCPImport
              mapaId={id}
              itensDoMapa={current.itens || []}
              onImportado={(msg) => {
                setMsg({ type: 'success', text: msg })
                fetchMapa(id)
              }}
            />
          )}
          {isEditavel && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Adicionar item</p>
              <ItemForm onSave={async (payload) => { await act(() => addItem(id, payload), 'Item adicionado.') }} />
            </div>
          )}

          {(current.itens || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhum item cadastrado. Adicione os itens que compõem o objeto da pesquisa.</p>
            : (current.itens || []).map((item) => (
              <div key={item.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                {/* Cabeçalho do item */}
                <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-200">
                  <div>
                    <span className="text-xs font-bold text-gray-500 mr-2">#{item.ordem}</span>
                    <span className="font-medium text-gray-800">{item.descricao}</span>
                    {item.codigo_simpas && <span className="ml-2 text-xs font-mono text-blue-600">[{item.codigo_simpas}]</span>}
                    <span className="ml-3 text-xs text-gray-500">{item.quantidade} {item.unidade_medida}</span>
                  </div>
                  {item.valor_unitario_calculado && (
                    <div className="text-right">
                      <p className="text-xs text-gray-400">{item.metodo_aplicado} · {item.qtd_precos_validos} preço(s)</p>
                      <p className="font-semibold text-green-700 text-sm">{fmt(item.valor_unitario_calculado)}/un · Total: {fmt(item.valor_total_calculado)}</p>
                    </div>
                  )}
                  {isEditavel && (
                    <button onClick={() => act(() => deleteItem(id, item.id), 'Item removido.')}
                      className="text-xs text-red-500 hover:text-red-700 ml-4">Remover item</button>
                  )}
                </div>

                {/* Alertas */}
                {item.alerta && (
                  <div className="px-5 py-2 bg-amber-50 border-b border-amber-200">
                    <p className="text-xs text-amber-800">⚠ {item.alerta}</p>
                  </div>
                )}

                {/* Preços coletados */}
                <div className="px-5 py-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-3">
                    Preços coletados ({item.precos?.length ?? 0})
                  </p>

                  {(item.precos || []).length > 0 && (
                    <div className="mb-4 overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-50 border border-gray-200">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Fonte</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Origem / Órgão</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Certame</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Data</th>
                            <th className="text-right px-3 py-2 font-medium text-gray-500">Valor Unit.</th>
                            <th className="text-center px-3 py-2 font-medium text-gray-500">Válido</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Obs / Alerta</th>
                            {isEditavel && <th className="px-3 py-2"></th>}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 border border-gray-200">
                          {item.precos.map((p) => (
                            <tr key={p.id} className={!p.valido ? 'opacity-50 bg-red-50' : p.sugestao_exclusao ? 'bg-amber-50' : ''}>
                              <td className="px-3 py-2">
                                <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs font-semibold">
                                  {p.fonte_tipo}
                                </span>
                                <span className="ml-1 text-gray-500">{p.fonte_descricao?.slice(0,20)}</span>
                              </td>
                              <td className="px-3 py-2 text-gray-700">{p.origem_orgao_empresa || '—'}</td>
                              <td className="px-3 py-2 text-gray-500">{p.numero_certame || '—'}</td>
                              <td className="px-3 py-2 text-gray-500">
                                {p.data_referencia ? new Date(p.data_referencia).toLocaleDateString('pt-BR') : '—'}
                              </td>
                              <td className="px-3 py-2 text-right font-semibold text-gray-800">{fmt(p.valor_unitario)}</td>
                              <td className="px-3 py-2 text-center">
                                {isEditavel ? (
                                  <input type="checkbox" checked={p.valido}
                                    onChange={async (e) => {
                                      await act(
                                        () => updatePreco(id, item.id, p.id, { valido: e.target.checked }),
                                        e.target.checked ? 'Preço reativado.' : 'Preço excluído do cálculo.'
                                      )
                                    }}
                                    className="accent-blue-600" />
                                ) : (
                                  <span className={p.valido ? 'text-green-600' : 'text-red-500'}>
                                    {p.valido ? '✓' : '✗'}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2">
                                {p.sugestao_exclusao && <span className="text-amber-700">⚠ {p.sugestao_exclusao}</span>}
                                {!p.valido && p.motivo_exclusao_display && <span className="text-red-600">{p.motivo_exclusao_display}</span>}
                                {p.arquivo_url && (
                                  <a href={p.arquivo_url} target="_blank" rel="noreferrer"
                                    className="ml-1 text-xs text-blue-600 hover:underline">
                                    📄 Ver doc
                                  </a>
                                )}
                              </td>
                              {isEditavel && (
                                <td className="px-3 py-2 text-right">
                                  <button onClick={() => act(() => deletePreco(id, item.id, p.id), 'Preço removido.')}
                                    className="text-red-500 hover:text-red-700">✕</button>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Formulário novo preço */}
                  {isEditavel && (
                    <PrecoForm
                      itemId={item.id}
                      fontes={current.fontes || []}
                      onSave={async (payload) => {
                        await act(() => addPreco(id, item.id, payload), 'Preço adicionado.')
                      }}
                    />
                  )}
                </div>
              </div>
            ))
          }
        </div>
      )}

      {/* Tab: Análise e Método */}
      {activeTab === 'analise' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm text-gray-600">
              A variação dos preços coletados indica o método estatístico mais adequado
              conforme o Art. 8º do Decreto 22.886/2024.
            </p>
            <button onClick={loadAnalise} disabled={loadingAnalise}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">
              {loadingAnalise ? 'Analisando...' : 'Reanalisar'}
            </button>
          </div>

          {loadingAnalise && <LoadingSpinner message="Analisando distribuição dos preços..." />}

          {!loadingAnalise && !analise && (
            <button onClick={loadAnalise}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg">
              Analisar preços coletados
            </button>
          )}

          {analise && (
            <div className="space-y-4">
              {/* Sugestão global */}
              <div className={`rounded-xl p-4 border ${
                analise.metodo_sugerido_global === 'mediana'
                  ? 'bg-amber-50 border-amber-300'
                  : 'bg-green-50 border-green-300'
              }`}>
                <p className="text-sm font-semibold mb-1">
                  Método sugerido pelo sistema:{' '}
                  <span className="text-blue-700">
                    {analise.metodo_sugerido_global === 'media' ? 'Média aritmética'
                      : analise.metodo_sugerido_global === 'mediana' ? 'Mediana'
                      : 'Menor preço válido'}
                  </span>
                </p>
                <p className="text-xs text-gray-600">{analise.nota}</p>
                {analise.precisa_justificativa && (
                  <p className="text-xs text-orange-700 mt-1 font-medium">
                    ⚠ Justificativa obrigatória para um ou mais itens (§5, Art. 8º, Decreto 22.886/2024).
                  </p>
                )}
              </div>

              {/* Estatísticas por item */}
              <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium text-gray-500">Item</th>
                      <th className="text-center px-3 py-2 font-medium text-gray-500">Preços válidos</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">Mínimo</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">Mediana</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">Média</th>
                      <th className="text-right px-3 py-2 font-medium text-gray-500">Máximo</th>
                      <th className="text-center px-3 py-2 font-medium text-gray-500">Variação</th>
                      <th className="text-center px-3 py-2 font-medium text-gray-500">Outliers</th>
                      <th className="text-left px-3 py-2 font-medium text-gray-500">Sugestão</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {analise.itens.map((item) => (
                      <tr key={item.item_id} className={item.sem_precos_validos ? 'bg-red-50' : ''}>
                        <td className="px-4 py-2 font-medium text-gray-800">{item.descricao}</td>
                        <td className="px-3 py-2 text-center">
                          <span className={`font-semibold ${item.qtd_validos < 3 ? 'text-orange-600' : 'text-green-700'}`}>
                            {item.qtd_validos}
                          </span>
                          {item.qtd_invalidos > 0 && <span className="text-red-500 ml-1">({item.qtd_invalidos}✗)</span>}
                        </td>
                        {item.sem_precos_validos ? (
                          <td colSpan={6} className="px-3 py-2 text-center text-red-600 text-xs">{item.motivo_sugestao}</td>
                        ) : (
                          <>
                            <td className="px-3 py-2 text-right text-gray-700">{fmt(item.minimo)}</td>
                            <td className="px-3 py-2 text-right text-blue-700 font-semibold">{fmt(item.mediana)}</td>
                            <td className="px-3 py-2 text-right text-gray-700">{fmt(item.media)}</td>
                            <td className="px-3 py-2 text-right text-gray-700">{fmt(item.maximo)}</td>
                            <td className="px-3 py-2 text-center">
                              <span className={`font-semibold ${item.variacao_pct > 30 ? 'text-red-600' : item.variacao_pct > 10 ? 'text-amber-600' : 'text-green-600'}`}>
                                {item.variacao_pct.toFixed(1)}%
                              </span>
                            </td>
                            <td className="px-3 py-2 text-center">
                              {item.outliers > 0
                                ? <span className="text-red-600 font-semibold">⚠ {item.outliers}</span>
                                : <span className="text-green-600">—</span>}
                            </td>
                          </>
                        )}
                        <td className="px-3 py-2 text-xs text-blue-700 max-w-[180px]">
                          {!item.sem_precos_validos && (
                            <span className="font-semibold">
                              {item.metodo_sugerido === 'media' ? 'Média' : item.metodo_sugerido === 'mediana' ? 'Mediana' : 'Menor válido'}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Seleção do método */}
              {isEditavel && (
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-5">
                  <p className="text-sm font-semibold text-gray-700 mb-3">
                    Definir método de cálculo e justificativa
                  </p>
                  <div className="space-y-2 mb-4">
                    {METODOS.map(({ value, label, desc }) => {
                      const isSugerido = value === analise.metodo_sugerido_global
                      return (
                        <label key={value}
                          className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                            metodoForm.metodo_calculo === value
                              ? 'border-blue-400 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}>
                          <input type="radio" name="metodo" value={value}
                            checked={metodoForm.metodo_calculo === value}
                            onChange={() => setMetodoForm(p => ({ ...p, metodo_calculo: value }))}
                            className="mt-0.5 accent-blue-600" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="text-sm font-medium text-gray-800">{label}</p>
                              {isSugerido && (
                                <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full font-medium">
                                  Sugerido
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                          </div>
                        </label>
                      )
                    })}
                  </div>
                  <div className="mb-4">
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Justificativa da metodologia adotada *
                      {analise.precisa_justificativa && <span className="text-orange-600 ml-1">(obrigatória)</span>}
                    </label>
                    <textarea rows={3} value={metodoForm.justificativa_metodologia}
                      onChange={e => setMetodoForm(p => ({ ...p, justificativa_metodologia: e.target.value }))}
                      placeholder="Explique o critério adotado para escolha do método (Art. 3º, inciso VI, Decreto 22.886/2024)..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <button
                    onClick={() => act(
                      () => salvarMetodo(id, metodoForm.metodo_calculo, metodoForm.justificativa_metodologia),
                      'Método e justificativa salvos. Execute "Recalcular" para aplicar.'
                    )}
                    disabled={saving}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                    {saving ? 'Salvando...' : 'Salvar método e justificativa'}
                  </button>
                </div>
              )}

              {!isEditavel && (
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Método adotado</p>
                  <p className="text-sm font-semibold text-gray-800">{current.metodo_display}</p>
                  {current.justificativa_metodologia && (
                    <p className="text-sm text-gray-600 mt-1">{current.justificativa_metodologia}</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab: Histórico Weber-e */}
      {activeTab === 'historico_wb' && (
        <div>
          {loadingHist && <LoadingSpinner message="Consultando histórico Weber-e..." />}
          {!loadingHist && !historicoWB && (
            <button onClick={loadHistoricoWB}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg">
              Consultar histórico de contratações por item
            </button>
          )}
          {historicoWB && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 text-sm text-blue-800">
                {historicoWB.nota}
                <span className="ml-2 font-semibold">({historicoWB.total} contratação(ões) encontrada(s))</span>
              </div>

              {(historicoWB.grupos || []).length === 0 && (
                <p className="text-sm text-gray-400">Nenhum item configurado neste mapa.</p>
              )}

              {(historicoWB.grupos || []).map((grupo, gi) => (
                <div key={gi} className="border border-gray-200 rounded-xl overflow-hidden">
                  {/* Cabeçalho do item */}
                  <div className="flex items-center justify-between px-4 py-2.5 bg-gray-50 border-b border-gray-200">
                    <div>
                      <span className="text-sm font-semibold text-gray-800">{grupo.item_descricao}</span>
                      {grupo.codigo_simpas && (
                        <span className="ml-2 text-xs font-mono text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded">
                          {grupo.codigo_simpas}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        grupo.match_por === 'simpas'   ? 'bg-green-100 text-green-700'
                        : grupo.match_por === 'familia' ? 'bg-blue-100 text-blue-700'
                        : grupo.match_por === 'descricao' ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-500'
                      }`}>
                        {grupo.match_por === 'simpas'    ? 'Match SIMPAS exato ✓'
                          : grupo.match_por === 'familia'  ? `Match família ${grupo.familia_simpas || ''}`
                          : grupo.match_por === 'descricao' ? 'Match por descrição'
                          : 'Sem histórico'}
                      </span>
                      <span className="text-xs text-gray-400">{grupo.total} registro(s)</span>
                    </div>
                  </div>

                  {grupo.historico.length === 0 ? (
                    <p className="px-4 py-3 text-sm text-gray-400 italic">
                      Nenhuma contratação anterior encontrada para este item nos últimos 2 anos.
                    </p>
                  ) : (
                    <table className="w-full text-xs">
                      <thead className="bg-gray-50/60">
                        <tr>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">DFD (SEI)</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Descrição anterior</th>
                          <th className="text-right px-4 py-2 font-medium text-gray-500">Qtd</th>
                          <th className="text-right px-4 py-2 font-medium text-gray-500">Valor Unit.</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Data DFD</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Contrato</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {grupo.historico.map((h, hi) => (
                          <tr key={hi} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-mono text-blue-700">{h.dfd_numero_sei}</td>
                            <td className="px-4 py-2 text-gray-700 max-w-xs truncate" title={h.item_descricao}>
                              {h.item_descricao}
                            </td>
                            <td className="px-4 py-2 text-right text-gray-600">{h.quantidade} {h.unidade_medida}</td>
                            <td className="px-4 py-2 text-right font-semibold text-gray-800">{fmt(h.valor_unitario)}</td>
                            <td className="px-4 py-2 text-gray-400">{h.dfd_data}</td>
                            <td className="px-4 py-2 text-gray-500">
                              {h.contrato
                                ? <span className="text-green-700 font-medium">{h.contrato}</span>
                                : <span className="text-gray-300">—</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab: Tramitação */}
      {activeTab === 'historico' && (
        <div>
          {(current.historico || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhuma tramitação registrada.</p>
            : (
              <div className="space-y-2">
                {current.historico.map((h) => (
                  <div key={h.id} className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
                    <div className="shrink-0 text-xs text-gray-400 w-36">
                      {new Date(h.criado_em).toLocaleString('pt-BR')}
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">{h.usuario_nome}</span>
                      {' · '}
                      <span className="text-gray-500">{h.status_anterior}</span>
                      {' → '}
                      <span className="font-semibold text-gray-800">{h.status_novo}</span>
                      {h.motivo && (
                        <p className="text-xs text-gray-500 mt-0.5">{h.motivo}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
        </div>
      )}

      {/* Modal: Devolver */}
      <ModalDevolver
        show={showDevolver}
        onClose={() => setShowDevolver(false)}
        onConfirm={async (motivo, categoria) => {
          await act(() => devolver(id, motivo, categoria), 'Mapa devolvido.')
          setShowDevolver(false)
        }}
        loading={saving}
        titulo="Devolver mapa para correção"
        categorias={MOTIVOS_MAPA}
      />

      {/* Modal: Cancelar */}
      {showCancelar && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">Cancelar mapa</h3>
            <label className="block text-xs font-medium text-gray-600 mb-1 mt-3">Motivo (opcional)</label>
            <textarea rows={2} value={motivoCancelar}
              onChange={(e) => setMotivoCancelar(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  await act(() => cancelar(id, motivoCancelar), 'Mapa cancelado.')
                  setShowCancelar(false); setMotivoCancelar('')
                }}
                disabled={saving}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? 'Cancelando...' : 'Confirmar cancelamento'}
              </button>
              <button onClick={() => { setShowCancelar(false); setMotivoCancelar('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Voltar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Sub-componentes de formulário ─────────────────────────────────────────────

function FonteForm({ metadados, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    tipo: 'I', descricao: '', referencia: '', data_consulta: hoje,
    documento_sei: '', infrutífera: false, justificativa_infrutífera: '',
  })
  const [saving, setSaving] = useState(false)
  const tipos = metadados?.tipos_fonte || []

  const handleSave = async () => {
    if (!form.descricao.trim()) return
    setSaving(true)
    try { await onSave(form) } finally { setSaving(false) }
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Parâmetro (Art. 5º) *</label>
        <select value={form.tipo} onChange={(e) => setForm(p => ({ ...p, tipo: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
          {tipos.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Data da consulta *</label>
        <input type="date" value={form.data_consulta}
          onChange={(e) => setForm(p => ({ ...p, data_consulta: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2">
        <label className="block text-xs font-medium text-gray-600 mb-1">Descrição da fonte *</label>
        <input type="text" value={form.descricao}
          onChange={(e) => setForm(p => ({ ...p, descricao: e.target.value }))}
          placeholder="Ex: Portal SIMPAS — consulta 26/04/2026, Pregão PMMG 001/2025"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Referência (SEI, URL, certame)</label>
        <input type="text" value={form.referencia}
          onChange={(e) => setForm(p => ({ ...p, referencia: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Nº documento SEI</label>
        <input type="text" value={form.documento_sei}
          onChange={(e) => setForm(p => ({ ...p, documento_sei: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2 flex items-center gap-2">
        <input type="checkbox" id="infrutífera" checked={form.infrutífera}
          onChange={(e) => setForm(p => ({ ...p, infrutífera: e.target.checked }))}
          className="accent-orange-500" />
        <label htmlFor="infrutífera" className="text-xs text-gray-600 cursor-pointer">
          Consulta infrutífera (fornecedor não respondeu / item indisponível)
        </label>
      </div>
      {form.infrutífera && (
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">Justificativa da consulta infrutífera</label>
          <input type="text" value={form.justificativa_infrutífera}
            onChange={(e) => setForm(p => ({ ...p, justificativa_infrutífera: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      )}
      <div className="col-span-2">
        <button onClick={handleSave} disabled={saving || !form.descricao.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
          {saving ? 'Salvando...' : 'Adicionar fonte'}
        </button>
      </div>
    </div>
  )
}

function ItemForm({ onSave }) {
  const [form, setForm] = useState({ ordem: 1, descricao: '', codigo_simpas: '', unidade_medida: 'UND', quantidade: 1 })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.descricao.trim()) return
    setSaving(true)
    try { await onSave({ ...form, quantidade: Number(form.quantidade), ordem: Number(form.ordem) }) } finally { setSaving(false) }
  }

  return (
    <div className="grid grid-cols-4 gap-3">
      <div className="col-span-2">
        <label className="block text-xs font-medium text-gray-600 mb-1">Descrição do item *</label>
        <input type="text" value={form.descricao}
          onChange={(e) => setForm(p => ({ ...p, descricao: e.target.value }))}
          placeholder="Ex: Torniquete tático de combate"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Código SIMPAS</label>
        <input type="text" value={form.codigo_simpas}
          onChange={(e) => setForm(p => ({ ...p, codigo_simpas: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Unid. medida</label>
        <input type="text" value={form.unidade_medida}
          onChange={(e) => setForm(p => ({ ...p, unidade_medida: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Quantidade</label>
        <input type="number" min="0.001" step="0.001" value={form.quantidade}
          onChange={(e) => setForm(p => ({ ...p, quantidade: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Ordem</label>
        <input type="number" min="1" value={form.ordem}
          onChange={(e) => setForm(p => ({ ...p, ordem: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2 flex items-end">
        <button onClick={handleSave} disabled={saving || !form.descricao.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
          {saving ? 'Adicionando...' : 'Adicionar item'}
        </button>
      </div>
    </div>
  )
}

function SolicitacaoForm({ fontes, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({ fonte: '', familia_simpas: '', data_envio: hoje, prazo_resposta: '' })
  const [sugestoes, setSugestoes] = useState([])
  const [destinatarios, setDestinatarios] = useState(null)
  const [buscandoDest, setBuscandoDest] = useState(false)
  const [arquivo, setArquivo] = useState(null)
  const [saving, setSaving] = useState(false)
  const [copiado, setCopiado] = useState(false)

  useEffect(() => {
    api.get('/core/catalogo/familias/').then(({ data }) => setSugestoes(data)).catch(() => {})
  }, [])

  useEffect(() => {
    const familia = form.familia_simpas.trim()
    if (!familia) { setDestinatarios(null); return }
    setBuscandoDest(true)
    const t = setTimeout(() => {
      api.get('/fornecedores/', { params: { familia, ativos: 'true', page_size: 100 } })
        .then(({ data }) => setDestinatarios(data.results ?? data))
        .catch(() => setDestinatarios([]))
        .finally(() => setBuscandoDest(false))
    }, 400)
    return () => clearTimeout(t)
  }, [form.familia_simpas])

  const handleSave = async () => {
    if (!form.familia_simpas.trim() || !form.prazo_resposta) return
    setSaving(true)
    try {
      let payload
      if (arquivo) {
        payload = new FormData()
        payload.append('familia_simpas', form.familia_simpas.trim())
        payload.append('data_envio', form.data_envio)
        payload.append('prazo_resposta', form.prazo_resposta)
        if (form.fonte) payload.append('fonte', form.fonte)
        payload.append('email_enviado_pdf', arquivo)
      } else {
        payload = { ...form, familia_simpas: form.familia_simpas.trim(), fonte: form.fonte || null }
      }
      await onSave(payload)
      setForm({ fonte: '', familia_simpas: '', data_envio: hoje, prazo_resposta: '' })
      setDestinatarios(null)
      setArquivo(null)
    } finally { setSaving(false) }
  }

  const emails = (destinatarios || []).map(f => f.email).filter(Boolean)
  const copiarEmails = () => {
    navigator.clipboard.writeText(emails.join('; ')).then(() => {
      setCopiado(true); setTimeout(() => setCopiado(false), 2000)
    })
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div className="col-span-3 sm:col-span-1">
        <label className="block text-xs font-medium text-gray-600 mb-1">Família SIMPAS *</label>
        <input list="familias-disparo" value={form.familia_simpas}
          onChange={(e) => setForm(p => ({ ...p, familia_simpas: e.target.value }))}
          placeholder="Ex: 42.40"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <datalist id="familias-disparo">
          {sugestoes.map((f) => <option key={f} value={f} />)}
        </datalist>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Data de envio *</label>
        <input type="date" value={form.data_envio}
          onChange={(e) => setForm(p => ({ ...p, data_envio: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Prazo para resposta *</label>
        <input type="date" value={form.prazo_resposta}
          onChange={(e) => setForm(p => ({ ...p, prazo_resposta: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      {form.familia_simpas.trim() && (
        <div className="col-span-3 bg-white border border-gray-200 rounded-lg p-3">
          {buscandoDest ? (
            <p className="text-xs text-gray-400">Buscando fornecedores da família...</p>
          ) : (destinatarios || []).length === 0 ? (
            <p className="text-xs text-orange-600">
              Nenhum fornecedor cadastrado com a família "{form.familia_simpas}" ainda —
              cadastre/taguear fornecedores em Fornecedores antes de disparar.
            </p>
          ) : (
            <>
              <p className="text-xs text-gray-600 mb-1.5">
                <strong>{destinatarios.length}</strong> fornecedor(es) serão destinatários deste disparo:
              </p>
              <p className="text-xs text-gray-500 max-h-20 overflow-y-auto">
                {destinatarios.map(f => f.nome_razao_social).join(', ')}
              </p>
              {emails.length > 0 && (
                <button type="button" onClick={copiarEmails}
                  className="mt-2 text-xs text-blue-600 hover:underline">
                  {copiado ? '✓ Copiado!' : `Copiar ${emails.length} e-mail(s) para BCC`}
                </button>
              )}
            </>
          )}
        </div>
      )}

      {fontes.length > 0 && (
        <div className="col-span-3">
          <label className="block text-xs font-medium text-gray-600 mb-1">Vincular à fonte (Parâmetro V)</label>
          <select value={form.fonte} onChange={(e) => setForm(p => ({ ...p, fonte: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Sem vínculo</option>
            {fontes.map(f => <option key={f.id} value={f.id}>{f.descricao.slice(0, 60)}</option>)}
          </select>
        </div>
      )}
      <div className="col-span-3">
        <label className="block text-xs font-medium text-gray-600 mb-1">Comprovante do e-mail enviado (PDF, opcional agora — obrigatório pelo Art. 7º, IV)</label>
        <input type="file" accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => setArquivo(e.target.files[0] || null)}
          className="w-full text-xs text-gray-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
        {arquivo && <p className="text-xs text-green-700 mt-0.5">📄 {arquivo.name}</p>}
      </div>
      <div className="col-span-3">
        <button onClick={handleSave}
          disabled={saving || !form.familia_simpas.trim() || !form.prazo_resposta}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
          {saving ? 'Salvando...' : 'Registrar disparo'}
        </button>
      </div>
    </div>
  )
}

function SolicitacaoCard({ sol, isEditavel, onEncerrar, onDelete, onAddResposta, onUpdateResposta, onDeleteResposta }) {
  const [showRespostaForm, setShowRespostaForm] = useState(false)
  const hoje = new Date().toISOString().split('T')[0]
  const vencido = !sol.encerrada && sol.prazo_resposta && sol.prazo_resposta < hoje

  return (
    <div className={`p-4 rounded-xl border ${vencido ? 'border-orange-300 bg-orange-50' : 'border-gray-200 bg-white'}`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded-full">
              Família {sol.familia_simpas}
            </span>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${sol.encerrada ? 'bg-gray-200 text-gray-600' : 'bg-green-100 text-green-700'}`}>
              {sol.encerrada ? 'Encerrado' : 'Aberto'}
            </span>
            {vencido && <span className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded-full">Prazo vencido</span>}
          </div>
          <p className="text-xs text-gray-400">
            Enviado em {new Date(sol.data_envio + 'T00:00:00').toLocaleDateString('pt-BR')}
            {' · '}Prazo: {new Date(sol.prazo_resposta + 'T00:00:00').toLocaleDateString('pt-BR')}
            {' · '}{sol.qtd_respostas} resposta(s)
          </p>
          {sol.email_enviado_pdf_url && (
            <a href={sol.email_enviado_pdf_url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">📄 Comprovante de envio</a>
          )}
        </div>
        {isEditavel && (
          <div className="flex flex-col items-end gap-1 shrink-0 ml-4">
            <button onClick={() => setShowRespostaForm(v => !v)} className="text-xs text-green-700 hover:underline">+ Resposta</button>
            {!sol.encerrada && <button onClick={onEncerrar} className="text-xs text-gray-500 hover:underline">Encerrar disparo</button>}
            <button onClick={onDelete} className="text-xs text-red-500 hover:text-red-700">Remover</button>
          </div>
        )}
      </div>

      {showRespostaForm && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <RespostaForm
            familia={sol.familia_simpas}
            onSave={async (payload) => { await onAddResposta(payload); setShowRespostaForm(false) }}
          />
        </div>
      )}

      {(sol.respostas || []).length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
          {sol.respostas.map((r) => (
            <RespostaRow key={r.id} resp={r} isEditavel={isEditavel}
              onUpdate={(payload) => onUpdateResposta(r.id, payload)}
              onDelete={() => onDeleteResposta(r.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function RespostaForm({ familia, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({ fornecedor: null, valor_respondido: '', recusou: false, data_resposta: hoje })
  const [fornecedorLabel, setFornecedorLabel] = useState('')
  const [arquivo, setArquivo] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.fornecedor || !form.data_resposta) return
    setSaving(true)
    try {
      let payload
      if (arquivo) {
        payload = new FormData()
        payload.append('fornecedor', form.fornecedor)
        payload.append('recusou', form.recusou ? 'true' : 'false')
        if (form.valor_respondido) payload.append('valor_respondido', form.valor_respondido)
        payload.append('data_resposta', form.data_resposta)
        payload.append('resposta_pdf', arquivo)
      } else {
        payload = {
          fornecedor: form.fornecedor, recusou: form.recusou, data_resposta: form.data_resposta,
          valor_respondido: form.valor_respondido ? Number(form.valor_respondido) : null,
        }
      }
      await onSave(payload)
      setForm({ fornecedor: null, valor_respondido: '', recusou: false, data_resposta: hoje })
      setFornecedorLabel(''); setArquivo(null)
    } finally { setSaving(false) }
  }

  return (
    <div className="grid grid-cols-2 gap-2 bg-gray-50 rounded-lg p-3">
      <div className="col-span-2">
        <label className="block text-xs text-gray-500 mb-1">Fornecedor *</label>
        <FornecedorPicker
          value={form.fornecedor}
          valueLabel={fornecedorLabel}
          extraParams={{ familia }}
          onChange={(fid, fornecedor) => {
            setForm(p => ({ ...p, fornecedor: fid }))
            setFornecedorLabel(fornecedor ? `${fornecedor.documento} — ${fornecedor.nome_razao_social}` : '')
          }}
        />
      </div>
      <div className="flex items-center gap-2">
        <input type="checkbox" id={`recusou-${familia}`} checked={form.recusou}
          onChange={(e) => setForm(p => ({ ...p, recusou: e.target.checked }))} className="accent-red-500" />
        <label htmlFor={`recusou-${familia}`} className="text-xs text-gray-600">Fornecedor recusou</label>
      </div>
      <div>
        <label className="block text-xs text-gray-500 mb-1">Data da resposta *</label>
        <input type="date" value={form.data_resposta}
          onChange={(e) => setForm(p => ({ ...p, data_resposta: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
      </div>
      {!form.recusou && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Valor unitário cotado (R$)</label>
          <CampoMoeda value={form.valor_respondido} onChange={(v) => setForm(p => ({ ...p, valor_respondido: v }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
      )}
      <div>
        <label className="block text-xs text-gray-500 mb-1">Proposta/cotação recebida (PDF)</label>
        <input type="file" accept=".pdf,.png,.jpg,.jpeg"
          onChange={(e) => setArquivo(e.target.files[0] || null)}
          className="w-full text-xs text-gray-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
      </div>
      <div className="col-span-2 flex justify-end">
        <button onClick={handleSave} disabled={saving || !form.fornecedor}
          className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-1.5 rounded-lg">
          {saving ? 'Salvando...' : 'Registrar resposta'}
        </button>
      </div>
    </div>
  )
}

function RespostaRow({ resp, isEditavel, onUpdate, onDelete }) {
  const [showJustificativa, setShowJustificativa] = useState(false)
  const [justificativa, setJustificativa] = useState(resp.justificativa_escolha || '')
  const [saving, setSaving] = useState(false)

  const toggleEscolhida = async () => {
    if (!resp.escolhida && !justificativa.trim()) { setShowJustificativa(true); return }
    setSaving(true)
    try { await onUpdate({ escolhida: !resp.escolhida, justificativa_escolha: justificativa }) }
    finally { setSaving(false); setShowJustificativa(false) }
  }

  return (
    <div className={`p-2.5 rounded-lg border text-sm ${resp.escolhida ? 'border-green-300 bg-green-50' : 'border-gray-100 bg-white'}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium text-gray-800">
            {resp.fornecedor_nome}
            {resp.escolhida && <span className="ml-2 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Referência</span>}
            {resp.recusou && <span className="ml-2 text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full">Recusou</span>}
          </p>
          <p className="text-xs text-gray-500">{resp.fornecedor_cnpj} · {resp.fornecedor_email}</p>
          <p className="text-xs text-gray-400">Respondeu em {new Date(resp.data_resposta + 'T00:00:00').toLocaleDateString('pt-BR')}</p>
          {!resp.recusou && resp.valor_respondido && (
            <p className="text-sm font-semibold text-green-700 mt-0.5">
              {Number(resp.valor_respondido).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </p>
          )}
          {resp.resposta_pdf_url && (
            <a href={resp.resposta_pdf_url} target="_blank" rel="noreferrer" className="text-xs text-blue-600 hover:underline">📄 Proposta recebida</a>
          )}
        </div>
        {isEditavel && (
          <div className="flex flex-col items-end gap-1 shrink-0 ml-3">
            {!resp.recusou && (
              <button onClick={toggleEscolhida} disabled={saving} className="text-xs text-green-700 hover:underline">
                {resp.escolhida ? 'Desmarcar referência' : 'Usar como referência'}
              </button>
            )}
            <button onClick={onDelete} className="text-xs text-red-500 hover:text-red-700">Remover</button>
          </div>
        )}
      </div>
      {showJustificativa && (
        <div className="mt-2 pt-2 border-t border-gray-100">
          <label className="block text-xs text-gray-500 mb-1">Justificativa da escolha (Art. 3º, VII) *</label>
          <textarea rows={2} value={justificativa} onChange={(e) => setJustificativa(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
          <button onClick={toggleEscolhida} disabled={saving || !justificativa.trim()}
            className="mt-1.5 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1 rounded-lg">
            Confirmar
          </button>
        </div>
      )}
    </div>
  )
}

function PrecoForm({ itemId, fontes, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    fonte: '', valor_unitario: '', origem_orgao_empresa: '',
    numero_certame: '', data_referencia: hoje, observacao: '', fornecedor: null,
  })
  const [fornecedorLabel, setFornecedorLabel] = useState('')
  const [arquivo, setArquivo] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.fonte || !form.valor_unitario) return
    setSaving(true)
    try {
      let payload
      if (arquivo) {
        payload = new FormData()
        payload.append('fonte', form.fonte)
        payload.append('valor_unitario', form.valor_unitario)
        payload.append('origem_orgao_empresa', form.origem_orgao_empresa)
        payload.append('numero_certame', form.numero_certame)
        payload.append('data_referencia', form.data_referencia)
        payload.append('observacao', form.observacao)
        payload.append('arquivo', arquivo)
        if (form.fornecedor) payload.append('fornecedor', form.fornecedor)
      } else {
        payload = {
          ...form,
          valor_unitario: Number(form.valor_unitario),
          fonte: Number(form.fonte),
          fornecedor: form.fornecedor || null,
        }
      }
      await onSave(payload)
      setForm(p => ({ ...p, valor_unitario: '', origem_orgao_empresa: '', numero_certame: '', observacao: '', fornecedor: null }))
      setFornecedorLabel('')
      setArquivo(null)
    } finally { setSaving(false) }
  }

  return (
    <div className="bg-gray-50 rounded-lg p-3 mt-2">
      <p className="text-xs font-semibold text-gray-600 mb-2">+ Adicionar preço coletado</p>
      <div className="grid grid-cols-3 gap-2">
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1">Fonte *</label>
          <select value={form.fonte} onChange={(e) => setForm(p => ({ ...p, fonte: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
            <option value="">Selecione a fonte...</option>
            {fontes.filter(f => !f.infrutífera).map(f => (
              <option key={f.id} value={f.id}>[{f.tipo}] {f.descricao.slice(0,40)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Valor unitário (R$) *</label>
          <CampoMoeda value={form.valor_unitario}
            onChange={(v) => setForm(p => ({ ...p, valor_unitario: v }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="col-span-3">
          <label className="block text-xs text-gray-500 mb-1">Fornecedor cadastrado (opcional — verifica histórico com a administração)</label>
          <FornecedorPicker
            value={form.fornecedor}
            valueLabel={fornecedorLabel}
            onChange={(id, fornecedor) => {
              setForm(p => ({ ...p, fornecedor: id }))
              setFornecedorLabel(fornecedor ? `${fornecedor.documento} — ${fornecedor.nome_razao_social}` : '')
            }}
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Órgão / Empresa origem</label>
          <input type="text" value={form.origem_orgao_empresa}
            onChange={(e) => setForm(p => ({ ...p, origem_orgao_empresa: e.target.value }))}
            placeholder="Ex: PMMG, CNPJ 12.345.678/0001-00"
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Certame / Processo</label>
          <input type="text" value={form.numero_certame}
            onChange={(e) => setForm(p => ({ ...p, numero_certame: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Data referência *</label>
          <input type="date" value={form.data_referencia}
            onChange={(e) => setForm(p => ({ ...p, data_referencia: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="col-span-3">
          <label className="block text-xs text-gray-500 mb-1">Documento comprobatório (PDF/imagem, opcional)</label>
          <input type="file" accept=".pdf,.png,.jpg,.jpeg"
            onChange={(e) => setArquivo(e.target.files[0] || null)}
            className="w-full text-xs text-gray-600 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
          {arquivo && <p className="text-xs text-green-700 mt-0.5">📄 {arquivo.name}</p>}
        </div>
        <div className="col-span-3 flex justify-end">
          <button onClick={handleSave} disabled={saving || !form.fonte || !form.valor_unitario}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-1.5 rounded-lg">
            {saving ? '...' : 'Registrar preço'}
          </button>
        </div>
      </div>
    </div>
  )
}
