import { useEffect, useState } from 'react'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'
import FormErrors from '../../components/FormErrors'

const BLANK = { codigo_simpas: '', nome: '', descricao: '', unidade_medida: '', ativo: true }

export default function CatalogoAdmin() {
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving]   = useState(false)
  const [form, setForm]       = useState({ ...BLANK })
  const [editId, setEditId]   = useState(null)
  const [errors, setErrors]   = useState({})
  const [msg, setMsg]         = useState(null)
  const [busca, setBusca]     = useState('')
  const [familiaFiltro, setFamiliaFiltro] = useState('')

  const load = () => {
    setLoading(true)
    api.get('/core/catalogo/', { params: { inativas: true, page_size: 500 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const familias = [...new Set(list.map(i => i.familia).filter(Boolean))].sort()

  const listFiltrada = list.filter(i => {
    const matchBusca = !busca || i.nome.toLowerCase().includes(busca.toLowerCase()) ||
      i.codigo_simpas.includes(busca) || i.codigo_interno.includes(busca)
    const matchFamilia = !familiaFiltro || i.familia === familiaFiltro
    return matchBusca && matchFamilia
  })

  const reset = () => { setForm({ ...BLANK }); setEditId(null); setErrors({}) }
  const startEdit = (item) => {
    setForm({ codigo_simpas: item.codigo_simpas, nome: item.nome, descricao: item.descricao, unidade_medida: item.unidade_medida, ativo: item.ativo })
    setEditId(item.id)
    setErrors({})
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const validate = () => {
    const e = {}
    if (!form.nome.trim())           e.nome = 'Campo obrigatório'
    if (!form.unidade_medida.trim()) e.unidade_medida = 'Campo obrigatório'
    return e
  }

  const handleSubmit = async (ev) => {
    ev.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true); setMsg(null)
    try {
      const payload = { ...form }
      if (editId) {
        await api.patch(`/core/catalogo/${editId}/`, payload)
        setMsg({ type: 'success', text: 'Item atualizado.' })
      } else {
        await api.post('/core/catalogo/', payload)
        setMsg({ type: 'success', text: 'Item criado.' })
      }
      reset(); load()
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally { setSaving(false) }
  }

  const handleInativar = async (item) => {
    if (!confirm(`Inativar "${item.nome}"?`)) return
    await api.delete(`/core/catalogo/${item.id}/`)
    load()
  }

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Catálogo de Itens</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Itens com código interno WEBBER e código SIMPAS. A família é extraída automaticamente dos dois primeiros segmentos do SIMPAS.
        </p>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-2 rounded-lg text-sm border ${msg.type === 'success' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
          {msg.text}
        </div>
      )}

      {/* Formulário */}
      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-700">{editId ? 'Editar item' : 'Novo item'}</h2>
        <FormErrors errors={errors} />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Código SIMPAS</label>
            <input value={form.codigo_simpas}
              onChange={e => setForm(p => ({ ...p, codigo_simpas: e.target.value }))}
              placeholder="Ex: 42.40.20.00016900-5"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono" />
            {form.codigo_simpas && (
              <p className="text-xs text-blue-600 mt-1">
                Família: <strong>{form.codigo_simpas.split('.').slice(0, 2).join('.') || '—'}</strong>
              </p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Unidade de medida *</label>
            <input value={form.unidade_medida}
              onChange={e => { setForm(p => ({ ...p, unidade_medida: e.target.value })); setErrors(p => ({ ...p, unidade_medida: undefined })) }}
              placeholder="UN, M², HR, TURMA..."
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.unidade_medida ? 'border-red-400' : 'border-gray-300'}`} />
            {errors.unidade_medida && <p className="text-xs text-red-600 mt-1">{errors.unidade_medida}</p>}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Descrição do item *</label>
          <input value={form.nome}
            onChange={e => { setForm(p => ({ ...p, nome: e.target.value })); setErrors(p => ({ ...p, nome: undefined })) }}
            placeholder="Ex: Notebook Dell Latitude 5540 i5/16GB/512GB"
            className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${errors.nome ? 'border-red-400' : 'border-gray-300'}`} />
          {errors.nome && <p className="text-xs text-red-600 mt-1">{errors.nome}</p>}
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Especificação complementar (opcional)</label>
          <textarea rows={2} value={form.descricao}
            onChange={e => setForm(p => ({ ...p, descricao: e.target.value }))}
            placeholder="Detalhes técnicos adicionais..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        <div className="flex gap-2">
          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {saving ? 'Salvando...' : editId ? 'Salvar' : 'Cadastrar item'}
          </button>
          {editId && (
            <button type="button" onClick={reset}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
          )}
        </div>
      </form>

      {/* Filtros */}
      <div className="flex gap-3 mb-4">
        <input value={busca} onChange={e => setBusca(e.target.value)}
          placeholder="Buscar por nome, código SIMPAS ou código interno..."
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <select value={familiaFiltro} onChange={e => setFamiliaFiltro(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todas as famílias</option>
          {familias.map(f => <option key={f} value={f}>{f}</option>)}
        </select>
      </div>

      {/* Tabela */}
      {loading ? <LoadingSpinner /> : listFiltrada.length === 0 ? (
        <EmptyState icon="clipboard" title="Nenhum item encontrado"
          description="Cadastre os itens do catálogo com código SIMPAS." />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Código</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">SIMPAS / Família</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Descrição</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Unid.</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {listFiltrada.map(item => (
                <tr key={item.id} className={`hover:bg-gray-50 ${!item.ativo ? 'opacity-40' : ''}`}>
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">{item.codigo_interno}</td>
                  <td className="px-4 py-3">
                    {item.codigo_simpas && (
                      <p className="font-mono text-xs text-gray-600">{item.codigo_simpas}</p>
                    )}
                    {item.familia && (
                      <span className="inline-block mt-0.5 bg-blue-50 text-blue-700 text-[10px] font-semibold px-1.5 py-0.5 rounded">
                        {item.familia}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-800 max-w-xs">
                    <p className="truncate">{item.nome}</p>
                    {item.descricao && (
                      <p className="text-xs text-gray-400 truncate mt-0.5">{item.descricao}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs font-mono">{item.unidade_medida}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${item.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {item.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {item.ativo && <button onClick={() => startEdit(item)} className="text-xs text-blue-600 hover:underline">Editar</button>}
                    {item.ativo && <button onClick={() => handleInativar(item)} className="text-xs text-red-500 hover:underline">Inativar</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400">
            {listFiltrada.length} item{listFiltrada.length !== 1 ? 's' : ''} · {familias.length} famíli{familias.length !== 1 ? 'as' : 'a'}
          </div>
        </div>
      )}
    </div>
  )
}
