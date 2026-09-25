import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import StatTile from '../components/viz/StatTile'
import EtapasBar from '../components/viz/EtapasBar'
import DistribuicaoBar, { corStatusDoc } from '../components/viz/DistribuicaoBar'
import { ETAPA, STATUS, fmtPct } from '../components/viz/tokens'

const STATUS_CONTRATO_OPTS = [
  { value: 'Vigente',    label: 'Vigente' },
  { value: 'Suspenso',   label: 'Suspenso' },
  { value: 'Encerrado',  label: 'Encerrado' },
  { value: 'Rescindido', label: 'Rescindido' },
]
const STATUS_CONTRATO_CLS = {
  Vigente:    'bg-green-100 text-green-700',
  Suspenso:   'bg-yellow-100 text-yellow-700',
  Encerrado:  'bg-gray-100 text-gray-500',
  Rescindido: 'bg-red-100 text-red-600',
}
const NOTIF_STATUS_CLS = {
  andamento: 'bg-blue-100 text-blue-700',
  cpa:       'bg-amber-100 text-amber-700',
  concluido: 'bg-green-100 text-green-700',
}
const ACAO_CLS = {
  notificacao: 'bg-gray-100 text-gray-600',
  rescisao:    'bg-red-100 text-red-600',
}

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtDate = (v) => v ? new Date(v + 'T00:00').toLocaleDateString('pt-BR') : '—'

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Contratos',
  descricao: 'Visão gerencial e de controle rápido da área de Contratos: quantos existem por status, valores contratados/medidos/pagos, contratos vencendo em breve, e como as Notificações Contratuais se distribuem entre eles.',
  acoes: [
    { label: 'Filtros',              texto: 'Exercício e Status restringem quais contratos entram no painel — os totais e a tabela por contrato são recalculados sobre esse recorte.' },
    { label: 'Vencendo em Breve',    texto: 'Contratos Vigentes cuja vigência termina nos próximos 60 dias, ordenados pelo mais urgente.' },
    { label: 'Por Contrato',         texto: 'Cruza cada contrato com o saldo a pagar e a contagem de notificações — contratos com notificações em CPA aparecem primeiro, por exigirem mais atenção.' },
    { label: 'Notificações Recentes', texto: 'Últimos 15 lançamentos (notificação ou rescisão) entre todos os contratos do recorte. Para o histórico completo ou para criar uma nova, use a tela de Notificações.' },
  ],
  dica: 'Para o controle detalhado de uma notificação específica (editar status, ver todos os campos), use a tela "Notificações" ou a aba "Notificações" dentro do contrato.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PainelContratos() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filtros, setFiltros] = useState({ exercicio: '', status: '' })

  const load = () => {
    setLoading(true); setError(null)
    const params = {}
    for (const [k, v] of Object.entries(filtros)) if (v !== '') params[k] = v
    api.get('/contratos/painel/', { params })
      .then(({ data }) => setDados(data))
      .catch(() => setError('Erro ao carregar o painel de contratos.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const tc = dados?.totais_contratos
  const tn = dados?.totais_notificacoes
  const vencendo = dados?.vencendo_em_breve ?? []
  const porContrato = dados?.por_contrato ?? []
  const timeline = dados?.timeline_notificacoes ?? []

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Painel de Contratos</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Visão gerencial e de controle rápido: contratos por status, valores, vencimentos e notificações.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mb-6 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" value={filtros.exercicio} onChange={(e) => setFiltros((p) => ({ ...p, exercicio: e.target.value }))}
            className="w-28 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status do Contrato</label>
          <select value={filtros.status} onChange={(e) => setFiltros((p) => ({ ...p, status: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos</option>
            {STATUS_CONTRATO_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button onClick={load}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Atualizar
        </button>
        <Link to="/contratos/notificacoes" className="text-sm text-blue-600 hover:underline ml-auto">
          Ver todas as notificações →
        </Link>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && tc && (
        <>
          {/* Contratos por status + financeiro (Contratado ⊇ Medido ⊇ Pago) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-4">
            <StatTile label="Contratos" value={tc.total} sub={`${tc.Vigente || 0} vigente(s)`}>
              <DistribuicaoBar itens={['Vigente', 'Suspenso', 'Encerrado', 'Rescindido'].map((st) => ({
                label: st, valor: tc[st] || 0, cor: corStatusDoc(st),
              }))} />
            </StatTile>
            <div className="lg:col-span-2 bg-white border border-gray-200 rounded-xl p-4">
              <div className="flex items-baseline justify-between flex-wrap gap-2 mb-3">
                <p className="text-xs font-medium text-gray-500">Execução financeira do valor contratado</p>
                <p className="text-xs text-gray-500">Contratado <b className="text-gray-900">{fmt(tc.valor_total_contratado)}</b></p>
              </div>
              <EtapasBar base={tc.valor_total_contratado}
                etapas={[{ label: 'Pago', valor: tc.valor_pago_total }, { label: 'Medido, a pagar', valor: tc.valor_medido_total }]}
                resto="A medir" />
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <StatTile label="Valor contratado" value={fmt(tc.valor_total_contratado)} />
            <StatTile label="Valor medido" value={fmt(tc.valor_medido_total)} sub={`${fmtPct(tc.valor_medido_total, tc.valor_total_contratado)} do contratado`} />
            <StatTile label="Valor pago" value={fmt(tc.valor_pago_total)} sub={`${fmtPct(tc.valor_pago_total, tc.valor_total_contratado)} do contratado`} />
            <StatTile label="Medido, a pagar" value={fmt(tc.saldo_a_pagar_total)} sub="medido − pago (aguardando pagamento)" />
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
            {/* Vencendo em breve */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Vencendo em Breve (60 dias)</h2>
              {vencendo.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhum contrato vigente vence nos próximos 60 dias.</p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <ul className="divide-y divide-gray-100">
                    {vencendo.map((v) => (
                      <li key={v.contrato_id} className="px-4 py-2.5 flex items-center justify-between hover:bg-gray-50">
                        <div>
                          <Link to={`/contratos/${v.contrato_id}`} className="font-mono text-sm text-blue-600 hover:underline">{v.numero}</Link>
                          {v.fornecedor_nome && <span className="text-xs text-gray-400 ml-2">{v.fornecedor_nome}</span>}
                        </div>
                        <div className="text-right">
                          <span className={`text-xs font-semibold ${v.dias_restantes <= 15 ? 'text-red-600' : v.dias_restantes <= 30 ? 'text-amber-600' : 'text-gray-500'}`}>
                            {v.dias_restantes} dia(s)
                          </span>
                          <p className="text-[11px] text-gray-400">{fmtDate(v.data_vigencia_fim)}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Notificações — resumo */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Notificações Contratuais</h2>
              <div className="bg-white border border-gray-200 rounded-xl p-4 mb-3">
                <DistribuicaoBar vazio="Nenhuma notificação no recorte." itens={[
                  { label: 'Em andamento', valor: tn?.andamento || 0, cor: ETAPA[1] },
                  { label: 'Em CPA', valor: tn?.cpa || 0, cor: STATUS.atencao },
                  { label: 'Concluído', valor: tn?.concluido || 0, cor: STATUS.bom },
                ]} />
              </div>
              <p className="text-xs text-gray-500">
                {tn?.total || 0} lançamento(s) no total ({tn?.notificacoes || 0} notificações, {tn?.rescisoes || 0} rescisões),
                afetando {tn?.contratos_afetados || 0} contrato(s).
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Por Contrato */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Por Contrato</h2>
              {porContrato.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhum contrato encontrado para os filtros selecionados.</p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                    <table className="w-full text-xs min-w-[560px]">
                      <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
                        <tr>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Contrato</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Status</th>
                          <th className="text-right px-3 py-2 font-medium text-gray-500" title="Medido − pago">Medido, a pagar</th>
                          <th className="text-left px-3 py-2 font-medium text-gray-500">Notificações</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {porContrato.map((g) => (
                          <tr key={g.contrato_id} className="hover:bg-gray-50">
                            <td className="px-3 py-2">
                              <Link to={`/contratos/${g.contrato_id}`} className="font-mono text-blue-600 hover:underline" title={g.objeto}>
                                {g.numero}
                              </Link>
                              {g.fornecedor_nome && <p className="text-[11px] text-gray-400 truncate max-w-[160px]">{g.fornecedor_nome}</p>}
                            </td>
                            <td className="px-3 py-2">
                              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${STATUS_CONTRATO_CLS[g.status] || 'bg-gray-100 text-gray-600'}`}>{g.status}</span>
                            </td>
                            <td className="px-3 py-2 text-right font-semibold text-gray-700">{fmt(g.saldo_a_pagar)}</td>
                            <td className="px-3 py-2">
                              {g.notificacoes_total === 0 ? <span className="text-gray-300">—</span> : (
                                <div className="flex gap-1 flex-wrap">
                                  {g.notificacoes_andamento > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${NOTIF_STATUS_CLS.andamento}`}>{g.notificacoes_andamento}</span>}
                                  {g.notificacoes_cpa > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${NOTIF_STATUS_CLS.cpa}`}>{g.notificacoes_cpa} CPA</span>}
                                  {g.notificacoes_concluido > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${NOTIF_STATUS_CLS.concluido}`}>{g.notificacoes_concluido}</span>}
                                  {g.rescisoes_total > 0 && <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${ACAO_CLS.rescisao}`}>{g.rescisoes_total} rescisão</span>}
                                </div>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Notificações recentes */}
            <div>
              <h2 className="text-sm font-semibold text-gray-700 mb-3">Notificações Recentes</h2>
              {timeline.length === 0 ? (
                <p className="text-sm text-gray-400">Nenhuma notificação registrada para os filtros selecionados.</p>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-4 max-h-[500px] overflow-y-auto">
                  <ol className="relative border-l-2 border-gray-100 space-y-4 pl-4">
                    {timeline.map((t) => (
                      <li key={t.id} className="relative">
                        <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-blue-500 ring-4 ring-white" />
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono text-gray-500">{fmtDate(t.data)}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${ACAO_CLS[t.tipo_acao] || 'bg-gray-100 text-gray-600'}`}>{t.tipo_acao_display}</span>
                          <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${NOTIF_STATUS_CLS[t.status] || 'bg-gray-100 text-gray-600'}`}>{t.status_display}</span>
                          <Link to={`/contratos/${t.contrato_id}`} className="text-xs font-mono text-blue-600 hover:underline">{t.contrato_numero}</Link>
                        </div>
                        <p className="text-sm text-gray-800 mt-0.5">{t.resumo_fato}</p>
                        {t.fornecedor_nome && <p className="text-xs text-gray-400 mt-0.5">{t.fornecedor_nome}</p>}
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
