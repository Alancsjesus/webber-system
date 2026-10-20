/**
 * Painel de pesquisa de preços unitários no Compras.gov.br (Dados Abertos).
 * Exibido no cartão de cada item do MapaDetail (mapas em Rascunho ou Devolvido):
 * a pesquisa sempre atende a um item — ele é a referência da similaridade, da
 * unidade e o destino dos preços.
 *
 * Fluxo:
 *  1. Usuário informa o código CATMAT/CATSER do item
 *  2. Backend consulta a API oficial (só código, período e UF saem do sistema)
 *  3. Tela mostra a estatística e marca preços fora da faixa de ±30% da mediana
 *     e unidades divergentes; os demais já vêm pré-selecionados
 *  4. "Importar selecionados" → backend refaz a consulta e grava só o que consta
 *     do retorno oficial, como Parâmetro II
 */
import { useState } from 'react'
import api from '../services/api'
import { formatarMoeda } from '../utils/currencyMask'

const UF_OPTS = [
  'BA','SP','RJ','MG','RS','PR','SC','GO','DF','PE','CE','PA','MA','AM','ES',
  'RN','PB','AL','SE','PI','MT','MS','RO','TO','AC','AP','RR',
]

const SITUACAO = {
  ok:          { label: 'Na faixa',    cls: 'bg-green-100 text-green-700' },
  inexequivel: { label: 'Inexequível', cls: 'bg-amber-100 text-amber-800' },
  excessivo:   { label: 'Excessivo',   cls: 'bg-red-100 text-red-700' },
}

export const NATUREZA_OPTS = [
  { value: 'auto',      label: 'Automática (detectada no item/mapa)' },
  { value: 'aquisicao', label: 'Aquisição' },
  { value: 'locacao',   label: 'Locação' },
  { value: 'servico',   label: 'Serviço (manutenção, instalação…)' },
  { value: 'qualquer',  label: 'Qualquer natureza' },
]

export function CampoNatureza({ value, onChange }) {
  return (
    <div>
      <label className="block text-xs text-gray-600 mb-1">Natureza da contratação</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
        {NATUREZA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
      <p className="text-[11px] text-gray-400 mt-0.5">Resultados de outra natureza (ex.: locação numa aquisição) são ocultados.</p>
    </div>
  )
}

export function NaturezaUsada({ natureza }) {
  if (!natureza) return null
  return (
    <p className="text-[11px] text-gray-600 mb-2">
      Natureza considerada: <strong>{natureza.rotulo}</strong> ({natureza.origem}).
    </p>
  )
}

export function SimilBadge({ v }) {
  if (v === null || v === undefined) return <span className="text-gray-400">—</span>
  const cls = v >= 70 ? 'bg-green-100 text-green-700' : v >= 40 ? 'bg-amber-100 text-amber-800' : 'bg-gray-100 text-gray-500'
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${cls}`}>{v}%</span>
}

const fmtData = (d) => d ? new Date(d + 'T00:00:00').toLocaleDateString('pt-BR') : '—'
const fmtNum = (v) => Number(v).toLocaleString('pt-BR', { maximumFractionDigits: 4 })

export default function ComprasGovImport({ mapaId, item, onImportado }) {
  const [aberto,     setAberto]     = useState(false)
  const [buscando,   setBuscando]   = useState(false)
  const [importando, setImportando] = useState(false)
  const [erro,       setErro]       = useState(null)

  const [filtros, setFiltros] = useState({
    item_mapa_id: item.id,
    tipo:   'material',
    codigo: '',
    uf:     '',
    natureza: 'auto',
  })
  const [catalogo,     setCatalogo]     = useState(null)
  const [resultado,    setResultado]    = useState(null)
  const [selecionados, setSelecionados] = useState(new Set())

  const setF = (campo, val) => {
    setFiltros(p => ({ ...p, [campo]: val }))
    setResultado(null)
    if (campo === 'codigo' || campo === 'tipo') setCatalogo(null)
  }

  const registros = resultado?.registros || []
  const est = resultado?.estatistica

  // ── Passo 1: conferir o código e buscar os preços ─────────────────────────
  const buscar = async () => {
    setBuscando(true)
    setErro(null)
    setResultado(null)
    setSelecionados(new Set())
    try {
      const { data: cat } = await api.get(`/pesquisa/mapa/${mapaId}/comprasgov/catalogo/`, {
        params: { tipo: filtros.tipo, codigo: filtros.codigo.trim() },
      })
      setCatalogo(cat)
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/comprasgov/precos/`, {
        ...filtros, codigo: filtros.codigo.trim(),
      })
      setResultado(data)
      setSelecionados(new Set(
        data.registros.filter(r => r.situacao === 'ok' && !r.unidade_diverge && !r.ja_importado).map(r => r.id)
      ))
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao consultar o Compras.gov.br.')
    } finally {
      setBuscando(false)
    }
  }

  const toggleSel = (r) => {
    if (r.ja_importado) return
    setSelecionados(prev => {
      const n = new Set(prev)
      n.has(r.id) ? n.delete(r.id) : n.add(r.id)
      return n
    })
  }

  // ── Passo 2: importar ─────────────────────────────────────────────────────
  const importar = async () => {
    if (!selecionados.size) return
    setImportando(true)
    setErro(null)
    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/comprasgov/importar/`, {
        ...filtros, codigo: filtros.codigo.trim(), ids: [...selecionados],
      })
      const extra = data.ignorados?.length ? ` ${data.ignorados.length} ignorado(s).` : ''
      onImportado?.(data.detail + extra)
      setResultado(null)
      setSelecionados(new Set())
      setAberto(false)
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao importar.')
    } finally {
      setImportando(false)
    }
  }

  const itemSel = item

  return (
    <div>
      <button
        onClick={() => setAberto(p => !p)}
        className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        {aberto ? 'Fechar Compras.gov.br' : 'Pesquisar no Compras.gov.br (CATMAT/CATSER)'}
      </button>

      {aberto && (
        <div className="mt-3 bg-indigo-50 border border-indigo-200 rounded-xl p-5">
          <h3 className="font-semibold text-indigo-800 text-sm mb-1">
            Compras.gov.br — preços unitários homologados por item de catálogo
          </h3>
          <p className="text-[11px] text-gray-600 mb-4">
            Consulta direta à API oficial de Dados Abertos. Só o código do catálogo, o período e a UF são enviados —
            nenhuma informação do mapa, do órgão ou do usuário sai do WEBBER. Os preços entram como
            <strong> Parâmetro II</strong> (contratações similares), dentro do prazo de validade configurado.
          </p>

          <p className="text-xs text-indigo-900 bg-white border border-indigo-100 rounded-lg px-3 py-2 mb-3">
            Pesquisa para o item <strong>#{item.ordem} {item.descricao}</strong> ({item.unidade_medida}) —
            os preços selecionados serão registrados neste item.
          </p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Catálogo</label>
              <select value={filtros.tipo} onChange={e => setF('tipo', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                <option value="material">Material (CATMAT)</option>
                <option value="servico">Serviço (CATSER)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Código do item</label>
              <input value={filtros.codigo} inputMode="numeric" maxLength={9}
                onChange={e => setF('codigo', e.target.value.replace(/\D/g, ''))}
                placeholder="Ex: 461633"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm font-mono" />
              <p className="text-[11px] text-gray-400 mt-0.5">
                A API oficial não busca por texto — localize o código em catalogo.compras.gov.br.
              </p>
            </div>
            <CampoNatureza value={filtros.natureza} onChange={v => setF('natureza', v)} />
            <div>
              <label className="block text-xs text-gray-600 mb-1">UF da compra (opcional)</label>
              <select value={filtros.uf} onChange={e => setF('uf', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                <option value="">Todo o Brasil</option>
                {UF_OPTS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
          </div>

          <button onClick={buscar} disabled={buscando || !filtros.codigo}
            className="px-4 py-2 bg-indigo-700 hover:bg-indigo-800 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
            {buscando ? 'Consultando Compras.gov.br…' : 'Buscar preços'}
          </button>

          {erro && (
            <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">{erro}</div>
          )}

          {catalogo && (
            <div className="mt-3 bg-white border border-indigo-100 rounded-lg p-3 text-xs">
              <p className="font-semibold text-gray-800">{catalogo.nome}</p>
              {catalogo.classe && <p className="text-gray-500">{catalogo.classe}</p>}
              {!catalogo.ativo && <p className="text-amber-700 mt-1">Código inativo no catálogo — confira se ainda é o item correto.</p>}
              <p className="text-gray-500 mt-1">
                Confira se corresponde a <strong>{itemSel?.descricao}</strong> antes de importar.
              </p>
            </div>
          )}

          {resultado && (
            <div className="mt-4">
              <p className="text-xs text-gray-600 mb-2">
                {registros.length} preço(s) homologado(s) entre {fmtData(resultado.periodo_inicio)} e {fmtData(resultado.periodo_fim)}
                {resultado.uf ? ` em ${resultado.uf}` : ' (todo o Brasil)'}.
                {resultado.truncado && ' Mostrando os mais recentes — refine pela UF para ver outros.'}
              </p>
              <NaturezaUsada natureza={resultado.natureza} />
              {resultado.avisos?.length > 0 && (
                <p className="text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded px-2 py-1 mb-2">
                  {resultado.avisos.join(' ')}
                </p>
              )}

              {est?.n > 0 && (
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-3">
                  {[
                    ['Amostra', est.n],
                    ['Mínimo', formatarMoeda(est.minimo)],
                    ['Mediana', formatarMoeda(est.mediana)],
                    ['Média', formatarMoeda(est.media)],
                    ['Máximo', formatarMoeda(est.maximo)],
                    ['Coef. variação', `${fmtNum(est.coef_variacao_pct)}%`],
                  ].map(([k, v]) => (
                    <div key={k} className="bg-white border border-indigo-100 rounded-lg px-2 py-1.5">
                      <p className="text-[10px] text-gray-500">{k}</p>
                      <p className="text-sm font-semibold text-gray-800">{v}</p>
                    </div>
                  ))}
                </div>
              )}
              {est?.n > 0 && (
                <p className="text-[11px] text-gray-600 mb-2">
                  Faixa de aceitação (±30% da mediana, Decreto 22.886/2024): {formatarMoeda(est.limite_inferior)} a {formatarMoeda(est.limite_superior)}.
                  {est.coef_variacao_pct > 25 && ' CV acima de 25%: amostra heterogênea, prefira a mediana.'}
                  {itemSel && est.qtd_mesma_unidade < registros.length &&
                    ` Estatística calculada só com os ${est.qtd_mesma_unidade} registro(s) na unidade do item (${itemSel.unidade_medida}).`}
                </p>
              )}

              {registros.length > 0 ? (
                <div className="border border-gray-200 rounded-lg overflow-hidden max-h-80 overflow-y-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-indigo-700 text-white">
                        <th className="px-2 py-2 w-8"></th>
                        <th className="px-3 py-2 text-left">Descrição comprada</th>
                        <th className="px-3 py-2 text-right" title="Semelhança com a descrição do item do mapa">Simil.</th>
                        <th className="px-3 py-2 text-right">Preço unit.</th>
                        <th className="px-3 py-2 text-left">Unid.</th>
                        <th className="px-3 py-2 text-left">Órgão / UASG</th>
                        <th className="px-3 py-2 text-left">Fornecedor</th>
                        <th className="px-3 py-2 text-left">Data</th>
                        <th className="px-3 py-2 text-left">Situação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {registros.map((r, idx) => (
                        <tr key={r.id} onClick={() => toggleSel(r)}
                          className={`border-t border-gray-100 ${r.ja_importado ? 'opacity-50' : 'cursor-pointer hover:bg-indigo-50'} ${
                            selecionados.has(r.id) ? 'bg-indigo-50' : idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                          }`}>
                          <td className="px-2 py-2 text-center">
                            <input type="checkbox" className="rounded" disabled={r.ja_importado}
                              checked={selecionados.has(r.id)} onChange={() => toggleSel(r)}
                              onClick={e => e.stopPropagation()} />
                          </td>
                          <td className="px-3 py-2 text-gray-700 max-w-[220px]">
                            <p className="truncate" title={r.descricao}>{r.descricao || '—'}</p>
                            <p className="text-[10px] text-gray-400">{r.origem === 'ata' ? r.forma : 'Compra homologada'}</p>
                          </td>
                          <td className="px-3 py-2 text-right whitespace-nowrap">
                            <SimilBadge v={r.similaridade} />
                          </td>
                          <td className="px-3 py-2 text-right font-medium text-gray-800 whitespace-nowrap">
                            {formatarMoeda(r.preco_unitario)}
                          </td>
                          <td className={`px-3 py-2 ${r.unidade_diverge ? 'text-red-700 font-semibold' : 'text-gray-600'}`}
                            title={r.unidade_diverge ? 'Unidade diferente da do item do mapa' : r.unidade_nome}>
                            {r.unidade || '—'}
                          </td>
                          <td className="px-3 py-2 text-gray-600 max-w-[180px]">
                            <p className="truncate" title={r.orgao}>{r.orgao || r.uasg_nome || '—'}</p>
                            <p className="text-[10px] text-gray-400">UASG {r.uasg} · {r.municipio}/{r.uf}</p>
                          </td>
                          <td className="px-3 py-2 text-gray-600 max-w-[160px]">
                            <p className="truncate" title={r.fornecedor}>{r.fornecedor || '—'}</p>
                            {r.marca && <p className="text-[10px] text-gray-400 truncate">Marca {r.marca}</p>}
                          </td>
                          <td className="px-3 py-2 text-gray-600 whitespace-nowrap">{fmtData(r.data_referencia)}</td>
                          <td className="px-3 py-2">
                            {r.ja_importado
                              ? <span className="px-1.5 py-0.5 rounded text-[10px] bg-gray-100 text-gray-600">Já importado</span>
                              : <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${SITUACAO[r.situacao]?.cls}`}>
                                  {SITUACAO[r.situacao]?.label}
                                </span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  Nenhum preço homologado no período. Tente sem UF ou registre outra fonte (Parâmetros III a V).
                </p>
              )}

              {registros.length > 0 && (
                <div className="mt-3 flex items-center gap-3 flex-wrap">
                  <button onClick={importar} disabled={importando || selecionados.size === 0}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg">
                    {importando ? 'Importando…' : `↓ Importar ${selecionados.size} selecionado(s)`}
                  </button>
                  <p className="text-[11px] text-gray-500">
                    Pré-selecionados só os preços na faixa e na mesma unidade. Incluir um preço fora da faixa exige justificativa no item.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
