import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useLicitacaoStore from '../stores/licitacaoStore'
import useAuthStore from '../stores/authStore'
import LoadingSpinner from '../components/LoadingSpinner'
import { downloadFile } from '../services/api'
import DownloadButton from '../components/DownloadButton'
import HelpTip from '../components/HelpTip'
import CampoSei, { NumeroSeiTexto } from '../components/CampoSei'
import FornecedorPicker from '../components/FornecedorPicker'
import CampoMoeda from '../components/CampoMoeda'

const fmt = v => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtPct = v => v != null ? `${Number(v).toFixed(1)}%` : '—'

const STATUS_CLS = {
  'Em Instrução':         'bg-gray-100 text-gray-600',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-800',
  'Aprovado':             'bg-teal-100 text-teal-700',
  'Publicado':            'bg-blue-100 text-blue-700',
  'Em Sessão':            'bg-indigo-100 text-indigo-700',
  'Homologado':           'bg-green-100 text-green-700',
  'Contratado':           'bg-green-200 text-green-800',
  'Deserto':              'bg-red-100 text-red-600',
  'Fracassado':           'bg-red-100 text-red-700',
  'Revogado':             'bg-gray-200 text-gray-500',
  'Anulado':              'bg-gray-200 text-gray-500',
}

const PECA_STATUS_CLS = {
  ok: 'bg-green-100 text-green-700',
  pendente: 'bg-yellow-100 text-yellow-700',
  erro: 'bg-red-100 text-red-600',
}

const ORGAOS_EXTERNOS = [
  { value: 'PGE',       label: 'PGE — Procuradoria Geral do Estado' },
  { value: 'SAEB',      label: 'SAEB — Secretaria de Administração' },
  { value: 'CasaCivil', label: 'Casa Civil' },
  { value: 'SEFAZ',     label: 'SEFAZ — Secretaria da Fazenda' },
  { value: 'TCE',       label: 'TCE — Tribunal de Contas do Estado' },
  { value: 'CGE',       label: 'CGE — Controladoria Geral' },
  { value: 'outro',     label: 'Outro' },
]

const TIPO_TRAM = [
  { value: 'aprovacao_juridica',  label: 'Aprovação jurídica' },
  { value: 'aprovacao_tecnica',   label: 'Aprovação técnica' },
  { value: 'consulta',            label: 'Consulta/parecer' },
  { value: 'anuencia',            label: 'Anuência prévia' },
  { value: 'registro',            label: 'Registro/publicação' },
  { value: 'outro',               label: 'Outro' },
]

const TRAM_STATUS_CLS = {
  Retornado: 'bg-green-100 text-green-700',
  Atrasado:  'bg-red-100 text-red-700',
  Pendente:  'bg-yellow-100 text-yellow-700',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Procedimento Licitatório — Detalhe',
  descricao: 'Gerencie as etapas, peças instrutórias e tramitações de um procedimento licitatório ou contratação direta conforme a Lei 14.133/2021.',
  acoes: [
    { label: 'Submeter',      texto: 'Envia o procedimento para análise da unidade licitante. Após submeter, o documento não pode ser editado sem devolução.' },
    { label: 'Aprovar',       texto: 'Aprova o procedimento internamente e libera para publicação no PNCP/DOU. Disponível para gestores e ordenadores.' },
    { label: 'Devolver',      texto: 'Retorna o procedimento para ajustes com justificativa obrigatória. O responsável receberá notificação.' },
    { label: 'Publicar',      texto: 'Registra a publicação oficial no PNCP ou diário oficial. Informe a data e o veículo de publicação.' },
    { label: 'Iniciar Sessão',texto: 'Marca o início da sessão pública de abertura de propostas. A data de sessão deve estar preenchida.' },
    { label: 'Homologar',     texto: 'Confirma o resultado da sessão pública e habilita a geração do contrato. Use após registrar o resultado por lote.' },
    { label: 'Deserto',       texto: 'Declara o procedimento deserto por ausência de propostas válidas.' },
    { label: 'Fracassado',    texto: 'Declara o procedimento fracassado quando nenhuma proposta atende os requisitos.' },
    { label: 'Revogar',       texto: 'Encerra o procedimento por interesse público superveniente, com justificativa. Ato irreversível.' },
    { label: '+ Tramitação',  texto: 'Registra envio a órgão externo (PGE, SAEB, TCE-BA, CGE, etc.) para parecer jurídico, técnico ou anuência prévia. Informe o prazo de retorno.' },
    { label: '+ Resultado',   texto: 'Lança o resultado por lote: empresa vencedora, CNPJ, valor homologado. Necessário antes de homologar.' },
    { label: 'Nº controle PNCP / Valor publicado', texto: 'Registre manualmente o identificador e o valor exibidos na página pública do PNCP após a publicação — o sistema alerta se o valor publicado divergir do valor estimado deste procedimento em mais de 1%.' },
  ],
  fluxo: [
    { status: 'Em Instrução',         descricao: 'Procedimento em montagem. Peças instrutórias sendo anexadas.' },
    { status: 'Aguardando Aprovação', descricao: 'Submetido. Aguarda análise da unidade licitante.' },
    { status: 'Aprovado',             descricao: 'Aprovado internamente. Pronto para publicação.' },
    { status: 'Publicado',            descricao: 'Publicado no PNCP/DOU. Prazo de impugnação em curso.' },
    { status: 'Em Sessão',            descricao: 'Sessão pública iniciada. Propostas sendo analisadas.' },
    { status: 'Homologado',           descricao: 'Resultado homologado. Contrato pode ser gerado.' },
    { status: 'Contratado',           descricao: 'Contrato assinado e vigente.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Arts. 17 a 90 (licitações) e Arts. 72 a 90 (contratações diretas).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ProcedimentoDetail() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const papel       = useAuthStore(s => s.papel)
  const tipoUnidade = useAuthStore(s => s.tipoUnidade)
  const seiBaseUrl  = useAuthStore(s => s.seiBaseUrl)

  const {
    current, loading, error,
    fetchProcedimento, updateProcedimento, deleteProcedimento,
    submeter, aprovar, devolver, publicar, iniciarSessao,
    homologar, declararDeserto, declararFracassado, revogar, anular,
    addTramitacao, updateTramitacao, deleteTramitacao,
    addResultado, updateResultado, deleteResultado, gerarContrato,
    aprovarPeca, devolverPeca,
  } = useLicitacaoStore()

  const [activeTab,  setActiveTab]   = useState('visao_geral')
  const [actionMsg,  setActionMsg]   = useState(null)
  const [saving,     setSaving]      = useState(false)
  const [motivoModal, setMotivoModal] = useState(null) // {acao, label}
  const [motivoText,  setMotivoText]  = useState('')
  const [editingMain, setEditingMain] = useState(false)
  const [devolverPecaModal, setDevolverPecaModal] = useState(null) // {tipo, pk, label}
  const [motivoPeca, setMotivoPeca]   = useState('')
  const [editForm,    setEditForm]    = useState({})

  // Tramitação
  const [showTramForm, setShowTramForm] = useState(false)
  const [tramForm, setTramForm] = useState({
    orgao_externo: '', orgao_descricao: '', tipo: '', numero_sei: '',
    data_envio: new Date().toISOString().split('T')[0], prazo_esperado: '', observacoes: '',
  })
  const [editingTram, setEditingTram] = useState(null)

  // Resultado
  const [showResForm, setShowResForm] = useState(false)
  const [resForm, setResForm] = useState({
    lote: '', descricao_lote: '', resultado: 'homologado',
    fornecedor: null, empresa_vencedora: '', cnpj_vencedor: '',
    valor_estimado: '', valor_final: '', observacoes: '',
  })
  const [resFornecedorLabel, setResFornecedorLabel] = useState('')

  useEffect(() => { fetchProcedimento(id) }, [id])
  useEffect(() => {
    if (current) setEditForm({
      objeto: current.objeto,
      numero_sei: current.numero_sei || '',
      valor_estimado: current.valor_estimado || '',
      data_publicacao: current.data_publicacao || '',
      data_abertura: current.data_abertura || '',
      numero_controle_pncp: current.numero_controle_pncp || '',
      valor_publicado_pncp: current.valor_publicado_pncp || '',
      observacoes: current.observacoes || '',
    })
  }, [current])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando procedimento..." /></div>
  if (error)   return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current) return null

  const act = async (fn, ...args) => {
    setSaving(true)
    setActionMsg(null)
    try {
      await fn(...args)
      setActionMsg({ type: 'success', text: 'Operação realizada com sucesso.' })
    } catch (e) {
      const msg = e.response?.data?.detail || e.response?.data?.non_field_errors?.[0] || 'Erro na operação.'
      setActionMsg({ type: 'error', text: msg })
    } finally {
      setSaving(false) }
  }

  const handleMotivoConfirm = async () => {
    if (!motivoText.trim()) return
    setMotivoModal(null)
    const fn = {
      devolver: () => act(devolver, id, motivoText),
      revogar:  () => act(revogar,  id, motivoText),
      anular:   () => act(anular,   id, motivoText),
      deserto:  () => act(declararDeserto,    id, motivoText),
      fracassado: () => act(declararFracassado, id, motivoText),
    }[motivoModal?.acao]
    fn?.()
    setMotivoText('')
  }

  const handleSaveMain = async () => {
    setSaving(true)
    try {
      await updateProcedimento(id, editForm)
      setEditingMain(false)
      setActionMsg({ type: 'success', text: 'Salvo.' })
    } catch { setActionMsg({ type: 'error', text: 'Erro ao salvar.' }) }
    finally { setSaving(false) }
  }

  const handleAddTramitacao = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await addTramitacao(id, tramForm)
      setShowTramForm(false)
      setTramForm({ orgao_externo: '', orgao_descricao: '', tipo: '',
        numero_sei: '', data_envio: new Date().toISOString().split('T')[0],
        prazo_esperado: '', observacoes: '' })
    } catch (e) { setActionMsg({ type: 'error', text: e.response?.data?.detail || 'Erro.' }) }
    finally { setSaving(false) }
  }

  const handleRegistrarRetorno = async (tram) => {
    await act(updateTramitacao, id, tram.id, { data_retorno: new Date().toISOString().split('T')[0] })
  }

  const handleAddResultado = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = { ...resForm }
      if (payload.lote) payload.lote = Number(payload.lote)
      if (payload.valor_estimado) payload.valor_estimado = Number(payload.valor_estimado)
      if (payload.valor_final)    payload.valor_final    = Number(payload.valor_final)
      await addResultado(id, payload)
      setShowResForm(false)
      setResForm({ lote: '', descricao_lote: '', resultado: 'homologado',
        fornecedor: null, empresa_vencedora: '', cnpj_vencedor: '', valor_estimado: '', valor_final: '', observacoes: '' })
      setResFornecedorLabel('')
    } catch (e) { setActionMsg({ type: 'error', text: e.response?.data?.detail || 'Erro.' }) }
    finally { setSaving(false) }
  }

  const transicoes  = current.transicoes_disponiveis || []
  const isLicitante = papel === 'admin' || (tipoUnidade === 'licitante' &&
    ['analista', 'gestor_contrato', 'ordenador', 'admin'].includes(papel))
  const podeAprovar = isLicitante

  const TABS = [
    { key: 'visao_geral',    label: 'Visão Geral' },
    { key: 'pecas',          label: `Peças Instrutórias (${(current.pecas_instutorias || []).length})` },
    { key: 'tramitacoes',    label: `Tramitações (${(current.tramitacoes || []).length})` },
    { key: 'resultados',     label: `Resultados (${(current.resultados || []).length})` },
    { key: 'historico',      label: `Histórico (${(current.historico || []).length})` },
  ]

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || 'bg-gray-100 text-gray-600'}`}>
              {current.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-0.5">
            {current.modalidade_display} · Exercício {current.exercicio}
            {current.unidade_gestora_sigla && (
              <span className="ml-2 px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs font-mono">
                {current.unidade_gestora_sigla}
              </span>
            )}
          </p>
        </div>

        {/* Botões de ação contextuais */}
        <div className="flex gap-2 flex-wrap justify-end">
          <DownloadButton
              onClick={() => downloadFile(`/licitacao/procedimento/${id}/export/historico/`, `Relatorio_${current.numero}.pdf`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">
              ↓ Relatório Completo
            </DownloadButton>
          {transicoes.includes('Aguardando Aprovação') && isLicitante && (<>
            <button onClick={() => act(submeter, id)} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Submeter
            </button>
            <HelpTip text="Envia o procedimento para análise. Após submeter, não é possível editar sem devolução." />
          </>)}
          {transicoes.includes('Aprovado') && podeAprovar && (<>
            <button onClick={() => act(aprovar, id)} disabled={saving}
              className="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Aprovar
            </button>
            <HelpTip text="Aprova internamente e libera para publicação no PNCP/DOU." />
          </>)}
          {transicoes.includes('Em Instrução') && current.status === 'Aguardando Aprovação' && isLicitante && (<>
            <button onClick={() => { setMotivoModal({ acao: 'devolver', label: 'Devolver para instrução' }); setMotivoText('') }}
              className="border border-orange-300 text-orange-600 hover:bg-orange-50 text-sm px-3 py-1.5 rounded-lg">
              Devolver
            </button>
            <HelpTip text="Retorna para ajustes com justificativa obrigatória. O responsável receberá notificação." />
          </>)}
          {transicoes.includes('Publicado') && isLicitante && (<>
            <button onClick={() => act(publicar, id)} disabled={saving}
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Publicar edital
            </button>
            <HelpTip text="Registra a publicação oficial no PNCP ou diário oficial. Informe a data e o veículo." />
          </>)}
          {transicoes.includes('Em Sessão') && isLicitante && (<>
            <button onClick={() => act(iniciarSessao, id)} disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Iniciar Sessão
            </button>
            <HelpTip text="Marca o início da sessão pública de abertura de propostas. A data de sessão deve estar preenchida." />
          </>)}
          {transicoes.includes('Homologado') && isLicitante && (<>
            <button onClick={() => act(homologar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Homologar
            </button>
            <HelpTip text="Confirma o resultado da sessão pública e habilita a geração do contrato." />
          </>)}
          {/* Contratado direto (dispensas aprovadas) */}
          {transicoes.includes('Contratado') && current.status === 'Aprovado' && isLicitante && (
            <button onClick={() => act(homologar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-3 py-1.5 rounded-lg">
              Confirmar contratação
            </button>
          )}
          {transicoes.includes('Deserto') && isLicitante && (<>
            <button onClick={() => { setMotivoModal({ acao: 'deserto', label: 'Declarar Deserto' }); setMotivoText('Nenhuma proposta recebida.') }}
              className="border border-red-300 text-red-600 hover:bg-red-50 text-sm px-3 py-1.5 rounded-lg">
              Deserto
            </button>
            <HelpTip text="Declara o procedimento deserto por ausência de propostas válidas." />
          </>)}
          {transicoes.includes('Fracassado') && isLicitante && (<>
            <button onClick={() => { setMotivoModal({ acao: 'fracassado', label: 'Declarar Fracassado' }); setMotivoText('') }}
              className="border border-red-300 text-red-600 hover:bg-red-50 text-sm px-3 py-1.5 rounded-lg">
              Fracassado
            </button>
            <HelpTip text="Declara fracassado quando nenhuma proposta atende os requisitos editalícios." />
          </>)}
          {transicoes.includes('Revogado') && isLicitante && (<>
            <button onClick={() => { setMotivoModal({ acao: 'revogar', label: 'Revogar' }); setMotivoText('') }}
              className="border border-gray-300 text-gray-500 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">
              Revogar
            </button>
            <HelpTip text="Encerra o procedimento por interesse público superveniente. Ato irreversível — exige justificativa." />
          </>)}
        </div>
      </div>

      {/* Alertas */}
      {current.alerta_prazo && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-300 rounded-xl p-3 text-sm text-red-800 mb-4">
          <span>⚠️</span><p>{current.alerta_prazo}</p>
        </div>
      )}
      {current.alerta_teto_dispensa && (
        <div className="flex items-start gap-2 bg-amber-50 border border-amber-300 rounded-xl p-3 text-sm text-amber-800 mb-4">
          <span>⚠️</span><p>{current.alerta_teto_dispensa}</p>
        </div>
      )}
      {actionMsg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${actionMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {actionMsg.text}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-5">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map(t => (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors ${
                activeTab === t.key
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Tab: Visão Geral ── */}
      {activeTab === 'visao_geral' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            {!editingMain
              ? <button onClick={() => setEditingMain(true)}
                  className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-3 py-1.5 rounded-lg">Editar</button>
              : <div className="flex gap-2">
                  <button onClick={handleSaveMain} disabled={saving}
                    className="bg-blue-600 text-white text-sm px-3 py-1.5 rounded-lg disabled:opacity-50">
                    {saving ? '...' : 'Salvar'}
                  </button>
                  <button onClick={() => setEditingMain(false)}
                    className="border border-gray-300 text-gray-600 text-sm px-3 py-1.5 rounded-lg">Cancelar</button>
                </div>}
          </div>

          {[
            ['Objeto', 'objeto', 'textarea'],
            ['Número SEI', 'numero_sei', 'text'],
            ['Valor estimado (R$)', 'valor_estimado', 'number'],
            ['Data de publicação', 'data_publicacao', 'date'],
            ['Data de abertura', 'data_abertura', 'date'],
            ['Nº de controle PNCP', 'numero_controle_pncp', 'text'],
            ['Valor publicado no PNCP (R$)', 'valor_publicado_pncp', 'number'],
            ['Observações', 'observacoes', 'textarea'],
          ].map(([label, key, type]) => (
            <div key={key}>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
              {editingMain
                ? key === 'numero_sei'
                  ? <CampoSei value={editForm[key] || ''} onChange={v => setEditForm(p => ({ ...p, [key]: v }))}
                      seiBaseUrl={seiBaseUrl}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                : type === 'textarea'
                  ? <textarea rows={3} value={editForm[key] || ''} onChange={e => setEditForm(p => ({ ...p, [key]: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  : <input type={type} value={editForm[key] || ''} onChange={e => setEditForm(p => ({ ...p, [key]: e.target.value }))}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                : key === 'numero_sei'
                  ? (current[key] ? <NumeroSeiTexto valor={current[key]} seiBaseUrl={seiBaseUrl} className="text-sm text-gray-700 font-mono" /> : <p className="text-sm text-gray-400">—</p>)
                : <p className="text-sm text-gray-700">
                    {['valor_estimado', 'valor_publicado_pncp'].includes(key) ? (current[key] != null ? fmt(current[key]) : <span className="text-gray-400">—</span>) : (current[key] ? (
                      ['data_publicacao','data_abertura'].includes(key)
                        ? new Date(current[key]+'T12:00').toLocaleDateString('pt-BR')
                        : current[key]
                    ) : <span className="text-gray-400">—</span>)}
                  </p>}
            </div>
          ))}
          {current.divergencia_valor_pncp && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
              <p className="text-sm font-semibold text-amber-800">⚠ Divergência de valor com o PNCP</p>
              <p className="text-xs text-amber-700 mt-0.5">
                O valor publicado no PNCP ({fmt(current.valor_publicado_pncp)}) diverge do valor estimado
                deste procedimento ({fmt(current.valor_estimado)}) em mais de 1%. Achado real do TCE/BA: ato de
                autorização com um valor, PNCP publicado com outro, sem explicação nos autos — confira e registre
                a justificativa no processo SEI se a diferença for legítima (ex.: parcela do objeto).
              </p>
            </div>
          )}

          {/* Info adicionais */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {current.unidade_gestora_sigla && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Unidade Gestora</p>
                <p className="text-sm text-gray-700">
                  <span className="font-mono font-semibold">{current.unidade_gestora_sigla}</span>
                  {current.unidade_gestora_nome && (
                    <span className="text-gray-500 ml-1">— {current.unidade_gestora_nome}</span>
                  )}
                </p>
              </div>
            )}
            {current.dfd_numero_sei && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">DFD de Origem</p>
                <p className="text-sm font-mono text-blue-700">{current.dfd_numero_sei}</p>
              </div>
            )}
            {current.tr_numero_sei && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">TR de Origem</p>
                <p className="text-sm font-mono text-blue-700">{current.tr_numero_sei}</p>
              </div>
            )}
            {current.prazo_minimo_dias_uteis > 0 && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Prazo mínimo legal</p>
                <p className="text-sm text-gray-700">{current.prazo_minimo_dias_uteis} dias úteis</p>
              </div>
            )}
            {current.dias_ate_abertura != null && (
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Dias até a abertura</p>
                <p className={`text-sm font-semibold ${current.dias_ate_abertura < 0 ? 'text-red-600' : current.dias_ate_abertura <= 5 ? 'text-orange-600' : 'text-gray-700'}`}>
                  {current.dias_ate_abertura < 0 ? `${Math.abs(current.dias_ate_abertura)} dias atrás` : `${current.dias_ate_abertura} dias`}
                </p>
              </div>
            )}
          </div>

          {current.justificativa && (
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Justificativa (contratação direta)</p>
              <p className="text-sm text-gray-700 whitespace-pre-line text-justify">{current.justificativa}</p>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Peças Instrutórias ── */}
      {activeTab === 'pecas' && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            Acompanhe e aprove as peças instrutórias diretamente deste painel.
            {isLicitante && ' Como Unidade Licitante, você pode aprovar ou devolver cada documento.'}
          </p>

          {(current.pecas_instutorias || []).length === 0 ? (
            <p className="text-sm text-gray-400 italic">Nenhum DFD vinculado a este procedimento.</p>
          ) : (
            <div className="space-y-2">
              {current.pecas_instutorias.map((p, i) => {
                const tipoPeca = p.tipo === 'ETP' ? 'etp' : p.tipo === 'TR' ? 'tr' : p.tipo === 'Mapa de Preços' ? 'mapa' : null
                return (
                  <div key={i} className={`rounded-xl border ${p.ok ? 'border-green-200 bg-green-50' : p.status === 'Devolvido' ? 'border-red-200 bg-red-50' : 'border-yellow-200 bg-yellow-50'}`}>
                    <div className="flex items-center justify-between px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className="text-lg">
                          {p.ok ? '✅' : p.status === 'Devolvido' ? '↩️' : '⏳'}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-gray-800">{p.tipo}</p>
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-mono text-gray-500">{p.numero_sei}</p>
                            {p.url && (
                              <button onClick={() => window.open(p.url, '_self')}
                                className="text-[10px] text-blue-600 hover:underline">
                                Ver documento →
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          p.ok ? 'bg-green-100 text-green-700'
                          : p.status === 'Devolvido' ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                        }`}>{p.status}</span>

                        {/* Botões de aprovação — apenas licitante + peças com pk */}
                        {isLicitante && tipoPeca && p.pk && (
                          <div className="flex gap-1.5 ml-2">
                            {p.pode_aprovar && (
                              <button
                                disabled={saving}
                                onClick={() => act(aprovarPeca, id, tipoPeca, p.pk)}
                                className="text-xs bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white px-2.5 py-1 rounded-lg font-medium">
                                Aprovar
                              </button>
                            )}
                            {p.pode_devolver && (
                              <button
                                disabled={saving}
                                onClick={() => { setDevolverPecaModal({ tipo: tipoPeca, pk: p.pk, label: p.tipo }); setMotivoPeca('') }}
                                className="text-xs border border-orange-300 text-orange-600 hover:bg-orange-50 px-2.5 py-1 rounded-lg font-medium">
                                Devolver
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}

              {current.pecas_instutorias.every(p => p.ok) && (
                <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-sm text-green-800 font-medium">
                  ✅ Todas as peças estão aprovadas. O procedimento pode ser publicado.
                </div>
              )}
              {!current.pecas_instutorias.every(p => p.ok) && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3 text-sm text-yellow-800">
                  ⚠️ Existem peças pendentes de aprovação.
                  {!isLicitante && ' Acesse cada documento para submeter à análise.'}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Modal devolução de peça */}
      {devolverPecaModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">
              Devolver {devolverPecaModal.label}
            </h3>
            <label className="block text-xs font-medium text-gray-600 mb-1 mt-3">Motivo *</label>
            <textarea rows={3} value={motivoPeca} onChange={e => setMotivoPeca(e.target.value)}
              placeholder="Descreva os ajustes necessários..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 mb-4" />
            <div className="flex gap-2">
              <button
                disabled={!motivoPeca.trim() || saving}
                onClick={async () => {
                  setSaving(true)
                  setActionMsg(null)
                  try {
                    await devolverPeca(id, devolverPecaModal.tipo, devolverPecaModal.pk, motivoPeca)
                    setDevolverPecaModal(null)
                    setMotivoPeca('')
                    setActionMsg({ type: 'success', text: `${devolverPecaModal.label} devolvido com sucesso.` })
                  } catch (e) {
                    setActionMsg({ type: 'error', text: e.response?.data?.detail || 'Erro ao devolver.' })
                  } finally { setSaving(false) }
                }}
                className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? '...' : 'Confirmar devolução'}
              </button>
              <button onClick={() => { setDevolverPecaModal(null); setMotivoPeca('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Tab: Tramitações Externas ── */}
      {activeTab === 'tramitacoes' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button onClick={() => setShowTramForm(v => !v)}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-3 py-1.5 rounded-lg">
              {showTramForm ? 'Cancelar' : '+ Registrar tramitação'}
            </button>
          </div>

          {showTramForm && (
            <form onSubmit={handleAddTramitacao} className="border border-blue-200 bg-blue-50 rounded-xl p-4 space-y-3">
              <p className="text-sm font-semibold text-blue-800">Nova Tramitação Externa</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Órgão externo *</label>
                  <select value={tramForm.orgao_externo} required
                    onChange={e => setTramForm(p => ({ ...p, orgao_externo: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs">
                    <option value="">Selecione...</option>
                    {ORGAOS_EXTERNOS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Tipo *</label>
                  <select value={tramForm.tipo} required
                    onChange={e => setTramForm(p => ({ ...p, tipo: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs">
                    <option value="">Selecione...</option>
                    {TIPO_TRAM.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Data de envio *</label>
                  <input type="date" value={tramForm.data_envio} required
                    onChange={e => setTramForm(p => ({ ...p, data_envio: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Prazo esperado</label>
                  <input type="date" value={tramForm.prazo_esperado}
                    onChange={e => setTramForm(p => ({ ...p, prazo_esperado: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Nº SEI da tramitação</label>
                  <CampoSei value={tramForm.numero_sei}
                    onChange={v => setTramForm(p => ({ ...p, numero_sei: v }))}
                    seiBaseUrl={seiBaseUrl}
                    placeholder="099.8188.2025.0027815-30"
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Observações</label>
                  <input type="text" value={tramForm.observacoes}
                    onChange={e => setTramForm(p => ({ ...p, observacoes: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                </div>
              </div>
              <button type="submit" disabled={saving}
                className="bg-blue-600 text-white text-xs font-medium px-4 py-1.5 rounded-lg disabled:opacity-50">
                {saving ? '...' : 'Registrar'}
              </button>
            </form>
          )}

          {(current.tramitacoes || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhuma tramitação registrada.</p>
            : (
              <div className="space-y-2">
                {current.tramitacoes.map(t => (
                  <div key={t.id} className="border border-gray-200 rounded-xl p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TRAM_STATUS_CLS[t.status] || 'bg-gray-100 text-gray-600'}`}>
                          {t.status}
                        </span>
                        <span className="text-sm font-semibold text-gray-800">{t.orgao_label}</span>
                        <span className="text-xs text-gray-500">— {TIPO_TRAM.find(x => x.value === t.tipo)?.label || t.tipo}</span>
                      </div>
                      <div className="flex gap-2">
                        {!t.data_retorno && (
                          <button onClick={() => handleRegistrarRetorno(t)} disabled={saving}
                            className="text-xs text-green-600 hover:underline">Registrar retorno</button>
                        )}
                        <button onClick={() => act(deleteTramitacao, id, t.id)} disabled={saving}
                          className="text-xs text-red-400 hover:text-red-600">✕</button>
                      </div>
                    </div>
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-gray-500">
                      <span>Envio: {new Date(t.data_envio+'T12:00').toLocaleDateString('pt-BR')}</span>
                      <span>Prazo: {t.prazo_esperado ? new Date(t.prazo_esperado+'T12:00').toLocaleDateString('pt-BR') : '—'}</span>
                      <span>Retorno: {t.data_retorno ? new Date(t.data_retorno+'T12:00').toLocaleDateString('pt-BR') : '—'}</span>
                    </div>
                    {t.numero_sei && (
                      <p className="text-xs mt-1">SEI: <NumeroSeiTexto valor={t.numero_sei} seiBaseUrl={seiBaseUrl} className="font-mono text-blue-600" /></p>
                    )}
                    {t.observacoes && <p className="text-xs text-gray-500 mt-1">{t.observacoes}</p>}
                  </div>
                ))}
              </div>
            )}
        </div>
      )}

      {/* ── Tab: Resultados dos Lotes ── */}
      {activeTab === 'resultados' && (
        <div className="space-y-4">
          {['Homologado', 'Em Sessão', 'Aprovado'].some(s => current.status === s || current.status.includes(s)) && (
            <div className="flex justify-end">
              <button onClick={() => setShowResForm(v => !v)}
                className="bg-green-600 hover:bg-green-700 text-white text-sm px-3 py-1.5 rounded-lg">
                {showResForm ? 'Cancelar' : '+ Registrar resultado'}
              </button>
            </div>
          )}

          {showResForm && (
            <form onSubmit={handleAddResultado} className="border border-green-200 bg-green-50 rounded-xl p-4 space-y-3">
              <p className="text-sm font-semibold text-green-800">Resultado do Lote</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-600 mb-1">Descrição do lote *</label>
                  <input type="text" value={resForm.descricao_lote} required
                    onChange={e => setResForm(p => ({ ...p, descricao_lote: e.target.value }))}
                    placeholder="Ex: Lote 1 — Notebooks"
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Resultado *</label>
                  <select value={resForm.resultado} required
                    onChange={e => setResForm(p => ({ ...p, resultado: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs">
                    <option value="homologado">Homologado</option>
                    <option value="deserto">Deserto</option>
                    <option value="fracassado">Fracassado</option>
                    <option value="cancelado">Cancelado</option>
                  </select>
                </div>
                {resForm.resultado === 'homologado' && (
                  <>
                    <div className="col-span-2">
                      <label className="block text-xs font-medium text-gray-600 mb-1">Fornecedor cadastrado (opcional — verifica histórico com a administração)</label>
                      <FornecedorPicker
                        value={resForm.fornecedor}
                        valueLabel={resFornecedorLabel}
                        onChange={(fid, fornecedor) => {
                          setResForm(p => ({ ...p, fornecedor: fid }))
                          setResFornecedorLabel(fornecedor ? `${fornecedor.documento} — ${fornecedor.nome_razao_social}` : '')
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Empresa vencedora</label>
                      <input type="text" value={resForm.empresa_vencedora}
                        onChange={e => setResForm(p => ({ ...p, empresa_vencedora: e.target.value }))}
                        className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">CNPJ</label>
                      <input type="text" value={resForm.cnpj_vencedor}
                        onChange={e => setResForm(p => ({ ...p, cnpj_vencedor: e.target.value }))}
                        placeholder="00.000.000/0000-00"
                        className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Valor estimado (R$)</label>
                      <CampoMoeda value={resForm.valor_estimado}
                        onChange={v => setResForm(p => ({ ...p, valor_estimado: v }))}
                        className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Valor final adjudicado (R$)</label>
                      <CampoMoeda value={resForm.valor_final}
                        onChange={v => setResForm(p => ({ ...p, valor_final: v }))}
                        className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
                    </div>
                  </>
                )}
              </div>
              <button type="submit" disabled={saving}
                className="bg-green-600 text-white text-xs font-medium px-4 py-1.5 rounded-lg disabled:opacity-50">
                {saving ? '...' : 'Registrar resultado'}
              </button>
            </form>
          )}

          {(current.resultados || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhum resultado registrado ainda.</p>
            : (
              <div className="space-y-3">
                {current.resultados.map(r => (
                  <div key={r.id} className={`border rounded-xl p-4 ${r.resultado === 'homologado' ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}>
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{r.descricao_lote || `Resultado ${r.id}`}</p>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full mt-1 inline-block ${
                          r.resultado === 'homologado' ? 'bg-green-100 text-green-700'
                          : r.resultado === 'deserto' ? 'bg-red-100 text-red-600'
                          : 'bg-gray-100 text-gray-600'
                        }`}>{r.resultado_display}</span>
                      </div>
                      <div className="flex gap-2 items-center">
                        {r.resultado === 'homologado' && !r.contrato_gerado && (
                          <button onClick={() => act(gerarContrato, id, r.id)} disabled={saving}
                            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1 rounded-lg">
                            Gerar Contrato
                          </button>
                        )}
                        {r.contrato_numero && (
                          <span className="text-xs text-green-700 font-medium bg-green-100 px-2 py-0.5 rounded-full">
                            Contrato: {r.contrato_numero}
                          </span>
                        )}
                        <button onClick={() => act(deleteResultado, id, r.id)} disabled={saving}
                          className="text-xs text-red-400 hover:text-red-600">✕</button>
                      </div>
                    </div>
                    {r.resultado === 'homologado' && (
                      <div className="mt-2 grid grid-cols-4 gap-2 text-xs text-gray-600">
                        <span><strong>Empresa:</strong> {r.empresa_vencedora || '—'}</span>
                        <span><strong>CNPJ:</strong> {r.cnpj_vencedor || '—'}</span>
                        <span><strong>Estimado:</strong> {r.valor_estimado ? fmt(r.valor_estimado) : '—'}</span>
                        <span><strong>Final:</strong> {r.valor_final ? fmt(r.valor_final) : '—'}
                          {r.percentual_desconto != null && ` (${r.percentual_desconto > 0 ? '-' : '+'}${Math.abs(r.percentual_desconto)}%)`}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
        </div>
      )}

      {/* ── Tab: Histórico ── */}
      {activeTab === 'historico' && (
        <div className="space-y-2">
          {(current.historico || []).length === 0
            ? <p className="text-sm text-gray-400">Sem histórico.</p>
            : current.historico.map(h => (
              <div key={h.id} className="flex items-start gap-3 py-3 border-b border-gray-100 last:border-0">
                <span className="text-xs text-gray-400 shrink-0 w-36">
                  {new Date(h.criado_em).toLocaleString('pt-BR')}
                </span>
                <div>
                  <span className="text-sm font-medium text-gray-700">{h.usuario_nome}</span>
                  {' '}
                  {h.status_anterior && <><span className="text-gray-400 text-xs">{h.status_anterior} →</span>{' '}</>}
                  <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full ${STATUS_CLS[h.status_novo] || 'bg-gray-100 text-gray-600'}`}>{h.status_novo}</span>
                  {h.motivo && <p className="text-xs text-gray-500 mt-0.5">{h.motivo}</p>}
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Modal de motivo */}
      {motivoModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-3">{motivoModal.label}</h3>
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo *</label>
            <textarea rows={3} value={motivoText} onChange={e => setMotivoText(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button disabled={!motivoText.trim() || saving} onClick={handleMotivoConfirm}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? '...' : 'Confirmar'}
              </button>
              <button onClick={() => { setMotivoModal(null); setMotivoText('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
