import { useEffect, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import StatTile from '../components/viz/StatTile'
import EtapasBar from '../components/viz/EtapasBar'
import { fmtPct } from '../components/viz/tokens'

function fmt(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function BarraExecucao({ pendentes, executados }) {
  const total = pendentes + executados
  if (total === 0) return <p className="text-xs text-gray-400">Sem itens.</p>
  return (
    <div>
      <EtapasBar compacto base={total} etapas={[{ label: 'Executados', valor: executados }]} resto="Pendentes" />
      <p className="text-[11px] text-gray-500 mt-1 tabular-nums">{executados} de {total} itens executados</p>
    </div>
  )
}

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Execução — Plano de Aplicação',
  descricao: 'Mostra a evolução da execução dos itens de Planos de Aplicação, agrupados por órgão beneficiário/exercício/eixo. "Executado" significa que o DFD gerado pela necessidade do item já tem pelo menos um Contrato (qualquer status).',
  acoes: [
    { label: 'Filtros (exercício, eixo)', texto: 'Restringe os grupos exibidos. Sem filtro, mostra todos os grupos com itens.' },
    { label: 'Barra de execução',         texto: 'Parte escura = itens já executados (com contrato); trilho cinza = pendentes. O percentual é executados ÷ total de itens do grupo.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FespPainelExecucao() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [exercicio, setExercicio] = useState('')
  const [eixo, setEixo] = useState('')

  const load = () => {
    setLoading(true); setError(null)
    const params = {}
    if (exercicio) params.exercicio = exercicio
    if (eixo) params.eixo = eixo
    api.get('/fesp/indicadores/execucao/', { params })
      .then(({ data }) => setDados(data))
      .catch(() => setError('Erro ao carregar o painel de execução.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const totais = dados?.totais
  const grupos = dados?.grupos ?? []

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Painel de Execução — Planos de Aplicação</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Evolução de itens pendentes vs. já executados (contratados), por órgão beneficiário, exercício e eixo.
        </p>
      </div>

      <div className="flex flex-wrap gap-3 mb-6">
        <input type="number" placeholder="Exercício" value={exercicio}
          onChange={(e) => setExercicio(e.target.value)}
          className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
        <input type="text" placeholder="Eixo/Ementa" value={eixo}
          onChange={(e) => setEixo(e.target.value)}
          className="flex-1 min-w-[200px] border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500" />
        <button onClick={load}
          className="bg-amber-500 hover:bg-amber-600 text-white text-sm font-medium px-4 py-2 rounded-lg">
          Atualizar
        </button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && totais && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <StatTile label="Itens executados" value={totais.executados}
              sub={`${fmtPct(totais.executados, totais.executados + totais.pendentes)} dos itens`} />
            <StatTile label="Itens pendentes" value={totais.pendentes} tom={totais.pendentes > 0 ? 'atencao' : 'bom'}
              sub="sem contrato ainda" />
            <StatTile label="Valor executado" value={fmt(totais.valor_executado)}
              sub={`${fmtPct(totais.valor_executado, Number(totais.valor_executado) + Number(totais.valor_pendente))} do valor`} />
            <StatTile label="Valor pendente" value={fmt(totais.valor_pendente)} />
          </div>
          {Number(totais.valor_executado) + Number(totais.valor_pendente) > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
              <p className="text-xs font-medium text-gray-500 mb-3">Execução do valor planejado</p>
              <EtapasBar base={Number(totais.valor_executado) + Number(totais.valor_pendente)}
                etapas={[{ label: 'Executado', valor: totais.valor_executado }]} resto="Pendente" />
            </div>
          )}

          {grupos.length === 0 ? (
            <p className="text-sm text-gray-400">Nenhum item encontrado para os filtros selecionados.</p>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[820px]">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão Beneficiário</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Eixo</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Execução</th>
                      <th className="text-right px-5 py-3 font-medium text-gray-500">Valor Pendente</th>
                      <th className="text-right px-5 py-3 font-medium text-gray-500">Valor Executado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {grupos.map((g, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-5 py-3 text-gray-700">{g.org_sigla} — {g.org_nome}</td>
                        <td className="px-5 py-3 text-gray-600">{g.exercicio}</td>
                        <td className="px-5 py-3 text-gray-600">{g.eixo}</td>
                        <td className="px-5 py-3 w-56"><BarraExecucao pendentes={g.pendentes} executados={g.executados} /></td>
                        <td className="px-5 py-3 text-right text-gray-700">{fmt(g.valor_pendente)}</td>
                        <td className="px-5 py-3 text-right font-semibold text-gray-800 tabular-nums">{fmt(g.valor_executado)}</td>
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
