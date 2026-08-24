import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useIndicacaoStore from '../stores/indicacaoStore'
import useOrcamentoStore from '../stores/orcamentoStore'
import useAuthStore from '../stores/authStore'
import api, { downloadFile } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import CampoMoeda from '../components/CampoMoeda'

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
    registrarNpos, cancelarNpo,
    registrarConcessoes, cancelarConcessao,
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
  const [showNpoModal, setShowNpoModal] = useState(false)  // 'npo' | 'concessao' | null
  const [npoForms, setNpoForms]     = useState([])   // [{indicacao_dotacao_id, numero, data, valor, obs}]
  const [npoSaving, setNpoSaving]   = useState(false)
  const [showCancelNpo, setShowCancelNpo] = useState(null)  // {type, id}
  const [motivoCancelNpo, setMotivoCancelNpo] = useState('')

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
    <div className="p-6 lg:p-8 max-w-3xl">
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
            <button
              onClick={() => downloadFile(`/orcamento/indicacao/${id}/export/pdf/`, `DOD_${current?.numero || id}.pdf`)}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg inline-block">
              Baixar DOD (PDF)
            </button>
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
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                  <CampoMoeda value={vincForm.valor_indicado}
                    onChange={(v) => { setVincForm((p) => ({ ...p, valor_indicado: v })); setVincErrors((p) => ({ ...p, valor_indicado: undefined })) }}
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

        {/* Execução Orçamentária — NPOs e Concessões */}
        {isAprovada && (current.itens || []).length > 0 && (
          <div className="pt-2 border-t border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-semibold text-gray-400 uppercase">Execução Orçamentária</p>
              <div className="flex gap-2">
                <button onClick={() => {
                    setNpoForms((current.itens || []).map(i => ({ indicacao_dotacao_id: i.id, numero: '', data: new Date().toISOString().split('T')[0], valor: '', obs: '' })))
                    setShowNpoModal('npo')
                  }}
                  className="text-xs bg-yellow-50 border border-yellow-300 text-yellow-800 hover:bg-yellow-100 px-3 py-1 rounded-lg font-medium">
                  + Registrar NPO(s)
                </button>
                <button onClick={() => {
                    setNpoForms((current.itens || []).map(i => ({ indicacao_dotacao_id: i.id, numero: '', data: new Date().toISOString().split('T')[0], valor: '', obs: '' })))
                    setShowNpoModal('concessao')
                  }}
                  className="text-xs bg-green-50 border border-green-300 text-green-800 hover:bg-green-100 px-3 py-1 rounded-lg font-medium">
                  + Registrar Concessão(ões)
                </button>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Dotação</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Indicado</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Descentralizado</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Concedido</th>
                    <th className="text-right px-3 py-2 font-medium text-gray-500">Exec. %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {current.itens.map(item => {
                    const desc = item.valor_descentralizado || 0
                    const conc = item.valor_concedido || 0
                    const ind  = parseFloat(item.valor_indicado) || 0
                    const pctDesc = ind > 0 ? Math.round(desc / ind * 100) : 0
                    const pctConc = desc > 0 ? Math.round(conc / desc * 100) : 0
                    return (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-700">
                          <span className="font-mono text-blue-700 mr-1">{item.acao_codigo}</span>
                          {item.elemento_codigo} {item.natureza_formato && `· ${item.natureza_formato}`}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-gray-800">{fmt(item.valor_indicado)}</td>
                        <td className="px-3 py-2 text-right">
                          <span className="font-semibold text-yellow-700">{fmt(desc)}</span>
                          <span className="ml-1 text-gray-400">({pctDesc}%)</span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <span className="font-semibold text-green-700">{fmt(conc)}</span>
                          <span className="ml-1 text-gray-400">({pctConc}% desc.)</span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <span className={`font-bold ${pctDesc >= 80 ? 'text-green-600' : pctDesc >= 40 ? 'text-yellow-600' : 'text-red-500'}`}>
                            {pctDesc}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>

              {/* Detalhe NPOs e concessões por dotação */}
              {current.itens.some(i => (i.descentralizacoes || []).length > 0 || (i.concessoes || []).length > 0) && (
                <div className="border-t border-gray-100 px-3 py-3 space-y-3">
                  {current.itens.map(item => (
                    <div key={item.id}>
                      {(item.descentralizacoes || []).filter(d => !d.cancelada).length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-yellow-700 uppercase mb-1">NPOs — {item.acao_codigo}</p>
                          {item.descentralizacoes.filter(d => !d.cancelada).map(d => (
                            <div key={d.id} className="flex items-center justify-between text-xs py-0.5">
                              <span className="font-mono text-gray-600">{d.numero_npo}</span>
                              <span className="text-gray-400">{new Date(d.data_emissao).toLocaleDateString('pt-BR')}</span>
                              <span className="font-semibold text-yellow-700">{fmt(d.valor)}</span>
                              <button onClick={() => { setShowCancelNpo({ type: 'npo', id: d.id }); setMotivoCancelNpo('') }}
                                className="text-red-400 hover:text-red-600 ml-2">✕</button>
                            </div>
                          ))}
                        </div>
                      )}
                      {(item.concessoes || []).filter(c => !c.cancelada).length > 0 && (
                        <div>
                          <p className="text-[10px] font-semibold text-green-700 uppercase mb-1">Concessões — {item.acao_codigo}</p>
                          {item.concessoes.filter(c => !c.cancelada).map(c => (
                            <div key={c.id} className="flex items-center justify-between text-xs py-0.5">
                              <span className="font-mono text-gray-600">{c.numero_doc}</span>
                              <span className="text-gray-400">{new Date(c.data_emissao).toLocaleDateString('pt-BR')}</span>
                              <span className="font-semibold text-green-700">{fmt(c.valor)}</span>
                              <button onClick={() => { setShowCancelNpo({ type: 'concessao', id: c.id }); setMotivoCancelNpo('') }}
                                className="text-red-400 hover:text-red-600 ml-2">✕</button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

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

      {/* Modal registro em bloco (NPO ou Concessão) */}
      {showNpoModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-100">
              <h3 className="text-base font-semibold text-gray-800">
                {showNpoModal === 'npo' ? 'Registrar NPOs — Descentralização' : 'Registrar Concessões'}
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                {showNpoModal === 'npo'
                  ? 'Informe o número e valor da NPO para cada dotação. Campos em branco serão ignorados.'
                  : 'Informe o documento e valor para cada dotação. Valor não pode superar o descentralizado.'}
              </p>
            </div>
            <div className="px-6 py-4 space-y-4">
              {(current.itens || []).map((item, idx) => {
                const f = npoForms[idx] || {}
                const descMax = parseFloat(item.valor_descentralizado || 0)
                const concAtual = parseFloat(item.valor_concedido || 0)
                return (
                  <div key={item.id} className="border border-gray-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-gray-700 mb-2">
                      <span className="font-mono text-blue-700 mr-1">{item.acao_codigo}</span>
                      {item.elemento_codigo} — {item.natureza_formato || '—'}
                      <span className="ml-2 text-gray-400">
                        Indicado: {fmt(item.valor_indicado)}
                        {showNpoModal === 'concessao' && ` · Descentralizado: ${fmt(descMax)} · Concedido: ${fmt(concAtual)}`}
                      </span>
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="block text-[10px] text-gray-500 mb-0.5">
                          {showNpoModal === 'npo' ? 'Nº NPO' : 'Nº Documento'}
                        </label>
                        <input type="text" value={f.numero || ''}
                          onChange={e => setNpoForms(prev => prev.map((p, i) => i === idx ? { ...p, numero: e.target.value } : p))}
                          className="w-full border border-gray-300 rounded px-2 py-1.5 text-xs" />
                      </div>
                      <div>
                        <label className="block text-[10px] text-gray-500 mb-0.5">Data emissão</label>
                        <input type="date" value={f.data || ''}
                          onChange={e => setNpoForms(prev => prev.map((p, i) => i === idx ? { ...p, data: e.target.value } : p))}
                          className="w-full border border-gray-300 rounded px-2 py-1.5 text-xs" />
                      </div>
                      <div>
                        <label className="block text-[10px] text-gray-500 mb-0.5">Valor (R$)</label>
                        <CampoMoeda value={f.valor || ''}
                          onChange={v => setNpoForms(prev => prev.map((p, i) => i === idx ? { ...p, valor: v } : p))}
                          className="w-full border border-gray-300 rounded px-2 py-1.5 text-xs" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex gap-2">
              <button
                disabled={npoSaving}
                onClick={async () => {
                  setNpoSaving(true)
                  try {
                    const payload = npoForms
                      .filter(f => f.numero && f.data && f.valor)
                      .map(f => ({
                        indicacao_dotacao_id: f.indicacao_dotacao_id,
                        [showNpoModal === 'npo' ? 'numero_npo' : 'numero_doc']: f.numero,
                        data_emissao: f.data,
                        valor: parseFloat(f.valor),
                      }))
                    if (showNpoModal === 'npo') await registrarNpos(id, payload)
                    else await registrarConcessoes(id, payload)
                    setShowNpoModal(null)
                    setActionMsg({ type: 'success', text: 'Registrado com sucesso.' })
                  } catch (e) {
                    setActionMsg({ type: 'error', text: e.response?.data?.detail || 'Erro ao registrar.' })
                  } finally { setNpoSaving(false) }
                }}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                {npoSaving ? 'Salvando...' : 'Confirmar'}
              </button>
              <button onClick={() => setShowNpoModal(null)}
                className="border border-gray-300 text-gray-600 text-sm px-5 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal cancelar NPO/Concessão */}
      {showCancelNpo && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800 mb-1">
              Cancelar {showCancelNpo.type === 'npo' ? 'NPO' : 'Concessão'}
            </h3>
            <label className="block text-xs font-medium text-gray-600 mb-1 mt-3">Motivo *</label>
            <textarea rows={3} value={motivoCancelNpo} onChange={e => setMotivoCancelNpo(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400 mb-4" />
            <div className="flex gap-2">
              <button
                disabled={!motivoCancelNpo.trim() || npoSaving}
                onClick={async () => {
                  setNpoSaving(true)
                  try {
                    if (showCancelNpo.type === 'npo') await cancelarNpo(id, showCancelNpo.id, motivoCancelNpo)
                    else await cancelarConcessao(id, showCancelNpo.id, motivoCancelNpo)
                    setShowCancelNpo(null)
                    setMotivoCancelNpo('')
                    setActionMsg({ type: 'success', text: 'Cancelado com sucesso.' })
                  } catch (e) {
                    setActionMsg({ type: 'error', text: e.response?.data?.detail || 'Erro ao cancelar.' })
                  } finally { setNpoSaving(false) }
                }}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {npoSaving ? 'Cancelando...' : 'Confirmar'}
              </button>
              <button onClick={() => { setShowCancelNpo(null); setMotivoCancelNpo('') }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Voltar
              </button>
            </div>
          </div>
        </div>
      )}

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
