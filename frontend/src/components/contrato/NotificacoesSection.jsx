import { useState } from 'react'
import useContratoStore from '../../stores/contratoStore'
import useAuthStore from '../../stores/authStore'
import HelpTip from '../HelpTip'
import FornecedorPicker from '../FornecedorPicker'
import { NumeroSeiTexto } from '../CampoSei'

const ACAO_OPTS = [
  { value: 'notificacao', label: 'Notificação' },
  { value: 'rescisao',    label: 'Rescisão' },
]
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
const ACAO_CLS = {
  notificacao: 'bg-gray-100 text-gray-600',
  rescisao:    'bg-red-100 text-red-600',
}
const fmtDate = (v) => v ? new Date(v + 'T00:00').toLocaleDateString('pt-BR') : '—'
const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

const ANO_ATUAL = new Date().getFullYear()

const formVazio = (contrato) => ({
  fornecedor: contrato?.fornecedor || '',
  tipo_acao: 'notificacao', categoria_objeto: 'aquisicao',
  exercicio: ANO_ATUAL,
  numero_processo_sei: '', numero_sei_comunicacao: '', numero_sei_notificacao: '',
  data_notificacao: '', resumo_fato: '', observacoes: '',
})

/**
 * Notificações continuam editáveis mesmo com o contrato Encerrado/Rescindido
 * (ex.: pendência de garantia após o fim da vigência) — por isso não usa a
 * flag `podeEditar` (que bloqueia edição de dados do contrato em si).
 */
export default function NotificacoesSection({ contratoId, contrato, notificacoes }) {
  const { addNotificacao, updateNotificacao, deleteNotificacao } = useContratoStore()
  const seiBaseUrl = useAuthStore((s) => s.seiBaseUrl)
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm] = useState(formVazio(contrato))
  const [fornecedorLabel, setFornecedorLabel] = useState(contrato?.fornecedor_nome || '')

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleAdd = async () => {
    if (!form.resumo_fato) return
    setSaving(true)
    try {
      await addNotificacao(contratoId, {
        ...form,
        fornecedor: form.fornecedor ? Number(form.fornecedor) : null,
        exercicio: Number(form.exercicio),
        data_notificacao: form.data_notificacao || null,
      })
      setShowForm(false)
      setForm(formVazio(contrato))
      setFornecedorLabel(contrato?.fornecedor_nome || '')
    } finally { setSaving(false) }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold text-gray-400 uppercase">Notificações</p>
          <HelpTip text="Controle de notificações formais (ou rescisões) enviadas à empresa — atraso, ausência de garantia, paralisação etc. Continua editável mesmo após o contrato encerrar, para acompanhar pendências finais." position="right" />
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
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${ACAO_CLS[n.tipo_acao] || 'bg-gray-100 text-gray-600'}`}>{n.tipo_acao_display}</span>
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${STATUS_CLS[n.status]}`}>{n.status_display}</span>
                    <span className="ml-2 text-xs text-gray-500">{n.categoria_objeto_display}</span>
                    <p className="text-sm text-gray-800 mt-0.5">{n.resumo_fato}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Data: {fmtDate(n.data_notificacao)}
                      {n.fornecedor_nome && <> · Fornecedor: {n.fornecedor_nome}</>}
                      {n.numero_processo_sei && <> · SEI processo: <NumeroSeiTexto valor={n.numero_processo_sei} seiBaseUrl={seiBaseUrl} className="font-mono" /></>}
                    </p>
                    {n.numero_sei_comunicacao && (
                      <p className="text-xs text-gray-500">Nº Comunicação: <span className="font-mono">{n.numero_sei_comunicacao}</span></p>
                    )}
                    {n.numero_sei_notificacao && (
                      <p className="text-xs text-gray-500">Nº Notificação: <span className="font-mono">{n.numero_sei_notificacao}</span></p>
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
              <label className="block text-xs text-gray-500 mb-0.5">Ação</label>
              <select value={form.tipo_acao} onChange={(e) => set('tipo_acao', e.target.value)} className={inp()}>
                {ACAO_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Tipo</label>
              <select value={form.categoria_objeto} onChange={(e) => set('categoria_objeto', e.target.value)} className={inp()}>
                {CATEGORIA_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Fornecedor</label>
              <FornecedorPicker
                value={form.fornecedor}
                valueLabel={fornecedorLabel}
                onChange={(id, fornecedor) => {
                  set('fornecedor', id || '')
                  setFornecedorLabel(fornecedor ? `${fornecedor.documento} — ${fornecedor.nome_razao_social}` : '')
                }}
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Data da notificação</label>
              <input type="date" value={form.data_notificacao} onChange={(e) => set('data_notificacao', e.target.value)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Exercício *</label>
              <input type="number" value={form.exercicio} onChange={(e) => set('exercicio', e.target.value)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Processo SEI</label>
              <input type="text" value={form.numero_processo_sei} onChange={(e) => set('numero_processo_sei', e.target.value)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Nº Comunicação</label>
              <input type="text" value={form.numero_sei_comunicacao} onChange={(e) => set('numero_sei_comunicacao', e.target.value)} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Nº da Notificação</label>
              <input type="text" value={form.numero_sei_notificacao} onChange={(e) => set('numero_sei_notificacao', e.target.value)} className={inp()} />
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
