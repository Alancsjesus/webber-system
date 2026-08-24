import { Fragment, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function fmt(v) {
  return Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function CountCard({ label, value, sub, color }) {
  const bg = { blue: 'bg-blue-600', green: 'bg-green-600', amber: 'bg-amber-500', purple: 'bg-purple-600', teal: 'bg-teal-600', red: 'bg-red-500' }
  return (
    <div className={`rounded-xl p-5 text-white ${bg[color]}`}>
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

function BarraExecucao({ indicado, empenhado, liquidado, pago }) {
  const total = Number(indicado) || 0
  if (total === 0) return <p className="text-xs text-gray-400">Sem indicação.</p>
  const pctPago = Math.min(100, (Number(pago) / total) * 100)
  const pctLiq  = Math.min(100 - pctPago, (Number(liquidado) / total) * 100)
  const pctEmp  = Math.min(100 - pctPago - pctLiq, (Number(empenhado) / total) * 100)
  return (
    <div className="min-w-[160px]">
      <div className="flex h-2 rounded-full overflow-hidden bg-gray-100">
        <div style={{ width: `${pctPago}%` }} className="bg-teal-500" title={`Pago: ${fmt(pago)}`} />
        <div style={{ width: `${pctLiq}%` }} className="bg-purple-500" title={`Liquidado: ${fmt(liquidado)}`} />
        <div style={{ width: `${pctEmp}%` }} className="bg-blue-500" title={`Empenhado: ${fmt(empenhado)}`} />
      </div>
    </div>
  )
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Orçamento',
  descricao: 'Visão de gerenciamento do recurso orçamentário: quanto já foi aplicado (por Fonte, com o estágio de execução) e quanto ainda falta indicar para as Necessidades já aprovadas (por Área de Aplicação e Órgão Executor).',
  acoes: [
    { label: 'Aplicação de Recursos', texto: 'Cards de totais e tabela por Fonte de Recurso, mostrando Indicado/Empenhado/Liquidado/Pago/Saldo de todas as Indicações Orçamentárias do órgão.' },
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
        <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Aplicação de Recursos</p>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-5">
          <CountCard label="Indicado" value={fmt(aplicacao.totais.indicado)} color="blue" />
          <CountCard label="Empenhado" value={fmt(aplicacao.totais.empenhado)} color="blue" />
          <CountCard label="Liquidado" value={fmt(aplicacao.totais.liquidado)} color="purple" />
          <CountCard label="Pago" value={fmt(aplicacao.totais.pago)} color="teal" />
          <CountCard label="Saldo" value={fmt(aplicacao.totais.saldo)} color="amber" />
        </div>

        {aplicacao.por_fonte.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma indicação ativa encontrada.</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[820px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Fonte de Recurso</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Itens</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Execução</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Indicado</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Pago</th>
                    <th className="text-right px-4 py-2 font-medium text-gray-500">Saldo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {aplicacao.por_fonte.map((g, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-700">{g.fonte_codigo} — {g.fonte_nome}</td>
                      <td className="px-4 py-2 text-right text-gray-500">{g.qtd_itens}</td>
                      <td className="px-4 py-2"><BarraExecucao {...g} /></td>
                      <td className="px-4 py-2 text-right font-semibold text-gray-800">{fmt(g.indicado)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-teal-700">{fmt(g.pago)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-amber-700">{fmt(g.saldo)}</td>
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
        <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Necessidades Pendentes de Indicação</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-5">
          <CountCard label="Necessidades" value={pendentes.totais.qtd} sub="ainda sem cobertura total" color="red" />
          <CountCard label="Valor Estimado" value={fmt(pendentes.totais.valor_estimado)} color="amber" />
          <CountCard label="Sem Cobertura" value={fmt(pendentes.totais.valor_pendente)} color="red" />
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
                      <td className="px-4 py-2 text-right text-gray-500">{g.qtd}</td>
                      <td className="px-4 py-2 text-right text-gray-700">{fmt(g.valor_estimado)}</td>
                      <td className="px-4 py-2 text-right text-gray-500">{fmt(g.valor_indicado)}</td>
                      <td className="px-4 py-2 text-right font-semibold text-red-600">{fmt(g.valor_pendente)}</td>
                    </tr>
                    {expandedArea === g.area && (
                      <tr>
                        <td colSpan={5} className="px-4 py-0 bg-gray-50">
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
                                  <td className="py-1.5 text-right font-semibold text-red-600">{fmt(n.valor_pendente)}</td>
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
