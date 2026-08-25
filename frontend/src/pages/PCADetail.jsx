import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { downloadFile } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { formatarMoeda } from '../utils/currencyMask'

const CATEGORIA_OPTS = [
  { value: '',             label: '—' },
  { value: 'custeio',      label: 'Custeio' },
  { value: 'investimento', label: 'Investimento' },
]

const STATUS_BADGE = {
  rascunho:  'bg-yellow-100 text-yellow-700',
  publicado: 'bg-green-100 text-green-700',
}

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'PCA — Plano de Contratações Anual',
  descricao: 'Consolida as necessidades aprovadas de um exercício em um documento formal e sequenciado, exigido pela Lei 14.133/2021. Enquanto em Rascunho, itens podem ser vinculados e editados livremente.',
  acoes: [
    { label: '+ Vincular necessidades', texto: 'Abre um painel com as necessidades aprovadas do exercício ainda não incluídas no PCA. Só necessidades com esse status ficam disponíveis.' },
    { label: 'Editar (por item)',       texto: 'Preenche Categoria (Custeio/Investimento), Programa/Ação, Data estimada de início e Objetivo Estratégico — necessários antes de publicar.' },
    { label: 'Publicar PCA',            texto: 'Gera os números sequenciais definitivos e torna o documento somente leitura. Ação irreversível — revise os itens antes.' },
    { label: 'Exportar PDF',            texto: 'Gera o PCA em PDF no formato exigido pela IN SEGES/ME nº 65/2021, disponível tanto em rascunho quanto publicado.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 12, VII e IN SEGES/ME nº 65/2021.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PCADetail() {
  const { id }   = useParams()
  const navigate = useNavigate()

  const [plano,       setPlano]       = useState(null)
  const [loading,     setLoading]     = useState(true)
  const [saving,      setSaving]      = useState(false)
  const [exporting,   setExporting]   = useState(false)
  const [publishing,  setPublishing]  = useState(false)
  const [error,       setError]       = useState(null)
  const [editando,    setEditando]    = useState({})
  const [msg,         setMsg]         = useState(null)

  // painel de vínculo
  const [showVincular, setShowVincular] = useState(false)
  const [necessidades, setNecessidades] = useState([])
  const [loadingNec,   setLoadingNec]   = useState(false)
  const [busca,        setBusca]        = useState('')
  const [vinculando,   setVinculando]   = useState(null)
  const [desvinculando,setDesvinculando]= useState(null)

  // ── Carregar plano ────────────────────────────────────────────────────────
  const carregar = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get(`/planejamento/planoorcamentario/${id}/`)
      setPlano(data)
    } catch {
      setError('Erro ao carregar o Plano.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { carregar() }, [carregar])

  // ── Carregar necessidades disponíveis para vincular ───────────────────────
  const carregarNecessidades = useCallback(async () => {
    if (!plano) return
    setLoadingNec(true)
    try {
      const { data } = await api.get('/planejamento/necessidade/', {
        params: { status: 'Aprovada', exercicio_fiscal: plano.exercicio_fiscal, page_size: 200 },
      })
      const ja_vinculadas = new Set((plano.itens || []).map(i => i.necessidade))
      const disponiveis = (data.results ?? data).filter(n => !ja_vinculadas.has(n.id))
      setNecessidades(disponiveis)
    } catch {
      setNecessidades([])
    } finally {
      setLoadingNec(false)
    }
  }, [plano])

  useEffect(() => {
    if (showVincular) carregarNecessidades()
  }, [showVincular, carregarNecessidades])

  // ── Vincular necessidade ──────────────────────────────────────────────────
  const vincular = async (necessidade_id) => {
    setVinculando(necessidade_id)
    try {
      await api.post(`/planejamento/planoorcamentario/${id}/vincular_necessidade/`, {
        necessidade_id,
        origem: 'propria',
      })
      flashMsg('Necessidade vinculada.')
      await carregar()
      await carregarNecessidades()
    } catch (err) {
      flashMsg(err?.response?.data?.detail || 'Erro ao vincular.', true)
    } finally {
      setVinculando(null)
    }
  }

  // ── Desvincular necessidade ───────────────────────────────────────────────
  const desvincular = async (necessidade_id) => {
    if (!window.confirm('Remover esta necessidade do PCA?')) return
    setDesvinculando(necessidade_id)
    try {
      await api.post(`/planejamento/planoorcamentario/${id}/desvincular_necessidade/`, { necessidade_id })
      flashMsg('Necessidade removida.')
      await carregar()
    } catch (err) {
      flashMsg(err?.response?.data?.detail || 'Erro ao remover.', true)
    } finally {
      setDesvinculando(null)
    }
  }

  // ── Edição inline campos PCA ──────────────────────────────────────────────
  const iniciarEdicao = (item) => {
    setEditando(prev => ({
      ...prev,
      [item.id]: {
        categoria_orcamentaria: item.categoria_orcamentaria || '',
        programa_acao:          item.programa_acao          || '',
        data_estimada_inicio:   item.data_estimada_inicio   || '',
        vinculacao_pgi:         item.vinculacao_pgi          || '',
      },
    }))
  }

  const cancelarEdicao = (itemId) => {
    setEditando(prev => { const n = {...prev}; delete n[itemId]; return n })
  }

  const salvarItem = async (itemId) => {
    setSaving(true)
    try {
      await api.patch(`/planejamento/planoorcamentario/${id}/atualizar_item_pca/`, {
        item_id: itemId,
        ...editando[itemId],
      })
      cancelarEdicao(itemId)
      await carregar()
      flashMsg('Item atualizado.')
    } catch {
      flashMsg('Erro ao salvar item.', true)
    } finally {
      setSaving(false)
    }
  }

  const editCampo = (itemId, campo, valor) => {
    setEditando(prev => ({ ...prev, [itemId]: { ...prev[itemId], [campo]: valor } }))
  }

  // ── Publicar ──────────────────────────────────────────────────────────────
  const publicar = async () => {
    if (!window.confirm('Publicar o PCA? Os números sequenciais serão gerados e o documento ficará somente leitura.')) return
    setPublishing(true)
    try {
      const { data } = await api.post(`/planejamento/planoorcamentario/${id}/publicar_pca/`)
      flashMsg(data.detail)
      await carregar()
    } catch (err) {
      flashMsg(err?.response?.data?.detail || 'Erro ao publicar.', true)
    } finally {
      setPublishing(false)
    }
  }

  // ── Exportar PDF ──────────────────────────────────────────────────────────
  const exportarPDF = async () => {
    setExporting(true)
    try {
      await downloadFile(
        `/planejamento/planoorcamentario/${id}/exportar_pca/`,
        `PCA_${plano?.orgao_sigla}_${plano?.exercicio_fiscal}.pdf`
      )
    } catch {
      flashMsg('Erro ao gerar PDF.', true)
    } finally {
      setExporting(false)
    }
  }

  const flashMsg = (texto, isError = false) => {
    setMsg({ texto, isError })
    setTimeout(() => setMsg(null), 4000)
  }

  // ── Filtro de busca nas necessidades disponíveis ──────────────────────────
  const necFiltradas = necessidades.filter(n =>
    !busca || n.titulo.toLowerCase().includes(busca.toLowerCase()) ||
    n.departamento_solicitante?.toLowerCase().includes(busca.toLowerCase())
  )

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner /></div>
  if (error)   return <div className="p-8 text-red-600">{error}</div>
  if (!plano)  return null

  const podeEditar = plano.status_pca !== 'publicado'

  return (
    <div className="p-6 max-w-screen-xl mx-auto">

      {/* Toast */}
      {msg && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          msg.isError ? 'bg-red-600 text-white' : 'bg-green-600 text-white'
        }`}>
          {msg.texto}
        </div>
      )}

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
        <div>
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-gray-600 text-sm mb-1 block">
            ← Voltar
          </button>
          <h1 className="text-xl font-bold text-gray-800">
            PCA — {plano.orgao_sigla} / {plano.exercicio_fiscal}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">{plano.orgao_nome}</p>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${STATUS_BADGE[plano.status_pca] || 'bg-gray-100 text-gray-600'}`}>
              {plano.status_pca === 'publicado' ? 'Publicado' : 'Rascunho'}
            </span>
            <span className="text-xs text-gray-500">{plano.itens?.length || 0} itens vinculados</span>
            {plano.dotacao_total && (
              <span className="text-xs text-gray-500">
                Dotação: {formatarMoeda(plano.dotacao_total)}
              </span>
            )}
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          {podeEditar && (
            <button
              onClick={() => setShowVincular(p => !p)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg"
            >
              {showVincular ? '✕ Fechar painel' : '+ Vincular necessidades'}
            </button>
          )}
          {podeEditar && (
            <button
              onClick={publicar}
              disabled={publishing || !plano.itens?.length}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
            >
              {publishing ? 'Publicando…' : 'Publicar PCA'}
            </button>
          )}
          <button
            onClick={exportarPDF}
            disabled={exporting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg"
          >
            {exporting ? 'Gerando…' : '↓ Exportar PDF'}
          </button>
        </div>
      </div>

      {/* ── Painel: vincular necessidades ─────────────────────────────────── */}
      {showVincular && (
        <div className="mb-5 bg-white rounded-xl border border-emerald-200 shadow-sm">
          <div className="px-5 py-3 border-b border-emerald-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-700 text-sm">
              Necessidades aprovadas disponíveis — exercício {plano.exercicio_fiscal}
            </h2>
            <input
              value={busca}
              onChange={e => setBusca(e.target.value)}
              placeholder="Buscar por título ou departamento…"
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>

          {loadingNec ? (
            <div className="flex justify-center py-8"><LoadingSpinner /></div>
          ) : necFiltradas.length === 0 ? (
            <p className="text-center text-sm text-gray-400 py-8">
              {necessidades.length === 0
                ? 'Nenhuma necessidade aprovada disponível para este exercício.'
                : 'Nenhuma necessidade encontrada para o filtro informado.'}
            </p>
          ) : (
            <div className="divide-y divide-gray-100 max-h-80 overflow-y-auto">
              {necFiltradas.map(n => (
                <div key={n.id} className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                  <div className="flex-1 min-w-0 mr-4">
                    <p className="text-sm font-medium text-gray-800 truncate">{n.titulo}</p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {n.departamento_solicitante} ·{' '}
                      {(n.area_aplicacao || []).join(', ')} ·{' '}
                      <span className="font-medium text-gray-700">
                        {formatarMoeda(n.valor_estimado)}
                      </span>
                    </p>
                  </div>
                  <button
                    onClick={() => vincular(n.id)}
                    disabled={vinculando === n.id}
                    className="shrink-0 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg"
                  >
                    {vinculando === n.id ? 'Vinculando…' : '+ Vincular'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Aviso rascunho */}
      {podeEditar && !showVincular && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-800">
          <strong>Rascunho</strong> — Use <strong>"+ Vincular necessidades"</strong> para adicionar itens ao PCA.
          Depois preencha Categoria, Programa/Ação e Data estimada de início antes de publicar.
        </div>
      )}

      {/* ── Tabela de itens vinculados ──────────────────────────────────── */}
      {(!plano.itens || plano.itens.length === 0) ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
          Nenhuma necessidade vinculada.
          {podeEditar && (
            <button onClick={() => setShowVincular(true)} className="text-emerald-600 hover:underline ml-1">
              Clique aqui para vincular →
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-blue-700 text-white text-xs">
                  <th className="px-3 py-2.5 text-left w-8">Seq</th>
                  <th className="px-3 py-2.5 text-left">Necessidade</th>
                  <th className="px-3 py-2.5 text-left">Área</th>
                  <th className="px-3 py-2.5 text-right">Valor Est.</th>
                  <th className="px-3 py-2.5 text-left">Categoria</th>
                  <th className="px-3 py-2.5 text-left">Prog./Ação</th>
                  <th className="px-3 py-2.5 text-left">Data Est. Início</th>
                  <th className="px-3 py-2.5 text-left">OE — Obj. Estratégico</th>
                  <th className="px-3 py-2.5 text-center w-24">Ações</th>
                </tr>
              </thead>
              <tbody>
                {plano.itens.map((item, idx) => {
                  const emEdicao = !!editando[item.id]
                  const ed = editando[item.id] || {}

                  return (
                    <tr key={item.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-blue-50/30'}>
                      <td className="px-3 py-2 text-gray-400 text-xs">
                        {item.numero_sequencial_pca || idx + 1}
                      </td>
                      <td className="px-3 py-2">
                        <div className="font-medium text-gray-800 text-xs leading-tight">{item.necessidade_titulo}</div>
                        <div className="text-gray-400 text-[10px] mt-0.5">{item.departamento_solicitante}</div>
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-600">
                        {(item.necessidade_areas || []).join(', ') || '—'}
                      </td>
                      <td className="px-3 py-2 text-right text-xs font-medium text-gray-800 whitespace-nowrap">
                        {formatarMoeda(item.valor_estimado)}
                      </td>

                      {emEdicao ? (
                        <>
                          <td className="px-2 py-1">
                            <select value={ed.categoria_orcamentaria}
                              onChange={e => editCampo(item.id, 'categoria_orcamentaria', e.target.value)}
                              className="w-full border border-gray-300 rounded px-1.5 py-1 text-xs">
                              {CATEGORIA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                          </td>
                          <td className="px-2 py-1">
                            <input value={ed.programa_acao}
                              onChange={e => editCampo(item.id, 'programa_acao', e.target.value)}
                              placeholder="1234/0001"
                              className="w-full border border-gray-300 rounded px-1.5 py-1 text-xs" />
                          </td>
                          <td className="px-2 py-1">
                            <input type="date" value={ed.data_estimada_inicio}
                              onChange={e => editCampo(item.id, 'data_estimada_inicio', e.target.value)}
                              className="w-full border border-gray-300 rounded px-1.5 py-1 text-xs" />
                          </td>
                          <td className="px-2 py-1">
                            <input value={ed.vinculacao_pgi}
                              onChange={e => editCampo(item.id, 'vinculacao_pgi', e.target.value)}
                              placeholder="Ex: OE-04 Modernização TI"
                              className="w-full border border-gray-300 rounded px-1.5 py-1 text-xs" />
                          </td>
                          <td className="px-2 py-1 text-center whitespace-nowrap">
                            <button onClick={() => salvarItem(item.id)} disabled={saving}
                              className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 mr-1">✓</button>
                            <button onClick={() => cancelarEdicao(item.id)}
                              className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded hover:bg-gray-300">✕</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td className="px-3 py-2 text-xs text-gray-600">
                            {CATEGORIA_OPTS.find(o => o.value === item.categoria_orcamentaria)?.label || '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-600">{item.programa_acao || '—'}</td>
                          <td className="px-3 py-2 text-xs text-gray-600">
                            {item.data_estimada_inicio
                              ? new Date(item.data_estimada_inicio + 'T00:00:00').toLocaleDateString('pt-BR')
                              : '—'}
                          </td>
                          <td className="px-3 py-2 text-xs text-gray-600">{item.vinculacao_pgi || '—'}</td>
                          <td className="px-3 py-2 text-center whitespace-nowrap">
                            {podeEditar && (
                              <>
                                <button onClick={() => iniciarEdicao(item)}
                                  className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded hover:bg-gray-200 mr-1">
                                  Editar
                                </button>
                                <button
                                  onClick={() => desvincular(item.necessidade)}
                                  disabled={desvinculando === item.necessidade}
                                  className="text-xs px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100 disabled:opacity-50">
                                  {desvinculando === item.necessidade ? '…' : '✕'}
                                </button>
                              </>
                            )}
                          </td>
                        </>
                      )}
                    </tr>
                  )
                })}
              </tbody>
              <tfoot>
                <tr className="bg-green-50 border-t-2 border-green-200">
                  <td colSpan={3} className="px-3 py-2 text-xs font-bold text-gray-700 text-right">TOTAL GERAL</td>
                  <td className="px-3 py-2 text-right text-xs font-bold text-gray-800 whitespace-nowrap">
                    {formatarMoeda(plano.itens.reduce((acc, it) => acc + Number(it.valor_estimado || 0), 0))}
                  </td>
                  <td colSpan={5} />
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-400 mt-4 text-right">
        IN SEGES/ME nº 65, de 7 de julho de 2021 — Sistema WEBBER
      </p>
    </div>
  )
}
