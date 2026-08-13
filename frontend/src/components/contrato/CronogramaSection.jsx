import { useState } from 'react'
import useContratoStore from '../../stores/contratoStore'
import HelpTip from '../HelpTip'

const STATUS_CLS = {
  pendente:  'bg-gray-100 text-gray-500',
  entregue:  'bg-green-100 text-green-700',
  atrasado:  'bg-red-100 text-red-600',
  cancelado: 'bg-gray-100 text-gray-400 line-through',
}
const fmtDate = (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '—'
const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function CronogramaSection({ contratoId, itens, podeEditar }) {
  const { addCronograma, updateCronograma, deleteCronograma } = useContratoStore()
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm] = useState({ descricao: '', quantidade: '', unidade_medida: '', data_prevista: '' })

  const handleAdd = async () => {
    if (!form.descricao.trim() || !form.data_prevista) return
    setSaving(true)
    try {
      await addCronograma(contratoId, {
        ...form,
        quantidade: form.quantidade ? Number(form.quantidade) : null,
      })
      setShowForm(false)
      setForm({ descricao: '', quantidade: '', unidade_medida: '', data_prevista: '' })
    } finally { setSaving(false) }
  }

  const marcarEntregue = (item) => updateCronograma(contratoId, item.id, {
    status: 'entregue', data_realizada: new Date().toISOString().slice(0, 10),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold text-gray-400 uppercase">Cronograma de Entrega</p>
          <HelpTip text="Planejamento das etapas/itens a serem entregues, com data prevista de entrega." position="right" />
        </span>
        {podeEditar && <button onClick={() => setShowForm(v => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Adicionar item</button>}
      </div>

      {itens.length === 0
        ? <p className="text-xs text-gray-400 italic">Nenhum item de cronograma cadastrado.</p>
        : <ul className="space-y-2">
            {itens.map(item => (
              <li key={item.id} className="flex items-start justify-between bg-gray-50 rounded-lg px-3 py-2">
                <div>
                  <span className="font-mono text-xs font-semibold text-gray-700">{item.numero}</span>
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${STATUS_CLS[item.is_atrasado ? 'atrasado' : item.status]}`}>
                    {item.is_atrasado ? 'Atrasado' : item.status_display}
                  </span>
                  <p className="text-xs text-gray-600 mt-0.5">{item.descricao}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Previsto: {fmtDate(item.data_prevista)}
                    {item.data_realizada && ` · Realizado: ${fmtDate(item.data_realizada)}`}
                    {item.quantidade != null && ` · Qtd: ${item.quantidade}${item.unidade_medida ? ' ' + item.unidade_medida : ''}`}
                  </p>
                </div>
                {podeEditar && (
                  <div className="flex items-center gap-2 ml-3 shrink-0">
                    {item.status === 'pendente' && (
                      <button onClick={() => marcarEntregue(item)} className="text-xs text-green-600 hover:text-green-800 font-medium">Marcar entregue</button>
                    )}
                    <button onClick={() => deleteCronograma(contratoId, item.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                  </div>
                )}
              </li>
            ))}
          </ul>}

      {showForm && (
        <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
          <p className="text-xs font-semibold text-blue-700 mb-2">Novo item de cronograma</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Descrição *</label>
              <textarea rows={2} value={form.descricao} onChange={e => setForm(p => ({ ...p, descricao: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Data prevista *</label>
              <input type="date" value={form.data_prevista} onChange={e => setForm(p => ({ ...p, data_prevista: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Quantidade</label>
              <input type="number" step="0.01" value={form.quantidade} onChange={e => setForm(p => ({ ...p, quantidade: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Unidade de medida</label>
              <input type="text" value={form.unidade_medida} onChange={e => setForm(p => ({ ...p, unidade_medida: e.target.value }))} className={inp()} />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={handleAdd} disabled={saving || !form.descricao.trim() || !form.data_prevista}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
              {saving ? '...' : 'Salvar item'}
            </button>
            <button onClick={() => setShowForm(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
          </div>
        </div>
      )}
    </div>
  )
}
