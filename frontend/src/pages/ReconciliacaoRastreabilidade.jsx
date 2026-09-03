import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const fmt  = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtQ = (v) => Number(v ?? 0).toLocaleString('pt-BR', { maximumFractionDigits: 4 })

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Reconciliação de Rastreabilidade',
  descricao: 'Audita ativamente o saldo/vínculo de itens do DFD para achar duas classes de risco que nenhuma tela isolada mostra: pedidos possivelmente duplicados e comprometimentos "mortos" (presos num Procedimento revogado/anulado).',
  acoes: [
    { label: 'Duplicidade sem vínculo', texto: 'Mesmo item de catálogo + mesma unidade demandante aparecendo em 2 ou mais DFDs ativos, sem que um tenha sido registrado como origem de um agrupamento do outro. Pode ser um pedido de compra repetido que deveria ter sido consolidado.' },
    { label: 'Itens órfãos', texto: 'Item com quantidade comprometida num lote de TR cujo(s) Procedimento(s) foram todos Revogados/Anulados — nada libera esse saldo automaticamente, então o item fica "preso", sem aparecer como pendência em nenhuma outra tela.' },
  ],
  dica: 'Esta tela não corrige nada automaticamente — cada achado exige julgamento (agrupar os DFDs? reabrir o TR e remover o item do lote morto?). Use como ponto de partida para investigação, não como ação automática.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function ReconciliacaoRastreabilidade() {
  const [dados,   setDados]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [erro,    setErro]    = useState(null)

  const load = async () => {
    setLoading(true); setErro(null)
    try {
      const { data } = await api.get('/indicadores/reconciliacao/')
      setDados(data)
    } catch {
      setErro('Não foi possível carregar a reconciliação. Tente novamente.')
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Reconciliação de Rastreabilidade</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Duplicidade de pedidos e comprometimentos órfãos — checagens que nenhuma tela isolada mostra.
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>

      {loading ? <LoadingSpinner /> : erro ? (
        <p className="text-sm text-red-500">{erro}</p>
      ) : !dados ? null : (
        <>
          {/* Cards de resumo */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'Grupos duplicados', value: dados.resumo.total_grupos_duplicados, cls: 'text-amber-700' },
              { label: 'Valor em risco (duplicidade)', value: fmt(dados.resumo.valor_total_duplicados), cls: 'text-amber-700' },
              { label: 'Itens órfãos', value: dados.resumo.total_itens_orfaos, cls: 'text-red-700' },
              { label: 'Valor comprometido órfão', value: fmt(dados.resumo.valor_total_orfaos), cls: 'text-red-700' },
            ].map(({ label, value, cls }) => (
              <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
                <p className={`text-lg font-bold ${cls}`}>{value}</p>
              </div>
            ))}
          </div>

          {dados.resumo.total_grupos_duplicados === 0 && dados.resumo.total_itens_orfaos === 0 && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800 mb-6">
              Nenhuma duplicidade nem item órfão encontrado nesta checagem.
            </div>
          )}

          {/* Duplicidade */}
          {dados.duplicados.length > 0 && (
            <div className="mb-8">
              <h2 className="text-sm font-bold text-gray-700 mb-2">
                Possível duplicidade — {dados.duplicados.length} grupo(s)
              </h2>
              <p className="text-xs text-gray-500 mb-3">
                Mesmo item de catálogo + mesma unidade demandante, presente em mais de um DFD ativo,
                sem vínculo de agrupamento registrado entre eles.
              </p>
              <div className="space-y-3">
                {dados.duplicados.map((g, i) => (
                  <div key={i} className="bg-white border border-amber-200 rounded-xl p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{g.catalogo_nome}</p>
                        <p className="text-xs text-gray-500">
                          {g.unidade_demandante || 'Unidade demandante não informada'}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-bold text-amber-700">{fmt(g.valor_total)}</p>
                        <p className="text-xs text-gray-400">{fmtQ(g.quantidade_total)} un. no total</p>
                      </div>
                    </div>
                    <table className="w-full text-xs mt-2">
                      <thead>
                        <tr className="text-left text-gray-400 border-b border-gray-100">
                          <th className="py-1 font-medium">DFD</th>
                          <th className="py-1 font-medium">Status</th>
                          <th className="py-1 font-medium">Qtd.</th>
                          <th className="py-1 font-medium">Item</th>
                        </tr>
                      </thead>
                      <tbody>
                        {g.itens.map(it => (
                          <tr key={it.item_id} className="border-b border-gray-50 last:border-0">
                            <td className="py-1">
                              <Link to={`/demanda/dfd/${it.dfd_id}`} className="text-blue-600 hover:underline">
                                {it.dfd_sei}
                              </Link>
                            </td>
                            <td className="py-1">{it.dfd_status}</td>
                            <td className="py-1">{fmtQ(it.quantidade)}</td>
                            <td className="py-1 text-gray-400">status: {it.status_execucao}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Órfãos */}
          {dados.orfaos.length > 0 && (
            <div>
              <h2 className="text-sm font-bold text-gray-700 mb-2">
                Itens órfãos — {dados.orfaos.length}
              </h2>
              <p className="text-xs text-gray-500 mb-3">
                Comprometidos num lote de TR cujo(s) Procedimento(s) foram todos Revogados/Anulados —
                o saldo não foi liberado automaticamente.
              </p>
              <div className="bg-white border border-red-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 bg-gray-50 border-b border-gray-100">
                      <th className="py-2 px-4 font-medium">Item</th>
                      <th className="py-2 px-4 font-medium">DFD</th>
                      <th className="py-2 px-4 font-medium">Qtd. comprometida</th>
                      <th className="py-2 px-4 font-medium">Valor comprometido</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.orfaos.map(o => (
                      <tr key={o.item_id} className="border-b border-gray-50 last:border-0">
                        <td className="py-2 px-4">{o.objeto}</td>
                        <td className="py-2 px-4">
                          <Link to={`/demanda/dfd/${o.dfd_id}`} className="text-blue-600 hover:underline">
                            {o.dfd_sei}
                          </Link>
                        </td>
                        <td className="py-2 px-4">{fmtQ(o.quantidade_comprometida)}</td>
                        <td className="py-2 px-4 font-medium text-red-700">{fmt(o.valor_comprometido)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
