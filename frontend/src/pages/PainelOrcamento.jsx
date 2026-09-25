import { Fragment, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import StatTile from '../components/viz/StatTile'
import EtapasBar, { EtapasLegenda } from '../components/viz/EtapasBar'
import { fmtBRL as fmt, fmtPct } from '../components/viz/tokens'

// Etapas acumulativas da despesa (Lei 4.320/64): cada uma contém a seguinte.
const etapasDespesa = (g) => [
  { label: 'Pago', valor: g.pago },
  { label: 'Liquidado, a pagar', valor: g.liquidado },
  { label: 'Empenhado, a liquidar', valor: g.empenhado },
]
const RESTO_DESPESA = 'Indicado, a empenhar'

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Orçamento',
  descricao: 'Visão de gerenciamento do recurso orçamentário: quanto já foi aplicado (por Fonte, com o estágio de execução) e quanto ainda falta indicar para as Necessidades já aprovadas (por Área de Aplicação e Órgão Executor).',
  acoes: [
    { label: 'Aplicação de Recursos', texto: 'Totais e tabela por Fonte de Recurso. A barra de execução mostra, dentro do valor indicado, quanto já foi pago, quanto está liquidado aguardando pagamento, quanto está empenhado aguardando liquidação e quanto ainda falta empenhar — os quatro trechos somam o indicado. O percentual ao lado é o executado (pago ÷ indicado).' },
    { label: 'Necessidades Pendentes de Indicação', texto: 'Necessidades já aprovadas (ou com DFD criado) cujo valor estimado ainda não está totalmente coberto por indicações ativas — agrupadas por Área de Aplicação.' },
    { label: 'Expandir área', texto: 'Clique numa área para ver a lista de necessidades individuais daquele grupo, com valor pendente de cada uma.' },
  ],
  dica: 'Uma necessidade some do bloco de pendentes assim que o total indicado contra ela cobrir o valor estimado.',
  baseLegal: 'Lei 14.133/2021 — Art. 7º (indicação orçamentária) e Art. 12 (planejamento das contratações).',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PainelOrcamento() {
  const navigate = useNavigate()
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedArea, setExpandedArea] = useState(null)

  useEffect(() => {
    api.get('/orcamento/painel/')
      .then(({ data }) => setDados(data))
      .catch(() => setError('Erro ao carregar o painel de orçamento.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando painel..." /></div>
  if (error) return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!dados) return null

  const { aplicacao, pendentes } = dados

  return (
    <div className="p-6 lg:p-8 space-y-10">
      <div>
        <h1 className="text-xl font-bold text-gray-800">Painel de Orçamento</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Quanto já está aplicado, em que estágio, e quais necessidades aprovadas ainda não têm cobertura orçamentária.
        </p>
      </div>

      {/* ── Aplicação de Recursos ── */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Aplicação de recursos</h2>
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
          <StatTile label="Indicado" value={fmt(aplicacao.totais.indicado)} sub="base da execução" />
          <StatTile label="Empenhado" value={fmt(aplicacao.totais.empenhado)} sub={`${fmtPct(aplicacao.totais.empenhado, aplicacao.totais.indicado)} do indicado`} />
          <StatTile label="Liquidado" value={fmt(aplicacao.totais.liquidado)} sub={`${fmtPct(aplicacao.totais.liquidado, aplicacao.totais.indicado)} do indicado`} />
          <StatTile label="Pago" value={fmt(aplicacao.totais.pago)} sub={`${fmtPct(aplicacao.totais.pago, aplicacao.totais.indicado)} do indicado`} />
          <StatTile label="Saldo a pagar" value={fmt(aplicacao.totais.saldo)} sub="indicado − pago" />
        </div>

        {Number(aplicacao.totais.indicado) > 0 && (
          <div className="bg-white border border-gray-200 rounded-xl p-5 mb-4">
            <p className="text-xs font-medium text-gray-500 mb-3">Execução do total indicado</p>
            <EtapasBar base={aplicacao.totais.indicado} etapas={etapasDespesa(aplicacao.totais)} resto={RESTO_DESPESA} />
          </div>
        )}

        {aplicacao.por_fonte.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma indicação ativa encontrada.</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between flex-wrap gap-2 px-4 py-3 border-b border-gray-100">
              <p className="text-sm font-medium text-gray-700">Por fonte de recurso</p>
              <EtapasLegenda etapas={etapasDespesa({})} resto={RESTO_DESPESA} />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[820px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Fonte de Recurso</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Itens</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Execução <span className="font-normal text-gray-400">(% pago)</span></th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Indicado</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Pago</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Saldo a pagar</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[...aplicacao.por_fonte].sort((a, b) => Number(b.indicado) - Number(a.indicado)).map((g, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 text-gray-700">{g.fonte_codigo} — {g.fonte_nome}</td>
                      <td className="px-4 py-2.5 text-right text-gray-500 tabular-nums">{g.qtd_itens}</td>
                      <td className="px-4 py-2.5"><EtapasBar compacto base={g.indicado} etapas={etapasDespesa(g)} resto={RESTO_DESPESA} /></td>
                      <td className="px-4 py-2.5 text-right font-semibold text-gray-800 tabular-nums">{fmt(g.indicado)}</td>
                      <td className="px-4 py-2.5 text-right text-gray-700 tabular-nums">{fmt(g.pago)}</td>
                      <td className="px-4 py-2.5 text-right text-gray-700 tabular-nums">{fmt(g.saldo)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* ── Necessidades Pendentes de Indicação ── */}
      <section>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Necessidades pendentes de indicação</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <StatTile label="Necessidades sem cobertura total" value={pendentes.totais.qtd}
            tom={pendentes.totais.qtd > 0 ? 'atencao' : 'bom'}
            sub={pendentes.totais.qtd > 0 ? 'aprovadas, aguardando indicação' : 'todas cobertas'} />
          <StatTile label="Valor estimado" value={fmt(pendentes.totais.valor_estimado)} sub="dessas necessidades" />
          <StatTile label="Sem cobertura orçamentária" value={fmt(pendentes.totais.valor_pendente)}
            tom={Number(pendentes.totais.valor_pendente) > 0 ? 'critico' : 'bom'}
            sub={`${fmtPct(pendentes.totais.valor_pendente, pendentes.totais.valor_estimado)} do estimado`} />
        </div>

        {pendentes.por_area.length === 0 ? (
          <p className="text-sm text-gray-400">Todas as necessidades aprovadas já têm cobertura orçamentária completa.</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-2 font-medium text-gray-500">Área de Aplicação</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-500">Necessidades</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-500">Cobertura <span className="font-normal text-gray-400">(% indicado)</span></th>
                  <th className="text-right px-4 py-2 font-medium text-gray-500">Valor Estimado</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-500">Indicado</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-500">Sem Cobertura</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {pendentes.por_area.map((g) => (
                  <Fragment key={g.area}>
                    <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpandedArea(expandedArea === g.area ? null : g.area)}>
                      <td className="px-4 py-2 text-gray-700 font-medium">
                        <span className="text-gray-400 mr-1">{expandedArea === g.area ? '▾' : '▸'}</span>
                        {g.area_label}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-500 tabular-nums">{g.qtd}</td>
                      <td className="px-4 py-2 w-56">
                        <EtapasBar compacto base={g.valor_estimado} etapas={[{ label: 'Indicado', valor: g.valor_indicado }]} resto="Sem cobertura" />
                      </td>
                      <td className="px-4 py-2 text-right text-gray-700">{fmt(g.valor_estimado)}</td>
                      <td className="px-4 py-2 text-right text-gray-500">{fmt(g.valor_indicado)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-gray-900 tabular-nums">{fmt(g.valor_pendente)}</td>
                    </tr>
                    {expandedArea === g.area && (
                      <tr>
                        <td colSpan={6} className="px-4 py-0 bg-gray-50">
                          <table className="w-full text-xs my-2">
                            <thead>
                              <tr className="text-gray-400">
                                <th className="text-left py-1.5 font-medium">Necessidade</th>
                                <th className="text-left py-1.5 font-medium">Órgão Executor</th>
                                <th className="text-right py-1.5 font-medium">Estimado</th>
                                <th className="text-right py-1.5 font-medium">Indicado</th>
                                <th className="text-right py-1.5 font-medium">Pendente</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {g.necessidades.map((n) => (
                                <tr key={n.id} className="hover:bg-gray-100 cursor-pointer" onClick={() => navigate(`/planejamento/necessidades/${n.id}`)}>
                                  <td className="py-1.5 text-gray-700">
                                    {n.titulo}
                                    {n.dfd_numero_sei && <span className="ml-1.5 font-mono text-gray-400">({n.dfd_numero_sei})</span>}
                                  </td>
                                  <td className="py-1.5 text-gray-500">{n.orgao_executor_sigla || '—'}</td>
                                  <td className="py-1.5 text-right text-gray-600">{fmt(n.valor_estimado)}</td>
                                  <td className="py-1.5 text-right text-gray-500">{fmt(n.valor_indicado)}</td>
                                  <td className="py-1.5 text-right font-semibold text-gray-900">{fmt(n.valor_pendente)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
