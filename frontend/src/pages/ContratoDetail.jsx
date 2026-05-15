import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useContratoStore from '../stores/contratoStore'
import useAuthStore from '../stores/authStore'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Vigente:    'bg-green-100 text-green-700',
  Encerrado:  'bg-gray-100 text-gray-500',
  Suspenso:   'bg-yellow-100 text-yellow-700',
  Rescindido: 'bg-red-100 text-red-600',
}
const STATUS_OPTS = ['Vigente', 'Encerrado', 'Suspenso', 'Rescindido']
const GARANTIA_TIPOS = [
  { value: 'caucao_dinheiro', label: 'Caução em Dinheiro' },
  { value: 'caucao_titulos',  label: 'Caução em Títulos da Dívida Pública' },
  { value: 'seguro_garantia', label: 'Seguro-Garantia' },
  { value: 'fianca_bancaria', label: 'Fiança Bancária' },
]
const TIPOS_ADITIVO = [
  { value: 'prazo',    label: 'Prorrogação de Prazo' },
  { value: 'valor',    label: 'Acréscimo/Redução de Valor' },
  { value: 'objeto',   label: 'Alteração de Objeto' },
  { value: 'rescisao', label: 'Rescisão' },
]
const fmt = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function ContratoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const papel = useAuthStore((s) => s.papel)
  const { current, loading, error, fetchContrato, updateContrato, deleteContrato, addApostila, deleteApostila, addAditivo, deleteAditivo } = useContratoStore()

  const [editing, setEditing]   = useState(false)
  const [form, setForm]         = useState(null)
  const [saving, setSaving]     = useState(false)

  const [showApostila, setShowApostila] = useState(false)
  const [apostilaForm, setApostilaForm] = useState({ objeto: '', data: '' })
  const [savingAp, setSavingAp]         = useState(false)

  const [showAditivo, setShowAditivo] = useState(false)
  const [aditivoForm, setAditivoForm] = useState({ tipo: 'prazo', objeto: '', data: '', valor_acrescimo: '', nova_vigencia: '' })
  const [savingAd, setSavingAd]       = useState(false)

  useEffect(() => { fetchContrato(id) }, [id])
  useEffect(() => { if (current) setForm({ ...current }) }, [current])

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateContrato(id, {
        objeto: form.objeto,
        valor_contrato: Number(form.valor_contrato),
        data_assinatura: form.data_assinatura || null,
        data_vigencia_inicio: form.data_vigencia_inicio || null,
        data_vigencia_fim: form.data_vigencia_fim || null,
        status: form.status,
        fiscal_contrato: form.fiscal_contrato || null,
        gestor_contrato: form.gestor_contrato || null,
        ordenador: form.ordenador || null,
        observacoes: form.observacoes,
        garantia_exigida: form.garantia_exigida,
        garantia_tipo: form.garantia_tipo || '',
        garantia_percentual: form.garantia_percentual !== '' && form.garantia_percentual != null
          ? Number(form.garantia_percentual) : null,
        garantia_apolice: form.garantia_apolice || '',
        garantia_vigencia_inicio: form.garantia_vigencia_inicio || null,
        garantia_vigencia_fim: form.garantia_vigencia_fim || null,
        garantia_justificativa_acima_5: form.garantia_justificativa_acima_5 || '',
      })
      setEditing(false)
    } finally { setSaving(false) }
  }

  const handleDelete = async () => {
    if (!confirm('Excluir este contrato? Esta ação não pode ser desfeita.')) return
    await deleteContrato(id)
    navigate('/contratos')
  }

  const handleAddApostila = async () => {
    if (!apostilaForm.objeto.trim() || !apostilaForm.data) return
    setSavingAp(true)
    try { await addApostila(id, apostilaForm); setShowApostila(false); setApostilaForm({ objeto: '', data: '' }) }
    finally { setSavingAp(false) }
  }

  const handleAddAditivo = async () => {
    if (!aditivoForm.objeto.trim() || !aditivoForm.data) return
    setSavingAd(true)
    try {
      const payload = { ...aditivoForm, valor_acrescimo: aditivoForm.valor_acrescimo ? Number(aditivoForm.valor_acrescimo) : null, nova_vigencia: aditivoForm.nova_vigencia || null }
      await addAditivo(id, payload)
      setShowAditivo(false); setAditivoForm({ tipo: 'prazo', objeto: '', data: '', valor_acrescimo: '', nova_vigencia: '' })
    } finally { setSavingAd(false) }
  }

  if (loading) return <LoadingSpinner />
  if (error)   return <div className="p-8 text-red-600">{error}</div>
  if (!current || !form) return null

  const podeEditar = !['Encerrado', 'Rescindido'].includes(current.status)

  return (
    <div className="p-8 max-w-2xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero}</h1>
          <span className={`mt-1 inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status]}`}>
            {current.status}
          </span>
          <p className="text-xs text-gray-400 mt-1">{current.orgao_executor_sigla} · Ex. {current.exercicio} · {current.tipo_origem_display}</p>
        </div>
        <div className="flex gap-2">
          {podeEditar && !editing && <button onClick={() => setEditing(true)} className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">Editar</button>}
          {editing && <>
            <button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">{saving ? 'Salvando...' : 'Salvar'}</button>
            <button onClick={() => { setEditing(false); setForm({ ...current }) }} className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg">Cancelar</button>
          </>}
          {papel === 'admin' && <button onClick={handleDelete} className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">Excluir</button>}
        </div>
      </div>

      <div className="space-y-5">
        {/* Objeto */}
        <Section label="Objeto">
          {editing
            ? <textarea rows={3} value={form.objeto} onChange={e => set('objeto', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700 text-justify">{current.objeto}</p>}
        </Section>

        {/* Valor e status */}
        <div className="grid grid-cols-2 gap-5">
          <Section label="Valor do contrato">
            {editing
              ? <input type="number" step="0.01" value={form.valor_contrato} onChange={e => set('valor_contrato', e.target.value)} className={inp()} />
              : <p className="text-base font-bold text-gray-800">{fmt(current.valor_contrato)}</p>}
          </Section>
          <Section label="Status">
            {editing
              ? <select value={form.status} onChange={e => set('status', e.target.value)} className={inp()}>
                  {STATUS_OPTS.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              : <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status]}`}>{current.status}</span>}
          </Section>
        </div>

        {/* Datas */}
        <div className="grid grid-cols-3 gap-4">
          <Section label="Data de assinatura">
            {editing
              ? <input type="date" value={form.data_assinatura || ''} onChange={e => set('data_assinatura', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700">{current.data_assinatura ? new Date(current.data_assinatura).toLocaleDateString('pt-BR') : '—'}</p>}
          </Section>
          <Section label="Início da vigência">
            {editing
              ? <input type="date" value={form.data_vigencia_inicio || ''} onChange={e => set('data_vigencia_inicio', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700">{current.data_vigencia_inicio ? new Date(current.data_vigencia_inicio).toLocaleDateString('pt-BR') : '—'}</p>}
          </Section>
          <Section label="Fim da vigência">
            {editing
              ? <input type="date" value={form.data_vigencia_fim || ''} onChange={e => set('data_vigencia_fim', e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-700">{current.data_vigencia_fim ? new Date(current.data_vigencia_fim).toLocaleDateString('pt-BR') : '—'}</p>}
          </Section>
        </div>

        {/* DFD / Origem */}
        {current.dfd_numero_sei && (
          <Section label="DFD de origem">
            <p className="text-sm font-mono text-blue-700">{current.dfd_numero_sei}</p>
          </Section>
        )}

        {/* Observações */}
        <Section label="Observações">
          {editing
            ? <textarea rows={2} value={form.observacoes || ''} onChange={e => set('observacoes', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500 text-justify">{current.observacoes || '—'}</p>}
        </Section>

        {/* Garantia contratual */}
        <div className="pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Garantia Contratual</p>
          {editing ? (
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input type="checkbox" checked={form.garantia_exigida ?? false}
                  onChange={e => set('garantia_exigida', e.target.checked)}
                  className="w-4 h-4 accent-blue-600" />
                <span className="text-sm text-gray-700">Garantia exigida (art. 96, Lei 14.133/2021)</span>
              </label>
              {form.garantia_exigida && (
                <div className="space-y-3 pl-7">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Tipo</p>
                      <select value={form.garantia_tipo || ''} onChange={e => set('garantia_tipo', e.target.value)} className={inp()}>
                        <option value="">Selecione...</option>
                        {GARANTIA_TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Percentual (%)</p>
                      <input type="number" min="0" max="10" step="0.01"
                        value={form.garantia_percentual ?? ''}
                        onChange={e => set('garantia_percentual', e.target.value)}
                        className={inp()} />
                    </div>
                  </div>
                  {Number(form.garantia_percentual) > 5 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Justificativa (&gt;5%)</p>
                      <textarea rows={2} value={form.garantia_justificativa_acima_5 || ''}
                        onChange={e => set('garantia_justificativa_acima_5', e.target.value)}
                        className={inp()} />
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Nº apólice / título</p>
                    <input type="text" value={form.garantia_apolice || ''}
                      onChange={e => set('garantia_apolice', e.target.value)} className={inp()} />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Início da vigência</p>
                      <input type="date" value={form.garantia_vigencia_inicio || ''}
                        onChange={e => set('garantia_vigencia_inicio', e.target.value)} className={inp()} />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Fim da vigência</p>
                      <input type="date" value={form.garantia_vigencia_fim || ''}
                        onChange={e => set('garantia_vigencia_fim', e.target.value)} className={inp()} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : current.garantia_exigida ? (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-semibold text-amber-800">Garantia exigida</span>
                {current.garantia_tipo_display && (
                  <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full border border-amber-200">
                    {current.garantia_tipo_display}
                  </span>
                )}
                {current.garantia_percentual != null && (
                  <span className="text-xs font-bold text-amber-800">
                    {Number(current.garantia_percentual).toFixed(2)}%
                    {Number(current.garantia_percentual) > 5 && (
                      <span className="ml-1 text-orange-600">(acima de 5%)</span>
                    )}
                  </span>
                )}
              </div>
              {current.garantia_apolice && (
                <p className="text-xs text-amber-700">Apólice/título: <strong>{current.garantia_apolice}</strong></p>
              )}
              {(current.garantia_vigencia_inicio || current.garantia_vigencia_fim) && (
                <p className="text-xs text-amber-700">
                  Vigência: {current.garantia_vigencia_inicio ? new Date(current.garantia_vigencia_inicio).toLocaleDateString('pt-BR') : '—'}
                  {' → '}
                  {current.garantia_vigencia_fim ? new Date(current.garantia_vigencia_fim).toLocaleDateString('pt-BR') : '—'}
                </p>
              )}
              {current.garantia_justificativa_acima_5 && (
                <p className="text-xs text-amber-700 italic">{current.garantia_justificativa_acima_5}</p>
              )}
            </div>
          ) : (
            <p className="text-xs text-gray-400 italic">Garantia não exigida para este contrato.</p>
          )}
        </div>

        {/* Apostilas */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">Apostilas</p>
            {podeEditar && <button onClick={() => setShowApostila(v => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Adicionar</button>}
          </div>
          {(current.apostilas || []).length === 0
            ? <p className="text-xs text-gray-400 italic">Nenhuma apostila cadastrada.</p>
            : <ul className="space-y-2">
                {current.apostilas.map(a => (
                  <li key={a.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                    <div>
                      <span className="font-mono text-xs font-semibold text-gray-700">{a.numero}</span>
                      <span className="ml-2 text-xs text-gray-400">{new Date(a.data).toLocaleDateString('pt-BR')}</span>
                      <p className="text-xs text-gray-600 mt-0.5">{a.objeto}</p>
                    </div>
                    {podeEditar && <button onClick={() => deleteApostila(id, a.id)} className="text-red-400 hover:text-red-600 text-xs ml-3">✕</button>}
                  </li>
                ))}
              </ul>}
          {showApostila && (
            <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
              <p className="text-xs font-semibold text-blue-700 mb-2">Nova apostila</p>
              <div className="grid grid-cols-2 gap-2">
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Objeto *</label>
                  <textarea rows={2} value={apostilaForm.objeto} onChange={e => setApostilaForm(p => ({ ...p, objeto: e.target.value }))} className={inp()} />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Data *</label>
                  <input type="date" value={apostilaForm.data} onChange={e => setApostilaForm(p => ({ ...p, data: e.target.value }))} className={inp()} />
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <button onClick={handleAddApostila} disabled={savingAp || !apostilaForm.objeto.trim() || !apostilaForm.data}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                  {savingAp ? '...' : 'Salvar apostila'}
                </button>
                <button onClick={() => setShowApostila(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
              </div>
            </div>
          )}
        </div>

        {/* Aditivos */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">Aditivos</p>
            {podeEditar && <button onClick={() => setShowAditivo(v => !v)} className="text-xs text-blue-600 hover:text-blue-800 font-medium">+ Adicionar</button>}
          </div>
          {(current.aditivos || []).length === 0
            ? <p className="text-xs text-gray-400 italic">Nenhum aditivo cadastrado.</p>
            : <ul className="space-y-2">
                {current.aditivos.map(a => (
                  <li key={a.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                    <div>
                      <span className="font-mono text-xs font-semibold text-gray-700">{a.numero}</span>
                      <span className="ml-2 text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">{a.tipo_display}</span>
                      <span className="ml-2 text-xs text-gray-400">{new Date(a.data).toLocaleDateString('pt-BR')}</span>
                      {a.valor_acrescimo && <span className="ml-2 text-xs font-semibold text-gray-700">{fmt(a.valor_acrescimo)}</span>}
                      <p className="text-xs text-gray-600 mt-0.5">{a.objeto}</p>
                    </div>
                    {podeEditar && <button onClick={() => deleteAditivo(id, a.id)} className="text-red-400 hover:text-red-600 text-xs ml-3">✕</button>}
                  </li>
                ))}
              </ul>}
          {showAditivo && (
            <div className="mt-3 border border-blue-200 rounded-lg p-3 bg-blue-50">
              <p className="text-xs font-semibold text-blue-700 mb-2">Novo aditivo</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Tipo *</label>
                  <select value={aditivoForm.tipo} onChange={e => setAditivoForm(p => ({ ...p, tipo: e.target.value }))} className={inp()}>
                    {TIPOS_ADITIVO.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Data *</label>
                  <input type="date" value={aditivoForm.data} onChange={e => setAditivoForm(p => ({ ...p, data: e.target.value }))} className={inp()} />
                </div>
                {aditivoForm.tipo === 'valor' && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Valor (R$) — negativo para redução</label>
                    <input type="number" step="0.01" value={aditivoForm.valor_acrescimo} onChange={e => setAditivoForm(p => ({ ...p, valor_acrescimo: e.target.value }))} className={inp()} />
                  </div>
                )}
                {aditivoForm.tipo === 'prazo' && (
                  <div>
                    <label className="block text-xs text-gray-500 mb-0.5">Nova data de vigência</label>
                    <input type="date" value={aditivoForm.nova_vigencia} onChange={e => setAditivoForm(p => ({ ...p, nova_vigencia: e.target.value }))} className={inp()} />
                  </div>
                )}
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Objeto *</label>
                  <textarea rows={2} value={aditivoForm.objeto} onChange={e => setAditivoForm(p => ({ ...p, objeto: e.target.value }))} className={inp()} />
                </div>
              </div>
              <div className="flex gap-2 mt-2">
                <button onClick={handleAddAditivo} disabled={savingAd || !aditivoForm.objeto.trim() || !aditivoForm.data}
                  className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                  {savingAd ? '...' : 'Salvar aditivo'}
                </button>
                <button onClick={() => setShowAditivo(false)} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
              </div>
            </div>
          )}
        </div>

        {/* Metadados */}
        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado por: {current.created_by_username} em {new Date(current.created_at).toLocaleString('pt-BR')}</p>
        </div>
      </div>
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

const inp = () => 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
