import { useState } from 'react'
import useContratoStore from '../../stores/contratoStore'
import HelpTip from '../HelpTip'
import CampoMoeda from '../CampoMoeda'
import CampoSei from '../CampoSei'

const STATUS_CLS = {
  pendente:  'bg-yellow-100 text-yellow-700',
  aprovada:  'bg-green-100 text-green-700',
  rejeitada: 'bg-red-100 text-red-600',
}
const fmtDate = (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '—'
const fmt = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function MedicoesSection({ contratoId, medicoes, podeEditar }) {
  const { addMedicao, updateMedicao, deleteMedicao } = useContratoStore()
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [form, setForm] = useState({
    competencia_inicio: '', competencia_fim: '', data_medicao: '',
    percentual_executado: '', valor_medido: '', numero_processo_sei: '',
  })

  const handleAdd = async () => {
    if (!form.competencia_inicio || !form.competencia_fim || !form.data_medicao || !form.valor_medido) return
    setSaving(true)
    try {
      await addMedicao(contratoId, {
        ...form,
        percentual_executado: form.percentual_executado ? Number(form.percentual_executado) : null,
        valor_medido: Number(form.valor_medido),
      })
      setShowForm(false)
      setForm({ competencia_inicio: '', competencia_fim: '', data_medicao: '', percentual_executado: '', valor_medido: '', numero_processo_sei: '' })
    } finally { setSaving(false) }
  }

  const aprovar = (m) => updateMedicao(contratoId, m.id, { status: 'aprovada', data_aprovacao: new Date().toISOString().slice(0, 10) })
  const rejeitar = (m) => {
    const parecer = prompt('Motivo da rejeição:')
    if (parecer === null) return
    updateMedicao(contratoId, m.id, { status: 'rejeitada', parecer_fiscal: parecer })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold text-gray-400 uppercase">Medições</p>
          <HelpTip text="Registro periódico do fiscal atestando o percentual/valor executado no período. Precisa ser aprovada para gerar saldo a pagar." position="right" />
        </span>
        {podeEditar && <button onClick={() => setShowForm(v => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Nova medição</button>}
      </div>

      {medicoes.length === 0
        ? <p className="text-xs text-gray-400 italic">Nenhuma medição registrada.</p>
        : <ul className="space-y-3">
            {medicoes.map(m => (
              <li key={m.id} className="bg-gray-50 rounded-lg px-3 py-2">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-mono text-xs font-semibold text-gray-700">{m.numero}</span>
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${STATUS_CLS[m.status]}`}>{m.status_display}</span>
                    <p className="text-xs text-gray-600 mt-0.5">
                      Período: {fmtDate(m.competencia_inicio)} → {fmtDate(m.competencia_fim)}
                      {m.percentual_executado != null && ` · ${Number(m.percentual_executado).toFixed(2)}% executado`}
                    </p>
                    <p className="text-sm font-semibold text-gray-800 mt-0.5">{fmt(m.valor_medido)}</p>
                    {m.numero_processo_sei && <p className="text-xs text-gray-400 mt-0.5">SEI: <span className="font-mono">{m.numero_processo_sei}</span></p>}
                    {m.parecer_fiscal && <p className="text-xs text-gray-500 italic mt-0.5">{m.parecer_fiscal}</p>}
                  </div>
                  {podeEditar && (
                    <div className="flex items-center gap-2 ml-3 shrink-0">
                      {m.status === 'pendente' && <>
                        <button onClick={() => aprovar(m)} className="text-xs text-green-600 hover:text-green-800 font-medium">Aprovar</button>
                        <button onClick={() => rejeitar(m)} className="text-xs text-red-500 hover:text-red-700 font-medium">Rejeitar</button>
                      </>}
                      <button onClick={() => deleteMedicao(contratoId, m.id)} className="text-red-400 hover:text-red-600 text-xs">✕</button>
                    </div>
                  )}
                </div>
                {(m.pagamentos || []).length > 0 && (
                  <ul className="mt-2 pl-3 border-l-2 border-gray-200 space-y-1">
                    {m.pagamentos.map(p => (
                      <li key={p.id} className="text-xs text-gray-500">
                        <span className="font-mono">{p.numero}</span> · {fmt(p.valor_pago)} · {p.status_display}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>}

      {showForm && (
        <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
          <p className="text-xs font-semibold text-blue-700 mb-2">Nova medição</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Início do período *</label>
              <input type="date" value={form.competencia_inicio} onChange={e => setForm(p => ({ ...p, competencia_inicio: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Fim do período *</label>
              <input type="date" value={form.competencia_fim} onChange={e => setForm(p => ({ ...p, competencia_fim: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Data da medição *</label>
              <input type="date" value={form.data_medicao} onChange={e => setForm(p => ({ ...p, data_medicao: e.target.value }))} className={inp()} />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-0.5">Percentual executado (%)</label>
              <input type="number" min="0" max="100" step="0.01" value={form.percentual_executado} onChange={e => setForm(p => ({ ...p, percentual_executado: e.target.value }))} className={inp()} />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Valor medido (R$) *</label>
              <CampoMoeda value={form.valor_medido} onChange={v => setForm(p => ({ ...p, valor_medido: v }))} className={inp()} />
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-0.5">Processo SEI</label>
              <CampoSei value={form.numero_processo_sei} onChange={v => setForm(p => ({ ...p, numero_processo_sei: v }))} className={inp()} />
            </div>
          </div>
          <div className="flex gap-2 mt-2">
            <button onClick={handleAdd}
              disabled={saving || !form.competencia_inicio || !form.competencia_fim || !form.data_medicao || !form.valor_medido}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
              {saving ? '...' : 'Salvar medição'}
            </button>
            <button onClick={() => setShowForm(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
          </div>
        </div>
      )}
    </div>
  )
}
