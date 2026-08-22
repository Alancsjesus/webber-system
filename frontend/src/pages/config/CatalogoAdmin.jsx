import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import EmptyState from '../../components/EmptyState'
import LoadingSpinner from '../../components/LoadingSpinner'
import CategoriaCascade from '../../components/CategoriaCascade'
import CampoMoeda from '../../components/CampoMoeda'

const BLANK = {
  codigo_simpas: '', nome: '', descricao: '', unidade_medida: '', ativo: true, categoria: '',
  item_sustentavel: false, item_luxo: false, classificacao_tipo: '',
  valor_referencia: '', data_referencia: '', num_licitacao_ref: '',
}
const PAGE_SIZE = 50

const cls = {
  input:  'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500',
  inputErr: 'w-full border border-red-400 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-400',
  label:  'block text-xs font-medium text-gray-600 mb-1',
  select: 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white',
}

const CLASSIF_BADGE = {
  consumo:    'bg-orange-100 text-orange-700',
  permanente: 'bg-purple-100 text-purple-700',
  servico:    'bg-sky-100 text-sky-700',
}
const CLASSIF_LABEL = { consumo: 'Consumo', permanente: 'Permanente', servico: 'Serviço' }

function Field({ label, error, children }) {
  return (
    <div>
      <label className={cls.label}>{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

// ── Formulário de criação/modal (reutilizado) ─────────────────────────────────
function ItemForm({ form, setForm, errors, categorias, compact = false }) {
  const set = (k, v) => setForm(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Código SIMPAS">
          <input value={form.codigo_simpas} onChange={e => set('codigo_simpas', e.target.value)}
            placeholder="Ex: 70.15.00.00178869-8"
            className={`${cls.input} font-mono`} />
          {form.codigo_simpas && (
            <p className="text-[10px] text-blue-500 mt-1">
              Família: <strong>{form.codigo_simpas.split('.').slice(0, 2).join('.') || '—'}</strong>
            </p>
          )}
        </Field>
        <Field label="Unidade de medida *" error={errors?.unidade_medida}>
          <input value={form.unidade_medida} onChange={e => set('unidade_medida', e.target.value)}
            placeholder="UN, M², HR, KG..."
            className={errors?.unidade_medida ? cls.inputErr : cls.input} />
        </Field>
      </div>

      <Field label="Descrição do item *" error={errors?.nome}>
        <input value={form.nome} onChange={e => set('nome', e.target.value)}
          placeholder="Ex: Notebook Dell Latitude 5540"
          className={errors?.nome ? cls.inputErr : cls.input} />
      </Field>

      <Field label="Especificação técnica (opcional)">
        <textarea rows={compact ? 2 : 3} value={form.descricao} onChange={e => set('descricao', e.target.value)}
          placeholder="Detalhes complementares da especificação..."
          className={cls.input} />
      </Field>

      <Field label="Categoria (opcional)" error={errors?.categoria}>
        <CategoriaCascade
          categorias={categorias}
          value={form.categoria ? Number(form.categoria) : null}
          onChange={id => set('categoria', id ? String(id) : '')}
        />
      </Field>

      {/* Atributos SIMPAS */}
      <div className="rounded-xl border border-gray-200 overflow-hidden">
        <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Atributos SIMPAS</span>
        </div>
        <div className="p-4 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Classificação">
              <select value={form.classificacao_tipo} onChange={e => set('classificacao_tipo', e.target.value)}
                className={cls.select}>
                <option value="">— Não classificado —</option>
                <option value="consumo">Material de Consumo</option>
                <option value="permanente">Material Permanente</option>
                <option value="servico">Serviço</option>
              </select>
            </Field>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Valor referência (R$)">
                <CampoMoeda value={form.valor_referencia}
                  onChange={v => set('valor_referencia', v)}
                  className={cls.input} />
              </Field>
              <Field label="Data da referência">
                <input type="date" value={form.data_referencia}
                  onChange={e => set('data_referencia', e.target.value)}
                  className={cls.input} />
              </Field>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Nº licitação de referência">
              <input type="text" value={form.num_licitacao_ref}
                onChange={e => set('num_licitacao_ref', e.target.value)}
                placeholder="Ex: PE-SSP-001/2025" className={cls.input} />
            </Field>
            <div className="flex items-end gap-6 pb-2">
              <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700 select-none">
                <input type="checkbox" checked={!!form.item_sustentavel}
                  onChange={e => set('item_sustentavel', e.target.checked)}
                  className="w-4 h-4 rounded accent-green-600" />
                <span>Sustentável</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700 select-none">
                <input type="checkbox" checked={!!form.item_luxo}
                  onChange={e => set('item_luxo', e.target.checked)}
                  className="w-4 h-4 rounded accent-red-500" />
                <span>Item de luxo</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Componente principal ──────────────────────────────────────────────────────
export default function CatalogoAdmin() {
  const navigate    = useNavigate()
  const debounceRef = useRef(null)

  const [list, setList]             = useState([])
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage]             = useState(1)
  const [categorias, setCategorias] = useState([])
  const [loading, setLoading]       = useState(true)
  const [showForm, setShowForm]     = useState(false)

  // filtros
  const [busca, setBusca]                     = useState('')
  const [familiaFiltro, setFamiliaFiltro]     = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState('')
  const [filtroClassif, setFiltroClassif]     = useState('')
  const [filtroSust, setFiltroSust]           = useState('')
  const [filtroLuxo, setFiltroLuxo]           = useState('')

  // form de criação
  const [form, setForm]   = useState({ ...BLANK })
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [msgOk, setMsgOk]   = useState(false)

  // modal de edição
  const [modal, setModal]           = useState(null)
  const [modalForm, setModalForm]   = useState({})
  const [modalErrors, setModalErrors] = useState({})
  const [modalSaving, setModalSaving] = useState(false)

  const totalPages = Math.ceil(totalCount / PAGE_SIZE)

  // ── carregamento ────────────────────────────────────────────────────────────
  const buildParams = (p) => {
    const params = { inativas: 'true', page_size: PAGE_SIZE, page: p }
    if (busca)                params.search             = busca
    if (familiaFiltro)        params.familia            = familiaFiltro
    if (categoriaFiltro)      params.categoria          = categoriaFiltro
    if (filtroClassif)        params.classificacao_tipo = filtroClassif
    if (filtroSust === 'sim') params.item_sustentavel   = 'true'
    if (filtroLuxo === 'sim') params.item_luxo          = 'true'
    return params
  }

  const load = (p = page) => {
    setLoading(true)
    api.get('/core/catalogo/', { params: buildParams(p) })
      .then(({ data }) => {
        setList(data.results ?? data)
        setTotalCount(data.count ?? (data.results ?? data).length)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/core/categorias/', { params: { page_size: 500 } })
      .then(({ data }) => setCategorias(data.results ?? data))
  }, [])

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => load(page), busca ? 350 : 0)
    return () => clearTimeout(debounceRef.current)
  }, [busca, familiaFiltro, categoriaFiltro, filtroClassif, filtroSust, filtroLuxo, page])

  const setFilter = (setter) => (v) => { setter(v); setPage(1) }

  // ── criação ─────────────────────────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.nome.trim())           errs.nome = 'Obrigatório'
    if (!form.unidade_medida.trim()) errs.unidade_medida = 'Obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      await api.post('/core/catalogo/', {
        ...form,
        categoria:        form.categoria ? Number(form.categoria) : null,
        valor_referencia: form.valor_referencia !== '' ? Number(form.valor_referencia) : null,
        data_referencia:  form.data_referencia || null,
      })
      setForm({ ...BLANK }); setErrors({}); setMsgOk(true)
      setTimeout(() => setMsgOk(false), 3000)
      setPage(1)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : v])))
    } finally { setSaving(false) }
  }

  // ── modal edição ─────────────────────────────────────────────────────────────
  const openModal = (item) => {
    setModal(item)
    setModalForm({
      codigo_simpas:      item.codigo_simpas || '',
      nome:               item.nome,
      descricao:          item.descricao || '',
      unidade_medida:     item.unidade_medida,
      ativo:              item.ativo,
      categoria:          item.categoria ? String(item.categoria) : '',
      item_sustentavel:   item.item_sustentavel ?? false,
      item_luxo:          item.item_luxo ?? false,
      classificacao_tipo: item.classificacao_tipo || '',
      valor_referencia:   item.valor_referencia ?? '',
      data_referencia:    item.data_referencia || '',
      num_licitacao_ref:  item.num_licitacao_ref || '',
    })
    setModalErrors({})
  }
  const closeModal = () => setModal(null)

  const handleModalSave = async () => {
    const errs = {}
    if (!modalForm.nome?.trim())           errs.nome = 'Obrigatório'
    if (!modalForm.unidade_medida?.trim()) errs.unidade_medida = 'Obrigatório'
    if (Object.keys(errs).length) { setModalErrors(errs); return }
    setModalSaving(true)
    try {
      await api.patch(`/core/catalogo/${modal.id}/`, {
        ...modalForm,
        categoria:        modalForm.categoria ? Number(modalForm.categoria) : null,
        valor_referencia: modalForm.valor_referencia !== '' ? Number(modalForm.valor_referencia) : null,
        data_referencia:  modalForm.data_referencia || null,
      })
      closeModal(); setPage(p => p)
    } catch (err) {
      const d = err.response?.data || {}
      setModalErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : v])))
    } finally { setModalSaving(false) }
  }

  const handleToggleAtivo = async (item) => {
    if (!confirm(`${item.ativo ? 'Inativar' : 'Reativar'} "${item.nome}"?`)) return
    if (item.ativo) await api.delete(`/core/catalogo/${item.id}/`)
    else            await api.patch(`/core/catalogo/${item.id}/`, { ativo: true })
    setPage(p => p)
  }

  // ── render ───────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 max-w-6xl space-y-4">

      {/* Cabeçalho */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Catálogo de Itens</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {totalCount > 0 ? `${totalCount.toLocaleString('pt-BR')} itens cadastrados` : 'Gerencie os itens do catálogo SIMPAS/WEBBER'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate('/config/catalogo/importar')}
            className="flex items-center gap-1.5 border border-blue-300 text-blue-600 hover:bg-blue-50 text-sm font-medium px-3 py-2 rounded-lg">
            ↑ Importar CSV
          </button>
          <button onClick={() => setShowForm(v => !v)}
            className={`flex items-center gap-1.5 text-sm font-medium px-3 py-2 rounded-lg transition-colors ${
              showForm ? 'bg-gray-200 text-gray-700' : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}>
            {showForm ? '× Cancelar' : '+ Novo item'}
          </button>
        </div>
      </div>

      {/* Formulário colapsável de criação */}
      {showForm && (
        <div className="bg-white border border-blue-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Novo item</h2>
          {msgOk && (
            <div className="mb-3 px-3 py-2 bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg">
              Item cadastrado com sucesso.
            </div>
          )}
          <form onSubmit={handleCreate}>
            <ItemForm form={form} setForm={setForm} errors={errors} categorias={categorias} compact />
            <div className="flex gap-2 mt-4">
              <button type="submit" disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg">
                {saving ? 'Salvando...' : 'Cadastrar item'}
              </button>
              <button type="button" onClick={() => { setForm({ ...BLANK }); setErrors({}) }}
                className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Limpar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Barra de filtros */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
        {/* Linha 1: busca + família */}
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
            <input value={busca} onChange={e => { setBusca(e.target.value); setPage(1) }}
              placeholder="Buscar por descrição, código SIMPAS ou código interno..."
              className="w-full border border-gray-300 rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <input value={familiaFiltro} onChange={e => setFilter(setFamiliaFiltro)(e.target.value)}
            placeholder="Família (ex: 70.15)"
            className="w-40 border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        {/* Linha 2: filtros de atributos */}
        <div className="flex gap-3 flex-wrap">
          <select value={categoriaFiltro} onChange={e => setFilter(setCategoriaFiltro)(e.target.value)}
            className="flex-1 min-w-48 border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todas as categorias</option>
            {[...categorias].sort((a, b) => a.caminho_completo.localeCompare(b.caminho_completo))
              .map(c => <option key={c.id} value={c.id}>{c.caminho_completo}</option>)}
          </select>
          <select value={filtroClassif} onChange={e => setFilter(setFiltroClassif)(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Toda classificação</option>
            <option value="consumo">Mat. Consumo</option>
            <option value="permanente">Mat. Permanente</option>
            <option value="servico">Serviço</option>
          </select>
          <select value={filtroSust} onChange={e => setFilter(setFiltroSust)(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Sustentável: todos</option>
            <option value="sim">Apenas sustentáveis</option>
            <option value="nao">Não sustentáveis</option>
          </select>
          <select value={filtroLuxo} onChange={e => setFilter(setFiltroLuxo)(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Luxo: todos</option>
            <option value="sim">Apenas itens de luxo</option>
          </select>
          {(busca || familiaFiltro || categoriaFiltro || filtroClassif || filtroSust || filtroLuxo) && (
            <button onClick={() => {
              setBusca(''); setFamiliaFiltro(''); setCategoriaFiltro('')
              setFiltroClassif(''); setFiltroSust(''); setFiltroLuxo(''); setPage(1)
            }} className="text-xs text-gray-400 hover:text-red-500 px-2 py-2 rounded-lg hover:bg-red-50 border border-transparent hover:border-red-200">
              ✕ Limpar filtros
            </button>
          )}
        </div>
      </div>

      {/* Tabela */}
      {loading ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12"><LoadingSpinner /></div>
      ) : list.length === 0 ? (
        <EmptyState icon="clipboard" title="Nenhum item encontrado"
          description={busca || familiaFiltro || filtroClassif ? 'Tente ajustar os filtros.' : 'Cadastre itens manualmente ou importe um CSV do SIMPAS.'} />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
          {/* 5 colunas: Código | Descrição + meta | Unid. | Atributos | Ações */}
          <table className="w-full text-sm table-fixed min-w-[640px]">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                <th className="text-left px-4 py-3 w-28">Código</th>
                <th className="text-left px-4 py-3">Descrição</th>
                <th className="text-left px-4 py-3 w-16">Unid.</th>
                <th className="text-left px-4 py-3 w-44">Atributos</th>
                <th className="text-right px-4 py-3 w-32">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {list.map(item => (
                <tr key={item.id} className={`hover:bg-slate-50 transition-colors ${!item.ativo ? 'opacity-50' : ''}`}>

                  {/* Código + status */}
                  <td className="px-4 py-3">
                    <p className="font-mono text-xs font-bold text-blue-700">{item.codigo_interno}</p>
                    {item.codigo_simpas && (
                      <p className="font-mono text-[10px] text-gray-400 mt-0.5 truncate" title={item.codigo_simpas}>
                        {item.codigo_simpas}
                      </p>
                    )}
                    <span className={`mt-1 inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium ${item.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {item.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>

                  {/* Descrição + categoria + família */}
                  <td className="px-4 py-3 min-w-0">
                    <p className="font-medium text-gray-900 truncate" title={item.nome}>{item.nome}</p>
                    <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                      {item.familia && (
                        <span className="bg-blue-50 text-blue-600 text-[10px] font-semibold px-1.5 py-0.5 rounded font-mono">
                          {item.familia}
                        </span>
                      )}
                      {item.categoria_path && (
                        <span className="text-[10px] text-purple-600 truncate max-w-xs" title={item.categoria_path}>
                          {item.categoria_path}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Unidade */}
                  <td className="px-4 py-3">
                    <span className="font-mono text-xs text-gray-600">{item.unidade_medida}</span>
                  </td>

                  {/* Atributos */}
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      {item.classificacao_tipo && (
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded w-fit ${CLASSIF_BADGE[item.classificacao_tipo] || 'bg-gray-100 text-gray-500'}`}>
                          {CLASSIF_LABEL[item.classificacao_tipo]}
                        </span>
                      )}
                      <div className="flex gap-1 flex-wrap">
                        {item.item_sustentavel && (
                          <span className="bg-green-100 text-green-700 text-[10px] font-medium px-1.5 py-0.5 rounded">Sust.</span>
                        )}
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${item.item_luxo ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-400'}`}>
                          Luxo: {item.item_luxo ? 'Sim' : 'Não'}
                        </span>
                      </div>
                      {item.valor_referencia && (
                        <p className="text-[10px] text-gray-500 font-medium mt-0.5">
                          {Number(item.valor_referencia).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                          {item.data_referencia && (
                            <span className="text-gray-400 ml-1">
                              ({new Date(item.data_referencia + 'T00:00:00').toLocaleDateString('pt-BR')})
                            </span>
                          )}
                        </p>
                      )}
                    </div>
                  </td>

                  {/* Ações */}
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <button onClick={() => openModal(item)}
                        className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline whitespace-nowrap">
                        Editar
                      </button>
                      <button onClick={() => handleToggleAtivo(item)}
                        className={`text-xs whitespace-nowrap hover:underline ${item.ativo ? 'text-amber-500' : 'text-green-600'}`}>
                        {item.ativo ? 'Inativar' : 'Reativar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>

          {/* Paginação */}
          <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
            <span className="text-xs text-gray-500">
              {totalCount.toLocaleString('pt-BR')} item{totalCount !== 1 ? 's' : ''}
              {' · '}página <strong>{page}</strong> de <strong>{totalPages || 1}</strong>
            </span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(1)} disabled={page === 1}
                className="px-2 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed">«</button>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed">‹ Ant.</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const start = Math.max(1, Math.min(page - 2, totalPages - 4))
                const p = start + i
                if (p < 1 || p > totalPages) return null
                return (
                  <button key={p} onClick={() => setPage(p)}
                    className={`px-3 py-1 text-xs border rounded-lg ${p === page
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-200 hover:bg-white'}`}>
                    {p}
                  </button>
                )
              })}
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                className="px-3 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed">Próx. ›</button>
              <button onClick={() => setPage(totalPages)} disabled={page >= totalPages}
                className="px-2 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30 disabled:cursor-not-allowed">»</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de edição */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">

            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div>
                  <h2 className="text-base font-bold text-gray-800">Editar item</h2>
                  <p className="text-xs text-gray-400 font-mono">{modal.codigo_interno}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${modal.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                  {modal.ativo ? 'Ativo' : 'Inativo'}
                </span>
              </div>
              <button onClick={closeModal}
                className="w-8 h-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 text-lg">×</button>
            </div>

            {/* Body */}
            <div className="overflow-y-auto flex-1 px-6 py-5">
              {Object.keys(modalErrors).length > 0 && (
                <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
                  {Object.values(modalErrors).join(' · ')}
                </div>
              )}
              <ItemForm form={modalForm} setForm={setModalForm} errors={modalErrors} categorias={categorias} compact />
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
              <button onClick={() => { closeModal(); handleToggleAtivo(modal) }}
                className={`text-xs px-3 py-2 rounded-lg border font-medium ${modal.ativo
                  ? 'border-amber-200 text-amber-600 hover:bg-amber-50'
                  : 'border-green-200 text-green-600 hover:bg-green-50'}`}>
                {modal.ativo ? '⊘ Inativar item' : '↺ Reativar item'}
              </button>
              <div className="flex gap-2">
                <button onClick={closeModal}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-white">
                  Cancelar
                </button>
                <button onClick={handleModalSave} disabled={modalSaving}
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
                  {modalSaving ? 'Salvando...' : 'Salvar alterações'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
