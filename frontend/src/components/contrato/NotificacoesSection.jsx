import { useState } from 'react'
import useContratoStore from '../../stores/contratoStore'
import useAuthStore from '../../stores/authStore'
import HelpTip from '../HelpTip'
import CampoSei, { NumeroSeiTexto } from '../CampoSei'

const CATEGORIA_OPTS = [
  { value: 'aquisicao', label: 'Aquisição' },
  { value: 'obra',      label: 'Obra' },
  { value: 'servico',   label: 'Serviço' },
]
const STATUS_OPTS = [
  { value: 'andamento', label: 'Em Andamento' },
  { value: 'cpa',       label: 'Em CPA' },
  { value: 'concluido', label: 'Concluído' },
]
const STATUS_CLS = {
  andamento: 'bg-blue-100 text-blue-700',
  cpa:       'bg-amber-100 text-amber-700',
  concluido: 'bg-green-100 text-green-700',
}
const fmtDate = (v) => v ? new Date(v + 'T00:00').toLocaleDateString('pt-BR') : '—'
const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

const FORM_VAZIO = {
  categoria_objeto: 'aquisicao', numero_processo_sei: '',
  numero_sei_comunicacao: '', numero_sei_notificacao: '',
  data_notificacao: '', resumo_fato: '', observacoes: '',
}

/**
 * Notificações continuam editáveis mesmo com o contrato Encerrado/Rescindido
 * (ex.: pendência de garantia após o fim da vigência) — por isso não usa a
 * flag `podeEditar` (que bloqueia edição de dados do contrato em si).
 */
export default function NotificacoesSection({ contratoId, notificacoes }) {
  const { addNotificacao, updateNotificacao, deleteNotificacao } = useContratoStore()
  const seiBaseUrl = useAuthStore((s) => s.seiBaseUrl)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm] = useState(FORM_VAZIO)

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleAdd = async () => {
    if (!form.resumo_fato) return
    setSaving(true)
    try {
      await addNotificacao(contratoId, form)
      setShowForm(false)
      setForm(FORM_VAZIO)
    } finally { setSaving(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold text-gray-400 uppercase">Notificações</p>
          <HelpTip text="Controle de notificações formais enviadas à empresa (atraso, ausência de garantia, paralisação etc.). Continua editável mesmo após o contrato encerrar, para acompanhar pendências finais." position="right" />
        </span>
        <button onClick={() => setShowForm((v) => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Nova notificação</button>
      </div>

      {notificacoes.length === 0
        ? <p className="text-xs text-gray-400 italic">Nenhuma notificação registrada.</p>
        : <ul className="space-y-3">
            {notificacoes.map((n) => (
              <li key={n.id} className="bg-gray-50 rounded-lg px-3 py-2">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-xs font-semibold text-gray-700">{n.numero}</span>
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${STATUS_CLS[n.status]}`}>{n.status_display}</span>
                    <span className="ml-2 text-xs text-gray-500">{n.categoria_objeto_display}</span>
                    <p className="text-sm text-gray-800 mt-0.5">{n.resumo_fato}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Data: {fmtDate(n.data_notificacao)}
                      {n.numero_processo_sei && <> · SEI processo: <NumeroSeiTexto valor={n.numero_processo_sei} seiBaseUrl={seiBaseUrl} className="font-mono" /></>}
                    </p>
                    {n.numero_sei_comunicacao && (
                      <p className="text-xs text-gray-500">Nº Comunicação: <NumeroSeiTexto valor={n.numero_sei_comunicacao} seiBaseUrl={seiBaseUrl} className="font-mono" /></p>
                    )}
                    {n.numero_sei_notificacao && (
                      <p className="text-xs text-gray-500">Nº Notificação: <NumeroSeiTexto valor={n.numero_sei_notificacao} seiBaseUrl={seiBaseUrl} className="font-mono" /></p>
                    )}
                    {n.observacoes && <p className="text-xs text-gray-500 italic mt-0.5">{n.observacoes}</p>}
                  </div>
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    <select value={n.status} onChange={(e) => updateNotificacao(contratoId, n.id, { status: e.target.value })}
                      className="text-xs border border-gray-300 rounded px-1.5 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500">
                      {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                    <button onClick={() => deleteNotificacao(contratoId, n.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                  </div>
                </div>
              </li>
            ))}
          </ul>}

      {showForm && (
        <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
          <p className="text-xs font-semibold text-blue-700 mb-2">Nova notificação</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Tipo</label>
              <select value={form.categoria_objeto} onChange={(e) => set('categoria_objeto', e.target.value)} className={inp()}>
                {CATEGORIA_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Data da notificação</label>
              <input type="date" value={form.data_notificacao} onChange={(e) => set('data_notificacao', e.target.value)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Processo SEI</label>
              <CampoSei value={form.numero_processo_sei} onChange={(v) => set('numero_processo_sei', v)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Nº Comunicação (SEI)</label>
              <CampoSei value={form.numero_sei_comunicacao} onChange={(v) => set('numero_sei_comunicacao', v)} className={inp()} />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Nº da Notificação (SEI)</label>
              <CampoSei value={form.numero_sei_notificacao} onChange={(v) => set('numero_sei_notificacao', v)} className={inp()} />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Resumo do fato *</label>
              <textarea rows={2} value={form.resumo_fato} onChange={(e) => set('resumo_fato', e.target.value)} className={inp()} />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Observação</label>
              <textarea rows={2} value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)} className={inp()} />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={handleAdd} disabled={saving || !form.resumo_fato}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
              {saving ? '...' : 'Salvar notificação'}
            </button>
            <button onClick={() => setShowForm(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
          </div>
        </div>
      )}
    </div>
  )
}
