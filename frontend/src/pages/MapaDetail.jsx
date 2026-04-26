import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useMapaStore from '../stores/mapaStore'
import LoadingSpinner from '../components/LoadingSpinner'

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

const TIPO_FONTE_LABELS = {
  'I':    'I — SIMPAS / Comprasnet.BA',
  'II':   'II — Contratações similares',
  'III':  'III — Mídia especializada',
  'IV':   'IV — Pesquisa direta',
  'V':    'V — Notas fiscais',
  'HIST': 'Histórico WEBBER',
}

const MOTIVOS_EXCLUSAO = [
  { value: 'excessivo',    label: 'Excessivamente elevado (+30%)' },
  { value: 'inexequivel',  label: 'Inexequível (−30%)' },
  { value: 'inconsistente',label: 'Inconsistente / Especificação diferente' },
  { value: 'desatualizado',label: 'Desatualizado / Prazo vencido' },
  { value: 'manual',       label: 'Excluído manualmente' },
]

export default function MapaDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    current, loading, error,
    fetchMapa, fetchMetadados, updateMapa, deleteMapa,
    finalizar, recalcular, fetchHistoricoWebber,
    addFonte, deleteFonte,
    addItem, deleteItem,
    addPreco, updatePreco, deletePreco,
    metadados,
  } = useMapaStore()

  const [msg, setMsg]               = useState(null)
  const [saving, setSaving]         = useState(false)
  const [activeTab, setActiveTab]   = useState('fontes') // 'fontes' | 'itens' | 'historico'
  const [historicoWB, setHistoricoWB] = useState(null)
  const [loadingHist, setLoadingHist] = useState(false)

  // Forms locais
  const [fonteForm, setFonteForm]   = useState(null)
  const [itemForm, setItemForm]     = useState(null)
  const [precoForms, setPrecoForms] = useState({}) // keyed by itemId

  useEffect(() => { fetchMapa(id); fetchMetadados() }, [id])

  const act = async (fn, successMsg) => {
    setSaving(true); setMsg(null)
    try {
      const r = await fn()
      setMsg({ type: 'success', text: successMsg || 'Operação concluída.' })
      return r
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao executar operação.' })
    } finally { setSaving(false) }
  }

  const loadHistoricoWB = async () => {
    setLoadingHist(true)
    try { setHistoricoWB(await fetchHistoricoWebber(id)) }
    finally { setLoadingHist(false) }
  }

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando mapa..." /></div>
  if (error)   return <div className="p-8 text-sm text-red-600">{error}</div>
  if (!current) return null

  const isRascunho  = current.status === 'Rascunho'
  const isFinalizado = current.status === 'Finalizado'

  return (
    <div className="p-8 max-w-5xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Mapa Comparativo de Preços #{current.id}</h1>
          <p className="text-sm text-gray-500 mt-0.5 max-w-xl">{current.objeto}</p>
          <div className="flex items-center gap-3 mt-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              current.status === 'Finalizado' ? 'bg-green-100 text-green-700'
              : current.status === 'Cancelado' ? 'bg-red-100 text-red-600'
              : 'bg-gray-100 text-gray-600'
            }`}>{current.status}</span>
            <span className="text-xs text-gray-400">Exercício {current.exercicio_fiscal}</span>
            {current.dfd_numero_sei && (
              <span className="text-xs font-mono text-blue-700">DFD: {current.dfd_numero_sei}</span>
            )}
            <span className="text-xs text-gray-400">Método: {current.metodo_display}</span>
          </div>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {isRascunho && (
            <>
              <button onClick={() => act(() => recalcular(id), 'Valores recalculados.')} disabled={saving}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
                Recalcular
              </button>
              <button onClick={() => act(() => finalizar(id), 'Mapa finalizado.')} disabled={saving}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
                Finalizar Mapa
              </button>
            </>
          )}
          {isFinalizado && (
            <a href={`/api/pesquisa/mapa/${id}/export/pdf/`} target="_blank" rel="noreferrer"
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg inline-block">
              Baixar PDF
            </a>
          )}
        </div>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${
          msg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200'
                                 : 'bg-red-50 text-red-700 border border-red-200'
        }`}>{msg.text}</div>
      )}

      {/* Valor total */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6 flex gap-6">
        <div>
          <p className="text-xs font-semibold text-blue-800 uppercase">Valor Estimado Total</p>
          <p className="text-2xl font-bold text-blue-700">{fmt(current.valor_estimado_total)}</p>
        </div>
        <div className="border-l border-blue-200 pl-6">
          <p className="text-xs text-blue-700">Itens: <strong>{current.qtd_itens}</strong></p>
          <p className="text-xs text-blue-700">Fontes: <strong>{current.qtd_fontes}</strong></p>
          <p className="text-xs text-blue-700">Método: <strong>{current.metodo_display}</strong></p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-5 gap-1">
        {[
          { key: 'fontes', label: `Fontes (${current.fontes?.length ?? 0})` },
          { key: 'itens',  label: `Itens e Preços (${current.itens?.length ?? 0})` },
          { key: 'historico', label: 'Histórico WEBBER' },
        ].map(({ key, label }) => (
          <button key={key} onClick={() => { setActiveTab(key); if (key === 'historico' && !historicoWB) loadHistoricoWB() }}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === key
                ? 'border-b-2 border-blue-600 text-blue-700 bg-blue-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Fontes */}
      {activeTab === 'fontes' && (
        <div>
          {isRascunho && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Adicionar fonte consultada</p>
              <FonteForm
                metadados={metadados}
                onSave={async (payload) => {
                  await act(() => addFonte(id, payload), 'Fonte adicionada.')
                  setFonteForm(null)
                }}
              />
            </div>
          )}
          {(current.fontes || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhuma fonte cadastrada. Adicione as fontes consultadas conforme Art. 5º do Decreto 22.886/2024.</p>
            : (
              <div className="space-y-2">
                {current.fontes.map((f) => (
                  <div key={f.id} className={`flex items-start justify-between p-4 rounded-xl border ${
                    f.infrutífera ? 'border-orange-200 bg-orange-50' : 'border-gray-200 bg-white'
                  }`}>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                          {TIPO_FONTE_LABELS[f.tipo] || f.tipo}
                        </span>
                        {f.infrutífera && <span className="bg-orange-100 text-orange-700 text-xs px-2 py-0.5 rounded-full">Infrutífera</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-800">{f.descricao}</p>
                      {f.referencia && <p className="text-xs text-gray-500 mt-0.5">{f.referencia}</p>}
                      <p className="text-xs text-gray-400 mt-0.5">
                        Consulta: {f.data_consulta ? new Date(f.data_consulta).toLocaleDateString('pt-BR') : '—'}
                        {f.documento_sei && ` · SEI: ${f.documento_sei}`}
                      </p>
                      {f.infrutífera && f.justificativa_infrutífera && (
                        <p className="text-xs text-orange-700 mt-1">Justificativa: {f.justificativa_infrutífera}</p>
                      )}
                    </div>
                    {isRascunho && (
                      <button onClick={() => act(() => deleteFonte(id, f.id), 'Fonte removida.')}
                        className="text-xs text-red-500 hover:text-red-700 ml-4 shrink-0">Remover</button>
                    )}
                  </div>
                ))}
              </div>
            )}
        </div>
      )}

      {/* Tab: Itens e Preços */}
      {activeTab === 'itens' && (
        <div className="space-y-6">
          {isRascunho && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
              <p className="text-sm font-semibold text-gray-700 mb-3">Adicionar item</p>
              <ItemForm onSave={async (payload) => { await act(() => addItem(id, payload), 'Item adicionado.') }} />
            </div>
          )}

          {(current.itens || []).length === 0
            ? <p className="text-sm text-gray-400">Nenhum item cadastrado. Adicione os itens que compõem o objeto da pesquisa.</p>
            : (current.itens || []).map((item) => (
              <div key={item.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                {/* Cabeçalho do item */}
                <div className="flex items-center justify-between px-5 py-3 bg-gray-50 border-b border-gray-200">
                  <div>
                    <span className="text-xs font-bold text-gray-500 mr-2">#{item.ordem}</span>
                    <span className="font-medium text-gray-800">{item.descricao}</span>
                    {item.codigo_simpas && <span className="ml-2 text-xs font-mono text-blue-600">[{item.codigo_simpas}]</span>}
                    <span className="ml-3 text-xs text-gray-500">{item.quantidade} {item.unidade_medida}</span>
                  </div>
                  {item.valor_unitario_calculado && (
                    <div className="text-right">
                      <p className="text-xs text-gray-400">{item.metodo_aplicado} · {item.qtd_precos_validos} preço(s)</p>
                      <p className="font-semibold text-green-700 text-sm">{fmt(item.valor_unitario_calculado)}/un · Total: {fmt(item.valor_total_calculado)}</p>
                    </div>
                  )}
                  {isRascunho && (
                    <button onClick={() => act(() => deleteItem(id, item.id), 'Item removido.')}
                      className="text-xs text-red-500 hover:text-red-700 ml-4">Remover item</button>
                  )}
                </div>

                {/* Alertas */}
                {item.alerta && (
                  <div className="px-5 py-2 bg-amber-50 border-b border-amber-200">
                    <p className="text-xs text-amber-800">⚠ {item.alerta}</p>
                  </div>
                )}

                {/* Preços coletados */}
                <div className="px-5 py-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-3">
                    Preços coletados ({item.precos?.length ?? 0})
                  </p>

                  {(item.precos || []).length > 0 && (
                    <div className="mb-4 overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-50 border border-gray-200">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Fonte</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Origem / Órgão</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Certame</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Data</th>
                            <th className="text-right px-3 py-2 font-medium text-gray-500">Valor Unit.</th>
                            <th className="text-center px-3 py-2 font-medium text-gray-500">Válido</th>
                            <th className="text-left px-3 py-2 font-medium text-gray-500">Obs / Alerta</th>
                            {isRascunho && <th className="px-3 py-2"></th>}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100 border border-gray-200">
                          {item.precos.map((p) => (
                            <tr key={p.id} className={!p.valido ? 'opacity-50 bg-red-50' : p.sugestao_exclusao ? 'bg-amber-50' : ''}>
                              <td className="px-3 py-2">
                                <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs font-semibold">
                                  {p.fonte_tipo}
                                </span>
                                <span className="ml-1 text-gray-500">{p.fonte_descricao?.slice(0,20)}</span>
                              </td>
                              <td className="px-3 py-2 text-gray-700">{p.origem_orgao_empresa || '—'}</td>
                              <td className="px-3 py-2 text-gray-500">{p.numero_certame || '—'}</td>
                              <td className="px-3 py-2 text-gray-500">
                                {p.data_referencia ? new Date(p.data_referencia).toLocaleDateString('pt-BR') : '—'}
                              </td>
                              <td className="px-3 py-2 text-right font-semibold text-gray-800">{fmt(p.valor_unitario)}</td>
                              <td className="px-3 py-2 text-center">
                                {isRascunho ? (
                                  <input type="checkbox" checked={p.valido}
                                    onChange={async (e) => {
                                      await act(
                                        () => updatePreco(id, item.id, p.id, { valido: e.target.checked }),
                                        e.target.checked ? 'Preço reativado.' : 'Preço excluído do cálculo.'
                                      )
                                    }}
                                    className="accent-blue-600" />
                                ) : (
                                  <span className={p.valido ? 'text-green-600' : 'text-red-500'}>
                                    {p.valido ? '✓' : '✗'}
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2">
                                {p.sugestao_exclusao && <span className="text-amber-700">⚠ {p.sugestao_exclusao}</span>}
                                {!p.valido && p.motivo_exclusao_display && <span className="text-red-600">{p.motivo_exclusao_display}</span>}
                              </td>
                              {isRascunho && (
                                <td className="px-3 py-2 text-right">
                                  <button onClick={() => act(() => deletePreco(id, item.id, p.id), 'Preço removido.')}
                                    className="text-red-500 hover:text-red-700">✕</button>
                                </td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Formulário novo preço */}
                  {isRascunho && (
                    <PrecoForm
                      itemId={item.id}
                      fontes={current.fontes || []}
                      onSave={async (payload) => {
                        await act(() => addPreco(id, item.id, payload), 'Preço adicionado.')
                      }}
                    />
                  )}
                </div>
              </div>
            ))
          }
        </div>
      )}

      {/* Tab: Histórico WEBBER */}
      {activeTab === 'historico' && (
        <div>
          {loadingHist && <LoadingSpinner message="Consultando histórico WEBBER..." />}
          {!loadingHist && !historicoWB && (
            <button onClick={loadHistoricoWB}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm px-4 py-2 rounded-lg">
              Consultar histórico de aquisições
            </button>
          )}
          {historicoWB && (
            <div>
              <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 text-sm text-blue-800">
                <strong>Histórico WEBBER:</strong> {historicoWB.nota}
                <span className="ml-2 font-semibold">({historicoWB.total} item(s) encontrado(s))</span>
              </div>
              {historicoWB.itens.length === 0
                ? <p className="text-sm text-gray-400">Nenhum item de DFD aprovado encontrado nos últimos 2 anos para este órgão.</p>
                : (
                  <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">DFD</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Item</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Qtd</th>
                          <th className="text-right px-4 py-2 font-medium text-gray-500">Valor Unit.</th>
                          <th className="text-left px-4 py-2 font-medium text-gray-500">Data</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {historicoWB.itens.map((h, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="px-4 py-2 font-mono text-xs text-blue-700">{h.dfd_numero_sei}</td>
                            <td className="px-4 py-2 text-gray-700 max-w-xs truncate">{h.item_descricao}</td>
                            <td className="px-4 py-2 text-gray-500">{h.quantidade} {h.unidade_medida}</td>
                            <td className="px-4 py-2 text-right font-semibold">{fmt(h.valor_unitario)}</td>
                            <td className="px-4 py-2 text-xs text-gray-400">{h.dfd_data}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Sub-componentes de formulário ─────────────────────────────────────────────

function FonteForm({ metadados, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    tipo: 'I', descricao: '', referencia: '', data_consulta: hoje,
    documento_sei: '', infrutífera: false, justificativa_infrutífera: '',
  })
  const [saving, setSaving] = useState(false)
  const tipos = metadados?.tipos_fonte || []

  const handleSave = async () => {
    if (!form.descricao.trim()) return
    setSaving(true)
    try { await onSave(form) } finally { setSaving(false) }
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Parâmetro (Art. 5º) *</label>
        <select value={form.tipo} onChange={(e) => setForm(p => ({ ...p, tipo: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500">
          {tipos.map(({ value, label }) => <option key={value} value={value}>{label}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Data da consulta *</label>
        <input type="date" value={form.data_consulta}
          onChange={(e) => setForm(p => ({ ...p, data_consulta: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2">
        <label className="block text-xs font-medium text-gray-600 mb-1">Descrição da fonte *</label>
        <input type="text" value={form.descricao}
          onChange={(e) => setForm(p => ({ ...p, descricao: e.target.value }))}
          placeholder="Ex: Portal SIMPAS — consulta 26/04/2026, Pregão PMMG 001/2025"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Referência (SEI, URL, certame)</label>
        <input type="text" value={form.referencia}
          onChange={(e) => setForm(p => ({ ...p, referencia: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Nº documento SEI</label>
        <input type="text" value={form.documento_sei}
          onChange={(e) => setForm(p => ({ ...p, documento_sei: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2 flex items-center gap-2">
        <input type="checkbox" id="infrutífera" checked={form.infrutífera}
          onChange={(e) => setForm(p => ({ ...p, infrutífera: e.target.checked }))}
          className="accent-orange-500" />
        <label htmlFor="infrutífera" className="text-xs text-gray-600 cursor-pointer">
          Consulta infrutífera (fornecedor não respondeu / item indisponível)
        </label>
      </div>
      {form.infrutífera && (
        <div className="col-span-2">
          <label className="block text-xs font-medium text-gray-600 mb-1">Justificativa da consulta infrutífera</label>
          <input type="text" value={form.justificativa_infrutífera}
            onChange={(e) => setForm(p => ({ ...p, justificativa_infrutífera: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      )}
      <div className="col-span-2">
        <button onClick={handleSave} disabled={saving || !form.descricao.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
          {saving ? 'Salvando...' : 'Adicionar fonte'}
        </button>
      </div>
    </div>
  )
}

function ItemForm({ onSave }) {
  const [form, setForm] = useState({ ordem: 1, descricao: '', codigo_simpas: '', unidade_medida: 'UND', quantidade: 1 })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.descricao.trim()) return
    setSaving(true)
    try { await onSave({ ...form, quantidade: Number(form.quantidade), ordem: Number(form.ordem) }) } finally { setSaving(false) }
  }

  return (
    <div className="grid grid-cols-4 gap-3">
      <div className="col-span-2">
        <label className="block text-xs font-medium text-gray-600 mb-1">Descrição do item *</label>
        <input type="text" value={form.descricao}
          onChange={(e) => setForm(p => ({ ...p, descricao: e.target.value }))}
          placeholder="Ex: Torniquete tático de combate"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Código SIMPAS</label>
        <input type="text" value={form.codigo_simpas}
          onChange={(e) => setForm(p => ({ ...p, codigo_simpas: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Unid. medida</label>
        <input type="text" value={form.unidade_medida}
          onChange={(e) => setForm(p => ({ ...p, unidade_medida: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Quantidade</label>
        <input type="number" min="0.001" step="0.001" value={form.quantidade}
          onChange={(e) => setForm(p => ({ ...p, quantidade: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Ordem</label>
        <input type="number" min="1" value={form.ordem}
          onChange={(e) => setForm(p => ({ ...p, ordem: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>
      <div className="col-span-2 flex items-end">
        <button onClick={handleSave} disabled={saving || !form.descricao.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-2 rounded-lg">
          {saving ? 'Adicionando...' : 'Adicionar item'}
        </button>
      </div>
    </div>
  )
}

function PrecoForm({ itemId, fontes, onSave }) {
  const hoje = new Date().toISOString().split('T')[0]
  const [form, setForm] = useState({
    fonte: '', valor_unitario: '', origem_orgao_empresa: '',
    numero_certame: '', data_referencia: hoje, observacao: '',
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    if (!form.fonte || !form.valor_unitario) return
    setSaving(true)
    try {
      await onSave({ ...form, valor_unitario: Number(form.valor_unitario), fonte: Number(form.fonte) })
      setForm(p => ({ ...p, valor_unitario: '', origem_orgao_empresa: '', numero_certame: '', observacao: '' }))
    } finally { setSaving(false) }
  }

  return (
    <div className="bg-gray-50 rounded-lg p-3 mt-2">
      <p className="text-xs font-semibold text-gray-600 mb-2">+ Adicionar preço coletado</p>
      <div className="grid grid-cols-3 gap-2">
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-1">Fonte *</label>
          <select value={form.fonte} onChange={(e) => setForm(p => ({ ...p, fonte: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500">
            <option value="">Selecione a fonte...</option>
            {fontes.filter(f => !f.infrutífera).map(f => (
              <option key={f.id} value={f.id}>[{f.tipo}] {f.descricao.slice(0,40)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Valor unitário (R$) *</label>
          <input type="number" min="0" step="0.01" value={form.valor_unitario}
            onChange={(e) => setForm(p => ({ ...p, valor_unitario: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Órgão / Empresa origem</label>
          <input type="text" value={form.origem_orgao_empresa}
            onChange={(e) => setForm(p => ({ ...p, origem_orgao_empresa: e.target.value }))}
            placeholder="Ex: PMMG, CNPJ 12.345.678/0001-00"
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Certame / Processo</label>
          <input type="text" value={form.numero_certame}
            onChange={(e) => setForm(p => ({ ...p, numero_certame: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Data referência *</label>
          <input type="date" value={form.data_referencia}
            onChange={(e) => setForm(p => ({ ...p, data_referencia: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500" />
        </div>
        <div className="col-span-3 flex justify-end">
          <button onClick={handleSave} disabled={saving || !form.fonte || !form.valor_unitario}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-4 py-1.5 rounded-lg">
            {saving ? '...' : 'Registrar preço'}
          </button>
        </div>
      </div>
    </div>
  )
}
