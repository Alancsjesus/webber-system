import { useEffect, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function fmt(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

function CountCard({ label, value, sub, color }) {
  const bg = { blue: 'bg-blue-600', green: 'bg-green-600', amber: 'bg-amber-500' }
  return (
    <div className={`rounded-xl p-5 text-white ${bg[color]}`}>
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

function BarraExecucao({ pendentes, executados }) {
  const total = pendentes + executados
  if (total === 0) return <p className="text-xs text-gray-400">Sem itens.</p>
  const pctExec = (executados / total) * 100
  return (
    <div>
      <div className="flex h-2 rounded-full overflow-hidden gap-px bg-gray-100">
        <div style={{ width: `${100 - pctExec}%` }} className="bg-amber-400" title={`Pendente: ${pendentes}`} />
        <div style={{ width: `${pctExec}%` }} className="bg-green-500" title={`Executado: ${executados}`} />
      </div>
      <div className="flex gap-3 mt-1.5 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-amber-400" />Pendente: {pendentes}</span>
        <span className="flex items-center gap-1"><span className="inline-block w-2 h-2 rounded-full bg-green-500" />Executado: {executados}</span>
      </div>
    </div>
  )
}

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Painel de Execução — Plano de Aplicação',
  descricao: 'Mostra a evolução da execução dos itens de Planos de Aplicação, agrupados por órgão beneficiário/exercício/eixo. "Executado" significa que o DFD gerado pela necessidade do item já tem pelo menos um Contrato (qualquer status).',
  acoes: [
    { label: 'Filtros (exercício, eixo)', texto: 'Restringe os grupos exibidos. Sem filtro, mostra todos os grupos com itens.' },
    { label: 'Barra de execução',         texto: 'Proporção visual de itens pendentes (âmbar) vs. executados (verde) dentro de cada grupo.' },
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
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <CountCard label="Itens Pendentes" value={totais.pendentes} color="amber" />
            <CountCard label="Itens Executados" value={totais.executados} color="green" />
            <CountCard label="Valor Pendente" value={fmt(totais.valor_pendente)} color="blue" />
            <CountCard label="Valor Executado" value={fmt(totais.valor_executado)} color="green" />
          </div>

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
                        <td className="px-5 py-3 w-48"><BarraExecucao pendentes={g.pendentes} executados={g.executados} /></td>
                        <td className="px-5 py-3 text-right text-gray-700">{fmt(g.valor_pendente)}</td>
                        <td className="px-5 py-3 text-right font-semibold text-green-700">{fmt(g.valor_executado)}</td>
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
