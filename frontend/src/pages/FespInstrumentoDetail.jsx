import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useInstrumentoFinanceiroStore from '../stores/instrumentoFinanceiroStore'
import useOrcamentoStore from '../stores/orcamentoStore'
import CampoMoeda from '../components/CampoMoeda'
import CampoSei from '../components/CampoSei'
import LoadingSpinner from '../components/LoadingSpinner'
import { TIPO_INSTRUMENTO_OPTIONS, STATUS_INSTRUMENTO_CLS } from './FespInstrumentoList'
import { formatarMoeda } from '../utils/currencyMask'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Instrumento Financeiro — Detalhe',
  descricao: 'Detalhe do instrumento externo (convênio, emenda, repasse etc.) que financia itens de Planos de Aplicação.',
  acoes: [
    { label: 'Ativar',   texto: 'Torna o instrumento Vigente, habilitando-o a financiar itens de um Plano de Aplicação.' },
    { label: 'Encerrar', texto: 'Marca o instrumento como Encerrado ao fim de sua vigência — exige motivo.' },
    { label: 'Cancelar', texto: 'Cancela o instrumento definitivamente — exige motivo.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FespInstrumentoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    current, loading, error,
    fetchInstrumento, updateInstrumento, deleteInstrumento,
    ativar, encerrar, cancelar,
  } = useInstrumentoFinanceiroStore()
  const { fontes, fetchFontes } = useOrcamentoStore()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})
  const [actionMsg, setActionMsg] = useState(null)
  const [showMotivo, setShowMotivo] = useState(null) // 'encerrar' | 'cancelar'
  const [motivo, setMotivo] = useState('')

  useEffect(() => { fetchInstrumento(id); fetchFontes() }, [id])

  useEffect(() => {
    if (current) {
      setForm({
        objeto: current.objeto,
        orgao_concedente_nome: current.orgao_concedente_nome || '',
        fonte_recurso: current.fonte_recurso || '',
        valor_total_pactuado: current.valor_total_pactuado,
        valor_contrapartida: current.valor_contrapartida,
        data_assinatura: current.data_assinatura || '',
        vigencia_inicio: current.vigencia_inicio || '',
        vigencia_fim: current.vigencia_fim || '',
        numero_processo_sei: current.numero_processo_sei || '',
        observacoes: current.observacoes || '',
      })
    }
  }, [current])

  const set = (field, value) => {
    setForm((p) => ({ ...p, [field]: value }))
    setErrors((p) => ({ ...p, [field]: undefined }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateInstrumento(id, {
        ...form,
        fonte_recurso: form.fonte_recurso || null,
        valor_total_pactuado: Number(form.valor_total_pactuado),
        valor_contrapartida: Number(form.valor_contrapartida || 0),
        data_assinatura: form.data_assinatura || null,
        vigencia_inicio: form.vigencia_inicio || null,
        vigencia_fim: form.vigencia_fim || null,
      })
      setEditing(false)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Excluir este instrumento financeiro? Esta ação não pode ser desfeita.')) return
    setSaving(true)
    setActionMsg(null)
    try {
      await deleteInstrumento(id)
      navigate('/fesp/instrumentos')
    } catch (err) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao excluir o instrumento (pode estar em uso por itens de um plano).' })
      setSaving(false)
    }
  }

  const act = async (fn, ...args) => {
    setSaving(true)
    setActionMsg(null)
    try {
      await fn(...args)
      setActionMsg({ type: 'success', text: 'Operação realizada com sucesso.' })
      setShowMotivo(null)
      setMotivo('')
    } catch (err) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao executar operação.' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando instrumento..." /></div>
  if (error) return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current || !form) return null

  const isRascunho = current.status === 'rascunho'
  const isVigente = current.status === 'vigente'

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero_instrumento}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_INSTRUMENTO_CLS[current.status] || ''}`}>
              {current.status_display}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">{current.tipo_instrumento_display}</p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {!editing && (
            <button onClick={() => setEditing(true)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Editar
            </button>
          )}
          {isRascunho && (
            <button onClick={() => act(ativar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Ativar (tornar vigente)
            </button>
          )}
          {isVigente && (
            <button onClick={() => setShowMotivo('encerrar')}
              className="border border-blue-300 text-blue-600 hover:bg-blue-50 text-sm px-4 py-1.5 rounded-lg">
              Encerrar
            </button>
          )}
          {(isRascunho || isVigente) && (
            <button onClick={() => setShowMotivo('cancelar')}
              className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Cancelar
            </button>
          )}
          {isRascunho && (
            <button onClick={handleDelete}
              className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Excluir
            </button>
          )}
        </div>
      </div>

      {actionMsg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${actionMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {actionMsg.text}
        </div>
      )}

      {showMotivo && (
        <div className="mb-4 bg-gray-50 border border-gray-200 rounded-xl p-4">
          <p className="text-sm font-semibold text-gray-700 mb-2">
            {showMotivo === 'encerrar' ? 'Motivo do encerramento' : 'Motivo do cancelamento'}
          </p>
          <textarea rows={2} value={motivo} onChange={(e) => setMotivo(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-2" />
          <div className="flex gap-2">
            <button
              onClick={() => act(showMotivo === 'encerrar' ? encerrar : cancelar, id, motivo)}
              disabled={saving || !motivo.trim()}
              className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Confirmar
            </button>
            <button onClick={() => { setShowMotivo(null); setMotivo('') }}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="space-y-5">
        <DetailField label="Objeto" error={errors.objeto}>
          {editing ? (
            <textarea rows={3} value={form.objeto} onChange={(e) => set('objeto', e.target.value)} className={inputCls(errors.objeto)} />
          ) : <p className="text-sm text-gray-700">{current.objeto}</p>}
        </DetailField>

        <DetailField label="Órgão/ente concedente">
          {editing ? (
            <input type="text" value={form.orgao_concedente_nome} onChange={(e) => set('orgao_concedente_nome', e.target.value)} className={inputCls()} />
          ) : <p className="text-sm text-gray-500">{current.orgao_concedente_nome || '—'}</p>}
        </DetailField>

        <DetailField label="Fonte de recurso (Orçamento)">
          {editing ? (
            <select value={form.fonte_recurso} onChange={(e) => set('fonte_recurso', e.target.value)} className={inputCls()}>
              <option value="">Sem vínculo direto</option>
              {fontes.map((f) => <option key={f.id} value={f.id}>{f.codigo} — {f.nome}</option>)}
            </select>
          ) : <p className="text-sm text-gray-500">{current.fonte_recurso_nome || '—'}</p>}
        </DetailField>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <DetailField label="Valor total pactuado" error={errors.valor_total_pactuado}>
            {editing ? (
              <CampoMoeda value={form.valor_total_pactuado} onChange={(v) => set('valor_total_pactuado', v)} className={inputCls(errors.valor_total_pactuado)} />
            ) : <p className="text-sm font-semibold text-gray-800">{formatarMoeda(current.valor_total_pactuado)}</p>}
          </DetailField>
          <DetailField label="Valor de contrapartida">
            {editing ? (
              <CampoMoeda value={form.valor_contrapartida} onChange={(v) => set('valor_contrapartida', v)} className={inputCls()} />
            ) : <p className="text-sm text-gray-700">{formatarMoeda(current.valor_contrapartida)}</p>}
          </DetailField>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <DetailField label="Data de assinatura">
            {editing ? (
              <input type="date" value={form.data_assinatura} onChange={(e) => set('data_assinatura', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{current.data_assinatura ? new Date(current.data_assinatura + 'T00:00').toLocaleDateString('pt-BR') : '—'}</p>}
          </DetailField>
          <DetailField label="Início da vigência">
            {editing ? (
              <input type="date" value={form.vigencia_inicio} onChange={(e) => set('vigencia_inicio', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{current.vigencia_inicio ? new Date(current.vigencia_inicio + 'T00:00').toLocaleDateString('pt-BR') : '—'}</p>}
          </DetailField>
          <DetailField label="Fim da vigência">
            {editing ? (
              <input type="date" value={form.vigencia_fim} onChange={(e) => set('vigencia_fim', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{current.vigencia_fim ? new Date(current.vigencia_fim + 'T00:00').toLocaleDateString('pt-BR') : '—'}</p>}
          </DetailField>
        </div>

        <DetailField label="Número do processo SEI">
          {editing ? (
            <CampoSei value={form.numero_processo_sei} onChange={(v) => set('numero_processo_sei', v)} className={inputCls()} />
          ) : <p className="text-sm text-gray-500 font-mono">{current.numero_processo_sei || '—'}</p>}
        </DetailField>

        <DetailField label="Observações">
          {editing ? (
            <textarea rows={2} value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)} className={inputCls()} />
          ) : <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>}
        </DetailField>

        {editing && (
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving}
              className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button onClick={() => { setEditing(false); setErrors({}) }}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Cancelar edição
            </button>
          </div>
        )}

        {/* Histórico */}
        {current.historico?.length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Histórico</p>
            <div className="space-y-2">
              {current.historico.map((h) => (
                <div key={h.id} className="text-xs text-gray-500 border-l-2 border-gray-200 pl-3">
                  <span className="font-medium text-gray-700">{h.status_anterior || '—'} → {h.status_novo}</span>
                  {' '}por {h.usuario_nome} em {new Date(h.criado_em).toLocaleString('pt-BR')}
                  {h.motivo && <p className="text-gray-400">{h.motivo}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
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
  return `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500 ${error ? 'border-red-400' : 'border-gray-300'}`
}
