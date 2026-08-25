import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useAtaStore from '../stores/ataStore'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import CampoMoeda from '../components/CampoMoeda'
import FornecedorPicker from '../components/FornecedorPicker'

const STATUS_CLS = {
  rascunho:  'bg-gray-100 text-gray-600',
  vigente:   'bg-green-100 text-green-700',
  encerrada: 'bg-blue-100 text-blue-700',
  cancelada: 'bg-red-100 text-red-600',
}
const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtData = (v) => v ? new Date(v + 'T00:00').toLocaleDateString('pt-BR') : '—'

function itemVazio() {
  return { item_catalogo: null, item_catalogo_label: '', objeto: '', unidade_medida: '', fornecedor: null, fornecedor_label: '', quantidade_registrada: '', valor_unitario_registrado: '' }
}

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Ata de Registro de Preços — Detalhe',
  descricao: 'Detalhe da ata: dados gerais, itens registrados com saldo disponível, e o histórico de transições de status.',
  acoes: [
    { label: 'Ativar (tornar vigente)', texto: 'Só a partir daqui a ata entra no Confronto de Necessidades — Rascunho não conta para sugestões.' },
    { label: 'Encerrar',                texto: 'Marca a ata como Encerrada ao fim de sua vigência — exige motivo. A ata para de aparecer no confronto.' },
    { label: 'Cancelar',                texto: 'Cancela a ata definitivamente — exige motivo.' },
    { label: '+ Adicionar item',        texto: 'Vincular o item ao catálogo é o que permite que ele apareça no confronto contra DFDs pendentes com o mesmo item.' },
    { label: 'Saldo disponível',        texto: 'Quantidade registrada menos a já consumida. Nesta versão o consumo não é decrementado automaticamente — não há ainda fluxo de Saque de ata.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 82 a 86.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function AtaDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { current, loading, error, fetchAta, updateAta, ativarAta, encerrarAta, cancelarAta, criarItem, removerItem } = useAtaStore()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})
  const [actionMsg, setActionMsg] = useState(null)
  const [showMotivo, setShowMotivo] = useState(null)
  const [motivo, setMotivo] = useState('')
  const [showNovoItem, setShowNovoItem] = useState(false)
  const [novoItem, setNovoItem] = useState(itemVazio())
  const [itemQuery, setItemQuery] = useState('')
  const [itemResultados, setItemResultados] = useState([])

  useEffect(() => { fetchAta(id) }, [id])

  useEffect(() => {
    if (current) {
      setForm({
        objeto: current.objeto, observacoes: current.observacoes || '',
        data_assinatura: current.data_assinatura || '', data_vigencia_inicio: current.data_vigencia_inicio || '',
        data_vigencia_fim: current.data_vigencia_fim || '',
      })
    }
  }, [current])

  useEffect(() => {
    if (!itemQuery || itemQuery.length < 2) { setItemResultados([]); return }
    const t = setTimeout(async () => {
      const { data } = await api.get('/core/catalogo/', { params: { search: itemQuery, page_size: 8 } })
      setItemResultados(data.results ?? data)
    }, 300)
    return () => clearTimeout(t)
  }, [itemQuery])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    setSaving(true)
    try {
      await updateAta(id, form)
      setEditing(false)
    } catch (err) {
      const data = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const act = async (fn, ...args) => {
    setSaving(true); setActionMsg(null)
    try {
      await fn(...args)
      setActionMsg({ type: 'success', text: 'Operação realizada com sucesso.' })
      setShowMotivo(null); setMotivo('')
    } catch (err) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao executar operação.' })
    } finally { setSaving(false) }
  }

  const handleAddItem = async () => {
    if (!novoItem.objeto.trim() || !novoItem.unidade_medida.trim() ||
        !(parseFloat(novoItem.quantidade_registrada) > 0) || !(parseFloat(novoItem.valor_unitario_registrado) > 0)) {
      setActionMsg({ type: 'error', text: 'Preencha objeto, unidade, quantidade e valor unitário do item.' })
      return
    }
    setSaving(true)
    try {
      await criarItem(id, {
        item_catalogo: novoItem.item_catalogo || null,
        objeto: novoItem.objeto,
        unidade_medida: novoItem.unidade_medida,
        fornecedor: novoItem.fornecedor || null,
        quantidade_registrada: parseFloat(novoItem.quantidade_registrada),
        valor_unitario_registrado: parseFloat(novoItem.valor_unitario_registrado),
      })
      setNovoItem(itemVazio()); setItemQuery(''); setShowNovoItem(false)
    } catch (err) {
      setActionMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao adicionar item.' })
    } finally { setSaving(false) }
  }

  if (loading) return <div className="p-8"><LoadingSpinner /></div>
  if (error) return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current || !form) return null

  const isRascunho = current.status === 'rascunho'
  const isVigente = current.status === 'vigente'

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero_ata}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || ''}`}>
              {current.status_display}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {current.tipo_origem_display}
            {current.procedimento_numero && ` · Procedimento ${current.procedimento_numero}`}
            {current.orgao_gerenciador_nome && ` · Gerenciada por ${current.orgao_gerenciador_nome}`}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {!editing && (
            <button onClick={() => setEditing(true)}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Editar
            </button>
          )}
          {isRascunho && (
            <button onClick={() => act(ativarAta, id)} disabled={saving}
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
              onClick={() => act(showMotivo === 'encerrar' ? encerrarAta : cancelarAta, id, motivo)}
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
        <DetailField label="Objeto">
          {editing ? (
            <textarea rows={3} value={form.objeto} onChange={(e) => set('objeto', e.target.value)} className={inputCls()} />
          ) : <p className="text-sm text-gray-700">{current.objeto}</p>}
        </DetailField>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <DetailField label="Data de assinatura">
            {editing ? (
              <input type="date" value={form.data_assinatura} onChange={(e) => set('data_assinatura', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{fmtData(current.data_assinatura)}</p>}
          </DetailField>
          <DetailField label="Início da vigência">
            {editing ? (
              <input type="date" value={form.data_vigencia_inicio} onChange={(e) => set('data_vigencia_inicio', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{fmtData(current.data_vigencia_inicio)}</p>}
          </DetailField>
          <DetailField label="Fim da vigência">
            {editing ? (
              <input type="date" value={form.data_vigencia_fim} onChange={(e) => set('data_vigencia_fim', e.target.value)} className={inputCls()} />
            ) : <p className="text-sm text-gray-500">{fmtData(current.data_vigencia_fim)}</p>}
          </DetailField>
        </div>

        <DetailField label="Observações">
          {editing ? (
            <textarea rows={2} value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)} className={inputCls()} />
          ) : <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>}
        </DetailField>

        {editing && (
          <div className="flex gap-2">
            <button onClick={handleSave} disabled={saving}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              {saving ? 'Salvando...' : 'Salvar'}
            </button>
            <button onClick={() => { setEditing(false); setErrors({}) }}
              className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Cancelar edição
            </button>
          </div>
        )}

        {/* Itens */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">
              Itens da Ata ({(current.itens || []).length}) · Saldo total: {current.saldo_total}
            </p>
            {!showNovoItem && (
              <button onClick={() => setShowNovoItem(true)}
                className="text-xs text-indigo-600 hover:text-indigo-800 font-medium border border-indigo-200 hover:border-indigo-400 px-3 py-1 rounded-lg">
                + Adicionar item
              </button>
            )}
          </div>

          {(current.itens || []).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-3">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Objeto</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Fornecedor</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Qtd. registrada</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Vl. unit.</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Saldo</th>
                    <th className="px-4 py-2" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {current.itens.map(it => (
                    <tr key={it.id}>
                      <td className="px-4 py-2 text-gray-800">
                        {it.objeto}
                        {it.catalogo_codigo_simpas && <span className="block text-[10px] text-gray-400 font-mono">{it.catalogo_codigo_simpas}</span>}
                      </td>
                      <td className="px-4 py-2 text-gray-500 text-xs">{it.fornecedor_nome || '—'}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{it.quantidade_registrada} {it.unidade_medida}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{fmt(it.valor_unitario_registrado)}</td>
                      <td className="px-4 py-2 text-right font-medium text-gray-800">{it.saldo_disponivel}</td>
                      <td className="px-4 py-2 text-right">
                        {isRascunho && (
                          <button onClick={() => removerItem(id, it.id)} className="text-xs text-red-400 hover:text-red-600">Remover</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {showNovoItem && (
            <div className="border border-indigo-200 bg-indigo-50 rounded-lg p-3 space-y-3">
              <div className="relative">
                <label className="block text-xs text-gray-500 mb-0.5">Buscar no catálogo (opcional, recomendado)</label>
                <input type="text" value={itemQuery}
                  onChange={e => { setItemQuery(e.target.value); if (novoItem.item_catalogo) setNovoItem(p => ({ ...p, item_catalogo: null, item_catalogo_label: '' })) }}
                  placeholder="Buscar item do catálogo SIMPAS..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white" />
                {itemQuery && !novoItem.item_catalogo && itemResultados.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {itemResultados.map(cat => (
                      <button key={cat.id} type="button"
                        onClick={() => { setNovoItem(p => ({ ...p, item_catalogo: cat.id, item_catalogo_label: cat.nome, objeto: cat.nome, unidade_medida: cat.unidade_medida || '' })); setItemQuery(cat.nome) }}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                        <span className="block text-gray-800">{cat.nome}</span>
                        <span className="text-xs text-gray-400 font-mono">{cat.codigo_interno} {cat.codigo_simpas}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Objeto</label>
                  <input type="text" value={novoItem.objeto} onChange={e => setNovoItem(p => ({ ...p, objeto: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Unidade</label>
                  <input type="text" value={novoItem.unidade_medida} onChange={e => setNovoItem(p => ({ ...p, unidade_medida: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Quantidade registrada</label>
                  <input type="number" min="0" step="0.0001" value={novoItem.quantidade_registrada}
                    onChange={e => setNovoItem(p => ({ ...p, quantidade_registrada: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-0.5">Valor unitário (R$)</label>
                  <CampoMoeda value={novoItem.valor_unitario_registrado} onChange={v => setNovoItem(p => ({ ...p, valor_unitario_registrado: v }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs text-gray-500 mb-0.5">Fornecedor (opcional)</label>
                  <FornecedorPicker value={novoItem.fornecedor} valueLabel={novoItem.fornecedor_label}
                    onChange={(fid, forn) => setNovoItem(p => ({ ...p, fornecedor: fid, fornecedor_label: forn ? `${forn.documento} — ${forn.nome_razao_social}` : '' }))} />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={handleAddItem} disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg">
                  Adicionar
                </button>
                <button onClick={() => { setShowNovoItem(false); setNovoItem(itemVazio()); setItemQuery('') }}
                  className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>

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
  return `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${error ? 'border-red-400' : 'border-gray-300'}`
}
