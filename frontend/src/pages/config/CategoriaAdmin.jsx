import { useEffect, useState } from 'react'
import api from '../../services/api'
import LoadingSpinner from '../../components/LoadingSpinner'
import EmptyState from '../../components/EmptyState'

const BLANK = { nome: '', codigo: '', pai: '' }

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Categorias do Catálogo',
  descricao: 'Árvore hierárquica de categorias usada para classificar itens do Catálogo — cada categoria pode ter uma categoria-pai, formando o caminho completo exibido nos itens.',
  acoes: [
    { label: 'Categoria-pai', texto: 'Opcional — define onde a categoria se encaixa na árvore. Deixe em branco para criar uma categoria raiz.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function CategoriaAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [form, setForm]       = useState({ ...BLANK })
  const [editId, setEditId]   = useState(null)
  const [errors, setErrors]   = useState({})
  const [msg, setMsg]         = useState(null)
  const [expanded, setExpanded] = useState({})

  const load = () => {
    setLoading(true)
    api.get('/core/categorias/', { params: { page_size: 500 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  // Constrói a árvore a partir da lista plana
  const buildTree = (nodes) => {
    const map = {}
    nodes.forEach(n => { map[n.id] = { ...n, _filhos: [] } })
    const raizes = []
    nodes.forEach(n => {
      if (n.pai) map[n.pai]?._filhos.push(map[n.id])
      else raizes.push(map[n.id])
    })
    return raizes
  }

  const tree = buildTree(list)
  const raizes = list.filter(n => !n.pai)

  const reset = () => { setForm({ ...BLANK }); setEditId(null); setErrors({}) }

  const startEdit = (item) => {
    setForm({ nome: item.nome, codigo: item.codigo || '', pai: item.pai ? String(item.pai) : '' })
    setEditId(item.id)
    setErrors({})
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    if (!form.nome.trim()) { setErrors({ nome: 'Campo obrigatório' }); return }
    setSaving(true); setMsg(null)
    const payload = {
      nome:   form.nome.trim(),
      codigo: form.codigo.trim(),
      pai:    form.pai ? Number(form.pai) : null,
    }
    try {
      if (editId) {
        await api.patch(`/core/categorias/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Categoria atualizada.' })
      } else {
        await api.post('/core/categorias/', payload)
        setMsg({ type: 'success', text: 'Categoria criada.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleDelete = async (item) => {
    const aviso = item.tem_filhos
      ? `"${item.nome}" tem subcategorias. Remova-as antes.`
      : `Excluir a categoria "${item.nome}"?`
    if (item.tem_filhos) { alert(aviso); return }
    if (!confirm(aviso)) return
    try {
      await api.delete(`/core/categorias/${item.id}/`)
      load()
    } catch (err) {
      alert(err.response?.data?.detail || 'Não foi possível excluir.')
    }
  }

  const toggle = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }))

  const renderNode = (node, depth = 0) => {
    const hasChildren = node._filhos?.length > 0
    const open = expanded[node.id]
    const indent = depth * 20

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 px-4 py-2.5 border-b border-gray-100 hover:bg-gray-50 text-sm ${editId === node.id ? 'bg-blue-50' : ''}`}
          style={{ paddingLeft: `${16 + indent}px` }}
        >
          {/* Ícone de toggle */}
          <button
            type="button"
            onClick={() => hasChildren && toggle(node.id)}
            className={`w-4 h-4 flex items-center justify-center shrink-0 ${hasChildren ? 'text-gray-400 hover:text-gray-600 cursor-pointer' : 'text-transparent cursor-default'}`}
          >
            {hasChildren ? (open ? '▾' : '▸') : '·'}
          </button>

          {/* Nivel badge */}
          <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded ${
            depth === 0 ? 'bg-blue-100 text-blue-700' :
            depth === 1 ? 'bg-purple-100 text-purple-700' :
                          'bg-gray-100 text-gray-500'
          }`}>
            N{depth}
          </span>

          <span className="flex-1 font-medium text-gray-800">{node.nome}</span>
          {node.codigo && <span className="font-mono text-xs text-gray-400">{node.codigo}</span>}
          <span className="text-xs text-gray-400 shrink-0">{node.tem_filhos ? `${node._filhos?.length} sub` : 'folha'}</span>

          <div className="flex gap-2 shrink-0">
            <button onClick={() => startEdit(node)} className="text-xs text-blue-600 hover:underline">Editar</button>
            <button onClick={() => handleDelete(node)} className="text-xs text-red-500 hover:underline">Excluir</button>
            <button
              onClick={() => { setForm({ nome: '', codigo: '', pai: String(node.id) }); setEditId(null); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
              className="text-xs text-green-600 hover:underline"
            >
              + Sub
            </button>
          </div>
        </div>
        {hasChildren && open && node._filhos.map(child => renderNode(child, depth + 1))}
      </div>
    )
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Categorias de Itens</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Árvore hierárquica para classificação dos itens do catálogo.
          Exemplo: <span className="font-mono text-gray-600">FROTA › VEÍCULOS LEVES › PICKUP</span>
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm border ${msg.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
          {msg.text}
        </div>
      )}

      {/* Formulário */}
      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">
          {editId ? 'Editar categoria' : 'Nova categoria'}
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Nome *</label>
            <input
              value={form.nome}
              onChange={e => { setForm(p => ({ ...p, nome: e.target.value })); setErrors(p => ({ ...p, nome: undefined })) }}
              placeholder="Ex: VEÍCULOS LEVES"
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.nome ? 'border-red-400' : 'border-gray-300'}`}
            />
            {errors.nome && <p className="text-xs text-red-600 mt-1">{errors.nome}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código (opcional)</label>
            <input
              value={form.codigo}
              onChange={e => setForm(p => ({ ...p, codigo: e.target.value }))}
              placeholder="Ex: VL"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Categoria pai (deixe vazio para raiz)</label>
          <select
            value={form.pai}
            onChange={e => setForm(p => ({ ...p, pai: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">— Raiz (sem pai) —</option>
            {list
              .filter(n => n.id !== editId)
              .sort((a, b) => a.caminho_completo.localeCompare(b.caminho_completo))
              .map(n => (
                <option key={n.id} value={n.id}>{n.caminho_completo}</option>
              ))
            }
          </select>
          {form.pai && (
            <p className="text-xs text-blue-600 mt-1">
              Ficará em: <strong>{list.find(n => String(n.id) === form.pai)?.caminho_completo} › {form.nome || '...'}</strong>
            </p>
          )}
        </div>

        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar alterações' : 'Criar categoria'}
          </button>
          {(editId || form.pai) && (
            <button type="button" onClick={reset}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
          )}
        </div>
      </form>

      {/* Árvore */}
      {loading ? <LoadingSpinner /> : list.length === 0 ? (
        <EmptyState
          icon="folder"
          title="Nenhuma categoria cadastrada"
          description="Crie categorias para organizar os itens do catálogo de forma hierárquica."
        />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-4 py-2.5 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500">
              {list.length} categorias · {raizes.length} raízes
            </span>
            <button
              type="button"
              onClick={() => {
                const allIds = list.filter(n => n.tem_filhos).map(n => n.id)
                const allOpen = allIds.every(id => expanded[id])
                if (allOpen) setExpanded({})
                else setExpanded(Object.fromEntries(allIds.map(id => [id, true])))
              }}
              className="text-xs text-blue-600 hover:underline"
            >
              Expandir/Recolher tudo
            </button>
          </div>
          {tree.map(node => renderNode(node, 0))}
        </div>
      )}
    </div>
  )
}
