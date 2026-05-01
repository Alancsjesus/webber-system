import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useDFDStore from '../stores/dfdStore'
import useAuthStore from '../stores/authStore'
import api, { downloadFile } from '../services/api'

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetida:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvida:   'bg-orange-100 text-orange-700',
  Aprovada:    'bg-green-100 text-green-700',
  Rejeitada:   'bg-red-100 text-red-700',
}

const AREAS = ['TI', 'Formação', 'Ops', 'Rede', 'Frota', 'Derivados']

const ETAPAS_PROCESSO = [
  { value: 'dfd',       label: 'DFD' },
  { value: 'etp',       label: 'ETP' },
  { value: 'tr',        label: 'Termo de Referência' },
  { value: 'licitacao', label: 'Licitação' },
  { value: 'contrato',  label: 'Contrato' },
]

const PAPEIS_ANALISTA    = ['analista', 'gestor_planejamento', 'gestor_contrato', 'fiscal_contrato', 'ordenador', 'admin']
const PAPEIS_SOLICITANTE = ['solicitante', 'demandante', 'responsavel_tecnico', 'admin']

const MODALIDADES = [
  { value: 'licitacao',           label: 'Licitação' },
  { value: 'dispensa_valor',      label: 'Dispensa por Valor' },
  { value: 'dispensa_emergencia', label: 'Dispensa por Emergência' },
  { value: 'inexigibilidade',     label: 'Inexigibilidade' },
  { value: 'arp_saque',           label: 'Saque de ATA de Registro de Preços' },
]

export default function DFDDetail() {
  const { id }   = useParams()
  const navigate = useNavigate()
  const papel    = useAuthStore((s) => s.papel)
  const { current, loading, error, fetchDFD, updateDFD, deleteDFD,
          submeter, iniciarAnalise, aprovar, devolver } = useDFDStore()

  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [formErrors, setFormErrors] = useState({})

  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError]     = useState(null)
  const [showDevolverModal, setShowDevolverModal]   = useState(false)
  const [motivoDevolucao, setMotivoDevolucao]       = useState('')
  const [showDispensaModal, setShowDispensaModal]   = useState(false)
  const [motivoDispensa, setMotivoDispensa]         = useState('')
  const [dispensando, setDispensando]               = useState(false)

  // Itens
  const [itens, setItens]           = useState([])
  const [showAddItem, setShowAddItem] = useState(false)
  const [newItem, setNewItem]       = useState({ item_catalogo: '', objeto: '', unidade_medida: '', quantidade: '', valor_unitario_estimado: '', observacao: '' })
  const [savingItem, setSavingItem] = useState(false)
  const [catalogo, setCatalogo]     = useState([])
  const [buscaCatalogo, setBuscaCatalogo] = useState('')

  // Processos SEI
  const [processos, setProcessos] = useState([])
  const [showAddProcesso, setShowAddProcesso] = useState(false)
  const [newProcesso, setNewProcesso] = useState({ numero: '', etapa: 'dfd', descricao: '', data_abertura: '' })
  const [savingProcesso, setSavingProcesso] = useState(false)

  // Responsáveis pelo contrato
  const [users, setUsers]                       = useState([])
  const [editingResp, setEditingResp]           = useState(false)
  const [respForm, setRespForm]                 = useState({})
  const [savingResp, setSavingResp]             = useState(false)

  useEffect(() => {
    api.get('/core/users-list/').then(({ data }) => setUsers(data.results ?? data))
    api.get('/core/catalogo/', { params: { page_size: 500 } }).then(({ data }) => setCatalogo(data.results ?? data))
  }, [])

  useEffect(() => { fetchDFD(id) }, [id])

  useEffect(() => {
    if (current) {
      setForm({ ...current })
      setItens(current.itens || [])
      setProcessos(current.processos || [])
      setRespForm({
        fiscal_contrato:  current.fiscal_contrato  ?? '',
        fiscal_suplente:  current.fiscal_suplente  ?? '',
        gestor_contrato:  current.gestor_contrato  ?? '',
        gestor_suplente:  current.gestor_suplente  ?? '',
      })
    }
  }, [current])

  const setField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setFormErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const toggleArea = (area) => {
    setForm((prev) => {
      const list = prev.area_aplicacao
      return {
        ...prev,
        area_aplicacao: list.includes(area)
          ? list.filter((a) => a !== area)
          : [...list, area],
      }
    })
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateDFD(id, {
        descricao:                     form.descricao,
        modalidade_aquisicao:          form.modalidade_aquisicao,
        area_aplicacao:                form.area_aplicacao,
        prazo_necessidade:             form.prazo_necessidade,
        observacoes:                   form.observacoes,
        local_entrega:                 form.local_entrega,
        justificativa_sem_planejamento: form.justificativa_sem_planejamento,
      })
      setEditing(false)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      }
      setFormErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Deseja excluir este DFD? Esta ação não pode ser desfeita.')) return
    await deleteDFD(id)
    navigate('/demanda/dfd')
  }

  const runAction = async (fn) => {
    setActionLoading(true)
    setActionError(null)
    try {
      await fn()
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Erro ao executar ação.')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDevolver = async () => {
    if (!motivoDevolucao.trim()) return
    await runAction(() => devolver(id, motivoDevolucao))
    setShowDevolverModal(false)
    setMotivoDevolucao('')
  }

  // --- Itens ---
  const handleAddItem = async () => {
    if (!newItem.objeto.trim() || !newItem.unidade_medida.trim() ||
        !parseFloat(newItem.quantidade) || !parseFloat(newItem.valor_unitario_estimado)) return
    setSavingItem(true)
    try {
      const payload = {
        objeto: newItem.objeto,
        unidade_medida: newItem.unidade_medida,
        quantidade: parseFloat(newItem.quantidade),
        valor_unitario_estimado: parseFloat(newItem.valor_unitario_estimado),
        observacao: newItem.observacao,
      }
      if (newItem.item_catalogo) payload.item_catalogo = Number(newItem.item_catalogo)
      const { data } = await api.post(`/demanda/dfd/${id}/itens/`, payload)
      setItens((prev) => [...prev, data])
      setNewItem({ item_catalogo: '', objeto: '', unidade_medida: '', quantidade: '', valor_unitario_estimado: '', observacao: '' })
      setBuscaCatalogo('')
      setShowAddItem(false)
      fetchDFD(id)
    } finally {
      setSavingItem(false)
    }
  }

  const handleDeleteItem = async (itemId) => {
    await api.delete(`/demanda/dfd/${id}/itens/${itemId}/`)
    setItens((prev) => prev.filter((i) => i.id !== itemId))
    fetchDFD(id)
  }

  // --- Processos ---
  const handleAddProcesso = async () => {
    if (!newProcesso.numero.trim() || !newProcesso.etapa) return
    setSavingProcesso(true)
    try {
      const { data } = await api.post(`/demanda/dfd/${id}/processos/`, newProcesso)
      setProcessos((prev) => [...prev, data])
      setNewProcesso({ numero: '', etapa: 'dfd', descricao: '', data_abertura: '' })
      setShowAddProcesso(false)
    } finally {
      setSavingProcesso(false)
    }
  }

  const handleDeleteProcesso = async (procId) => {
    await api.delete(`/demanda/dfd/${id}/processos/${procId}/`)
    setProcessos((prev) => prev.filter((p) => p.id !== procId))
  }

  if (loading) return <div className="p-8 text-sm text-gray-400">Carregando...</div>
  if (error)   return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current || !form) return null

  const podeEditar             = ['Rascunho', 'Devolvida'].includes(current.status) && PAPEIS_SOLICITANTE.includes(papel)
  const podeSubmeter           = ['Rascunho', 'Devolvida'].includes(current.status) && PAPEIS_SOLICITANTE.includes(papel)
  const podeAnalisar           = current.status === 'Submetida'   && PAPEIS_ANALISTA.includes(papel)
  const podeAprovar            = current.status === 'Em Análise'  && PAPEIS_ANALISTA.includes(papel)
  const podeDevolver           = current.status === 'Em Análise'  && PAPEIS_ANALISTA.includes(papel)
  const podeCriarEtp           = current.status === 'Aprovada' && !current.etp_id && PAPEIS_ANALISTA.includes(papel)
  const podeDispensarEtp       = current.status === 'Aprovada' && !current.etp_id && PAPEIS_ANALISTA.includes(papel)
  const podeEditarResponsaveis = ['admin', 'gestor_contrato'].includes(papel)

  const handleDispensarEtp = async () => {
    if (!motivoDispensa.trim()) return
    setDispensando(true)
    setActionError(null)
    try {
      const { data } = await api.post(`/demanda/dfd/${id}/dispensar_etp/`, { motivo: motivoDispensa })
      setShowDispensaModal(false)
      setMotivoDispensa('')
      // Navega para criar TR diretamente, passando o ETP dispensado como contexto
      navigate('/analise-tecnica/trs/novo', { state: { etp: data } })
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Erro ao dispensar ETP.')
    } finally {
      setDispensando(false)
    }
  }

  const handleSaveResp = async () => {
    setSavingResp(true)
    try {
      await updateDFD(id, {
        fiscal_contrato: respForm.fiscal_contrato  || null,
        fiscal_suplente: respForm.fiscal_suplente  || null,
        gestor_contrato: respForm.gestor_contrato  || null,
        gestor_suplente: respForm.gestor_suplente  || null,
      })
      setEditingResp(false)
    } finally {
      setSavingResp(false)
    }
  }

  const totalItens = itens.reduce((acc, i) => acc + parseFloat(i.valor_total_estimado || 0), 0)

  return (
    <div className="p-8 max-w-2xl">
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-gray-400 hover:text-gray-600 mb-4 inline-flex items-center gap-1"
      >
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero_sei}</h1>
          <span className={`mt-1 inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || 'bg-gray-100 text-gray-600'}`}>
            {current.status}
          </span>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {!editing ? (
            <>
              {podeCriarEtp && (
                <button onClick={() => navigate('/etp/etps/novo', { state: { dfd: current } })}
                  className="bg-purple-600 hover:bg-purple-700 text-white text-sm px-4 py-1.5 rounded-lg transition-colors font-medium">
                  + Criar ETP
                </button>
              )}
              {podeDispensarEtp && (
                <button onClick={() => setShowDispensaModal(true)}
                  className="bg-amber-100 border border-amber-300 text-amber-800 hover:bg-amber-200 text-sm px-4 py-1.5 rounded-lg transition-colors font-medium">
                  Dispensar ETP → TR
                </button>
              )}
              {current.etp_id && !current.etp_dispensado && (
                <button onClick={() => navigate(`/etp/etps/${current.etp_id}`)}
                  className="bg-purple-50 border border-purple-200 text-purple-700 text-sm px-4 py-1.5 rounded-lg transition-colors">
                  Ver ETP
                </button>
              )}
              {current.etp_id && current.etp_dispensado && (
                <button onClick={() => navigate(`/etp/etps/${current.etp_id}`)}
                  className="bg-amber-50 border border-amber-200 text-amber-700 text-sm px-4 py-1.5 rounded-lg transition-colors">
                  ETP Dispensado → Ver TR
                </button>
              )}
              {podeEditar && (
                <button onClick={() => setEditing(true)}
                  className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
                  Editar
                </button>
              )}
              <button onClick={() => downloadFile(`/demanda/dfd/${id}/export/pdf/`, `DFD_${current.numero_sei}.pdf`)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
                ↓ PDF
              </button>
              <button onClick={() => downloadFile(`/demanda/dfd/${id}/export/html/`, `DFD_${current.numero_sei}.html`)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
                ↓ HTML
              </button>
              <button onClick={handleDelete}
                className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
                Excluir
              </button>
            </>
          ) : (
            <>
              <button onClick={handleSave} disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg transition-colors">
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button onClick={() => { setEditing(false); setForm({ ...current }) }}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>

      {current.status === 'Devolvida' && current.motivo_devolucao && (
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

      {/* Botões de workflow */}
      {(podeSubmeter || podeAnalisar || podeAprovar || podeDevolver) && (
        <div className="mb-6 flex flex-wrap gap-2">
          {podeSubmeter && (
            <button onClick={() => runAction(() => submeter(id))} disabled={actionLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              {actionLoading ? '...' : '↑ Submeter para análise'}
            </button>
          )}
          {podeAnalisar && (
            <button onClick={() => runAction(() => iniciarAnalise(id))} disabled={actionLoading}
              className="bg-yellow-500 hover:bg-yellow-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              {actionLoading ? '...' : '🔍 Iniciar análise'}
            </button>
          )}
          {podeAprovar && (
            <button onClick={() => runAction(() => aprovar(id))} disabled={actionLoading}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              {actionLoading ? '...' : '✓ Aprovar'}
            </button>
          )}
          {podeDevolver && (
            <button onClick={() => setShowDevolverModal(true)} disabled={actionLoading}
              className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
              ↩ Devolver para ajuste
            </button>
          )}
        </div>
      )}

      {showDevolverModal && (
        <div className="mb-6 bg-orange-50 border border-orange-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-orange-800 mb-2">Informe o motivo da devolução</p>
          <textarea rows={3} value={motivoDevolucao}
            onChange={(e) => setMotivoDevolucao(e.target.value)}
            placeholder="Descreva o que precisa ser ajustado..."
            className="w-full border border-orange-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white" />
          <div className="flex gap-2 mt-2">
            <button onClick={handleDevolver} disabled={!motivoDevolucao.trim() || actionLoading}
              className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors">
              {actionLoading ? '...' : 'Confirmar devolução'}
            </button>
            <button onClick={() => { setShowDevolverModal(false); setMotivoDevolucao('') }}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {showDispensaModal && (
        <div className="mb-6 bg-amber-50 border border-amber-300 rounded-xl p-4">
          <p className="text-sm font-semibold text-amber-800 mb-1">Dispensar ETP e criar TR diretamente</p>
          <p className="text-xs text-amber-700 mb-3">
            Use quando a modalidade for dispensa por valor, dispensa por emergência ou saque de ARP,
            ou quando o valor estimado estiver abaixo do limite configurado.
          </p>
          <textarea rows={3} value={motivoDispensa}
            onChange={(e) => setMotivoDispensa(e.target.value)}
            placeholder="Informe o motivo da dispensa (ex: valor abaixo do limite de R$ 62.000, ARP vigente nº ...)..."
            className="w-full border border-amber-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white" />
          <div className="flex gap-2 mt-2">
            <button onClick={handleDispensarEtp} disabled={!motivoDispensa.trim() || dispensando}
              className="bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors">
              {dispensando ? '...' : 'Confirmar dispensa → Criar TR'}
            </button>
            <button onClick={() => { setShowDispensaModal(false); setMotivoDispensa('') }}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Vínculo com planejamento */}
      {current.necessidade_origem ? (
        <div className="mb-5 bg-green-50 border border-green-200 rounded-xl px-4 py-3">
          <p className="text-xs font-semibold text-green-700 uppercase mb-1">Necessidade de planejamento vinculada</p>
          <p className="text-sm text-green-800 font-medium">{current.necessidade_origem.titulo}</p>
          <p className="text-xs text-green-600 mt-0.5">
            Exercício {current.necessidade_origem.exercicio_fiscal} · Status: {current.necessidade_origem.status}
          </p>
        </div>
      ) : (
        <div className="mb-5 bg-amber-50 border border-amber-300 rounded-xl px-4 py-3">
          <p className="text-xs font-semibold text-amber-700 uppercase mb-1">Fora do planejamento</p>
          {editing ? (
            <>
              <p className="text-xs text-amber-600 mb-1">Justificativa obrigatória para submissão:</p>
              <textarea
                rows={3}
                value={form.justificativa_sem_planejamento || ''}
                onChange={(e) => setField('justificativa_sem_planejamento', e.target.value)}
                placeholder="Justifique por que esta demanda não consta no planejamento..."
                className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white ${formErrors.justificativa_sem_planejamento ? 'border-red-400' : 'border-amber-300'}`}
              />
              {formErrors.justificativa_sem_planejamento && (
                <p className="text-xs text-red-600 mt-1">{formErrors.justificativa_sem_planejamento}</p>
              )}
            </>
          ) : current.justificativa_sem_planejamento ? (
            <p className="text-sm text-amber-800">{current.justificativa_sem_planejamento}</p>
          ) : (
            <p className="text-sm text-amber-700 italic">Justificativa não informada — necessária para submissão.</p>
          )}
        </div>
      )}

      {/* Unidades responsáveis */}
      <div className="mb-5 border border-gray-200 rounded-xl p-4 bg-white">
        <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Unidades responsáveis</p>
        <div className="grid grid-cols-3 gap-3">
          <UnitCard label="Demandante" nome={current.unidade_demandante_nome} color="blue" />
          <UnitCard label="Licitante"  nome={current.unidade_licitante_nome}  color="yellow" />
          <UnitCard label="Contratante" nome={current.unidade_contratante_nome} color="green" />
        </div>
      </div>

      {/* Responsáveis pelo Contrato */}
      <div className="mb-5 border border-gray-200 rounded-xl p-4 bg-white">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-gray-400 uppercase">Responsáveis pelo Contrato</p>
          {podeEditarResponsaveis && !editingResp && (
            <button onClick={() => setEditingResp(true)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              Editar
            </button>
          )}
          {editingResp && (
            <div className="flex gap-2">
              <button onClick={handleSaveResp} disabled={savingResp}
                className="text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-3 py-1 rounded-lg">
                {savingResp ? 'Salvando...' : 'Salvar'}
              </button>
              <button onClick={() => { setEditingResp(false); setRespForm({ fiscal_contrato: current.fiscal_contrato ?? '', fiscal_suplente: current.fiscal_suplente ?? '', gestor_contrato: current.gestor_contrato ?? '', gestor_suplente: current.gestor_suplente ?? '' }) }}
                className="text-xs border border-gray-300 text-gray-600 hover:bg-gray-50 px-3 py-1 rounded-lg">
                Cancelar
              </button>
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 gap-3">
          <RespCard
            label="Fiscal Titular"
            username={current.fiscal_contrato_username}
            fieldKey="fiscal_contrato"
            editing={editingResp}
            value={respForm.fiscal_contrato}
            users={users}
            onChange={(v) => setRespForm((p) => ({ ...p, fiscal_contrato: v }))}
          />
          <RespCard
            label="Fiscal Suplente"
            username={current.fiscal_suplente_username}
            fieldKey="fiscal_suplente"
            editing={editingResp}
            value={respForm.fiscal_suplente}
            users={users}
            onChange={(v) => setRespForm((p) => ({ ...p, fiscal_suplente: v }))}
          />
          <RespCard
            label="Gestor Titular"
            username={current.gestor_contrato_username}
            fieldKey="gestor_contrato"
            editing={editingResp}
            value={respForm.gestor_contrato}
            users={users}
            onChange={(v) => setRespForm((p) => ({ ...p, gestor_contrato: v }))}
          />
          <RespCard
            label="Gestor Suplente"
            username={current.gestor_suplente_username}
            fieldKey="gestor_suplente"
            editing={editingResp}
            value={respForm.gestor_suplente}
            users={users}
            onChange={(v) => setRespForm((p) => ({ ...p, gestor_suplente: v }))}
          />
        </div>
      </div>

      {/* Campos do DFD */}
      <div className="space-y-5">
        <DetailField label="Descrição" error={formErrors.descricao}>
          {editing ? (
            <textarea rows={3} value={form.descricao}
              onChange={(e) => setField('descricao', e.target.value)}
              className={inputCls(formErrors.descricao)} />
          ) : (
            <p className="text-sm text-gray-700">{current.descricao}</p>
          )}
        </DetailField>

        <DetailField label="Modalidade de aquisição">
          {editing ? (
            <select value={form.modalidade_aquisicao || 'licitacao'}
              onChange={(e) => setField('modalidade_aquisicao', e.target.value)}
              className={inputCls()}>
              {MODALIDADES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-gray-700">{current.modalidade_display || current.modalidade_aquisicao || 'Licitação'}</p>
          )}
        </DetailField>

        <DetailField label="Valor estimado">
          <p className="text-sm text-gray-700 font-semibold">
            {Number(current.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </p>
          {itens.length > 0 && Math.abs(totalItens - Number(current.valor_estimado)) > 0.01 && (
            <p className="text-xs text-amber-600 mt-0.5">
              Total dos itens: {totalItens.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
            </p>
          )}
        </DetailField>

        <DetailField label="Áreas de aplicação" error={formErrors.area_aplicacao}>
          {editing ? (
            <div className="flex flex-wrap gap-2">
              {AREAS.map((area) => {
                const selected = form.area_aplicacao.includes(area)
                return (
                  <button key={area} type="button" onClick={() => toggleArea(area)}
                    className={`px-3 py-1.5 rounded-lg text-sm border font-medium transition-colors ${
                      selected ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                    }`}>
                    {area}
                  </button>
                )
              })}
            </div>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {current.area_aplicacao.map((a) => (
                <span key={a} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded-full">{a}</span>
              ))}
            </div>
          )}
        </DetailField>

        <DetailField label="Prazo de necessidade" error={formErrors.prazo_necessidade}>
          {editing ? (
            <input type="date" value={form.prazo_necessidade}
              onChange={(e) => setField('prazo_necessidade', e.target.value)}
              className={inputCls(formErrors.prazo_necessidade)} />
          ) : (
            <p className="text-sm text-gray-700">
              {new Date(current.prazo_necessidade).toLocaleDateString('pt-BR')}
            </p>
          )}
        </DetailField>

        <DetailField label="Observações" error={formErrors.observacoes}>
          {editing ? (
            <textarea rows={2} value={form.observacoes || ''}
              onChange={(e) => setField('observacoes', e.target.value)}
              className={inputCls()} />
          ) : (
            <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>
          )}
        </DetailField>

        <DetailField label="Local de entrega">
          {editing ? (
            <textarea rows={2} value={form.local_entrega || ''}
              onChange={(e) => setField('local_entrega', e.target.value)}
              placeholder="Endereço ou local onde o bem/serviço será entregue..."
              className={inputCls()} />
          ) : (
            <p className="text-sm text-gray-500">{current.local_entrega || '—'}</p>
          )}
        </DetailField>

        {/* Itens da demanda */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">Itens da demanda</p>
            {podeEditar && (
              <button onClick={() => setShowAddItem((v) => !v)}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                {showAddItem ? 'Cancelar' : '+ Adicionar item'}
              </button>
            )}
          </div>

          {itens.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 uppercase text-left border-b border-gray-100">
                    <th className="pb-1 pr-3">Objeto</th>
                    <th className="pb-1 pr-3">Unid.</th>
                    <th className="pb-1 pr-3 text-right">Qtd</th>
                    <th className="pb-1 pr-3 text-right">Vl. Unit.</th>
                    <th className="pb-1 text-right">Total</th>
                    {podeEditar && <th className="pb-1 w-8" />}
                  </tr>
                </thead>
                <tbody>
                  {itens.map((item) => (
                    <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-1.5 pr-3 text-gray-700">
                        {item.catalogo_familia && (
                          <span className="mr-1 bg-blue-100 text-blue-700 text-[10px] font-mono px-1 py-0.5 rounded">{item.catalogo_familia}</span>
                        )}
                        {item.objeto}
                      </td>
                      <td className="py-1.5 pr-3 text-gray-500">{item.unidade_medida}</td>
                      <td className="py-1.5 pr-3 text-right text-gray-700">{Number(item.quantidade).toLocaleString('pt-BR')}</td>
                      <td className="py-1.5 pr-3 text-right text-gray-700">{Number(item.valor_unitario_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                      <td className="py-1.5 text-right font-semibold text-gray-800">{Number(item.valor_total_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                      {podeEditar && (
                        <td className="py-1.5 text-right">
                          <button onClick={() => handleDeleteItem(item.id)} className="text-red-400 hover:text-red-600">✕</button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={podeEditar ? 4 : 4} className="pt-2 text-right text-xs text-gray-400 uppercase font-semibold">Total</td>
                    <td className="pt-2 text-right text-sm font-bold text-gray-800">
                      {totalItens.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </td>
                    {podeEditar && <td />}
                  </tr>
                </tfoot>
              </table>
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">Nenhum item cadastrado.</p>
          )}

          {showAddItem && (
            <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
              <p className="text-xs font-semibold text-blue-700 mb-2">Novo item</p>
              <div className="grid grid-cols-2 gap-2">
                {/* Busca no catálogo */}
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Buscar no catálogo (opcional)</label>
                  <input type="text" value={buscaCatalogo}
                    onChange={e => setBuscaCatalogo(e.target.value)}
                    placeholder="Digite para buscar por nome, SIMPAS ou código..."
                    className={inputCls()} />
                  {buscaCatalogo.length >= 2 && (
                    <div className="mt-1 bg-white border border-blue-200 rounded-lg shadow-sm max-h-40 overflow-y-auto">
                      {catalogo.filter(c =>
                        c.nome.toLowerCase().includes(buscaCatalogo.toLowerCase()) ||
                        c.codigo_simpas.includes(buscaCatalogo) ||
                        c.codigo_interno.includes(buscaCatalogo)
                      ).slice(0, 8).map(c => (
                        <button key={c.id} type="button"
                          onClick={() => {
                            setNewItem(p => ({ ...p, item_catalogo: c.id, objeto: c.nome, unidade_medida: c.unidade_medida }))
                            setBuscaCatalogo('')
                          }}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-blue-50 border-b border-gray-50 last:border-0">
                          <span className="font-mono text-blue-700 mr-1">{c.codigo_interno}</span>
                          {c.familia && <span className="bg-blue-100 text-blue-600 text-[10px] px-1 rounded mr-1">{c.familia}</span>}
                          {c.nome}
                        </button>
                      ))}
                      {catalogo.filter(c =>
                        c.nome.toLowerCase().includes(buscaCatalogo.toLowerCase()) ||
                        c.codigo_simpas.includes(buscaCatalogo)
                      ).length === 0 && (
                        <p className="px-3 py-2 text-xs text-gray-400 italic">Nenhum item encontrado no catálogo.</p>
                      )}
                    </div>
                  )}
                  {newItem.item_catalogo && (
                    <div className="mt-1 flex items-center gap-2 text-xs text-blue-700 bg-blue-50 rounded px-2 py-1">
                      <span>Vinculado ao catálogo</span>
                      <button type="button" onClick={() => setNewItem(p => ({ ...p, item_catalogo: '' }))} className="text-red-500 hover:underline">remover</button>
                    </div>
                  )}
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Objeto</label>
                  <input type="text" value={newItem.objeto}
                    onChange={(e) => setNewItem((p) => ({ ...p, objeto: e.target.value }))}
                    className={inputCls()} placeholder="Ex: Notebook Dell" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Unidade</label>
                  <input type="text" value={newItem.unidade_medida}
                    onChange={(e) => setNewItem((p) => ({ ...p, unidade_medida: e.target.value }))}
                    className={inputCls()} placeholder="UN" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Quantidade</label>
                  <input type="number" min="0" step="0.0001" value={newItem.quantidade}
                    onChange={(e) => setNewItem((p) => ({ ...p, quantidade: e.target.value }))}
                    className={inputCls()} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Valor unitário (R$)</label>
                  <input type="number" min="0" step="0.01" value={newItem.valor_unitario_estimado}
                    onChange={(e) => setNewItem((p) => ({ ...p, valor_unitario_estimado: e.target.value }))}
                    className={inputCls()} />
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <button onClick={handleAddItem} disabled={savingItem}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                  {savingItem ? 'Salvando...' : 'Salvar item'}
                </button>
                <button onClick={() => setShowAddItem(false)}
                  className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg hover:bg-gray-50">
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Processos SEI */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">Processos SEI</p>
            <button onClick={() => setShowAddProcesso((v) => !v)}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              {showAddProcesso ? 'Cancelar' : '+ Vincular processo'}
            </button>
          </div>

          {processos.length > 0 ? (
            <ul className="space-y-2">
              {processos.map((proc) => (
                <li key={proc.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                  <div>
                    <span className="font-mono text-sm text-gray-800">{proc.numero}</span>
                    <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">
                      {proc.etapa_display}
                    </span>
                    {proc.descricao && (
                      <p className="text-xs text-gray-500 mt-0.5">{proc.descricao}</p>
                    )}
                  </div>
                  <button onClick={() => handleDeleteProcesso(proc.id)}
                    className="text-red-400 hover:text-red-600 text-xs ml-3">✕</button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-gray-400 italic">Nenhum processo vinculado.</p>
          )}

          {showAddProcesso && (
            <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
              <p className="text-xs font-semibold text-blue-700 mb-2">Vincular número de processo</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Número do processo</label>
                  <input type="text" value={newProcesso.numero}
                    onChange={(e) => setNewProcesso((p) => ({ ...p, numero: e.target.value }))}
                    placeholder="Ex: 00060.000123/2025-00"
                    className={inputCls()} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Etapa</label>
                  <select value={newProcesso.etapa}
                    onChange={(e) => setNewProcesso((p) => ({ ...p, etapa: e.target.value }))}
                    className={inputCls()}>
                    {ETAPAS_PROCESSO.map(({ value, label }) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Data de abertura</label>
                  <input type="date" value={newProcesso.data_abertura}
                    onChange={(e) => setNewProcesso((p) => ({ ...p, data_abertura: e.target.value }))}
                    className={inputCls()} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Descrição (opcional)</label>
                  <input type="text" value={newProcesso.descricao}
                    onChange={(e) => setNewProcesso((p) => ({ ...p, descricao: e.target.value }))}
                    className={inputCls()} />
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <button onClick={handleAddProcesso} disabled={savingProcesso}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                  {savingProcesso ? 'Salvando...' : 'Vincular'}
                </button>
                <button onClick={() => setShowAddProcesso(false)}
                  className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg hover:bg-gray-50">
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Metadados */}
        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado por: {current.created_by_username} em {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
        </div>

        {/* Histórico de tramitação */}
        {(current.historico || []).length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Histórico de tramitação</p>
            <ol className="relative border-l border-gray-200 space-y-4 ml-2">
              {current.historico.map((h) => (
                <li key={h.id} className="ml-4">
                  <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-blue-400 border-2 border-white" />
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
      </div>
    </div>
  )
}

function RespCard({ label, username, editing, value, users, onChange }) {
  return (
    <div className="border border-gray-200 rounded-lg px-3 py-2 bg-gray-50">
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
      {editing ? (
        <select
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
          className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="">— Não definido —</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.first_name ? `${u.first_name} ${u.last_name} (${u.username})` : u.username}
            </option>
          ))}
        </select>
      ) : (
        <p className="text-sm text-gray-700">
          {username || <span className="italic text-gray-400">Não definido</span>}
        </p>
      )}
    </div>
  )
}

function UnitCard({ label, nome, color }) {
  const colors = {
    blue:   'border-blue-200 bg-blue-50 text-blue-700',
    yellow: 'border-yellow-200 bg-yellow-50 text-yellow-700',
    green:  'border-green-200 bg-green-50 text-green-700',
  }
  return (
    <div className={`border rounded-lg px-3 py-2 ${colors[color]}`}>
      <p className="text-xs font-semibold uppercase mb-1 opacity-70">{label}</p>
      <p className="text-sm font-medium">{nome || <span className="italic opacity-50">não definida</span>}</p>
    </div>
  )
}

function DetailField({ label, error, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
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
