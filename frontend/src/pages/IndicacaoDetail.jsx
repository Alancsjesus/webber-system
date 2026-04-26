import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useIndicacaoStore from '../stores/indicacaoStore'
import useOrcamentoStore from '../stores/orcamentoStore'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Rascunho:  'bg-gray-100 text-gray-600',
  Submetida: 'bg-blue-100 text-blue-700',
  Aprovada:  'bg-green-100 text-green-700',
  Cancelada: 'bg-red-100 text-red-600',
}

const fmt = (v) =>
  Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function IndicacaoDetail() {
  const { id }     = useParams()
  const navigate   = useNavigate()
  const papel      = useAuthStore((s) => s.papel)

  const {
    current, loading, error,
    fetchIndicacao, updateIndicacao, deleteIndicacao,
    submeter, aprovar, cancelar,
    vincularDotacao, desvincularDotacao,
  } = useIndicacaoStore()

  const { dotacoes, fetchDotacoes } = useOrcamentoStore()

  const [editing, setEditing]       = useState(false)
  const [form, setForm]             = useState(null)
  const [saving, setSaving]         = useState(false)
  const [actionMsg, setActionMsg]   = useState(null)
  const [showCancelar, setShowCancelar] = useState(false)
  const [motivoCancelamento, setMotivoCancelamento] = useState('')
  const [showVincular, setShowVincular] = useState(false)
  const [vincForm, setVincForm]     = useState({ dotacao_id: '', valor_indicado: '' })
  const [vincSaving, setVincSaving] = useState(false)
  const [vincErrors, setVincErrors] = useState({})

  useEffect(() => { fetchIndicacao(id) }, [id])
  useEffect(() => {
    if (current) {
      setForm({ observacoes: current.observacoes || '' })
    }
  }, [current])

  const act = async (fn, ...args) => {
    setSaving(true)
    setActionMsg(null)
    try {
      await fn(...args)
      setActionMsg({ type: 'success', text: 'Operação realizada com sucesso.' })
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erro ao executar operação.'
      setActionMsg({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  const handleVincular = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!vincForm.dotacao_id) errs.dotacao_id = 'Selecione uma dotação'
    if (!vincForm.valor_indicado || isNaN(Number(vincForm.valor_indicado)))
      errs.valor_indicado = 'Valor inválido'
    if (Object.keys(errs).length) { setVincErrors(errs); return }
    setVincSaving(true)
    try {
      await vincularDotacao(id, Number(vincForm.dotacao_id), Number(vincForm.valor_indicado))
      setVincForm({ dotacao_id: '', valor_indicado: '' })
      setVincErrors({})
      setActionMsg({ type: 'success', text: 'Dotação vinculada.' })
    } catch (err) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao vincular.' })
    } finally {
      setVincSaving(false) }
  }

  const handleSaveEdit = async () => {
    setSaving(true)
    try {
      await updateIndicacao(id, { observacoes: form.observacoes })
      setEditing(false)
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (!confirm('Excluir esta indicação? Esta ação não pode ser desfeita.')) return
    await deleteIndicacao(id)
    navigate('/orcamento/indicacoes')
  }

  useEffect(() => {
    if (showVincular) {
      fetchDotacoes({ page_size: 100 })
    }
  }, [showVincular])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando indicação..." /></div>
  if (error)   return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current || !form) return null

  const isRascunho  = current.status === 'Rascunho'
  const isSubmetida = current.status === 'Submetida'
  const isAprovada  = current.status === 'Aprovada'
  const podeCancelar = ['Submetida', 'Aprovada'].includes(current.status)
  const podeAprovar = isSubmetida && ['admin', 'ordenador'].includes(papel)

  return (
    <div className="p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status]}`}>
              {current.status === 'Aprovada' ? 'DOD Emitida' : current.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">Exercício {current.exercicio_fiscal}</p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {isRascunho && !editing && (
            <button onClick={() => setEditing(true)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Editar
            </button>
          )}
          {isRascunho && (
            <button onClick={() => act(submeter, id)} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Submeter
            </button>
          )}
          {podeAprovar && (
            <button onClick={() => act(aprovar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Aprovar (emitir DOD)
            </button>
          )}
          {isAprovada && (
            <a href={`/api/orcamento/indicacao/${id}/export/pdf/`} target="_blank" rel="noreferrer"
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg inline-block">
              Baixar DOD (PDF)
            </a>
          )}
          {podeCancelar && (
            <button onClick={() => setShowCancelar(true)}
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

      {/* Mensagem de feedback */}
      {actionMsg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${
          actionMsg.type === 'success'
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {actionMsg.text}
        </div>
      )}

      <div className="space-y-5">
        {/* Demanda vinculada */}
        <Section label="Demanda vinculada">
          {current.dfd
            ? <p className="text-sm text-gray-700">DFD: <span className="font-mono font-semibold">{current.dfd_numero_sei}</span></p>
            : current.necessidade
            ? <p className="text-sm text-gray-700">Necessidade: <span className="font-semibold">{current.necessidade_titulo}</span></p>
            : <p className="text-sm text-gray-400">Sem vínculo</p>}
        </Section>

        {/* Observações */}
        <Section label="Observações">
          {editing ? (
            <div className="space-y-2">
              <textarea rows={3} value={form.observacoes}
                onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              <div className="flex gap-2">
                <button onClick={handleSaveEdit} disabled={saving}
                  className="bg-blue-600 text-white text-xs px-3 py-1.5 rounded-lg disabled:opacity-50">
                  {saving ? 'Salvando...' : 'Salvar'}
                </button>
                <button onClick={() => setEditing(false)}
                  className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-700">{current.observacoes || <span className="text-gray-400">—</span>}</p>
          )}
        </Section>

        {/* Ordenador */}
        {isAprovada && (
          <Section label="Ordenador de despesa">
            <p className="text-sm text-gray-700 font-semibold">{current.ordenador_nome}</p>
            <p className="text-xs text-gray-400">
              {current.data_aprovacao
                ? new Date(current.data_aprovacao).toLocaleDateString('pt-BR')
                : '—'}
            </p>
          </Section>
        )}

        {/* Pipeline — Valor total */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p className="text-xs font-semibold text-blue-800 uppercase mb-1">Valor Total Indicado</p>
          <p className="text-2xl font-bold text-blue-700">{fmt(current.valor_total)}</p>
        </div>

        {/* Dotações vinculadas */}
        <div className="pt-2">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">
              Dotações vinculadas ({(current.itens || []).length})
            </p>
            {isRascunho && (
              <button onClick={() => setShowVincular((v) => !v)}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium border border-blue-200 px-3 py-1 rounded-lg">
                {showVincular ? 'Fechar' : '+ Vincular dotação'}
              </button>
            )}
          </div>

          {/* Formulário vincular */}
          {showVincular && isRascunho && (
            <form onSubmit={handleVincular}
              className="mb-4 bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-3">
              <p className="text-sm font-semibold text-gray-700">Vincular dotação</p>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Dotação *</label>
                  <select value={vincForm.dotacao_id}
                    onChange={(e) => { setVincForm((p) => ({ ...p, dotacao_id: e.target.value })); setVincErrors((p) => ({ ...p, dotacao_id: undefined })) }}
                    className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${vincErrors.dotacao_id ? 'border-red-400' : 'border-gray-300'}`}>
                    <option value="">Selecione...</option>
                    {dotacoes.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.acao_codigo} / {d.elemento_codigo} — {fmt(d.valor_dotado)}
                      </option>
                    ))}
                  </select>
                  {vincErrors.dotacao_id && <p className="text-xs text-red-600 mt-1">{vincErrors.dotacao_id}</p>}
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Valor indicado (R$) *</label>
                  <input type="number" min="0" step="0.01" value={vincForm.valor_indicado}
                    onChange={(e) => { setVincForm((p) => ({ ...p, valor_indicado: e.target.value })); setVincErrors((p) => ({ ...p, valor_indicado: undefined })) }}
                    className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${vincErrors.valor_indicado ? 'border-red-400' : 'border-gray-300'}`} />
                  {vincErrors.valor_indicado && <p className="text-xs text-red-600 mt-1">{vincErrors.valor_indicado}</p>}
                </div>
              </div>
              <button type="submit" disabled={vincSaving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
                {vincSaving ? 'Vinculando...' : 'Vincular'}
              </button>
            </form>
          )}

          {(current.itens || []).length === 0 && !showVincular && (
            <p className="text-sm text-gray-400">Nenhuma dotação vinculada ainda.</p>
          )}

          {(current.itens || []).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Ação</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Elemento</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Natureza</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Fonte</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Valor Indicado</th>
                    {isRascunho && <th className="px-4 py-2"></th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {current.itens.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-xs font-mono text-gray-700">{item.acao_codigo}</td>
                      <td className="px-4 py-2 text-xs text-gray-600">{item.elemento_codigo} — {item.elemento_descricao}</td>
                      <td className="px-4 py-2 text-xs font-mono text-blue-700">{item.natureza_formato || '—'}</td>
                      <td className="px-4 py-2 text-xs text-gray-600">{item.fonte_codigo} — {item.fonte_nome}</td>
                      <td className="px-4 py-2 text-right font-semibold text-gray-800">{fmt(item.valor_indicado)}</td>
                      {isRascunho && (
                        <td className="px-4 py-2 text-right">
                          <button onClick={() => act(desvincularDotacao, id, item.dotacao_id)}
                            className="text-xs text-red-500 hover:text-red-700">
                            Remover
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Histórico */}
        {(current.historico || []).length > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Histórico</p>
            <div className="space-y-2">
              {current.historico.map((h) => (
                <div key={h.id} className="flex items-start gap-3 text-xs text-gray-600">
                  <span className="text-gray-400 shrink-0">
                    {new Date(h.criado_em).toLocaleString('pt-BR')}
                  </span>
                  <span>
                    <span className="font-medium">{h.usuario_nome}</span>
                    {' → '}
                    <span className="font-semibold">{h.status_novo}</span>
                    {h.motivo && <span className="text-gray-400"> — {h.motivo}</span>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado em: {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
        </div>
      </div>

      {/* Modal cancelamento */}
      {showCancelar && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">Cancelar indicação</h3>
            <p className="text-sm text-gray-500 mb-4">Esta ação não pode ser desfeita.</p>
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo *</label>
            <textarea rows={3} value={motivoCancelamento}
              onChange={(e) => setMotivoCancelamento(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button
                disabled={!motivoCancelamento.trim() || saving}
                onClick={async () => {
                  await act(cancelar, id, motivoCancelamento)
                  setShowCancelar(false)
                  setMotivoCancelamento('')
                }}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? 'Cancelando...' : 'Confirmar cancelamento'}
              </button>
              <button onClick={() => setShowCancelar(false)}
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

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
      {children}
    </div>
  )
}
