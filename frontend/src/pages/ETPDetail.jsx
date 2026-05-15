import { useEffect, useState } from 'react'
import ModalDevolver, { MOTIVOS_ETP } from '../components/ModalDevolver'
import { useNavigate, useParams } from 'react-router-dom'
import useEtpStore from '../stores/etpStore'
import useAuthStore from '../stores/authStore'
import { downloadFile } from '../services/api'
import DownloadButton from '../components/DownloadButton'

const STATUS_CLS = {
  Rascunho:     'bg-gray-100 text-gray-600',
  Submetido:    'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Devolvido:    'bg-orange-100 text-orange-700',
  Aprovado:     'bg-green-100 text-green-700',
  Cancelado:    'bg-red-100 text-red-700',
  Dispensado:   'bg-purple-100 text-purple-700',
}

const PAPEIS_ANALISTA    = ['admin', 'analista', 'gestor_planejamento', 'gestor_contrato', 'ordenador']
const PAPEIS_SOLICITANTE = ['solicitante', 'demandante', 'responsavel_tecnico', 'admin']


export default function ETPDetail() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const { current, loading, error, fetchEtp, updateEtp,
          submeterEtp, iniciarAnaliseEtp, aprovarEtp, devolverEtp, reabrirEtp } = useEtpStore()
  const { papel } = useAuthStore()

  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [formErrors, setFormErrors] = useState({})

  const [actionLoading, setActionLoading]   = useState(false)
  const [actionError, setActionError]       = useState(null)
  const [actionAviso, setActionAviso]       = useState(null)
  const [showDevolverModal, setShowDevolverModal]   = useState(false)
  const [showReabrirModal, setShowReabrirModal]     = useState(false)
  const [motivoReabrir, setMotivoReabrir]           = useState('')
  const [motivoNumeroSEI, setMotivoNumeroSEI]       = useState('')

  useEffect(() => { fetchEtp(id) }, [id])
  useEffect(() => {
    if (current) setForm({ ...current })
  }, [current])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setFormErrors((p) => ({ ...p, [field]: undefined }))
  }

  const numeroSeiAlterado = form && current && form.numero_sei !== current.numero_sei

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = {
        numero_sei:              form.numero_sei,
        necessidade_contratacao: form.necessidade_contratacao,
        requisitos_contratacao:  form.requisitos_contratacao,
        levantamento_mercado:    form.levantamento_mercado,
        estimativa_valor:        form.estimativa_valor ? Number(form.estimativa_valor) : null,
        descricao_solucao:       form.descricao_solucao,
        justificativa_solucao:   form.justificativa_solucao,
        riscos:                  form.riscos,
        sustentabilidade:        form.sustentabilidade,
        tipo_objeto:                form.tipo_objeto                ?? '',
        tipo_parcelamento:          form.tipo_parcelamento          ?? '',
        parcelamento_justificativa: form.parcelamento_justificativa ?? '',
        adjudicacao_por_item:       form.adjudicacao_por_item       ?? false,
        reserva_cota_me_epp:        form.reserva_cota_me_epp        ?? false,
        reserva_cota_justificativa: form.reserva_cota_justificativa ?? '',
        licitacao_exclusiva_me_epp: form.licitacao_exclusiva_me_epp ?? false,
        observacoes:             form.observacoes,
      }
      if (numeroSeiAlterado && motivoNumeroSEI.trim()) {
        payload.motivo_numero_sei = motivoNumeroSEI
      }
      await updateEtp(id, payload)
      setEditing(false)
      setMotivoNumeroSEI('')
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setFormErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const runAction = async (fn) => {
    setActionLoading(true)
    setActionError(null)
    setActionAviso(null)
    try {
      const result = await fn()
      if (result?.aviso) setActionAviso(result.aviso)
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Erro ao executar ação.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDevolver = async (motivo, categoria) => {
    await runAction(() => devolverEtp(id, motivo, categoria))
    setShowDevolverModal(false)
  }

  if (loading) return <p className="p-8 text-sm text-gray-400">Carregando...</p>
  if (error)   return <p className="p-8 text-sm text-red-600">{error}</p>
  if (!current || !form) return null

  const isAnalista    = PAPEIS_ANALISTA.includes(papel)
  const isSolicitante = PAPEIS_SOLICITANTE.includes(papel)

  // Regras de edição: status editável + papel com permissão de escrita
  const statusEditavel = ['Rascunho', 'Devolvido'].includes(current.status)
  const podeEditar     = statusEditavel && isSolicitante
  const podeSubmeter   = statusEditavel && isSolicitante
  const podeAnalisar   = current.status === 'Submetido'   && isAnalista
  const podeAprovar    = current.status === 'Em Análise'  && isAnalista
  const podeDevolver   = current.status === 'Em Análise'  && isAnalista
  const podeCriarTR    = current.status === 'Aprovado' && !current.tr_id
  const podeReabrir    = ['Aprovado', 'Cancelado'].includes(current.status) && papel === 'admin'
  const temTR          = !!current.tr_id

  return (
    <div className="p-8 max-w-2xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero_sei}</h1>
          <div className="flex gap-2 mt-1.5 flex-wrap">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || ''}`}>
              {current.status}
            </span>
            <span className="text-xs text-gray-400">DFD: {current.dfd_numero_sei}</span>
            {temTR && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-700 font-medium">
                TR vinculado
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 flex-wrap justify-end">
          {podeCriarTR && (
            <button onClick={() => navigate('/analise-tecnica/trs/novo', { state: { etp: current } })}
              className="bg-teal-600 hover:bg-teal-700 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              + Criar TR
            </button>
          )}
          {temTR && (
            <button onClick={() => navigate(`/analise-tecnica/trs/${current.tr_id}`)}
              className="bg-teal-50 border border-teal-200 text-teal-700 text-sm px-4 py-1.5 rounded-lg">
              Ver TR
            </button>
          )}
          <DownloadButton
              onClick={() => downloadFile(`/etp/etp/${id}/export/pdf/`, `ETP_${current.numero_sei}.pdf`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ PDF
            </DownloadButton>
          <DownloadButton
              onClick={() => downloadFile(`/etp/etp/${id}/export/historico/`, `Historico_ETP_${current.numero_sei}.pdf`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ Histórico
            </DownloadButton>
          <DownloadButton
              onClick={() => downloadFile(`/etp/etp/${id}/export/html/`, `ETP_${current.numero_sei}.html`)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              ↓ HTML
            </DownloadButton>
          {!editing ? (
            podeEditar && (
              <button onClick={() => setEditing(true)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
                Editar
              </button>
            )
          ) : (
            <>
              <button onClick={handleSave} disabled={saving}
                className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button onClick={() => { setEditing(false); setForm({ ...current }); setMotivoNumeroSEI('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg">
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>

      {/* Aviso TR cascata (após reabertura) */}
      {actionAviso && (
        <div className="mb-4 bg-amber-50 border border-amber-200 text-amber-800 text-sm rounded-lg px-4 py-3 flex items-start gap-2">
          <span className="text-lg leading-none">⚠</span>
          <p>{actionAviso}</p>
        </div>
      )}

      {/* Aviso: ETP editável com TR vinculado */}
      {editing && temTR && (
        <div className="mb-5 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-800">
          <strong>Atenção:</strong> Este ETP possui um TR vinculado. Alterações no conteúdo do ETP
          podem tornar o TR inconsistente. Se o TR estiver Aprovado, solicite reabertura ao administrador
          — o TR será devolvido automaticamente.
        </div>
      )}

      {/* Devolução banner */}
      {current.status === 'Devolvido' && current.motivo_devolucao && (
        <div className="mb-5 bg-orange-50 border border-orange-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-orange-700 uppercase mb-1">Motivo da devolução</p>
          <p className="text-sm text-orange-800">{current.motivo_devolucao}</p>
        </div>
      )}

      {actionError && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3">
          {actionError}
        </div>
      )}

      {/* Workflow buttons */}
      {(podeSubmeter || podeAnalisar || podeAprovar || podeDevolver || podeReabrir) && (
        <div className="mb-6 flex flex-wrap gap-2">
          {podeReabrir && (
            <button onClick={() => setShowReabrirModal(true)} disabled={actionLoading}
              className="border border-orange-400 text-orange-600 hover:bg-orange-50 text-sm font-medium px-4 py-2 rounded-lg">
              ↺ Reabrir ETP{temTR ? ' (e TR)' : ''}
            </button>
          )}
          {podeSubmeter && (
            <button onClick={() => runAction(() => submeterEtp(id))} disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
              {actionLoading ? '...' : '↑ Submeter para análise'}
            </button>
          )}
          {podeAnalisar && (
            <button onClick={() => runAction(() => iniciarAnaliseEtp(id))} disabled={actionLoading}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
              {actionLoading ? '...' : 'Iniciar análise'}
            </button>
          )}
          {podeAprovar && (
            <button onClick={() => runAction(() => aprovarEtp(id))} disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
              {actionLoading ? '...' : '✓ Aprovar'}
            </button>
          )}
          {podeDevolver && (
            <button onClick={() => setShowDevolverModal(true)} disabled={actionLoading}
              className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
              ↩ Devolver para ajuste
            </button>
          )}
        </div>
      )}

      <ModalDevolver
        show={showDevolverModal}
        onClose={() => setShowDevolverModal(false)}
        onConfirm={handleDevolver}
        loading={actionLoading}
        titulo="Devolver ETP para ajuste"
        categorias={MOTIVOS_ETP}
      />

      {showReabrirModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">Reabrir ETP</h3>
            {temTR && (
              <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-3">
                ⚠ Este ETP possui TR vinculado. Se o TR estiver Aprovado, será devolvido automaticamente.
              </p>
            )}
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo da reabertura *</label>
            <textarea rows={3} value={motivoReabrir} onChange={e => setMotivoReabrir(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400" />
            <div className="flex gap-2 mt-4">
              <button
                onClick={async () => {
                  if (!motivoReabrir.trim()) return
                  await runAction(() => reabrirEtp(id, motivoReabrir))
                  setShowReabrirModal(false)
                  setMotivoReabrir('')
                }}
                disabled={!motivoReabrir.trim() || actionLoading}
                className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {actionLoading ? '...' : 'Confirmar reabertura'}
              </button>
              <button onClick={() => { setShowReabrirModal(false); setMotivoReabrir('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fields */}
      <div className="space-y-5">
        {/* Número SEI */}
        <DF label="Número SEI do ETP">
          {editing ? (
            <>
              <input type="text" value={form.numero_sei}
                onChange={(e) => set('numero_sei', e.target.value)}
                className={inp(formErrors.numero_sei)} />
              {numeroSeiAlterado && (
                <input type="text" value={motivoNumeroSEI}
                  onChange={(e) => setMotivoNumeroSEI(e.target.value)}
                  placeholder="Motivo da alteração do número SEI (opcional)"
                  className="mt-1 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 text-gray-600" />
              )}
            </>
          ) : (
            <p className="text-sm text-gray-800 font-mono">{current.numero_sei}</p>
          )}
        </DF>

        {[
          ['necessidade_contratacao', 'Necessidade da contratação', 4],
          ['requisitos_contratacao',  'Requisitos da contratação',  3],
          ['levantamento_mercado',    'Levantamento de mercado',    3],
          ['descricao_solucao',       'Descrição da solução',       3],
          ['justificativa_solucao',   'Justificativa da solução',   2],
          ['riscos',                  'Mapa de riscos',             2],
          ['sustentabilidade',        'Critérios de sustentabilidade', 2],
          ['observacoes',             'Observações',                2],
        ].map(([field, label, rows]) => (
          <DF key={field} label={label} error={formErrors[field]}>
            {editing
              ? <textarea rows={rows} value={form[field] || ''} onChange={(e) => set(field, e.target.value)}
                  className={inp(formErrors[field])} />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current[field] || '—'}</p>}
          </DF>
        ))}

        <DF label="Estimativa de valor">
          {editing
            ? <input type="number" step="0.01" value={form.estimativa_valor || ''}
                onChange={(e) => set('estimativa_valor', e.target.value)}
                className={inp()} />
            : <p className="text-sm text-gray-700">
                {current.estimativa_valor
                  ? Number(current.estimativa_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                  : '—'}
              </p>}
        </DF>

        {/* ── Parcelamento e Adjudicação ── */}
        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Parcelamento e Adjudicação</p>
          <div className="space-y-4">
            <DF label="Tipo de objeto">
              {editing ? (
                <select value={form.tipo_objeto || ''} onChange={e => set('tipo_objeto', e.target.value)} className={inp()}>
                  <option value="">— Selecione —</option>
                  <option value="bens">Bens</option>
                  <option value="servicos">Serviços Comuns</option>
                  <option value="servicos_engenharia">Serviços de Engenharia</option>
                  <option value="obras">Obras</option>
                </select>
              ) : (
                <p className="text-sm text-gray-700">
                  {{ bens: 'Bens', servicos: 'Serviços Comuns', servicos_engenharia: 'Serviços de Engenharia', obras: 'Obras' }[current.tipo_objeto] || '—'}
                </p>
              )}
            </DF>

            <DF label="Tipo de parcelamento (Lei 14.133, Art. 40, V)">
              {editing ? (
                <select value={form.tipo_parcelamento || ''} onChange={e => set('tipo_parcelamento', e.target.value)} className={inp()}>
                  <option value="">— Selecione —</option>
                  <option value="lote_unico">Lote único — contratação global</option>
                  <option value="lotes">Dividido em lotes — adjudicação por lote</option>
                  <option value="por_item">Por item — adjudicação individualizada</option>
                </select>
              ) : (
                <p className="text-sm text-gray-700">
                  {{ lote_unico: 'Lote único', lotes: 'Dividido em lotes', por_item: 'Por item' }[current.tipo_parcelamento] || '—'}
                </p>
              )}
            </DF>

            <DF label="Justificativa do parcelamento">
              {editing
                ? <textarea rows={2} value={form.parcelamento_justificativa || ''} onChange={e => set('parcelamento_justificativa', e.target.value)} className={inp()} />
                : <p className="text-sm text-gray-700 whitespace-pre-wrap text-justify">{current.parcelamento_justificativa || '—'}</p>}
            </DF>
          </div>
        </div>

        {/* ── Tratamento ME/EPP (política por lote no TR) ── */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-start gap-2 mb-1">
            <p className="text-xs font-semibold text-gray-400 uppercase">Tratamento ME/EPP</p>
            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">LC 123/2006, Art. 48</span>
          </div>
          <p className="text-xs text-gray-400 mb-3">
            Políticas declaradas no ETP — aplicadas individualmente por lote no TR.
            Lotes podem ter modalidades diferentes conforme valor e divisibilidade.
          </p>

          <div className="space-y-3">
            {/* Política 1: Reserva de cota */}
            <div className={`rounded-xl border px-4 py-3 ${
              (editing ? form.reserva_cota_me_epp : current.reserva_cota_me_epp)
                ? 'bg-amber-50 border-amber-300'
                : 'bg-gray-50 border-gray-200'
            }`}>
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox"
                  checked={editing ? (form.reserva_cota_me_epp ?? false) : (current.reserva_cota_me_epp ?? false)}
                  disabled={!editing}
                  onChange={e => set('reserva_cota_me_epp', e.target.checked)}
                  className="mt-0.5 accent-amber-600 w-4 h-4 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-800">
                    Reserva de cota 25% para ME/EPP nos lotes divisíveis
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Art. 48, III — LC 123/2006. No TR, use "Gerar Cota ME/EPP" em cada lote amplo aplicável
                    para criar automaticamente o sub-lote de 25%.
                  </p>
                </div>
              </label>

              {/* Justificativa de não-reserva */}
              {!(editing ? form.reserva_cota_me_epp : current.reserva_cota_me_epp) && (
                <div className="mt-3 ml-7">
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Justificativa para não aplicar reserva de cota *
                  </label>
                  {editing
                    ? <textarea rows={2} value={form.reserva_cota_justificativa || ''}
                        onChange={e => set('reserva_cota_justificativa', e.target.value)}
                        placeholder="Ex: objeto indivisível, licitação exclusiva ME/EPP, valor abaixo do limite..."
                        className={inp(formErrors.reserva_cota_justificativa)} />
                    : <p className="text-sm text-gray-600 italic">
                        {current.reserva_cota_justificativa || '—'}
                      </p>}
                </div>
              )}
            </div>

            {/* Política 2: Licitação exclusiva */}
            <div className={`rounded-xl border px-4 py-3 ${
              (editing ? form.licitacao_exclusiva_me_epp : current.licitacao_exclusiva_me_epp)
                ? 'bg-green-50 border-green-300'
                : 'bg-gray-50 border-gray-200'
            }`}>
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox"
                  checked={editing ? (form.licitacao_exclusiva_me_epp ?? false) : (current.licitacao_exclusiva_me_epp ?? false)}
                  disabled={!editing}
                  onChange={e => set('licitacao_exclusiva_me_epp', e.target.checked)}
                  className="mt-0.5 accent-green-600 w-4 h-4 shrink-0" />
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    Licitação exclusiva ME/EPP para lotes com valor ≤ R$ 80.000
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Art. 48, I — LC 123/2006. No TR, crie os lotes com modalidade "Exclusivo ME/EPP"
                    para os que se enquadram no limite. Pode coexistir com lotes de ampla concorrência
                    (com ou sem cota) nos demais lotes.
                  </p>
                </div>
              </label>
            </div>

            {/* Info: ambas desmarcadas */}
            {!(editing ? form.reserva_cota_me_epp : current.reserva_cota_me_epp) &&
             !(editing ? form.licitacao_exclusiva_me_epp : current.licitacao_exclusiva_me_epp) && (
              <p className="text-xs text-gray-400 ml-1">
                Nenhum benefício ME/EPP aplicado — todos os lotes do TR serão de <strong>Ampla Concorrência</strong>.
              </p>
            )}
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado por: {current.created_by_username} em {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
          {current.org_sigla && <p>Órgão: {current.org_sigla}</p>}
        </div>

        {/* Histórico de tramitação */}
        {(current.historico || []).length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Histórico de tramitação</p>
            <ol className="relative border-l border-gray-200 space-y-4 ml-2">
              {current.historico.map((h) => (
                <li key={h.id} className="ml-4">
                  <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-purple-400 border-2 border-white" />
                  <p className="text-xs text-gray-400">
                    {new Date(h.criado_em).toLocaleString('pt-BR')} · {h.usuario_username}
                  </p>
                  <p className="text-sm text-gray-700 mt-0.5">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium mr-1 ${STATUS_CLS[h.status_anterior] || 'bg-gray-100 text-gray-600'}`}>
                      {h.status_anterior}
                    </span>
                    →
                    <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ml-1 ${STATUS_CLS[h.status_novo] || 'bg-gray-100 text-gray-600'}`}>
                      {h.status_novo}
                    </span>
                  </p>
                  {h.categoria_motivo && (
                    <span className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded mt-1 inline-block">
                      {h.categoria_motivo}
                    </span>
                  )}
                  {h.motivo && (
                    <p className="text-xs text-gray-500 mt-1 italic">"{h.motivo}"</p>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Histórico de número SEI */}
        {(current.historico_numero_sei || []).length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Histórico de número SEI</p>
            <ol className="relative border-l border-gray-200 space-y-3 ml-2">
              {current.historico_numero_sei.map((h) => (
                <li key={h.id} className="ml-4">
                  <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-gray-300 border-2 border-white" />
                  <p className="text-xs text-gray-400">
                    {new Date(h.criado_em).toLocaleString('pt-BR')} · {h.usuario_username}
                  </p>
                  <p className="text-sm text-gray-700 mt-0.5 font-mono">
                    <span className="line-through text-gray-400">{h.numero_anterior}</span>
                    {' → '}
                    <span className="text-gray-800">{h.numero_novo}</span>
                  </p>
                  {h.motivo && <p className="text-xs text-gray-500 mt-0.5 italic">"{h.motivo}"</p>}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  )
}

function DF({ label, error, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

const inp = (error) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 ${error ? 'border-red-400' : 'border-gray-300'}`
