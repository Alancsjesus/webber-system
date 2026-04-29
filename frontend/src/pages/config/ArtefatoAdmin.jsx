import { useEffect, useState } from 'react'
import api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'

const TIPOS = [
  { value: 'DFD', label: 'DFD — Documento de Formalização da Demanda', cor: 'bg-blue-100 text-blue-700 border-blue-200' },
  { value: 'ETP', label: 'ETP — Estudo Técnico Preliminar',             cor: 'bg-purple-100 text-purple-700 border-purple-200' },
  { value: 'TR',  label: 'TR — Minuta do Termo de Referência',          cor: 'bg-teal-100 text-teal-700 border-teal-200' },
]

const MODALIDADES = [
  { value: 'licitacao',          label: 'Licitação' },
  { value: 'dispensa_valor',     label: 'Dispensa por Valor' },
  { value: 'dispensa_emergencia',label: 'Dispensa por Emergência' },
  { value: 'inexigibilidade',    label: 'Inexigibilidade' },
  { value: 'arp_saque',          label: 'Saque de ARP' },
]

const BLANK = { tipo: 'TR', codigo: '', titulo: '', descricao: '', ordem: 0, ativo: true, obrigatorio: false, aplica_modalidades: [] }

export default function ArtefatoAdmin() {
  const [secoes, setSecoes]       = useState([])
  const [loading, setLoading]     = useState(true)
  const [activeTab, setActiveTab] = useState('TR')
  const [editItem, setEditItem]   = useState(null)   // null = fechado
  const [form, setForm]           = useState({ ...BLANK })
  const [saving, setSaving]       = useState(false)
  const [msg, setMsg]             = useState(null)

  const load = () => {
    setLoading(true)
    api.get('/core/secoes/', { params: { inativas: true, page_size: 200 } })
      .then(({ data }) => setSecoes(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const secoesTab = secoes
    .filter(s => s.tipo === activeTab)
    .sort((a, b) => a.ordem - b.ordem)

  const openAdd = () => {
    setForm({ ...BLANK, tipo: activeTab, ordem: secoesTab.length + 1 })
    setEditItem('new')
  }

  const openEdit = (s) => {
    setForm({ ...s })
    setEditItem(s.id)
  }

  const closeModal = () => { setEditItem(null); setForm({ ...BLANK }) }

  const handleSave = async () => {
    if (!form.titulo.trim() || !form.codigo.trim()) return
    setSaving(true); setMsg(null)
    try {
      if (editItem === 'new') {
        await api.post('/core/secoes/', form)
        setMsg({ type: 'success', text: 'Seção criada.' })
      } else {
        await api.patch(`/core/secoes/${editItem}/`, form)
        setMsg({ type: 'success', text: 'Seção atualizada.' })
      }
      closeModal(); load()
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.detail || 'Erro ao salvar.' })
    } finally { setSaving(false) }
  }

  const moverOrdem = async (secao, direcao) => {
    const idx = secoesTab.findIndex(s => s.id === secao.id)
    const alvo = secoesTab[idx + direcao]
    if (!alvo) return
    await api.patch(`/core/secoes/${secao.id}/`, { ordem: alvo.ordem })
    await api.patch(`/core/secoes/${alvo.id}/`,  { ordem: secao.ordem })
    load()
  }

  const toggleAtivo = async (secao) => {
    await api.patch(`/core/secoes/${secao.id}/`, { ativo: !secao.ativo })
    load()
  }

  const toggleModalidade = (mod) => {
    setForm(p => ({
      ...p,
      aplica_modalidades: p.aplica_modalidades.includes(mod)
        ? p.aplica_modalidades.filter(m => m !== mod)
        : [...p.aplica_modalidades, mod],
    }))
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Estrutura de Artefatos</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Configure as seções de cada documento (DFD, ETP, TR), sua ordem de apresentação e aplicabilidade por modalidade de aquisição.
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
          <button key={t.value}
            onClick={() => setActiveTab(t.value)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors ${
              activeTab === t.value
                ? 'border-blue-600 text-blue-700 bg-blue-50'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t.value}
          </button>
        ))}
      </div>

      {/* Info da aba ativa */}
      <div className={`mb-4 px-4 py-2 rounded-lg text-xs border ${TIPOS.find(t => t.value === activeTab)?.cor}`}>
        {TIPOS.find(t => t.value === activeTab)?.label}
        <span className="ml-2 text-gray-500">— {secoesTab.length} seções configuradas</span>
      </div>

      {/* Botão nova seção */}
      <div className="flex justify-end mb-3">
        <button onClick={openAdd}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Nova seção
        </button>
      </div>

      {/* Tabela */}
      {loading ? <LoadingSpinner /> : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500 w-12">Ordem</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Título</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Modalidades</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Obrig.</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Ativo</th>
                <th className="px-4 py-3 w-24"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {secoesTab.map((s, idx) => (
                <tr key={s.id} className={`hover:bg-gray-50 ${!s.ativo ? 'opacity-40' : ''}`}>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-0.5">
                      <button onClick={() => moverOrdem(s, -1)} disabled={idx === 0}
                        className="text-gray-400 hover:text-gray-700 disabled:opacity-20 text-xs leading-none">▲</button>
                      <span className="text-xs font-mono text-gray-500 text-center">{s.ordem}</span>
                      <button onClick={() => moverOrdem(s, 1)} disabled={idx === secoesTab.length - 1}
                        className="text-gray-400 hover:text-gray-700 disabled:opacity-20 text-xs leading-none">▼</button>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-800">{s.titulo}</p>
                    {s.descricao && <p className="text-xs text-gray-400 mt-0.5 truncate max-w-xs">{s.descricao}</p>}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">{s.codigo}</td>
                  <td className="px-4 py-3">
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
                  <td className="px-4 py-3 text-center">
                    {s.obrigatorio
                      ? <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded">Sim</span>
                      : <span className="text-xs text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button onClick={() => toggleAtivo(s)}
                      className={`w-9 h-5 rounded-full transition-colors ${s.ativo ? 'bg-green-500' : 'bg-gray-300'}`}>
                      <span className={`block w-4 h-4 rounded-full bg-white shadow-sm transition-transform mx-auto ${s.ativo ? 'translate-x-2' : '-translate-x-1'}`} />
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => openEdit(s)} className="text-xs text-blue-600 hover:underline">Editar</button>
                  </td>
                </tr>
              ))}
              {secoesTab.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-400 italic">Nenhuma seção configurada para este tipo.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de edição */}
      {editItem !== null && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-base font-semibold text-gray-800 mb-4">
              {editItem === 'new' ? 'Nova seção' : 'Editar seção'}
            </h3>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Código técnico *</label>
                  <input value={form.codigo} onChange={e => setForm(p => ({ ...p, codigo: e.target.value }))}
                    placeholder="ex: objeto, prazo_vigencia"
                    disabled={editItem !== 'new'}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 font-mono" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Ordem</label>
                  <input type="number" min="1" value={form.ordem} onChange={e => setForm(p => ({ ...p, ordem: Number(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Título da seção *</label>
                <input value={form.titulo} onChange={e => setForm(p => ({ ...p, titulo: e.target.value }))}
                  placeholder="Ex: Prazo de Vigência do Contrato"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Orientação de preenchimento</label>
                <textarea rows={2} value={form.descricao} onChange={e => setForm(p => ({ ...p, descricao: e.target.value }))}
                  placeholder="Instrução exibida ao elaborador do documento..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-2">Aplica para modalidades (vazio = todas)</label>
                <div className="flex flex-wrap gap-2">
                  {MODALIDADES.map(m => (
                    <button key={m.value} type="button"
                      onClick={() => toggleModalidade(m.value)}
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
                  <p className="text-xs text-gray-400 mt-1 italic">Nenhuma selecionada = aplica a todas as modalidades</p>
                )}
              </div>

              <div className="flex items-center gap-6">
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
                  Ativo
                </label>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button onClick={handleSave} disabled={saving || !form.titulo.trim() || !form.codigo.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                {saving ? 'Salvando...' : 'Salvar'}
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
