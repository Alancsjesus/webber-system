import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import usePlanejamentoStore from '../stores/planejamentoStore'
import useAuthStore from '../stores/authStore'
import api, { downloadFile } from '../services/api'
import CampoMoeda from '../components/CampoMoeda'

const PRIO_OPTIONS = ['Alta', 'Média', 'Baixa']
const AREAS = ['TI', 'Formação', 'Ops', 'Rede', 'Frota', 'Derivados']

const STATUS_CLS = {
  Identificada: 'bg-gray-100 text-gray-600',
  'Em Análise': 'bg-yellow-100 text-yellow-700',
  Aprovada:     'bg-green-100 text-green-700',
  'DFD Criado': 'bg-blue-100 text-blue-700',
  Cancelada:    'bg-red-100 text-red-700',
}

const ACEITE_CLS = {
  pendente: 'bg-amber-100 text-amber-700',
  aceita:   'bg-green-100 text-green-700',
  recusada: 'bg-red-100 text-red-700',
}

const ACEITE_LABEL = {
  pendente: 'Aguardando aceite do órgão pai',
  aceita:   'Aceita pelo órgão pai',
  recusada: 'Recusada pelo órgão pai',
}

const PRIO_CLS = {
  Alta:  'bg-red-100 text-red-700',
  Média: 'bg-yellow-100 text-yellow-700',
  Baixa: 'bg-gray-100 text-gray-500',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Necessidade de Planejamento — Detalhe',
  descricao: 'Detalhe de uma necessidade de planejamento. Permite acompanhar o fluxo de aprovação e o DFD vinculado.',
  acoes: [
    { label: 'Editar',      texto: 'Habilita edição dos campos enquanto a necessidade estiver em Rascunho ou Devolvida.' },
    { label: 'Submeter',    texto: 'Envia para análise do gestor de planejamento.' },
    { label: 'Aprovar',     texto: 'Aprova a necessidade, liberando a criação do DFD correspondente.' },
    { label: 'Cancelar',    texto: 'Cancela a necessidade definitivamente.' },
    { label: 'Iniciar DFD', texto: 'Cria automaticamente um DFD vinculado a esta necessidade aprovada.' },
    { label: 'Ata de Registro de Preços (saque)', texto: 'Vincule quando esta necessidade for atendida por saque de uma Ata gerenciada por esta Secretaria — permite baixar o instrumento preparatório da Ata junto com o DFD para compor o SEI. Para adesão a Ata de outro órgão, o vínculo é feito no ETP (exige análise de vantajosidade, Art. 86).' },
    { label: 'Tramitação',  texto: 'Exibe o histórico completo de transições de status da necessidade, com data, usuário responsável e motivo de cada etapa.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function NecessidadeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { current, loading, error, fetchNecessidade, updateNecessidade, deleteNecessidade } = usePlanejamentoStore()
  const papel      = useAuthStore((s) => s.papel)
  const tipoUnidade = useAuthStore((s) => s.tipoUnidade)
  const orgId      = useAuthStore((s) => s.orgId)

  const isPlanejamento = tipoUnidade === 'planejamento' ||
    ['gestor_planejamento', 'admin'].includes(papel)

  const [activeTab, setActiveTab]   = useState('detalhes')
  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [formErrors, setFormErrors] = useState({})
  const [showBloquear, setShowBloquear] = useState(false)
  const [showRejeitar, setShowRejeitar] = useState(false)
  const [showRecusar, setShowRecusar]   = useState(false)
  const [motivo, setMotivo]             = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [orgaoAtual, setOrgaoAtual]  = useState(null)
  const [atasGerenciador, setAtasGerenciador] = useState([])

  useEffect(() => { fetchNecessidade(id) }, [id])
  useEffect(() => {
    if (current) setForm({ ...current })
  }, [current])

  useEffect(() => {
    api.get('/arp/', { params: { tipo_origem: 'gerenciador', status: 'vigente', page_size: 100 } })
      .then(({ data }) => setAtasGerenciador(data.results ?? data))
      .catch(() => {})
  }, [])

  // O órgão pai já está cadastrado na relação do próprio órgão (Orgao.parent) —
  // não é uma escolha do usuário, só carregamos para exibir/preencher.
  useEffect(() => {
    if (!orgId) return
    api.get(`/core/orgaos/${orgId}/`)
      .then(({ data }) => setOrgaoAtual(data))
      .catch(() => {})
  }, [orgId])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setFormErrors((p) => ({ ...p, [field]: undefined }))
  }

  const toggleArea = (area) =>
    setForm((p) => ({
      ...p,
      area_aplicacao: p.area_aplicacao.includes(area)
        ? p.area_aplicacao.filter((a) => a !== area)
        : [...p.area_aplicacao, area],
    }))

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateNecessidade(id, {
        titulo: form.titulo,
        descricao: form.descricao,
        area_aplicacao: form.area_aplicacao,
        valor_estimado: Number(form.valor_estimado),
        departamento_solicitante: form.departamento_solicitante,
        exercicio_fiscal: Number(form.exercicio_fiscal),
        prioridade: form.prioridade,
        prazo_desejado: form.prazo_desejado || null,
        observacoes: form.observacoes,
        tipo_execucao: form.tipo_execucao,
        orgao_executor: form.tipo_execucao === 'externa' && form.orgao_executor
          ? Number(form.orgao_executor) : null,
        ata_origem: form.ata_origem || null,
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

  const handleDelete = async () => {
    if (!confirm('Excluir esta necessidade?')) return
    await deleteNecessidade(id)
    navigate('/planejamento/necessidades')
  }

  const doAction = async (endpoint, body = {}) => {
    setActionLoading(true)
    try {
      await api.post(`/planejamento/necessidade/${id}/${endpoint}/`, body)
      await fetchNecessidade(id)
      setMotivo('')
      setShowBloquear(false)
      setShowRejeitar(false)
      setShowRecusar(false)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <p className="p-8 text-sm text-gray-400">Carregando...</p>
  if (error)   return <p className="p-8 text-sm text-red-600">{error}</p>
  if (!current || !form) return null

  const podeCriarDFD  = current.status === 'Aprovada' && !current.dfd
  const podeAprovar   = isPlanejamento && ['Identificada', 'Em Análise'].includes(current.status)
  const podeAnalisar  = isPlanejamento && current.status === 'Identificada'
  const podeBloq      = isPlanejamento && ['Identificada', 'Em Análise'].includes(current.status)
  const podeAceitar   = isPlanejamento && current.tipo_execucao === 'externa' && current.aceite_pai === 'pendente'
  const podeRecusar   = isPlanejamento && current.tipo_execucao === 'externa' && current.aceite_pai === 'pendente'

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">{current.titulo}</h1>
          <div className="flex flex-wrap gap-2 mt-1.5">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || ''}`}>
              {current.status}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${PRIO_CLS[current.prioridade] || ''}`}>
              {current.prioridade}
            </span>
            {current.tipo_execucao === 'externa' && (
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700">
                Execução Externa
              </span>
            )}
            {current.aceite_pai && (
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ACEITE_CLS[current.aceite_pai]}`}>
                {ACEITE_LABEL[current.aceite_pai]}
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 flex-wrap justify-end">
          <button
            onClick={() => downloadFile(`/planejamento/necessidade/${id}/export/historico/`, `Historico_Necessidade_${id}.pdf`)}
            className="border border-gray-300 text-gray-600 text-sm px-3 py-1.5 rounded-lg hover:bg-gray-50">
            ↓ Histórico PDF
          </button>
          {podeCriarDFD && (
            <button
              onClick={() => navigate('/aquisicao/preparar', {
                state: { origem: 'necessidade', necessidade: current },
              })}
              className="bg-green-600 hover:bg-green-700 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Preparar DFD →
            </button>
          )}
          {current.dfd && (
            <button onClick={() => navigate(`/demanda/dfd/${current.dfd}`)}
              className="bg-blue-50 border border-blue-200 text-blue-700 text-sm px-4 py-1.5 rounded-lg">
              Ver DFD #{current.dfd_numero_sei}
            </button>
          )}
          {podeAnalisar && (
            <button onClick={() => doAction('iniciar_analise')} disabled={actionLoading}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Iniciar Análise
            </button>
          )}
          {podeAprovar && (
            <button onClick={() => doAction('aprovar')} disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Aprovar
            </button>
          )}
          {podeAceitar && (
            <button onClick={() => doAction('aceitar')} disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg font-medium">
              Aceitar
            </button>
          )}
          {podeRecusar && (
            <button onClick={() => setShowRecusar(true)}
              className="border border-orange-300 text-orange-600 hover:bg-orange-50 text-sm px-4 py-1.5 rounded-lg font-medium">
              Recusar
            </button>
          )}
          {podeBloq && (
            <button onClick={() => setShowBloquear(true)}
              className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Bloquear
            </button>
          )}
          {!editing ? (
            <>
              <button onClick={() => setEditing(true)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
                Editar
              </button>
              <button onClick={handleDelete}
                className="border border-red-200 text-red-400 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
                Excluir
              </button>
            </>
          ) : (
            <>
              <button onClick={handleSave} disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
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

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {[
          { key: 'detalhes',   label: 'Detalhes' },
          { key: 'tramitacao', label: `Tramitação (${current.historico?.length ?? 0})` },
        ].map(tab => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Aceite pendente aviso */}
      {current.aceite_pai === 'pendente' && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-5 text-sm text-amber-700">
          Esta necessidade aguarda aceite do órgão superior <strong>{current.orgao_executor_sigla}</strong>.
        </div>
      )}
      {current.aceite_pai === 'recusada' && current.observacoes && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-5 text-sm text-red-700">
          <strong>Recusada:</strong> {current.observacoes}
        </div>
      )}

      {/* Modal Bloquear */}
      {showBloquear && (
        <MotivoModal title="Bloquear necessidade" label="Motivo do bloqueio *"
          motivo={motivo} setMotivo={setMotivo} loading={actionLoading}
          onConfirm={() => doAction('bloquear', { motivo })}
          onCancel={() => { setShowBloquear(false); setMotivo('') }} />
      )}

      {/* Modal Recusar */}
      {showRecusar && (
        <MotivoModal title="Recusar necessidade" label="Motivo da recusa *"
          motivo={motivo} setMotivo={setMotivo} loading={actionLoading}
          onConfirm={() => doAction('recusar', { motivo })}
          onCancel={() => { setShowRecusar(false); setMotivo('') }} />
      )}

      {/* DFD vinculado */}
      {current.dfd && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mb-5 text-sm text-blue-700">
          DFD gerado: <strong>{current.dfd_numero_sei}</strong>
        </div>
      )}

      {/* ── Tab: Tramitação ──────────────────────────────────────────────── */}
      {activeTab === 'tramitacao' && (
        <div className="space-y-3">
          {(!current.historico || current.historico.length === 0) ? (
            <p className="text-sm text-gray-400 italic">Nenhuma transição de status registrada ainda.</p>
          ) : (
            current.historico.map((h, idx) => (
              <div key={h.id} className="flex gap-3">
                <div className="flex flex-col items-center">
                  <div className="w-2.5 h-2.5 rounded-full bg-blue-400 mt-1 shrink-0" />
                  {idx < current.historico.length - 1 && (
                    <div className="w-px flex-1 bg-gray-200 mt-1" />
                  )}
                </div>
                <div className="pb-4 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-0.5">
                    <span className="text-xs text-gray-400">
                      {new Date(h.criado_em).toLocaleString('pt-BR')}
                    </span>
                    <span className="text-xs text-gray-500 font-medium">{h.usuario_username}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs">
                    {h.status_anterior && (
                      <>
                        <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-600">{h.status_anterior}</span>
                        <span className="text-gray-400">→</span>
                      </>
                    )}
                    <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium">{h.status_novo}</span>
                  </div>
                  {h.motivo && (
                    <p className="mt-1 text-xs text-gray-500 italic">{h.motivo}</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* ── Tab: Detalhes ─────────────────────────────────────────────────── */}
      {activeTab === 'detalhes' && <div className="space-y-5">
        <DF label="Descrição" error={formErrors.descricao}>
          {editing
            ? <textarea rows={3} value={form.descricao} onChange={(e) => set('descricao', e.target.value)} className={inp(formErrors.descricao)} />
            : <p className="text-sm text-gray-700">{current.descricao}</p>}
        </DF>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <DF label="Departamento solicitante" error={formErrors.departamento_solicitante}>
            {editing
              ? <input type="text" value={form.departamento_solicitante} onChange={(e) => set('departamento_solicitante', e.target.value)} className={inp(formErrors.departamento_solicitante)} />
              : <p className="text-sm text-gray-700">{current.departamento_solicitante}</p>}
          </DF>
          <DF label="Exercício fiscal">
            {editing
              ? <input type="number" value={form.exercicio_fiscal} onChange={(e) => set('exercicio_fiscal', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700">{current.exercicio_fiscal}</p>}
          </DF>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <DF label="Valor estimado">
            {editing
              ? <CampoMoeda value={form.valor_estimado} onChange={(v) => set('valor_estimado', v)} className={inp()} />
              : <p className="text-sm text-gray-700">{Number(current.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>}
          </DF>
          <DF label="Prioridade">
            {editing
              ? <select value={form.prioridade} onChange={(e) => set('prioridade', e.target.value)} className={inp()}>
                  {PRIO_OPTIONS.map((p) => <option key={p}>{p}</option>)}
                </select>
              : <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${PRIO_CLS[current.prioridade] || ''}`}>{current.prioridade}</span>}
          </DF>
        </div>

        {/* Execução */}
        <DF label="Tipo de execução">
          {editing ? (
            <div className="space-y-2">
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input type="radio" name="tipo_exec_edit" value="interna"
                    checked={form.tipo_execucao === 'interna'}
                    onChange={() => { set('tipo_execucao', 'interna'); set('orgao_executor', null) }}
                    className="accent-blue-600" />
                  <span className="text-sm">Interna</span>
                </label>
                <label className={`flex items-center gap-2 ${orgaoAtual && !orgaoAtual.parent ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
                  <input type="radio" name="tipo_exec_edit" value="externa"
                    checked={form.tipo_execucao === 'externa'}
                    disabled={!!orgaoAtual && !orgaoAtual.parent}
                    onChange={() => {
                      set('tipo_execucao', 'externa')
                      set('orgao_executor', orgaoAtual?.parent ? String(orgaoAtual.parent) : null)
                    }}
                    className="accent-blue-600" />
                  <span className="text-sm">Externa (órgão pai)</span>
                </label>
              </div>
              {form.tipo_execucao === 'externa' && (
                orgaoAtual?.parent ? (
                  <div className="w-full border border-gray-200 bg-gray-100 text-gray-700 rounded-lg px-3 py-2 text-sm">
                    {orgaoAtual.parent_sigla} — {orgaoAtual.parent_nome}
                  </div>
                ) : (
                  <p className="text-xs text-red-600">
                    {orgaoAtual
                      ? 'Este órgão não tem um órgão superior cadastrado — contate o administrador.'
                      : 'Carregando dados do órgão...'}
                  </p>
                )
              )}
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">
                {current.tipo_execucao === 'externa' ? 'Externa' : 'Interna'}
              </span>
              {current.orgao_executor_sigla && (
                <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded-full">
                  {current.orgao_executor_sigla}
                </span>
              )}
            </div>
          )}
        </DF>

        <DF label="Ata de Registro de Preços (saque)">
          {editing ? (
            <select value={form.ata_origem || ''} onChange={(e) => set('ata_origem', e.target.value || null)} className={inp()}>
              <option value="">Nenhuma (contratação regular)</option>
              {atasGerenciador.map((a) => (
                <option key={a.id} value={a.id}>{a.numero_ata} — {a.objeto?.slice(0, 50)}</option>
              ))}
            </select>
          ) : current.ata_origem_numero_ata ? (
            <p className="text-sm text-gray-700">
              <span className="bg-indigo-100 text-indigo-700 text-xs font-medium px-2 py-0.5 rounded-full mr-2">Saque de Ata</span>
              {current.ata_origem_numero_ata}
            </p>
          ) : (
            <p className="text-sm text-gray-400">—</p>
          )}
        </DF>

        <DF label="Áreas de aplicação" error={formErrors.area_aplicacao}>
          {editing
            ? <div className="flex flex-wrap gap-2">
                {AREAS.map((area) => {
                  const sel = form.area_aplicacao.includes(area)
                  return (
                    <button key={area} type="button" onClick={() => toggleArea(area)}
                      className={`px-3 py-1.5 rounded-lg text-sm border font-medium transition-colors ${
                        sel ? 'bg-blue-600 border-blue-600 text-white'
                            : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                      }`}>
                      {area}
                    </button>
                  )
                })}
              </div>
            : <div className="flex flex-wrap gap-1.5">
                {current.area_aplicacao.map((a) => (
                  <span key={a} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">{a}</span>
                ))}
              </div>}
        </DF>

        <DF label="Prazo desejado">
          {editing
            ? <input type="date" value={form.prazo_desejado || ''} min={new Date().toISOString().split('T')[0]} onChange={(e) => set('prazo_desejado', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700">
                {current.prazo_desejado ? new Date(current.prazo_desejado).toLocaleDateString('pt-BR') : '—'}
              </p>}
        </DF>

        <DF label="Observações">
          {editing
            ? <textarea rows={2} value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>}
        </DF>

        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado em: {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
        </div>
      </div>}
    </div>
  )
}

function MotivoModal({ title, label, motivo, setMotivo, loading, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="text-base font-semibold text-gray-800 mb-4">{title}</h3>
        <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
        <textarea rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <div className="flex gap-2 mt-4">
          <button onClick={onConfirm} disabled={!motivo.trim() || loading}
            className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {loading ? 'Processando...' : 'Confirmar'}
          </button>
          <button onClick={onCancel}
            className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
        </div>
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
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
