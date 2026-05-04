import { useEffect, useState } from 'react'
import ModalDevolver, { MOTIVOS_ETP } from '../components/ModalDevolver'
import { useNavigate, useParams } from 'react-router-dom'
import useEtpStore from '../stores/etpStore'
import useAuthStore from '../stores/authStore'
import { downloadFile } from '../services/api'

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
  Cancelado:   'bg-red-100 text-red-700',
}

const PAPEIS_ANALISTA   = ['admin', 'analista', 'gestor_planejamento', 'gestor_contrato', 'ordenador']
const PAPEIS_SOLICITANTE = ['solicitante', 'demandante', 'responsavel_tecnico', 'admin']

export default function ETPDetail() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const { current, loading, error, fetchEtp, updateEtp,
          submeterEtp, iniciarAnaliseEtp, aprovarEtp, devolverEtp } = useEtpStore()
  const { papel } = useAuthStore()

  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [formErrors, setFormErrors] = useState({})

  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError]     = useState(null)
  const [showDevolverModal, setShowDevolverModal] = useState(false)
  const [motivoDevolucao, setMotivoDevolucao]     = useState('')
  const [motivoNumeroSEI, setMotivoNumeroSEI]     = useState('')

  useEffect(() => { fetchEtp(id) }, [id])
  useEffect(() => { if (current) setForm({ ...current }) }, [current])

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
    try { await fn() } catch (err) {
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

  const podeEditar     = ['Rascunho', 'Devolvido'].includes(current.status) && !isAnalista
  const podeSubmeter   = ['Rascunho', 'Devolvido'].includes(current.status) && isSolicitante
  const podeAnalisar   = current.status === 'Submetido'   && isAnalista
  const podeAprovar    = current.status === 'Em Análise'  && isAnalista
  const podeDevolver   = current.status === 'Em Análise'  && isAnalista
  const podeCriarTR    = current.status === 'Aprovado' && !current.tr_id

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
          </div>
        </div>

        <div className="flex gap-2 flex-wrap justify-end">
          {podeCriarTR && (
            <button onClick={() => navigate('/analise-tecnica/trs/novo', { state: { etp: current } })}
              className="bg-teal-600 hover:bg-teal-700 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              + Criar TR
            </button>
          )}
          {current.tr_id && (
            <button onClick={() => navigate(`/analise-tecnica/trs/${current.tr_id}`)}
              className="bg-teal-50 border border-teal-200 text-teal-700 text-sm px-4 py-1.5 rounded-lg">
              Ver TR
            </button>
          )}
          <button onClick={() => downloadFile(`/etp/etp/${id}/export/pdf/`, `ETP_${current.numero_sei}.pdf`)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
            ↓ PDF
          </button>
          <button onClick={() => downloadFile(`/etp/etp/${id}/export/html/`, `ETP_${current.numero_sei}.html`)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
            ↓ HTML
          </button>
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
      {(podeSubmeter || podeAnalisar || podeAprovar || podeDevolver) && (
        <div className="mb-6 flex flex-wrap gap-2">
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

      {/* Fields */}
      <div className="space-y-5">
        {/* Número SEI — with change motivo when edited */}
        <DF label="Número SEI do ETP">
          {editing ? (
            <>
              <input type="text" value={form.numero_sei}
                onChange={(e) => set('numero_sei', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
              : <p className="text-sm text-gray-700 whitespace-pre-wrap">{current[field] || '—'}</p>}
          </DF>
        ))}

        <DF label="Estimativa de valor">
          {editing
            ? <input type="number" step="0.01" value={form.estimativa_valor || ''}
                onChange={(e) => set('estimativa_valor', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
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

            <DF label="Tipo de parcelamento (Lei 14.133, Art. 40, V)">
              {editing ? (
                <select value={form.tipo_parcelamento || ''}
                  onChange={e => set('tipo_parcelamento', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500">
                  <option value="">— Selecione —</option>
                  <option value="lote_unico">Lote único — contratação global</option>
                  <option value="lotes">Dividido em lotes — adjudicação por lote</option>
                  <option value="por_item">Por item — adjudicação individualizada</option>
                </select>
              ) : (
                <p className="text-sm text-gray-700">
                  {{ lote_unico: 'Lote único — contratação global', lotes: 'Dividido em lotes — adjudicação por lote', por_item: 'Por item — adjudicação individualizada' }[current.tipo_parcelamento] || '—'}
                </p>
              )}
            </DF>

            <DF label="Justificativa do parcelamento">
              {editing
                ? <textarea rows={2} value={form.parcelamento_justificativa || ''}
                    onChange={e => set('parcelamento_justificativa', e.target.value)}
                    placeholder="Justifique a decisão de parcelamento conforme Art. 40, V da Lei 14.133/2021..."
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                : <p className="text-sm text-gray-700 whitespace-pre-wrap">{current.parcelamento_justificativa || '—'}</p>}
            </DF>

          </div>
        </div>

        {/* ── Reserva de Cota ME/EPP ── */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-start gap-2 mb-1">
            <p className="text-xs font-semibold text-gray-400 uppercase">Reserva de Cota ME/EPP</p>
            <span className="text-[10px] bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">LC 123/2006, Art. 48</span>
          </div>
          <div className="space-y-4">

            <div>
              <label className={`flex items-center gap-3 cursor-pointer ${!editing ? 'opacity-70' : ''}`}>
                <input type="checkbox"
                  checked={editing ? (form.reserva_cota_me_epp ?? false) : (current.reserva_cota_me_epp ?? false)}
                  disabled={!editing}
                  onChange={e => set('reserva_cota_me_epp', e.target.checked)}
                  className="accent-green-600 w-4 h-4" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Reserva de cota de 25% para ME/EPP</p>
                  <p className="text-xs text-gray-400">Obrigatória para objetos divisíveis — Art. 48, III, LC 123/2006</p>
                </div>
              </label>
            </div>

            {(editing ? !form.reserva_cota_me_epp : !current.reserva_cota_me_epp) && (
              <DF label="Justificativa para não-reserva de cota">
                {editing
                  ? <textarea rows={2} value={form.reserva_cota_justificativa || ''}
                      onChange={e => set('reserva_cota_justificativa', e.target.value)}
                      placeholder="Justifique por que a reserva de cota não se aplica (ex: objeto indivisível, valor abaixo do limite)..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
                  : <p className="text-sm text-gray-700 whitespace-pre-wrap">{current.reserva_cota_justificativa || '—'}</p>}
              </DF>
            )}

            <div>
              <label className={`flex items-center gap-3 cursor-pointer ${!editing ? 'opacity-70' : ''}`}>
                <input type="checkbox"
                  checked={editing ? (form.licitacao_exclusiva_me_epp ?? false) : (current.licitacao_exclusiva_me_epp ?? false)}
                  disabled={!editing}
                  onChange={e => set('licitacao_exclusiva_me_epp', e.target.checked)}
                  className="accent-green-600 w-4 h-4" />
                <div>
                  <p className="text-sm font-medium text-gray-700">Licitação exclusiva ME/EPP</p>
                  <p className="text-xs text-gray-400">Para itens/lotes com valor até R$80.000 — Art. 48, I, LC 123/2006</p>
                </div>
              </label>
            </div>
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
                  {h.motivo && (
                    <p className="text-xs text-gray-500 mt-0.5 italic">"{h.motivo}"</p>
                  )}
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
