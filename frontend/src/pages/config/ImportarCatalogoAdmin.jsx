import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../services/api'
import CategoriaCascade from '../../components/CategoriaCascade'

// ── etapas ────────────────────────────────────────────────────────────────────
const ETAPA = { UPLOAD: 1, MAPEAR: 2, RESULTADO: 3 }

// ── helpers ───────────────────────────────────────────────────────────────────
const fmt = (n) => Number(n ?? 0).toLocaleString('pt-BR')

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Importar Catálogo (CSV)',
  descricao: 'Wizard de 3 etapas para importação em lote de itens de catálogo a partir de um arquivo CSV.',
  acoes: [
    { label: '1. Upload',    texto: 'Envia o CSV para análise em modo dry-run (nada é salvo ainda) — o backend identifica as famílias de itens presentes no arquivo.' },
    { label: '2. Mapear',    texto: 'Associa cada família de item detectada no CSV a uma categoria já existente no Webber, antes da importação definitiva.' },
    { label: '3. Resultado', texto: 'Mostra quantos itens foram criados, atualizados ou ignorados por erro após a importação real.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ImportarCatalogoAdmin() {
  const navigate  = useNavigate()
  const inputRef  = useRef(null)

  const [etapa, setEtapa]         = useState(ETAPA.UPLOAD)
  const [arquivo, setArquivo]     = useState(null)
  const [loading, setLoading]     = useState(false)
  const [erro, setErro]           = useState(null)

  // dados do dry-run
  const [preview, setPreview]     = useState(null)   // resposta do backend

  // mapeamento familia_desc → categoria_id
  const [mapeamento, setMapeamento] = useState({})   // { desc: id_number | null }

  // categorias Webber disponíveis para o picker
  const [categorias, setCategorias] = useState([])

  // resultado final da importação
  const [resultado, setResultado] = useState(null)

  useEffect(() => {
    api.get('/core/categorias/', { params: { page_size: 500 } })
      .then(({ data }) => setCategorias(data.results ?? data))
  }, [])

  // ── etapa 1: upload + análise ─────────────────────────────────────────────
  const handleArquivo = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setArquivo(f)
    setErro(null)
    setPreview(null)
  }

  const handleAnalisar = async () => {
    if (!arquivo) return
    setLoading(true); setErro(null)
    const fd = new FormData()
    fd.append('arquivo', arquivo)
    fd.append('dry_run', 'true')
    try {
      const { data } = await api.post('/core/catalogo/importar-csv/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setPreview(data)
      // Inicializar mapeamento com null para cada família
      const init = {}
      data.familias.forEach(f => { init[f.desc] = null })
      setMapeamento(init)
      setEtapa(ETAPA.MAPEAR)
    } catch (err) {
      setErro(err.response?.data?.erro || 'Erro ao analisar o arquivo.')
    } finally { setLoading(false) }
  }

  // ── etapa 2: mapear e importar ────────────────────────────────────────────
  const handleImportar = async () => {
    setLoading(true); setErro(null)
    const fd = new FormData()
    fd.append('arquivo', arquivo)
    fd.append('dry_run', 'false')
    // Só envia mapeamentos preenchidos
    const map = Object.fromEntries(
      Object.entries(mapeamento).filter(([, v]) => v != null)
    )
    fd.append('mapeamento', JSON.stringify(map))
    try {
      const { data } = await api.post('/core/catalogo/importar-csv/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResultado(data)
      setEtapa(ETAPA.RESULTADO)
    } catch (err) {
      setErro(err.response?.data?.erro || 'Erro ao importar.')
    } finally { setLoading(false) }
  }

  // ── render ────────────────────────────────────────────────────────────────
  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      {/* Cabeçalho */}
      <div className="mb-6">
        <button onClick={() => navigate('/config/catalogo')}
          className="text-xs text-blue-600 hover:underline mb-2 block">
          ← Voltar ao Catálogo
        </button>
        <h1 className="text-xl font-bold text-gray-800">Importar Catálogo ComprasNet BA</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Importe itens do catálogo SIMPAS em lote. Itens já cadastrados pelo código SIMPAS serão ignorados (sem duplicatas).
        </p>
      </div>

      {/* Barra de etapas */}
      <div className="flex items-center gap-0 mb-8">
        {[
          { n: 1, label: 'Upload' },
          { n: 2, label: 'Mapeamento' },
          { n: 3, label: 'Conclusão' },
        ].map(({ n, label }, i) => (
          <div key={n} className="flex items-center">
            {i > 0 && <div className={`h-px w-12 ${etapa > n - 1 ? 'bg-blue-400' : 'bg-gray-200'}`} />}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${
              etapa === n ? 'bg-blue-600 text-white' :
              etapa > n   ? 'bg-blue-100 text-blue-700' :
                            'bg-gray-100 text-gray-400'
            }`}>
              <span className="font-bold">{n}</span>
              <span>{label}</span>
            </div>
          </div>
        ))}
      </div>

      {erro && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
          {erro}
        </div>
      )}

      {/* ── ETAPA 1: UPLOAD ─────────────────────────────────────────────── */}
      {etapa === ETAPA.UPLOAD && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
          <div>
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Selecione o arquivo CSV</h2>
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
              onClick={() => inputRef.current?.click()}>
              <input ref={inputRef} type="file" accept=".csv,.txt" className="hidden" onChange={handleArquivo} />
              {arquivo ? (
                <div>
                  <p className="text-sm font-medium text-blue-700">{arquivo.name}</p>
                  <p className="text-xs text-gray-400 mt-1">{(arquivo.size / 1024).toFixed(1)} KB — clique para trocar</p>
                </div>
              ) : (
                <div>
                  <p className="text-sm text-gray-500">Clique ou arraste o arquivo CSV aqui</p>
                  <p className="text-xs text-gray-400 mt-1">Formato: exportação ComprasNet BA (.csv, separador ponto-e-vírgula)</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 text-xs text-blue-700 space-y-1">
            <p className="font-semibold">Como obter o arquivo CSV do ComprasNet BA:</p>
            <ol className="list-decimal list-inside space-y-0.5 text-blue-600">
              <li>Acesse <span className="font-mono">comprasnet.ba.gov.br → Catálogo → Consulta</span></li>
              <li>Pesquise os itens desejados (por família ou por nome)</li>
              <li>Clique em <strong>"Baixar Catálogo Excel"</strong> na página de resultados</li>
              <li>Salve o arquivo e envie aqui — o sistema aceita CSV com separador <span className="font-mono">;</span></li>
            </ol>
            <p className="text-blue-500 mt-1">
              Colunas esperadas: <span className="font-mono">Descrição Família; Código Item; Nome Básico; Nome Modificador; Descrição Padrão; Tipo Item; Classificação; Situação; UM</span>
            </p>
          </div>

          <button onClick={handleAnalisar} disabled={!arquivo || loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg">
            {loading ? 'Analisando...' : 'Analisar arquivo →'}
          </button>
        </div>
      )}

      {/* ── ETAPA 2: MAPEAMENTO ─────────────────────────────────────────── */}
      {etapa === ETAPA.MAPEAR && preview && (
        <div className="space-y-5">
          {/* Resumo da análise */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { label: 'Total lidos',     value: fmt(preview.total_lidos),  cor: 'text-gray-700' },
              { label: 'Novos a importar', value: fmt(preview.novos),        cor: 'text-green-600' },
              { label: 'Já existentes',   value: fmt(preview.duplicados),   cor: 'text-amber-600' },
              { label: 'Inválidos',       value: fmt(preview.invalidos),    cor: 'text-red-500' },
            ].map(({ label, value, cor }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-4 text-center">
                <p className={`text-2xl font-bold ${cor}`}>{value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{label}</p>
              </div>
            ))}
          </div>

          {preview.novos === 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-700">
              Todos os itens do arquivo já existem no catálogo. Nada será importado.
            </div>
          )}

          {/* Mapeamento família → categoria */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-5 py-3 bg-gray-50 border-b border-gray-200">
              <h2 className="text-sm font-semibold text-gray-700">
                Mapear famílias ComprasNet → Categorias Webber
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Opcional — vincule cada família a uma categoria para facilitar o agrupamento no Plano de Compras. Deixe em branco para importar sem categoria.
              </p>
            </div>

            {categorias.length === 0 && (
              <div className="px-5 py-4 text-xs text-gray-500 italic">
                Nenhuma categoria cadastrada no Webber.{' '}
                <button onClick={() => navigate('/config/categorias')} className="text-blue-600 hover:underline">
                  Criar categorias primeiro
                </button>{' '}
                ou importe sem mapeamento.
              </div>
            )}

            <div className="divide-y divide-gray-100 max-h-[440px] overflow-y-auto">
              {preview.familias.map(fam => (
                <div key={fam.desc} className="px-5 py-3">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-800 truncate">{fam.desc || '(sem descrição)'}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        SIMPAS: <span className="font-mono">{fam.familia_simpas || '—'}</span>
                        {' · '}{fmt(fam.count)} item{fam.count !== 1 ? 'ns' : ''}
                      </p>
                    </div>
                    <div className="w-72 shrink-0">
                      {categorias.length > 0 ? (
                        <CategoriaCascade
                          categorias={categorias}
                          value={mapeamento[fam.desc] ?? null}
                          onChange={id => setMapeamento(p => ({ ...p, [fam.desc]: id }))}
                        />
                      ) : (
                        <span className="text-xs text-gray-300 italic">sem categorias</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Preview dos primeiros itens novos */}
          {preview.preview_novos?.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
              <div className="px-5 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-sm font-semibold text-gray-700">Prévia — primeiros {preview.preview_novos.length} itens novos</h2>
                {preview.novos > preview.preview_novos.length && (
                  <span className="text-xs text-gray-400">+ {fmt(preview.novos - preview.preview_novos.length)} outros</span>
                )}
              </div>
              <div className="overflow-x-auto max-h-52 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium text-gray-500">Código SIMPAS</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-500">Nome</th>
                      <th className="text-left px-4 py-2 font-medium text-gray-500">UM</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {preview.preview_novos.map(it => (
                      <tr key={it.codigo_simpas} className="hover:bg-gray-50">
                        <td className="px-4 py-1.5 font-mono text-blue-700">{it.codigo_simpas}</td>
                        <td className="px-4 py-1.5 text-gray-700 max-w-xs truncate">{it.nome}</td>
                        <td className="px-4 py-1.5 text-gray-500 font-mono">{it.unidade_medida}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Ações */}
          <div className="flex flex-wrap gap-3">
            <button onClick={handleImportar} disabled={loading || preview.novos === 0}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-lg">
              {loading ? 'Importando...' : `Importar ${fmt(preview.novos)} item${preview.novos !== 1 ? 'ns' : ''} →`}
            </button>
            <button onClick={() => { setEtapa(ETAPA.UPLOAD); setPreview(null); setArquivo(null) }}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-2.5 rounded-lg hover:bg-gray-50">
              ← Trocar arquivo
            </button>
          </div>
        </div>
      )}

      {/* ── ETAPA 3: RESULTADO ──────────────────────────────────────────── */}
      {etapa === ETAPA.RESULTADO && resultado && (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto text-3xl">
            ✓
          </div>
          <h2 className="text-lg font-bold text-gray-800">Importação concluída</h2>
          <div className="flex justify-center gap-8 mt-2">
            <div>
              <p className="text-3xl font-bold text-green-600">{fmt(resultado.criados)}</p>
              <p className="text-xs text-gray-500 mt-0.5">itens criados</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-amber-500">{fmt(resultado.duplicados_ignorados)}</p>
              <p className="text-xs text-gray-500 mt-0.5">duplicatas ignoradas</p>
            </div>
          </div>
          <div className="flex justify-center gap-3 pt-4">
            <button onClick={() => navigate('/config/catalogo')}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2.5 rounded-lg">
              Ver catálogo
            </button>
            <button onClick={() => { setEtapa(ETAPA.UPLOAD); setArquivo(null); setPreview(null); setResultado(null) }}
              className="border border-gray-300 text-gray-600 text-sm px-4 py-2.5 rounded-lg hover:bg-gray-50">
              Nova importação
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
