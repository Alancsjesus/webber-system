/**
 * Painel de importação de preços do PNCP.
 * Exibido dentro do MapaDetail para mapas em Rascunho ou Devolvido.
 *
 * Fluxo:
 *  1. Usuário preenche filtros e clica "Buscar no PNCP"
 *  2. Backend consulta a API do PNCP e retorna lista de registros
 *  3. Usuário seleciona os relevantes e escolhe o item do mapa destino
 *  4. Clica "Importar selecionados" → backend cria FonteConsultada + PrecoColetado
 */
import { useState } from 'react'
import api from '../services/api'

const TIPO_FONTE_OPTS = [
  { value: 'II',  label: 'Parâmetro II — Contratações similares' },
  { value: 'III', label: 'Parâmetro III — Mídia especializada' },
]

const UF_OPTS = [
  'BA','SP','RJ','MG','RS','PR','SC','GO','DF','PE','CE','PA','MA','AM','ES',
  'RN','PB','AL','SE','PI','MT','MS','RO','TO','AC','AP','RR',
]

export default function PNCPImport({ mapaId, itensDoMapa = [], onImportado }) {
  const [aberto,    setAberto]    = useState(false)
  const [buscando,  setBuscando]  = useState(false)
  const [importando,setImportando]= useState(false)
  const [erro,      setErro]      = useState(null)

  // Filtros — padrão 90 dias (período de 1 ano causa timeout no PNCP para contratos)
  const hoje = new Date()
  const noventa = new Date(hoje); noventa.setDate(hoje.getDate() - 90)
  const [filtros, setFiltros] = useState({
    periodo_inicio:       noventa.toISOString().split('T')[0],
    periodo_fim:          hoje.toISOString().split('T')[0],
    cnpj_orgao_referencia:'',
    uf:                   'BA',
    termo_busca:          '',
    incluir_contratos:    true,
    incluir_atas:         true,
    tipo_fonte:           'II',
  })

  // Resultado da busca
  const [importacaoId, setImportacaoId] = useState(null)
  const [registros,    setRegistros]    = useState([])
  const [errosApi,     setErrosApi]     = useState([])
  const [selecionados, setSelecionados] = useState(new Set())
  const [itemDestino,  setItemDestino]  = useState(itensDoMapa[0]?.id || null)

  const setF = (campo, val) => setFiltros(p => ({ ...p, [campo]: val }))

  // ── Passo 1: Buscar no PNCP ───────────────────────────────────────────────
  const buscar = async () => {
    setBuscando(true)
    setErro(null)
    setRegistros([])
    setSelecionados(new Set())
    setImportacaoId(null)

    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/pncp/preview/`, filtros)
      setImportacaoId(data.importacao_id)
      setRegistros(data.registros || [])
      setErrosApi(data.erros_api || [])
      if (data.erros_api?.length && !data.registros?.length) {
        // Sem resultados E com erros — mostrar como erro principal
        setErro(data.erros_api.join(' | '))
      }
      // Se há registros mesmo com erros parciais, exibe os registros e os erros como aviso
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Erro ao consultar o PNCP.'
      setErro(msg)
    } finally {
      setBuscando(false)
    }
  }

  const toggleSel = (id) => setSelecionados(prev => {
    const n = new Set(prev)
    n.has(id) ? n.delete(id) : n.add(id)
    return n
  })

  const toggleTodos = () => {
    if (selecionados.size === registros.length) setSelecionados(new Set())
    else setSelecionados(new Set(registros.map(r => r.id)))
  }

  // ── Passo 2: Confirmar importação ─────────────────────────────────────────
  const importar = async () => {
    if (!selecionados.size) return
    if (!importacaoId) return
    setImportando(true)
    setErro(null)
    try {
      const { data } = await api.post(`/pesquisa/mapa/${mapaId}/pncp/confirmar/`, {
        importacao_id:  importacaoId,
        ids:            [...selecionados],
        item_mapa_id:   itemDestino,
      })
      onImportado?.(`${data.importados} preço(s) importado(s) do PNCP com sucesso.`)
      setRegistros([])
      setSelecionados(new Set())
      setImportacaoId(null)
      setAberto(false)
    } catch (err) {
      setErro(err?.response?.data?.detail || 'Erro ao importar.')
    } finally {
      setImportando(false)
    }
  }

  const fmtValor = (v) => v
    ? `R$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
    : '—'

  return (
    <div className="mt-4">
      <button
        onClick={() => setAberto(p => !p)}
        className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
        </svg>
        {aberto ? 'Fechar painel PNCP' : 'Importar preços do PNCP'}
      </button>

      {aberto && (
        <div className="mt-3 bg-teal-50 border border-teal-200 rounded-xl p-5">
          <h3 className="font-semibold text-teal-800 text-sm mb-4">
            Portal Nacional de Contratações Públicas — Pesquisa de preços de referência
          </h3>

          {/* ── Filtros ─────────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Período — início</label>
              <input type="date" value={filtros.periodo_inicio}
                onChange={e => setF('periodo_inicio', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Período — fim</label>
              <input type="date" value={filtros.periodo_fim}
                onChange={e => setF('periodo_fim', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">CNPJ do órgão de referência (opcional)</label>
              <input value={filtros.cnpj_orgao_referencia}
                onChange={e => setF('cnpj_orgao_referencia', e.target.value)}
                placeholder="00.000.000/0001-00"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">UF</label>
              <select value={filtros.uf} onChange={e => setF('uf', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                <option value="">Todos os estados</option>
                {UF_OPTS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-600 mb-1">Palavra-chave no objeto (opcional)</label>
              <input value={filtros.termo_busca}
                onChange={e => setF('termo_busca', e.target.value)}
                placeholder="Ex: notebook, viatura, manutenção predial…"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Parâmetro de pesquisa (destino)</label>
              <select value={filtros.tipo_fonte} onChange={e => setF('tipo_fonte', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                {TIPO_FONTE_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
            <div className="flex items-end gap-4 pb-1">
              <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                <input type="checkbox" checked={filtros.incluir_contratos}
                  onChange={e => setF('incluir_contratos', e.target.checked)}
                  className="rounded" />
                Contratos
              </label>
              <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                <input type="checkbox" checked={filtros.incluir_atas}
                  onChange={e => setF('incluir_atas', e.target.checked)}
                  className="rounded" />
                Atas de RP
              </label>
            </div>
          </div>

          <button onClick={buscar} disabled={buscando}
            className="px-4 py-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-sm font-medium rounded-lg">
            {buscando ? 'Consultando PNCP…' : '🔍 Buscar no PNCP'}
          </button>

          {/* ── Erro ───────────────────────────────────────────────────── */}
          {erro && (
            <div className="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700">
              {erro}
            </div>
          )}

          {/* ── Avisos de erros parciais (um tipo falhou mas outro retornou) ── */}
          {errosApi.length > 0 && registros.length > 0 && (
            <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">
              <strong>Aviso:</strong> {errosApi.join(' | ')}
            </div>
          )}

          {/* ── Resultados ─────────────────────────────────────────────── */}
          {registros.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-semibold text-gray-700">
                  {registros.length} registro(s) encontrado(s)
                </p>
                <button onClick={toggleTodos}
                  className="text-xs text-teal-700 hover:underline">
                  {selecionados.size === registros.length ? 'Desmarcar todos' : 'Selecionar todos'}
                </button>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden max-h-72 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-teal-700 text-white">
                      <th className="px-2 py-2 w-8">
                        <input type="checkbox"
                          checked={selecionados.size === registros.length && registros.length > 0}
                          onChange={toggleTodos} className="rounded" />
                      </th>
                      <th className="px-3 py-2 text-left">Objeto</th>
                      <th className="px-3 py-2 text-left">Órgão</th>
                      <th className="px-3 py-2 text-left">UF</th>
                      <th className="px-3 py-2 text-right">Valor Global</th>
                      <th className="px-3 py-2 text-left">Data</th>
                      <th className="px-3 py-2 text-left">Tipo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {registros.map((r, idx) => (
                      <tr key={r.id}
                        onClick={() => toggleSel(r.id)}
                        className={`cursor-pointer border-t border-gray-100 ${
                          selecionados.has(r.id) ? 'bg-teal-50' : idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                        } hover:bg-teal-50`}>
                        <td className="px-2 py-2 text-center">
                          <input type="checkbox" checked={selecionados.has(r.id)}
                            onChange={() => toggleSel(r.id)} className="rounded"
                            onClick={e => e.stopPropagation()} />
                        </td>
                        <td className="px-3 py-2 max-w-xs">
                          <p className="truncate font-medium text-gray-800" title={r.objeto}>{r.objeto}</p>
                          {r.numero_certame && <p className="text-gray-400 text-[10px]">{r.numero_certame}</p>}
                        </td>
                        <td className="px-3 py-2 text-gray-600 max-w-[140px]">
                          <p className="truncate" title={r.orgao_nome}>{r.orgao_nome || '—'}</p>
                        </td>
                        <td className="px-3 py-2 text-gray-600">{r.uf || '—'}</td>
                        <td className="px-3 py-2 text-right font-medium text-gray-800 whitespace-nowrap">
                          {fmtValor(r.valor_global)}
                        </td>
                        <td className="px-3 py-2 text-gray-600 whitespace-nowrap">
                          {r.data_referencia
                            ? new Date(r.data_referencia + 'T00:00:00').toLocaleDateString('pt-BR')
                            : '—'}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            r.tipo_registro === 'ata' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                          }`}>
                            {r.tipo_registro === 'ata' ? 'Ata RP' : 'Contrato'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Item destino + botão confirmar */}
              <div className="mt-3 flex items-center gap-3 flex-wrap">
                {itensDoMapa.length > 1 && (
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Item do mapa destino</label>
                    <select value={itemDestino || ''}
                      onChange={e => setItemDestino(Number(e.target.value))}
                      className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm">
                      {itensDoMapa.map(it => (
                        <option key={it.id} value={it.id}>{it.descricao?.slice(0, 50) || `Item ${it.id}`}</option>
                      ))}
                    </select>
                  </div>
                )}

                <button
                  onClick={importar}
                  disabled={importando || selecionados.size === 0}
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-semibold rounded-lg mt-4"
                >
                  {importando
                    ? 'Importando…'
                    : `↓ Importar ${selecionados.size} selecionado(s)`}
                </button>
                <p className="text-xs text-gray-500 mt-4">
                  Os preços serão criados como <strong>{filtros.tipo_fonte === 'II' ? 'Parâmetro II' : 'Parâmetro III'}</strong> no mapa.
                </p>
              </div>
            </div>
          )}

          {registros.length === 0 && !buscando && importacaoId && (
            <p className="mt-3 text-sm text-gray-500">Nenhum registro encontrado para os filtros informados.</p>
          )}
        </div>
      )}
    </div>
  )
}
