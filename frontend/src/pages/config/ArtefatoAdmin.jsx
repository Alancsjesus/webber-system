import { useEffect, useState, useCallback } from 'react'
import api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'

const TIPOS = [
  { value: 'DFD', label: 'DFD — Documento de Formalização da Demanda', cor: 'bg-blue-100 text-blue-700 border-blue-200',   hdr: 'bg-blue-700'   },
  { value: 'ETP', label: 'ETP — Estudo Técnico Preliminar',             cor: 'bg-purple-100 text-purple-700 border-purple-200', hdr: 'bg-purple-700' },
  { value: 'TR',  label: 'TR — Minuta do Termo de Referência',          cor: 'bg-teal-100 text-teal-700 border-teal-200',   hdr: 'bg-teal-700'   },
]

const MODALIDADES = [
  { value: 'licitacao',           label: 'Licitação' },
  { value: 'dispensa_valor',      label: 'Dispensa por Valor' },
  { value: 'dispensa_emergencia', label: 'Dispensa por Emergência' },
  { value: 'inexigibilidade',     label: 'Inexigibilidade' },
  { value: 'arp_saque',           label: 'Saque de ARP' },
]

const TIPOS_OBJETO = [
  { value: 'bens',                label: 'Bens' },
  { value: 'servicos',            label: 'Serviços Comuns' },
  { value: 'servicos_engenharia', label: 'Serviços de Engenharia' },
  { value: 'hibrido',             label: 'Híbrido' },
  { value: 'obras',               label: 'Obras' },
]

const BLANK = { tipo: 'TR', codigo: '', titulo: '', descricao: '', ordem: 0, ativo: true, obrigatorio: false, aplica_modalidades: [], aplica_tipo_objeto: [] }

// ── Preview simulado do documento ─────────────────────────────────────────────
function PreviewDocumento({ tipo, secoes }) {
  const meta = TIPOS.find(t => t.value === tipo)
  const ativas   = secoes.filter(s => s.ativo)
  const inativas = secoes.filter(s => !s.ativo)

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden text-xs shadow-sm h-full flex flex-col">
      {/* Cabeçalho simulado do documento */}
      <div className={`${meta?.hdr || 'bg-gray-700'} text-white px-4 py-3`}>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 bg-white/20 rounded flex items-center justify-center font-black text-xs">{tipo}</div>
          <div>
            <div className="font-semibold text-sm">{meta?.label?.split('—')[0].trim()}</div>
            <div className="text-white/70 text-[10px]">Visualização da estrutura do documento</div>
          </div>
        </div>
      </div>

      {/* Conteúdo do preview */}
      <div className="overflow-y-auto flex-1 p-3 space-y-1.5">
        {ativas.length === 0 ? (
          <p className="text-gray-400 italic text-center py-6">Nenhuma seção ativa.</p>
        ) : (
          ativas.map((s, i) => (
            <div key={s.id} className="rounded-lg overflow-hidden border border-gray-100">
              {/* Título da seção */}
              <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-white">
                <span className="text-gray-400 font-mono text-[10px] w-5 shrink-0">{i + 1}.</span>
                <span className="font-semibold text-xs flex-1">{s.titulo.toUpperCase()}</span>
                {s.obrigatorio && (
                  <span className="text-[9px] bg-red-500/80 px-1.5 py-0.5 rounded">obrig.</span>
                )}
                {s.aplica_modalidades.length > 0 && (
                  <span className="text-[9px] bg-blue-500/60 px-1.5 py-0.5 rounded truncate max-w-[80px]" title={s.aplica_modalidades.join(', ')}>
                    {s.aplica_modalidades.length} modal.
                  </span>
                )}
              </div>
              {/* Conteúdo simulado */}
              <div className="px-3 py-2 bg-gray-50">
                {s.descricao ? (
                  <p className="text-gray-400 italic text-[10px] leading-relaxed">{s.descricao}</p>
                ) : (
                  <div className="space-y-1">
                    <div className="h-2 bg-gray-200 rounded w-full" />
                    <div className="h-2 bg-gray-200 rounded w-4/5" />
                    <div className="h-2 bg-gray-200 rounded w-3/5" />
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {/* Seções inativas */}
        {inativas.length > 0 && (
          <div className="mt-3 pt-3 border-t border-dashed border-gray-200">
            <p className="text-gray-400 text-[10px] font-semibold uppercase mb-1.5">
              Seções inativas ({inativas.length})
            </p>
            {inativas.map(s => (
              <div key={s.id} className="flex items-center gap-2 px-3 py-1.5 rounded bg-gray-100 text-gray-400 mb-1 opacity-60">
                <span className="font-mono text-[10px]">{s.ordem}.</span>
                <span className="text-[11px] line-through">{s.titulo}</span>
              </div>
            ))}
          </div>
        )}

        {/* Bloco simulado de assinaturas */}
        {ativas.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="flex items-center gap-2 px-3 py-2 bg-gray-800 text-white rounded-t-lg">
              <span className="font-semibold text-xs">ASSINATURAS</span>
            </div>
            <div className="grid grid-cols-2 gap-3 p-3 bg-gray-50 rounded-b-lg border border-t-0 border-gray-100">
              <div className="text-center">
                <div className="h-px bg-gray-300 mb-1" />
                <p className="text-[10px] text-gray-400">Elaborado por</p>
              </div>
              <div className="text-center">
                <div className="h-px bg-gray-300 mb-1" />
                <p className="text-[10px] text-gray-400">Aprovado por</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Rodapé */}
      <div className="px-3 py-2 border-t border-gray-100 bg-gray-50 flex justify-between items-center">
        <span className="text-[10px] text-gray-400">Sistema WEBBER — documento gerado eletronicamente</span>
        <span className="text-[10px] text-gray-400">{ativas.length} seção(ões)</span>
      </div>
    </div>
  )
}

// ── Componente principal ───────────────────────────────────────────────────────
export default function ArtefatoAdmin() {
  const [secoes, setSecoes]       = useState([])
  const [loading, setLoading]     = useState(true)
  const [activeTab, setActiveTab] = useState('TR')
  const [editItem, setEditItem]   = useState(null)
  const [form, setForm]           = useState({ ...BLANK })
  const [saving, setSaving]         = useState(false)
  const [msg, setMsg]               = useState(null)
  const [modalMsg, setModalMsg]     = useState(null)   // erro/sucesso dentro do modal
  const [reordering, setReordering] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    api.get('/core/secoes/', { params: { inativas: 'true', page_size: 200 } })
      .then(({ data }) => setSecoes(data.results ?? data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  const secoesTab = secoes
    .filter(s => s.tipo === activeTab)
    .sort((a, b) => a.ordem - b.ordem)

  const openAdd  = () => { setForm({ ...BLANK, tipo: activeTab, ordem: secoesTab.length + 1 }); setEditItem('new'); setModalMsg(null) }
  const openEdit = (s) => {
    // Extrai apenas os campos que o backend aceita (sem id, tipo_display, etc.)
    setForm({
      tipo:               s.tipo,
      codigo:             s.codigo,
      titulo:             s.titulo,
      descricao:          s.descricao || '',
      ordem:              s.ordem,
      ativo:              s.ativo,
      obrigatorio:        s.obrigatorio,
      aplica_modalidades:  s.aplica_modalidades  || [],
      aplica_tipo_objeto:  s.aplica_tipo_objeto  || [],
    })
    setEditItem(s.id)
    setModalMsg(null)
  }
  const closeModal = () => { setEditItem(null); setForm({ ...BLANK }); setModalMsg(null) }

  const handleSave = async () => {
    if (!form.titulo.trim() || !form.codigo.trim()) return
    setSaving(true); setModalMsg(null)
    try {
      const payload = {
        tipo:               form.tipo,
        codigo:             form.codigo,
        titulo:             form.titulo.trim(),
        descricao:          form.descricao || '',
        ordem:              Number(form.ordem) || 1,
        ativo:              Boolean(form.ativo),
        obrigatorio:        Boolean(form.obrigatorio),
        aplica_modalidades: form.aplica_modalidades || [],
        aplica_tipo_objeto: form.aplica_tipo_objeto  || [],
      }
      if (editItem === 'new') {
        await api.post('/core/secoes/', payload)
        setMsg({ type: 'success', text: 'Seção criada com sucesso.' })
      } else {
        await api.patch(`/core/secoes/${editItem}/`, payload)
        setMsg({ type: 'success', text: 'Seção atualizada com sucesso.' })
      }
      closeModal(); load()
    } catch (err) {
      const detail = err.response?.data?.detail
        || Object.entries(err.response?.data || {}).map(([k,v]) => `${k}: ${v}`).join(' | ')
        || 'Erro ao salvar. Verifique o console.'
      console.error('[ArtefatoAdmin] save error', err.response?.data)
      setModalMsg({ type: 'error', text: detail })
    } finally { setSaving(false) }
  }

  // Reordenação robusta: reindexar toda a lista após a troca
  const moverOrdem = async (secao, direcao) => {
    const idx  = secoesTab.findIndex(s => s.id === secao.id)
    const alvo = secoesTab[idx + direcao]
    if (!alvo) return

    setReordering(true)
    try {
      // Troca usando valor temporário para evitar conflito de unicidade
      const tempOrdem = Math.max(...secoesTab.map(s => s.ordem)) + 999
      await api.patch(`/core/secoes/${secao.id}/`, { ordem: tempOrdem })
      await api.patch(`/core/secoes/${alvo.id}/`,  { ordem: secao.ordem })
      await api.patch(`/core/secoes/${secao.id}/`, { ordem: alvo.ordem })
      load()
    } catch {
      load()
    } finally { setReordering(false) }
  }

  // Reativar/desativar — com feedback visual imediato (optimistic update)
  const toggleAtivo = async (secao) => {
    const novoEstado = !secao.ativo
    setSecoes(prev => prev.map(s => s.id === secao.id ? { ...s, ativo: novoEstado } : s))
    try {
      await api.patch(`/core/secoes/${secao.id}/`, { ativo: novoEstado })
    } catch {
      load() // reverte se API falhar
    }
  }

  const toggleTipoObjeto = (tipo) => {
    setForm(p => ({
      ...p,
      aplica_tipo_objeto: p.aplica_tipo_objeto.includes(tipo)
        ? p.aplica_tipo_objeto.filter(t => t !== tipo)
        : [...p.aplica_tipo_objeto, tipo],
    }))
  }

  const toggleModalidade = (mod) => {
    setForm(p => ({
      ...p,
      aplica_modalidades: p.aplica_modalidades.includes(mod)
        ? p.aplica_modalidades.filter(m => m !== mod)
        : [...p.aplica_modalidades, mod],
    }))
  }

  const meta = TIPOS.find(t => t.value === activeTab)

  return (
    <div className="p-6">
      <div className="mb-5">
        <h1 className="text-xl font-bold text-gray-800">Estrutura de Artefatos</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Configure as seções de cada documento, sua ordem e aplicabilidade por modalidade.
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm border ${msg.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
          {msg.text}
        </div>
      )}

      {/* Abas por tipo */}
      <div className="flex gap-2 mb-5 border-b border-gray-200">
        {TIPOS.map(t => (
          <button key={t.value} onClick={() => setActiveTab(t.value)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
              activeTab === t.value
                ? 'border-blue-600 text-blue-700 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t.value}
          </button>
        ))}
      </div>

      {/* Layout de dois painéis */}
      <div className="grid grid-cols-[1fr_300px] gap-5 items-start">

        {/* ── Painel esquerdo: tabela de configuração ── */}
        <div>
          <div className={`mb-3 px-4 py-2 rounded-lg text-xs border ${meta?.cor}`}>
            {meta?.label}
            <span className="ml-2 text-gray-500">— {secoesTab.filter(s => s.ativo).length} ativas / {secoesTab.length} total</span>
          </div>

          <div className="flex justify-end mb-3">
            <button onClick={openAdd}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
              + Nova seção
            </button>
          </div>

          {loading ? <LoadingSpinner /> : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-3 py-3 font-medium text-gray-500 w-16">Ordem</th>
                    <th className="text-left px-3 py-3 font-medium text-gray-500">Título / Código</th>
                    <th className="text-left px-3 py-3 font-medium text-gray-500">Modalidades</th>
                    <th className="text-center px-3 py-3 font-medium text-gray-500 w-16">Obrig.</th>
                    <th className="text-center px-3 py-3 font-medium text-gray-500 w-20">Status</th>
                    <th className="px-3 py-3 w-16"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {secoesTab.map((s, idx) => (
                    <tr key={s.id} className={`transition-opacity ${!s.ativo ? 'bg-gray-50' : 'hover:bg-blue-50/30'}`}>
                      {/* Controles de ordem */}
                      <td className="px-3 py-3">
                        <div className="flex flex-col items-center gap-0.5">
                          <button
                            onClick={() => moverOrdem(s, -1)}
                            disabled={idx === 0 || reordering || !s.ativo}
                            title="Mover para cima"
                            className="text-gray-400 hover:text-blue-600 disabled:opacity-20 text-xs leading-none transition-colors">
                            ▲
                          </button>
                          <span className={`text-xs font-mono w-6 text-center ${s.ativo ? 'text-gray-700 font-semibold' : 'text-gray-400'}`}>
                            {s.ordem}
                          </span>
                          <button
                            onClick={() => moverOrdem(s, 1)}
                            disabled={idx === secoesTab.length - 1 || reordering || !s.ativo}
                            title="Mover para baixo"
                            className="text-gray-400 hover:text-blue-600 disabled:opacity-20 text-xs leading-none transition-colors">
                            ▼
                          </button>
                        </div>
                      </td>

                      {/* Título + código */}
                      <td className="px-3 py-3">
                        <p className={`font-medium ${s.ativo ? 'text-gray-800' : 'text-gray-400 line-through'}`}>
                          {s.titulo}
                        </p>
                        <p className="text-[10px] font-mono text-gray-400 mt-0.5">{s.codigo}</p>
                      </td>

                      {/* Modalidades */}
                      <td className="px-3 py-3">
                        {s.aplica_modalidades.length === 0
                          ? <span className="text-xs text-gray-400 italic">Todas</span>
                          : <div className="flex flex-wrap gap-1">
                              {s.aplica_modalidades.map(m => (
                                <span key={m} className="bg-gray-100 text-gray-600 text-[10px] px-1.5 py-0.5 rounded-full">
                                  {MODALIDADES.find(x => x.value === m)?.label || m}
                                </span>
                              ))}
                            </div>
                        }
                      </td>

                      {/* Obrigatório */}
                      <td className="px-3 py-3 text-center">
                        {s.obrigatorio
                          ? <span className="text-[10px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-medium">Sim</span>
                          : <span className="text-xs text-gray-300">—</span>}
                      </td>

                      {/* Toggle ativo com label explícito */}
                      <td className="px-3 py-3 text-center">
                        <button
                          onClick={() => toggleAtivo(s)}
                          title={s.ativo ? 'Clique para desativar' : 'Clique para reativar'}
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold border transition-colors cursor-pointer ${
                            s.ativo
                              ? 'bg-green-100 text-green-700 border-green-300 hover:bg-green-200'
                              : 'bg-gray-100 text-gray-500 border-gray-300 hover:bg-blue-50 hover:text-blue-600 hover:border-blue-300'
                          }`}>
                          <span>{s.ativo ? '● Ativa' : '○ Inativa'}</span>
                        </button>
                      </td>

                      {/* Editar */}
                      <td className="px-3 py-3 text-right">
                        <button onClick={() => openEdit(s)}
                          className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-medium">
                          Editar
                        </button>
                      </td>
                    </tr>
                  ))}
                  {secoesTab.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-400 italic">
                        Nenhuma seção configurada. Clique em "+ Nova seção" para começar.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          <p className="text-xs text-gray-400 mt-2">
            ▲▼ reordena apenas seções ativas · ○ Inativa = oculta no documento gerado, mas conserva a configuração
          </p>
        </div>

        {/* ── Painel direito: preview ao vivo ── */}
        <div className="sticky top-4" style={{ maxHeight: 'calc(100vh - 140px)' }}>
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Preview do documento</span>
            <span className="text-[10px] text-gray-400 italic">— atualiza em tempo real</span>
          </div>
          <PreviewDocumento tipo={activeTab} secoes={secoesTab} />
        </div>
      </div>

      {/* ── Modal de edição ── */}
      {editItem !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-gray-800 mb-4">
              {editItem === 'new' ? 'Nova seção' : `Editar — ${form.titulo || 'seção'}`}
            </h3>

            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Código técnico *</label>
                  <input
                    value={form.codigo}
                    onChange={e => setForm(p => ({ ...p, codigo: e.target.value }))}
                    placeholder="ex: objeto, prazo_vigencia"
                    disabled={editItem !== 'new'}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Ordem</label>
                  <input
                    type="number" min="1"
                    value={form.ordem}
                    onChange={e => setForm(p => ({ ...p, ordem: Number(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Título da seção *</label>
                <input
                  value={form.titulo}
                  onChange={e => setForm(p => ({ ...p, titulo: e.target.value }))}
                  placeholder="Ex: Prazo de Vigência do Contrato"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Orientação de preenchimento</label>
                <textarea
                  rows={2}
                  value={form.descricao}
                  onChange={e => setForm(p => ({ ...p, descricao: e.target.value }))}
                  placeholder="Instrução exibida ao elaborador do documento..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">Aplica para modalidades (vazio = todas)</label>
                <div className="flex flex-wrap gap-2">
                  {MODALIDADES.map(m => (
                    <button key={m.value} type="button" onClick={() => toggleModalidade(m.value)}
                      className={`px-3 py-1 rounded-lg text-xs border font-medium transition-colors ${
                        form.aplica_modalidades.includes(m.value)
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                      }`}>
                      {m.label}
                    </button>
                  ))}
                </div>
                {form.aplica_modalidades.length === 0 && (
                  <p className="text-xs text-gray-400 mt-1 italic">Nenhuma = aplica a todas as modalidades</p>
                )}
              </div>

              {/* Aplica por tipo de objeto — só relevante para TR */}
              {form.tipo === 'TR' && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">Aplica para tipo de objeto (vazio = todos)</label>
                  <div className="flex flex-wrap gap-2">
                    {TIPOS_OBJETO.map(t => (
                      <button key={t.value} type="button" onClick={() => toggleTipoObjeto(t.value)}
                        className={`px-3 py-1 rounded-lg text-xs border font-medium transition-colors ${
                          (form.aplica_tipo_objeto || []).includes(t.value)
                            ? 'bg-teal-600 border-teal-600 text-white'
                            : 'bg-white border-gray-300 text-gray-600 hover:border-teal-400'
                        }`}>
                        {t.label}
                      </button>
                    ))}
                  </div>
                  {(form.aplica_tipo_objeto || []).length === 0 && (
                    <p className="text-xs text-gray-400 mt-1 italic">Nenhum = aplica a todos os tipos de objeto</p>
                  )}
                </div>
              )}

              <div className="flex items-center gap-6 pt-1">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={form.obrigatorio}
                    onChange={e => setForm(p => ({ ...p, obrigatorio: e.target.checked }))}
                    className="accent-blue-600" />
                  Preenchimento obrigatório
                </label>
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="checkbox" checked={form.ativo}
                    onChange={e => setForm(p => ({ ...p, ativo: e.target.checked }))}
                    className="accent-blue-600" />
                  Ativa
                </label>
              </div>
            </div>

            {modalMsg && (
              <div className={`mt-4 px-3 py-2 rounded-lg text-sm border ${
                modalMsg.type === 'error'
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-green-50 text-green-700 border-green-200'
              }`}>
                {modalMsg.text}
              </div>
            )}

            <div className="flex gap-2 mt-4">
              <button onClick={handleSave} disabled={saving || !form.titulo.trim() || !form.codigo.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                {saving ? 'Salvando…' : 'Salvar'}
              </button>
              <button onClick={closeModal}
                className="border border-gray-300 text-gray-600 text-sm px-5 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
