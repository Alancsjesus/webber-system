import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useEtpStore from '../stores/etpStore'
import useAuthStore from '../stores/authStore'

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

  const handleDevolver = async () => {
    if (!motivoDevolucao.trim()) return
    await runAction(() => devolverEtp(id, motivoDevolucao))
    setShowDevolverModal(false)
    setMotivoDevolucao('')
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

      {showDevolverModal && (
        <div className="mb-6 bg-orange-50 border border-orange-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-orange-800 mb-2">Motivo da devolução</p>
          <textarea rows={3} value={motivoDevolucao}
            onChange={(e) => setMotivoDevolucao(e.target.value)}
            placeholder="Descreva o que precisa ser ajustado..."
            className="w-full border border-orange-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white" />
          <div className="flex gap-2 mt-2">
            <button onClick={handleDevolver} disabled={!motivoDevolucao.trim() || actionLoading}
              className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
              {actionLoading ? '...' : 'Confirmar'}
            </button>
            <button onClick={() => { setShowDevolverModal(false); setMotivoDevolucao('') }}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg">
              Cancelar
            </button>
          </div>
        </div>
      )}

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
