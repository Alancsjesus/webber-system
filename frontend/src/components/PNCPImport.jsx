/**
 * Painel de pesquisa de preços no PNCP, exibido no cartão de cada item do mapa
 * (mapas em Rascunho ou Devolvido). A pesquisa sempre atende a um item: a descrição
 * dele é a palavra-chave padrão, a referência da similaridade e o destino dos preços.
 *
 * Fluxo:
 *  1. UF (ou todo o Brasil, ou CNPJ) + período + modalidade → filtrados no servidor
 *     (todo o Brasil usa só a base Compras.gov.br; com UF, completa com o PNCP)
 *     Descarta contratações sem preço homologado e de natureza diferente
 *     (aquisição × locação × serviço) da demandada
 *  2. Backend varre as publicações e ordena por similaridade com o objeto demandado
 *  3. Usuário abre uma contratação → itens com valor unitário HOMOLOGADO,
 *     também ordenados por similaridade com o item do mapa
 *  4. Seleciona os itens equivalentes → importados como Parâmetro II neste item
 */
import { useState } from 'react'
import api from '../services/api'
import { formatarMoeda } from '../utils/currencyMask'
import { SimilBadge, CampoNatureza, NaturezaUsada } from './ComprasGovImport'

const UF_OPTS = [
  'BA','SP','RJ','MG','RS','PR','SC','GO','DF','PE','CE','PA','MA','AM','ES',
  'RN','PB','AL','SE','PI','MT','MS','RO','TO','AC','AP','RR',
]

const MODALIDADES = [
  { value: 6, label: 'Pregão eletrônico' },
  { value: 4, label: 'Concorrência eletrônica' },
  { value: 8, label: 'Dispensa' },
]

const fmtData = (d) => d ? new Date(d + 'T00:00:00').toLocaleDateString('pt-BR') : '—'
const isoDias = (dias) => { const d = new Date(); d.setDate(d.getDate() - dias); return d.toISOString().split('T')[0] }

export default function PNCPImport({ mapaId, item, onImportado }) {
  const [aberto,     setAberto]     = useState(false)
  const [buscando,   setBuscando]   = useState(false)
  const [importando, setImportando] = useState(false)
  const [erro,       setErro]       = useState(null)

  // Padrão 60 dias: o PNCP limita a velocidade de consulta; períodos longos exigem mais de uma busca
  const [filtros, setFiltros] = useState({
    periodo_inicio:        isoDias(60),
    periodo_fim:           isoDias(0),
    uf:                    'BA',
    cnpj_orgao_referencia: '',
    termo_busca:           item.descricao || '',
    modalidades:           [6],
    incluir_atas:          false,
    natureza:              'auto',
  })
  const setF = (campo, val) => setFiltros(p => ({ ...p, [campo]: val }))
  const toggleMod = (m) => setF('modalidades',
    filtros.modalidades.includes(m) ? filtros.modalidades.filter(x => x !== m) : [...filtros.modalidades, m])

  const [busca,        setBusca]        = useState(null)   // resposta do preview
  const [abertoId,     setAbertoId]     = useState(null)   // contratação expandida
  const [itensPorReg,  setItensPorReg]  = useState({})     // registro_id → itens homologados
  const [carregando,   setCarregando]   = useState(null)
  const [selecionados, setSelecionados] = useState(new Set())

  // ── Passo 1: buscar contratações ──────────────────────────────────────────
  const buscar = async () => {
    setBuscando(true)
    setErro(null)
    setBusca(null)
    setAbertoId(null)
    setItensPorReg({})
    setSelecionados(new Set())
    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/pncp/preview/`, {
        ...filtros,
        item_mapa_id: item.id,
        incluir_contratos: filtros.modalidades.length > 0,
      })
      setBusca(data)
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao consultar o PNCP.')
    } finally {
      setBuscando(false)
    }
  }

  // ── Passo 2: abrir contratação → itens homologados ────────────────────────
  const abrir = async (reg) => {
    if (abertoId === reg.id) { setAbertoId(null); return }
    setAbertoId(reg.id)
    if (itensPorReg[reg.id] || reg.tipo_registro !== 'contratacao') return
    setCarregando(reg.id)
    setErro(null)
    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/pncp/itens/`, {
        importacao_id: busca.importacao_id, registro_id: reg.id, item_mapa_id: item.id,
        natureza: busca.natureza?.valor || filtros.natureza,
      })
      setItensPorReg(p => ({ ...p, [reg.id]: data.itens, [`aviso_${reg.id}`]: data.aviso }))
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao abrir os itens da contratação.')
    } finally {
      setCarregando(null)
    }
  }

  const toggleSel = (ln) => {
    if (ln.importado) return
    setSelecionados(prev => {
      const n = new Set(prev)
      n.has(ln.id) ? n.delete(ln.id) : n.add(ln.id)
      return n
    })
  }

  // ── Passo 3: importar no item ─────────────────────────────────────────────
  const importar = async () => {
    if (!selecionados.size) return
    setImportando(true)
    setErro(null)
    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/pncp/confirmar/`, {
        importacao_id: busca.importacao_id, ids: [...selecionados], item_mapa_id: item.id,
      })
      if (!data.importados) {
        setErro((data.log || data.erros || ['Nenhum preço importado.']).join(' | '))
        return
      }
      onImportado?.(`${data.importados} preço(s) do PNCP registrado(s) no item "${item.descricao?.slice(0, 50)}".`)
      setBusca(null)
      setSelecionados(new Set())
      setAberto(false)
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao importar.')
    } finally {
      setImportando(false)
    }
  }

  const registros = busca?.registros || []
  const parcial = (busca?.varredura || []).some(v => !v.completa)

  return (
    <div>
      <button
        onClick={() => setAberto(p => !p)}
        className="flex items-center gap-2 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium rounded-lg transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        {aberto ? 'Fechar PNCP' : 'Pesquisar no PNCP'}
      </button>

      {aberto && (
        <div className="mt-3 bg-teal-50 border border-teal-200 rounded-xl p-5">
          <h3 className="font-semibold text-teal-800 text-sm mb-1">
            Portal Nacional de Contratações Públicas — preços homologados de contratações similares
          </h3>
          <p className="text-xs text-teal-900 bg-white border border-teal-100 rounded-lg px-3 py-2 mb-3">
            Pesquisa para o item <strong>#{item.ordem} {item.descricao}</strong> ({item.unidade_medida}) —
            os resultados são ordenados pela semelhança com ele, e os preços selecionados serão registrados neste item.
          </p>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="col-span-2">
              <label className="block text-xs text-gray-600 mb-1">Objeto demandado / palavra-chave</label>
              <input value={filtros.termo_busca} onChange={e => setF('termo_busca', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
              <p className="text-[11px] text-gray-500 mt-0.5">
                Vem preenchido com a descrição do item. Os resultados recebem uma nota de semelhança (0–100%) com este texto,
                tolerando plural, acentos e pequenas variações de grafia; números (ex.: 24.000 BTUs) precisam bater.
              </p>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Período — início</label>
              <input type="date" value={filtros.periodo_inicio} onChange={e => setF('periodo_inicio', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Período — fim</label>
              <input type="date" value={filtros.periodo_fim} onChange={e => setF('periodo_fim', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">UF</label>
              <select value={filtros.uf} onChange={e => setF('uf', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                <option value="">Todo o Brasil</option>
                {UF_OPTS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
              <p className="text-[11px] text-gray-400 mt-0.5">
                {filtros.uf
                  ? 'Completa: base Compras.gov.br + varredura do PNCP (inclui municípios de outras plataformas).'
                  : 'Todo o Brasil: base Compras.gov.br (rápida). Para incluir municípios de outras plataformas, escolha uma UF.'}
              </p>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">CNPJ de um órgão específico (opcional)</label>
              <input value={filtros.cnpj_orgao_referencia} onChange={e => setF('cnpj_orgao_referencia', e.target.value)}
                placeholder="00.000.000/0001-00"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <CampoNatureza value={filtros.natureza} onChange={v => setF('natureza', v)} />
            <div className="col-span-2 flex flex-wrap items-center gap-4">
              {MODALIDADES.map(m => (
                <label key={m.value} className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                  <input type="checkbox" className="rounded" checked={filtros.modalidades.includes(m.value)}
                    onChange={() => toggleMod(m.value)} />
                  {m.label}
                </label>
              ))}
              <label className={`flex items-center gap-2 text-xs cursor-pointer ${filtros.cnpj_orgao_referencia ? 'text-gray-600' : 'text-gray-400'}`}
                title="O PNCP só filtra atas por CNPJ. Sem CNPJ, use o painel Compras.gov.br (atas por código CATMAT/CATSER).">
                <input type="checkbox" className="rounded" disabled={!filtros.cnpj_orgao_referencia}
                  checked={filtros.incluir_atas && !!filtros.cnpj_orgao_referencia}
                  onChange={e => setF('incluir_atas', e.target.checked)} />
                Atas de RP (com CNPJ)
              </label>
            </div>
          </div>

          <button onClick={buscar} disabled={buscando || filtros.modalidades.length === 0}
            className="px-4 py-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
            {buscando ? 'Consultando PNCP (pode levar até 1 min)…' : (parcial ? 'Continuar varredura' : 'Buscar no PNCP')}
          </button>

          {erro && (
            <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">{erro}</div>
          )}
          {busca?.erros_api?.length > 0 && (
            <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 space-y-1">
              {busca.erros_api.map((e, i) => <p key={i}>{e}</p>)}
            </div>
          )}

          {busca && (
            <div className="mt-4">
              <NaturezaUsada natureza={busca.natureza} />
              <p className="text-xs text-gray-600 mb-2">
                {registros.length} contratação(ões) com preço homologado semelhante(s) a “{busca.termo_usado}”
                {(busca.varredura || []).map(v => v.total_registros != null &&
                  ` · ${v.modalidade}: ${v.total_registros} publicações analisadas${v.completa ? '' : ' (parcial)'}`)}
                . Abra uma contratação para ver os itens com preço homologado.
              </p>

              {registros.length === 0 ? (
                <p className="text-sm text-gray-500">
                  Nenhuma contratação semelhante. Simplifique o objeto demandado (ex.: só o nome do bem), amplie o período ou inclua outra modalidade.
                </p>
              ) : (
                <div className="border border-gray-200 rounded-lg overflow-hidden max-h-[28rem] overflow-y-auto divide-y divide-gray-100">
                  {registros.map(reg => (
                    <div key={reg.id} className="bg-white">
                      <button onClick={() => abrir(reg)}
                        className="w-full text-left px-3 py-2 hover:bg-teal-50 flex items-start gap-3">
                        <SimilBadge v={reg.similaridade} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-gray-800 line-clamp-2" title={reg.objeto}>{reg.objeto}</p>
                          <p className="text-[10px] text-gray-500">
                            {reg.orgao_nome} · {reg.uf || '—'} · {reg.modalidade} · {fmtData(reg.data_referencia)} · {reg.numero_pncp}
                          </p>
                        </div>
                        <span className="text-[11px] text-teal-700 whitespace-nowrap">
                          {carregando === reg.id ? 'Abrindo…' : abertoId === reg.id ? '▲ fechar' : '▼ itens'}
                        </span>
                      </button>

                      {abertoId === reg.id && itensPorReg[reg.id] && (
                        <div className="px-3 pb-3">
                          {itensPorReg[`aviso_${reg.id}`] && (
                            <p className="text-[11px] text-amber-800 mb-1 pl-10">{itensPorReg[`aviso_${reg.id}`]}</p>
                          )}
                          {itensPorReg[reg.id].length === 0 ? (
                            <p className="text-xs text-gray-500 pl-10">
                              Nenhum item com resultado homologado ainda — não há preço praticado para importar.
                            </p>
                          ) : (
                            <table className="w-full text-xs border border-gray-200 rounded">
                              <thead>
                                <tr className="bg-teal-700 text-white">
                                  <th className="px-2 py-1.5 w-8"></th>
                                  <th className="px-2 py-1.5 text-right">Simil.</th>
                                  <th className="px-2 py-1.5 text-left">Item da contratação</th>
                                  <th className="px-2 py-1.5 text-left">Unid.</th>
                                  <th className="px-2 py-1.5 text-right">Preço unit. homologado</th>
                                  <th className="px-2 py-1.5 text-left">Fornecedor</th>
                                </tr>
                              </thead>
                              <tbody>
                                {itensPorReg[reg.id].map(ln => (
                                  <tr key={ln.id} onClick={() => toggleSel(ln)}
                                    className={`border-t border-gray-100 ${ln.importado ? 'opacity-50' : 'cursor-pointer hover:bg-teal-50'} ${selecionados.has(ln.id) ? 'bg-teal-50' : ''}`}>
                                    <td className="px-2 py-1.5 text-center">
                                      <input type="checkbox" className="rounded" disabled={ln.importado}
                                        checked={selecionados.has(ln.id)} onChange={() => toggleSel(ln)}
                                        onClick={e => e.stopPropagation()} />
                                    </td>
                                    <td className="px-2 py-1.5 text-right"><SimilBadge v={ln.similaridade} /></td>
                                    <td className="px-2 py-1.5 text-gray-700 max-w-[260px]">
                                      <p className="line-clamp-2" title={ln.descricao}>{ln.numero_item}. {ln.descricao}</p>
                                      {ln.importado && <p className="text-[10px] text-gray-500">Já importado</p>}
                                    </td>
                                    <td className={`px-2 py-1.5 ${ln.unidade_diverge ? 'text-red-700 font-semibold' : 'text-gray-600'}`}
                                      title={ln.unidade_diverge ? `Unidade diferente da do item (${item.unidade_medida})` : ''}>
                                      {ln.unidade_medida || '—'}
                                    </td>
                                    <td className="px-2 py-1.5 text-right font-medium text-gray-800 whitespace-nowrap">
                                      {formatarMoeda(ln.valor_unitario)}
                                    </td>
                                    <td className="px-2 py-1.5 text-gray-600 max-w-[160px]">
                                      <p className="truncate" title={ln.fornecedor}>{ln.fornecedor || '—'}</p>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {selecionados.size > 0 && (
                <div className="mt-3 flex items-center gap-3 flex-wrap">
                  <button onClick={importar} disabled={importando}
                    className="px-5 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg">
                    {importando ? 'Importando…' : `↓ Registrar ${selecionados.size} preço(s) no item #${item.ordem}`}
                  </button>
                  <p className="text-[11px] text-gray-500">
                    Entram como <strong>Parâmetro II</strong>. Confira se o item da contratação é equivalente ao demandado e se a unidade é a mesma.
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
