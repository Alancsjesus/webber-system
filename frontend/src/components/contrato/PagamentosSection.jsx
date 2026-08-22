import { useState } from 'react'
import useContratoStore from '../../stores/contratoStore'
import HelpTip from '../HelpTip'
import CampoMoeda from '../CampoMoeda'

const STATUS_CLS = {
  pendente:  'bg-yellow-100 text-yellow-700',
  pago:      'bg-green-100 text-green-700',
  atrasado:  'bg-red-100 text-red-600',
  cancelado: 'bg-gray-100 text-gray-400 line-through',
}
const fmtDate = (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '—'
const fmt = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function PagamentosSection({ contratoId, pagamentos, medicoes, podeEditar }) {
  const { addPagamento, updatePagamento, deletePagamento } = useContratoStore()
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm] = useState({
    medicao: '', numero_empenho: '', numero_nota_fiscal: '', valor_pago: '', data_vencimento: '',
  })

  const medicoesAprovadas = (medicoes || []).filter(m => m.status === 'aprovada')

  const handleAdd = async () => {
    if (!form.valor_pago) return
    setSaving(true)
    try {
      await addPagamento(contratoId, {
        ...form,
        medicao: form.medicao || null,
        valor_pago: Number(form.valor_pago),
        data_vencimento: form.data_vencimento || null,
      })
      setShowForm(false)
      setForm({ medicao: '', numero_empenho: '', numero_nota_fiscal: '', valor_pago: '', data_vencimento: '' })
    } finally { setSaving(false) }
  }

  const marcarPago = (p) => updatePagamento(contratoId, p.id, { status: 'pago', data_pagamento: new Date().toISOString().slice(0, 10) })

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold text-gray-400 uppercase">Pagamentos</p>
          <HelpTip text="Pagamentos vinculados a uma medição aprovada, ou avulsos (ex. pagamento único após entrega integral)." position="right" />
        </span>
        {podeEditar && <button onClick={() => setShowForm(v => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Novo pagamento</button>}
      </div>

      {pagamentos.length === 0
        ? <p className="text-xs text-gray-400 italic">Nenhum pagamento registrado.</p>
        : <ul className="space-y-2">
            {pagamentos.map(p => (
              <li key={p.id} className="flex items-start justify-between bg-gray-50 rounded-lg px-3 py-2">
                <div>
                  <span className="font-mono text-xs font-semibold text-gray-700">{p.numero}</span>
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${STATUS_CLS[p.status]}`}>{p.status_display}</span>
                  {p.medicao_numero && <span className="ml-2 text-xs text-blue-600 font-mono">{p.medicao_numero}</span>}
                  <p className="text-sm font-semibold text-gray-800 mt-0.5">{fmt(p.valor_pago)}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {p.numero_empenho && `Empenho: ${p.numero_empenho} · `}
                    {p.numero_nota_fiscal && `NF: ${p.numero_nota_fiscal} · `}
                    Vencimento: {fmtDate(p.data_vencimento)}
                    {p.data_pagamento && ` · Pago em: ${fmtDate(p.data_pagamento)}`}
                  </p>
                </div>
                {podeEditar && (
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    {p.status === 'pendente' && (
                      <button onClick={() => marcarPago(p)} className="text-xs text-green-600 hover:text-green-800 font-medium">Marcar pago</button>
                    )}
                    <button onClick={() => deletePagamento(contratoId, p.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                  </div>
                )}
              </li>
            ))}
          </ul>}

      {showForm && (
        <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
          <p className="text-xs font-semibold text-blue-700 mb-2">Novo pagamento</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Medição vinculada (opcional)</label>
              <select value={form.medicao} onChange={e => setForm(p => ({ ...p, medicao: e.target.value }))} className={inp()}>
                <option value="">Pagamento avulso (sem medição)</option>
                {medicoesAprovadas.map(m => <option key={m.id} value={m.id}>{m.numero} — {fmt(m.valor_medido)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Nº do empenho</label>
              <input type="text" value={form.numero_empenho} onChange={e => setForm(p => ({ ...p, numero_empenho: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Nº da nota fiscal</label>
              <input type="text" value={form.numero_nota_fiscal} onChange={e => setForm(p => ({ ...p, numero_nota_fiscal: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Valor (R$) *</label>
              <CampoMoeda value={form.valor_pago} onChange={v => setForm(p => ({ ...p, valor_pago: v }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Data de vencimento</label>
              <input type="date" value={form.data_vencimento} onChange={e => setForm(p => ({ ...p, data_vencimento: e.target.value }))} className={inp()} />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={handleAdd} disabled={saving || !form.valor_pago}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
              {saving ? '...' : 'Salvar pagamento'}
            </button>
            <button onClick={() => setShowForm(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
          </div>
        </div>
      )}
    </div>
  )
}
