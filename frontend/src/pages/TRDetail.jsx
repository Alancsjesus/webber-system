import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useTrStore from '../stores/trStore'
import useAuthStore from '../stores/authStore'
import api, { downloadFile } from '../services/api'
import DownloadButton from '../components/DownloadButton'
import ModalDevolver, { MOTIVOS_TR } from '../components/ModalDevolver'

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
  Cancelado:   'bg-red-100 text-red-700',
}

const PAPEIS_ANALISTA  = ['analista', 'gestor_contrato', 'fiscal_contrato', 'ordenador', 'admin']
const PAPEIS_SOLICITANTE = ['solicitante', 'demandante', 'responsavel_tecnico', 'admin']

export default function TRDetail() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const { current, loading, error, fetchTr, updateTr, submeterTr, iniciarAnaliseTr, aprovarTr, devolverTr, reabrirTr,
          criarLote, excluirLote, adicionarItemLote, removerItemLote, gerarCota, gerarPorItem } = useTrStore()
  const papel       = useAuthStore((s) => s.papel)
  const tipoUnidade = useAuthStore((s) => s.tipoUnidade)

  const isLicitante   = papel === 'admin' || (tipoUnidade === 'licitante' && PAPEIS_ANALISTA.includes(papel))
  const isSolicitante = PAPEIS_SOLICITANTE.includes(papel)

  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [showDevolver, setShowDevolver]   = useState(false)
  const [showReabrir, setShowReabrir]     = useState(false)
  const [motivo, setMotivo]               = useState('')
  const [motivoReabrir, setMotivoReabrir] = useState('')
  const [formErrors, setFormErrors]       = useState({})

  useEffect(() => { fetchTr(id) }, [id])
  useEffect(() => { if (current) setForm({ ...current }) }, [current])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setFormErrors((p) => ({ ...p, [field]: undefined }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateTr(id, {
        objeto_contratacao:     form.objeto_contratacao,
        justificativa:          form.justificativa,
        requisitos_contratacao: form.requisitos_contratacao,
        obrigacoes_contratada:  form.obrigacoes_contratada,
        obrigacoes_contratante: form.obrigacoes_contratante,
        criterios_selecao:      form.criterios_selecao,
        criterios_medicao:      form.criterios_medicao,
        tipo_prazo_vigencia:    form.tipo_prazo_vigencia,
        prazo_meses:            form.prazo_meses ? Number(form.prazo_meses) : null,
        instrumento_inicio:     form.instrumento_inicio,
        prazo_observacao:       form.prazo_observacao,
        local_entrega:          form.local_entrega,
        garantia_contrato:      form.garantia_contrato,
        estimativa_valor:       form.estimativa_valor ? Number(form.estimativa_valor) : null,
        observacoes:            form.observacoes,
      })
      setEditing(false)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setFormErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const doAction = async (fn) => {
    setActionLoading(true)
    try {
      await fn()
      await fetchTr(id)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDevolver = async (motivo, categoria) => {
    await doAction(() => devolverTr(id, motivo, categoria))
    setShowDevolver(false)
  }

  if (loading) return <p className="p-8 text-sm text-gray-400">Carregando...</p>
  if (error)   return <p className="p-8 text-sm text-red-600">{error}</p>
  if (!current || !form) return null

  const statusLoteEditavel = ['Rascunho', 'Devolvido'].includes(current.status)
  const podeEditar    = !['Aprovado', 'Cancelado'].includes(current.status) && isSolicitante
  const podeLotes     = statusLoteEditavel && isLicitante
  const podeSubmeter  = ['Rascunho', 'Devolvido'].includes(current.status) && isSolicitante
  const podeAnalisar  = current.status === 'Submetido'  && isLicitante
  const podeAprovar   = current.status === 'Em Análise' && isLicitante
  const podeDevolver  = current.status === 'Em Análise' && isLicitante
  const podeReabrir   = ['Aprovado', 'Cancelado'].includes(current.status) && papel === 'admin'

  return (
    <div className="p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Minuta TR {current.numero_sei}</h1>
          <div className="flex gap-2 mt-1.5">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || ''}`}>
              {current.status}
            </span>
            <span className="text-xs text-gray-400">
              ETP: <span className="font-mono">{current.etp_numero_sei}</span>
            </span>
            <span className="text-xs text-gray-400">
              DFD: <span className="font-mono">{current.dfd_numero_sei}</span>
            </span>
          </div>
        </div>

        <div className="flex gap-2 flex-wrap justify-end">
          {podeSubmeter && (
            <button onClick={() => doAction(() => submeterTr(id))} disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Submeter
            </button>
          )}
          {podeAnalisar && (
            <button onClick={() => doAction(() => iniciarAnaliseTr(id))} disabled={actionLoading}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Iniciar Análise
            </button>
          )}
          {podeAprovar && (
            <button onClick={() => doAction(() => aprovarTr(id))} disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Aprovar
            </button>
          )}
          {podeDevolver && (
            <button onClick={() => setShowDevolver(true)}
              className="border border-orange-300 text-orange-600 hover:bg-orange-50 text-sm px-4 py-1.5 rounded-lg font-medium">
              Devolver
            </button>
          )}
          {podeReabrir && (
            <button onClick={() => setShowReabrir(true)}
              className="border border-red-300 text-red-600 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg font-medium">
              Reabrir
            </button>
          )}
          <DownloadButton
              onClick={() => downloadFile(`/tr/tr/${id}/export/pdf/`, `TR_${current.numero_sei}.pdf`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ PDF
            </DownloadButton>
          <DownloadButton
              onClick={() => downloadFile(`/tr/tr/${id}/export/historico/`, `Historico_TR_${current.numero_sei}.pdf`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ Histórico
            </DownloadButton>
          <DownloadButton
              onClick={() => downloadFile(`/tr/tr/${id}/export/html/`, `TR_${current.numero_sei}.html`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ HTML
            </DownloadButton>
          {podeEditar && !editing && (
            <button onClick={() => setEditing(true)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Editar
            </button>
          )}
          {editing && (
            <>
              <button onClick={handleSave} disabled={saving}
                className="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button onClick={() => { setEditing(false); setForm({ ...current }) }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg">
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>

      {/* Banner devolução */}
      {current.status === 'Devolvido' && current.motivo_devolucao && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 mb-5 text-sm text-orange-700">
          <strong>Devolvido:</strong> {current.motivo_devolucao}
        </div>
      )}

      {/* Decisões do ETP que influenciam este TR — campos flat no objeto TR */}
      {(current.etp_tipo_parcelamento || current.etp_reserva_cota_me_epp || current.etp_licitacao_exclusiva_me) && (
        <EtpDecisoesBanner etp={current} />
      )}

      {/* Alerta de cota ME/EPP não configurada */}
      {current.alerta_cota_me_epp && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 rounded-xl p-3 text-sm text-amber-800">
          <span className="text-lg leading-none">⚠️</span>
          <p>{current.alerta_cota_me_epp}</p>
        </div>
      )}

      {/* Modal devolver */}
      <ModalDevolver
        show={showDevolver}
        onClose={() => setShowDevolver(false)}
        onConfirm={handleDevolver}
        loading={actionLoading}
        titulo="Devolver TR para ajuste"
        categorias={MOTIVOS_TR}
      />

      {/* Modal reabrir */}
      {showReabrir && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold mb-2">Reabrir TR</h3>
            <p className="text-xs text-gray-500 mb-4">A aprovação será revertida e o TR voltará para status "Devolvido". Esta ação ficará registrada no histórico.</p>
            <label className="block text-xs font-medium text-gray-600 mb-1">Justificativa da reabertura *</label>
            <textarea rows={3} value={motivoReabrir} onChange={(e) => setMotivoReabrir(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button
                onClick={async () => {
                  if (!motivoReabrir.trim()) return
                  await doAction(() => reabrirTr(id, motivoReabrir))
                  setShowReabrir(false); setMotivoReabrir('')
                }}
                disabled={!motivoReabrir.trim() || actionLoading}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {actionLoading ? 'Processando...' : 'Confirmar reabertura'}
              </button>
              <button onClick={() => { setShowReabrir(false); setMotivoReabrir('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Campos */}
      <div className="space-y-5">
        <Section label="Objeto da contratação" error={formErrors.objeto_contratacao}>
          {editing
            ? <textarea rows={3} value={form.objeto_contratacao}
                onChange={(e) => set('objeto_contratacao', e.target.value)}
                className={inp(formErrors.objeto_contratacao)} />
            : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.objeto_contratacao || '—'}</p>}
        </Section>

        <Section label="Justificativa">
          {editing
            ? <textarea rows={3} value={form.justificativa}
                onChange={(e) => set('justificativa', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.justificativa || '—'}</p>}
        </Section>

        <Section label="Requisitos da contratação">
          {editing
            ? <textarea rows={3} value={form.requisitos_contratacao}
                onChange={(e) => set('requisitos_contratacao', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.requisitos_contratacao || '—'}</p>}
        </Section>

        <div className="grid grid-cols-2 gap-5">
          <Section label="Obrigações da contratada">
            {editing
              ? <textarea rows={3} value={form.obrigacoes_contratada}
                  onChange={(e) => set('obrigacoes_contratada', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.obrigacoes_contratada || '—'}</p>}
          </Section>
          <Section label="Obrigações da contratante">
            {editing
              ? <textarea rows={3} value={form.obrigacoes_contratante}
                  onChange={(e) => set('obrigacoes_contratante', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.obrigacoes_contratante || '—'}</p>}
          </Section>
        </div>

        <div className="grid grid-cols-2 gap-5">
          <Section label="Critérios de seleção">
            {editing
              ? <textarea rows={2} value={form.criterios_selecao}
                  onChange={(e) => set('criterios_selecao', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.criterios_selecao || '—'}</p>}
          </Section>
          <Section label="Critérios de medição">
            {editing
              ? <textarea rows={2} value={form.criterios_medicao}
                  onChange={(e) => set('criterios_medicao', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.criterios_medicao || '—'}</p>}
          </Section>
        </div>

        <Section label="Forma de Execução do Contrato">
          {editing ? (
            <PrazoVigenciaEditor form={form} set={set} />
          ) : (
            <PrazoVigenciaDisplay tr={current} />
          )}
        </Section>

        <div className="grid grid-cols-2 gap-5">
          <Section label="Estimativa de valor">
            {editing
              ? <input type="number" step="0.01" value={form.estimativa_valor || ''}
                  onChange={(e) => set('estimativa_valor', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700">
                  {current.estimativa_valor
                    ? Number(current.estimativa_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                    : '—'}
                </p>}
          </Section>
        </div>

        <Section label="Local de entrega">
          {editing
            ? <input type="text" value={form.local_entrega}
                onChange={(e) => set('local_entrega', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700">{current.local_entrega || '—'}</p>}
        </Section>

        <Section label="Garantia contratual">
          {editing
            ? <textarea rows={2} value={form.garantia_contrato}
                onChange={(e) => set('garantia_contrato', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.garantia_contrato || '—'}</p>}
        </Section>

        <Section label="Observações">
          {editing
            ? <textarea rows={2} value={form.observacoes}
                onChange={(e) => set('observacoes', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>}
        </Section>

        {/* ── Lotes da Licitação ── */}
        <LotesSection
          tr={current}
          podeEditar={podeLotes}
          onCriarLote={(payload) => criarLote(id, payload)}
          onExcluirLote={(lotePk) => excluirLote(id, lotePk)}
          onAdicionarItem={(lotePk, payload) => adicionarItemLote(id, lotePk, payload)}
          onRemoverItem={(lotePk, itemPk) => removerItemLote(id, lotePk, itemPk)}
          onGerarCota={(lotePk) => gerarCota(id, lotePk)}
          onGerarPorItem={() => gerarPorItem(id)}
        />

        {/* Histórico */}
        {current.historico?.length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Histórico de tramitação</p>
            <ol className="space-y-2">
              {[...current.historico].reverse().map((h) => (
                <li key={h.id} className="flex items-start gap-3">
                  <span className="mt-1 w-2 h-2 rounded-full bg-teal-400 shrink-0" />
                  <div>
                    <p className="text-xs text-gray-500">
                      {new Date(h.criado_em).toLocaleString('pt-BR')} — <strong>{h.usuario_username}</strong>
                    </p>
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">{h.status_anterior}</span>
                      {' → '}
                      <span className="font-medium">{h.status_novo}</span>
                    </p>
                    {h.motivo && <p className="text-xs text-gray-500 mt-0.5">{h.motivo}</p>}
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}

        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado em: {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
        </div>
      </div>
    </div>
  )
}

// ── Lotes da Licitação ────────────────────────────────────────────────────────

const MODALIDADE_CLS = {
  ampla:            { badge: 'bg-blue-100 text-blue-700',   dot: 'bg-blue-500'  },
  cota_me_epp:      { badge: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' },
  exclusiva_me_epp: { badge: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
}
const MODALIDADE_LABELS = {
  ampla:            'Ampla Concorrência',
  cota_me_epp:      'Reserva de Cota ME/EPP',
  exclusiva_me_epp: 'Exclusivo ME/EPP',
}
const fmtQ = (v) => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 4 })
const fmtR = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

function LotesSection({ tr, podeEditar, onCriarLote, onExcluirLote, onAdicionarItem, onRemoverItem, onGerarCota, onGerarPorItem }) {
  const [showNovoLote, setShowNovoLote]   = useState(false)
  const [novoLoteForm, setNovoLoteForm]   = useState({ descricao: '', modalidade: 'ampla', justificativa_agrupamento: '' })
  const [showAddItem, setShowAddItem]     = useState(null)
  const [addItemForm, setAddItemForm]     = useState({ item_dfd: '', quantidade: '' })
  const [itensDfd, setItensDfd]           = useState([])
  const [saving, setSaving]               = useState(false)

  // Busca os itens do DFD uma vez ao montar o componente
  useEffect(() => {
    if (!tr.etp_dfd_id) return
    api.get(`/demanda/dfd/${tr.etp_dfd_id}/`)
      .then(({ data }) => setItensDfd(data.itens || []))
      .catch(() => {})
  }, [tr.etp_dfd_id])

  const handleCriarLote = async () => {
    if (!novoLoteForm.descricao.trim()) return
    setSaving(true)
    try { await onCriarLote(novoLoteForm); setShowNovoLote(false); setNovoLoteForm({ descricao: '', modalidade: 'ampla', justificativa_agrupamento: '' }) }
    finally { setSaving(false) }
  }

  const handleAdicionarItem = async (lotePk) => {
    if (!addItemForm.item_dfd || !addItemForm.quantidade) return
    setSaving(true)
    try {
      await onAdicionarItem(lotePk, { item_dfd: Number(addItemForm.item_dfd), quantidade: Number(addItemForm.quantidade) })
      setShowAddItem(null)
      setAddItemForm({ item_dfd: '', quantidade: '' })
    } finally { setSaving(false) }
  }

  const itemSelecionado = itensDfd.find(i => String(i.id) === String(addItemForm.item_dfd))

  return (
    <div className="pt-4 border-t border-gray-100">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold text-gray-400 uppercase">Lotes da Licitação</p>
        {podeEditar && (
          <div className="flex gap-2">
            {tr.etp_tipo_parcelamento === 'por_item' && (
              <button onClick={onGerarPorItem}
                className="text-xs bg-teal-50 border border-teal-300 text-teal-700 hover:bg-teal-100 px-3 py-1 rounded-lg font-medium">
                Criar um lote por item
              </button>
            )}
            <button onClick={() => setShowNovoLote(v => !v)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              {showNovoLote ? 'Cancelar' : '+ Novo lote'}
            </button>
          </div>
        )}
      </div>

      {/* Form novo lote */}
      {showNovoLote && (
        <div className="mb-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
          <div className="grid grid-cols-2 gap-2">
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Descrição do lote *</label>
              <input type="text" value={novoLoteForm.descricao}
                onChange={e => setNovoLoteForm(p => ({ ...p, descricao: e.target.value }))}
                placeholder="Ex: Lote 01 — Equipamentos de TI"
                className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Modalidade</label>
              <select value={novoLoteForm.modalidade}
                onChange={e => setNovoLoteForm(p => ({ ...p, modalidade: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs">
                <option value="ampla">Ampla Concorrência</option>
                <option value="exclusiva_me_epp">Exclusivo ME/EPP</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">
                Justificativa de agrupamento <span className="text-gray-400">(obrigatória se lote tiver mais de 1 item)</span>
              </label>
              <input type="text" value={novoLoteForm.justificativa_agrupamento}
                onChange={e => setNovoLoteForm(p => ({ ...p, justificativa_agrupamento: e.target.value }))}
                placeholder="Ex: Itens interdependentes — padronização de equipamentos"
                className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs" />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={handleCriarLote} disabled={saving || !novoLoteForm.descricao.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
              {saving ? '...' : 'Criar lote'}
            </button>
          </div>
        </div>
      )}

      {/* Lista de lotes */}
      {(!tr.lotes || tr.lotes.length === 0) ? (
        <p className="text-xs text-gray-400 italic">Nenhum lote configurado. {podeEditar ? 'Clique em "+ Novo lote" para começar.' : ''}</p>
      ) : (
        <div className="space-y-3">
          {tr.lotes.map(lote => {
            const cls = MODALIDADE_CLS[lote.modalidade] || MODALIDADE_CLS.ampla
            return (
              <div key={lote.id} className={`border rounded-xl overflow-hidden ${lote.modalidade === 'ampla' ? 'border-blue-200' : lote.modalidade === 'cota_me_epp' ? 'border-amber-200' : 'border-green-200'}`}>
                {/* Cabeçalho do lote */}
                <div className="flex items-center justify-between px-4 py-2.5 bg-gray-50">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${cls.dot}`} />
                    <span className="font-mono text-sm font-semibold text-gray-800">{lote.numero}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cls.badge}`}>
                      {MODALIDADE_LABELS[lote.modalidade]}
                    </span>
                    {lote.lote_origem_numero && (
                      <span className="text-xs text-gray-400">← {lote.lote_origem_numero}</span>
                    )}
                    {lote.alerta_agrupamento && (
                      <span title={lote.alerta_agrupamento} className="text-amber-500 cursor-help text-sm">⚠️</span>
                    )}
                    {lote.alerta_exclusivo && (
                      <span title={lote.alerta_exclusivo} className="text-red-500 cursor-help text-sm">🚫</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-gray-700">{fmtR(lote.valor_total_lote)}</span>
                    {podeEditar && (
                      <div className="flex gap-1">
                        {/* Cota ME/EPP: só para ampla + sem alerta de exclusivo */}
                        {lote.modalidade === 'ampla' && !lote.alerta_exclusivo && (
                          <button onClick={() => onGerarCota(lote.id)}
                            className="text-xs bg-amber-50 border border-amber-300 text-amber-700 hover:bg-amber-100 px-2 py-0.5 rounded font-medium">
                            + Cota ME/EPP
                          </button>
                        )}
                        <button onClick={() => setShowAddItem(showAddItem === lote.id ? null : lote.id)}
                          className="text-xs text-blue-600 hover:underline">
                          + Item
                        </button>
                        <button onClick={() => onExcluirLote(lote.id)}
                          className="text-xs text-red-500 hover:text-red-700">✕</button>
                      </div>
                    )}
                  </div>
                </div>

                {lote.descricao && (
                  <p className="px-4 py-1 text-xs text-gray-500 border-b border-gray-100">{lote.descricao}</p>
                )}

                {/* Alerta lote exclusivo ME/EPP (valor < R$80k) */}
                {lote.alerta_exclusivo && (
                  <div className="px-4 py-2 border-b border-red-200 bg-red-50 text-xs text-red-800 font-medium">
                    🚫 {lote.alerta_exclusivo}
                  </div>
                )}

                {/* Justificativa de agrupamento — exibe quando lote tem > 1 item */}
                {lote.itens.length > 1 && (
                  <div className={`px-4 py-1.5 border-b text-xs ${lote.justificativa_agrupamento ? 'bg-green-50 border-green-100 text-green-700' : 'bg-amber-50 border-amber-100 text-amber-700'}`}>
                    <span className="font-medium">Justificativa de agrupamento: </span>
                    {lote.justificativa_agrupamento || 'Não informada — obrigatória para lotes com múltiplos itens.'}
                  </div>
                )}

                {/* Itens do lote */}
                {lote.itens.length > 0 && (
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50/50">
                      <tr>
                        <th className="text-left px-4 py-1.5 font-medium text-gray-500">Item</th>
                        <th className="text-right px-4 py-1.5 font-medium text-gray-500">Qtd</th>
                        <th className="text-right px-4 py-1.5 font-medium text-gray-500">Vl. Unit.</th>
                        <th className="text-right px-4 py-1.5 font-medium text-gray-500">Origem</th>
                        <th className="text-right px-4 py-1.5 font-medium text-gray-500">Total</th>
                        {podeEditar && <th className="w-6" />}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {lote.itens.map(item => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-4 py-1.5 text-gray-700">
                            {item.catalogo_familia && (
                              <span className="mr-1 font-mono text-blue-600 text-[10px] bg-blue-50 px-1 rounded">{item.catalogo_familia}</span>
                            )}
                            {item.item_objeto}
                            <span className="ml-1 text-gray-400">({item.item_unidade})</span>
                          </td>
                          <td className="px-4 py-1.5 text-right text-gray-600">{fmtQ(item.quantidade)}</td>
                          <td className="px-4 py-1.5 text-right text-gray-600">
                            {fmtR(item.valor_unitario_efetivo)}
                            {item.preco_origem === 'mapa' && item.item_valor_est && (
                              <span className="ml-1 text-[10px] text-gray-400 line-through">{fmtR(item.item_valor_est)}</span>
                            )}
                          </td>
                          <td className="px-4 py-1.5 text-right">
                            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
                              item.preco_origem === 'mapa'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-500'
                            }`}>
                              {item.preco_origem === 'mapa' ? 'Mapa' : 'DFD'}
                            </span>
                          </td>
                          <td className="px-4 py-1.5 text-right font-semibold text-gray-800">{fmtR(item.valor_total)}</td>
                          {podeEditar && (
                            <td className="px-2 py-1.5 text-center">
                              <button onClick={() => onRemoverItem(lote.id, item.id)}
                                className="text-red-400 hover:text-red-600">✕</button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                {lote.itens.length === 0 && (
                  <p className="px-4 py-2 text-xs text-gray-400 italic">Nenhum item neste lote.</p>
                )}

                {/* Form inline adicionar item */}
                {showAddItem === lote.id && (
                  <div className="px-4 py-3 bg-blue-50 border-t border-blue-100">
                    <p className="text-xs font-semibold text-blue-700 mb-2">Adicionar item ao lote</p>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="col-span-2">
                        <label className="block text-xs text-gray-500 mb-0.5">Item do DFD *</label>
                        <select value={addItemForm.item_dfd}
                          onChange={e => {
                            const item = itensDfd.find(i => String(i.id) === e.target.value)
                            setAddItemForm({ item_dfd: e.target.value, quantidade: item ? String(item.quantidade) : '' })
                          }}
                          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
                          <option value="">— Selecione —</option>
                          {itensDfd.map(i => (
                            <option key={i.id} value={i.id}>{i.objeto} ({i.unidade_medida})</option>
                          ))}
                        </select>
                        {itensDfd.length === 0 && <p className="text-[10px] text-amber-600 mt-0.5">Carregando itens do DFD...</p>}
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-0.5">Quantidade *</label>
                        <input type="number" min="0" step="0.0001"
                          value={addItemForm.quantidade}
                          onChange={e => setAddItemForm(p => ({ ...p, quantidade: e.target.value }))}
                          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
                        {itemSelecionado && (
                          <p className="text-[10px] text-gray-400 mt-0.5">Original: {itemSelecionado.quantidade} {itemSelecionado.unidade_medida}</p>
                        )}
                      </div>
                      <div className="col-span-3 flex gap-2">
                        <button
                          onClick={() => handleAdicionarItem(lote.id)}
                          disabled={saving || !addItemForm.item_dfd || !addItemForm.quantidade}
                          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                          {saving ? 'Salvando...' : 'Adicionar item'}
                        </button>
                        <button onClick={() => { setShowAddItem(null); setAddItemForm({ item_dfd: '', quantidade: '' }) }}
                          className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg hover:bg-gray-50">
                          Cancelar
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function EtpDecisoesBanner({ etp }) {
  const PARCELAMENTO_LABELS = {
    lote_unico: 'Lote único',
    lotes:      'Dividido em lotes',
    por_item:   'Por item',
  }
  const TIPO_OBJETO_LABELS = {
    bens: 'Bens', servicos: 'Serviços Comuns',
    servicos_engenharia: 'Serviços de Engenharia', obras: 'Obras',
  }
  const itens = []
  if (etp.etp_tipo_objeto)
    itens.push({ icon: '🏗️', label: 'Tipo de objeto', valor: TIPO_OBJETO_LABELS[etp.etp_tipo_objeto] || etp.etp_tipo_objeto })
  if (etp.etp_tipo_parcelamento)
    itens.push({ icon: '📦', label: 'Parcelamento', valor: PARCELAMENTO_LABELS[etp.etp_tipo_parcelamento] || etp.etp_tipo_parcelamento })
  if (etp.etp_reserva_cota_me_epp)
    itens.push({ icon: '🏷️', label: 'Cota ME/EPP', valor: 'Reserva de 25% (LC 123, Art. 48)' })
  if (etp.etp_licitacao_exclusiva_me)
    itens.push({ icon: '⭐', label: 'Licitação exclusiva ME/EPP', valor: 'Sim (até R$80.000)' })

  if (itens.length === 0) return null
  return (
    <div className="mb-5 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3">
      <p className="text-xs font-semibold text-purple-700 uppercase mb-2">Decisões do ETP que influenciam este TR</p>
      <div className="flex flex-wrap gap-3">
        {itens.map(({ icon, label, valor }) => (
          <div key={label} className="flex items-center gap-1.5 text-xs text-purple-800">
            <span>{icon}</span>
            <span className="font-medium">{label}:</span>
            <span>{valor}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Section({ label, error, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

const inp = (error) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`

const TIPO_PRAZO_OPTS = [
  { value: '',           label: '— Selecione a forma de execução —' },
  { value: 'escopo',     label: 'Por Escopo — Entrega/aquisição única (Art. 105)' },
  { value: 'continuo',   label: 'Contínuo — Serviço continuado (Art. 106/107)' },
  { value: 'emergencial',label: 'Emergencial — Contratação direta (Art. 75, VIII)' },
  { value: 'direta_108', label: 'Contratação Direta Art. 108' },
]
const INSTRUMENTO_OPTS = [
  { value: '',        label: '— Selecione —' },
  { value: 'contrato',label: 'Assinatura do Contrato' },
  { value: 'afm',     label: 'AFM — Autorização de Fornecimento de Material' },
  { value: 'aps',     label: 'APS — Autorização de Prestação de Serviços' },
]

function gerarRedacao(tipo, meses, instrumento) {
  const inst = INSTRUMENTO_OPTS.find(i => i.value === instrumento)?.label || instrumento || 'assinatura do Contrato'
  if (tipo === 'escopo')
    return `O prazo de vigência do Contrato é de 30 dias, a contar da data da ${inst}, observado o artigo 105 da Lei Federal n° 14.133/2021.`
  if (tipo === 'continuo')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 5 anos), a contar da data da ${inst}, prorrogável até atingir o limite de 10 anos, na forma dos artigos 106 e 107 da Lei Federal n° 14.133/2021.`
  if (tipo === 'emergencial')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses, podendo ser prorrogado, desde que o prazo total não ultrapasse 1 (um) ano, observado o art. 75, inc. VIII, da Lei Federal n° 14.133/2021.`
  if (tipo === 'direta_108')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 10 anos), a contar da data da ${inst}, nos termos do artigo 108 da Lei Federal n° 14.133/2021.`
  return ''
}

function PrazoVigenciaEditor({ form, set }) {
  const tipo = form.tipo_prazo_vigencia || ''
  const meses = form.prazo_meses || ''
  const instrumento = form.instrumento_inicio || ''
  const precisaMeses = ['continuo', 'emergencial', 'direta_108'].includes(tipo)
  const precisaInstrumento = ['escopo', 'continuo', 'direta_108'].includes(tipo)

  const redacao = tipo ? gerarRedacao(tipo, meses, instrumento) : ''

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs text-gray-500 mb-1">Tipo de vigência *</label>
        <select value={tipo} onChange={e => { set('tipo_prazo_vigencia', e.target.value); set('prazo_observacao', gerarRedacao(e.target.value, meses, instrumento)) }}
          className={inp()}>
          {TIPO_PRAZO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>
      {precisaMeses && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">
              Prazo em meses {tipo === 'continuo' ? '(máx. 60)' : tipo === 'emergencial' ? '(máx. 12)' : '(máx. 120)'}
            </label>
            <input type="number" min="1" max={tipo === 'continuo' ? 60 : tipo === 'emergencial' ? 12 : 120}
              value={meses} onChange={e => { set('prazo_meses', e.target.value); set('prazo_observacao', gerarRedacao(tipo, e.target.value, instrumento)) }}
              className={inp()} />
          </div>
        </div>
      )}
      {precisaInstrumento && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Instrumento de início</label>
          <select value={instrumento} onChange={e => { set('instrumento_inicio', e.target.value); set('prazo_observacao', gerarRedacao(tipo, meses, e.target.value)) }}
            className={inp()}>
            {INSTRUMENTO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
      )}
      {redacao && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-blue-700 mb-1">Redação gerada:</p>
          <p className="text-xs text-blue-800 leading-relaxed">{redacao}</p>
        </div>
      )}
    </div>
  )
}

function PrazoVigenciaDisplay({ tr }) {
  const tipo = TIPO_PRAZO_OPTS.find(o => o.value === tr.tipo_prazo_vigencia)
  if (!tr.tipo_prazo_vigencia) return <p className="text-sm text-gray-400 italic">Não definido</p>
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-gray-600">{tipo?.label}</p>
      {tr.prazo_observacao && (
        <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-2 leading-relaxed">{tr.prazo_observacao}</p>
      )}
    </div>
  )
}
