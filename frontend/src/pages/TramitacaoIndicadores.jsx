import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export const pageHelp = {
  titulo: 'Indicadores de Tramitação',
  descricao: 'Onde estão os gargalos: tempo médio de permanência na etapa/fase atual de cada processo, por setor e por etapa (DFD/ETP/TR/Procedimento), a partir dos mesmos dados do Painel Gerencial de Tramitação. "Crítico" e "Em atenção" usam limiares configuráveis (Parâmetros do Sistema: tramitacao_dias_atencao/tramitacao_dias_critico — padrão 15/30 dias).',
  acoes: [
    { label: 'Cards de topo', texto: 'Visão geral: total de processos abertos, quantos estão críticos/em atenção, tempo médio geral e qual etapa concentra o maior tempo médio.' },
    { label: 'Por setor / Por etapa', texto: 'Tabelas ordenadas do maior para o menor tempo médio — o topo de cada uma é onde vale investigar primeiro.' },
    { label: 'Processos mais parados', texto: 'Os 10 processos com mais dias na fase atual, com link direto para abrir o registro (quando não é um item manual).' },
  ],
}

const ROTA_ETAPA = {
  DFD: (id) => `/demanda/dfd/${id}`,
  ETP: (id) => `/etp/etps/${id}`,
  TR: (id) => `/analise-tecnica/trs/${id}`,
  Procedimento: (id) => `/licitacao/${id}`,
}

function CountCard({ label, value, sub, color }) {
  const bg = { blue: 'bg-blue-600', red: 'bg-red-600', amber: 'bg-amber-500', slate: 'bg-slate-600' }
  return (
    <div className={`rounded-xl p-5 text-white ${bg[color]}`}>
      <p className="text-xs font-semibold uppercase opacity-80 mb-1">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
      {sub && <p className="text-xs opacity-70 mt-1">{sub}</p>}
    </div>
  )
}

function Selo({ classificacao }) {
  if (classificacao === 'critico') {
    return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-700">Crítico</span>
  }
  if (classificacao === 'atencao') {
    return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Atenção</span>
  }
  return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">Normal</span>
}

function BarraTempo({ valor, max }) {
  if (!valor) return <span className="text-xs text-gray-400">—</span>
  const pct = max > 0 ? Math.min(100, (valor / max) * 100) : 0
  const cor = valor >= 30 ? 'bg-red-500' : valor >= 15 ? 'bg-amber-400' : 'bg-green-500'
  return (
    <div className="flex items-center gap-2 min-w-[120px]">
      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
        <div style={{ width: `${pct}%` }} className={`h-full ${cor}`} />
      </div>
      <span className="text-xs text-gray-600 tabular-nums w-12 text-right">{valor}d</span>
    </div>
  )
}

export default function TramitacaoIndicadores() {
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/tramitacao/indicadores/')
      .then(({ data }) => setDados(data))
      .catch(() => setError('Não foi possível carregar os indicadores de tramitação.'))
      .finally(() => setLoading(false))
  }, [])

  const maxSetor = Math.max(1, ...(dados?.por_setor ?? []).map((g) => g.tempo_medio || 0))
  const maxEtapa = Math.max(1, ...(dados?.por_etapa ?? []).map((g) => g.tempo_medio || 0))

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-6 flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Indicadores de Tramitação</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Tempo de permanência na etapa atual — onde estão os gargalos, por setor e por etapa.
          </p>
        </div>
        <Link to="/tramitacao" className="text-sm text-blue-600 hover:underline">← Voltar ao Painel Gerencial</Link>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && dados && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <CountCard label="Processos abertos" value={dados.total_processos} color="blue" />
            <CountCard label="Críticos" value={dados.processos_criticos}
              sub={`≥ ${dados.limiar_dias_critico} dias parado`} color="red" />
            <CountCard label="Em atenção" value={dados.processos_atencao}
              sub={`≥ ${dados.limiar_dias_atencao} dias parado`} color="amber" />
            <CountCard label="Tempo médio geral" value={dados.tempo_medio_geral != null ? `${dados.tempo_medio_geral}d` : '—'}
              sub={dados.etapa_maior_tempo_medio ? `Maior em: ${dados.etapa_maior_tempo_medio}` : undefined} color="slate" />
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                <h2 className="text-sm font-bold text-gray-700">Tempo médio por setor</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400">
                    <th className="py-2 px-5 font-medium">Setor</th>
                    <th className="py-2 px-5 font-medium">Total</th>
                    <th className="py-2 px-5 font-medium">Tempo médio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dados.por_setor.map((g) => (
                    <tr key={g.setor}>
                      <td className="py-2 px-5 text-gray-700">{g.setor}</td>
                      <td className="py-2 px-5 text-gray-500">
                        {g.total}
                        {g.criticos > 0 && <span className="ml-1 text-red-600">({g.criticos} crít.)</span>}
                      </td>
                      <td className="py-2 px-5"><BarraTempo valor={g.tempo_medio} max={maxSetor} /></td>
                    </tr>
                  ))}
                  {dados.por_setor.length === 0 && (
                    <tr><td colSpan={3} className="py-4 px-5 text-center text-gray-400">Nenhum processo em tramitação.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                <h2 className="text-sm font-bold text-gray-700">Tempo médio por etapa</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400">
                    <th className="py-2 px-5 font-medium">Etapa</th>
                    <th className="py-2 px-5 font-medium">Total</th>
                    <th className="py-2 px-5 font-medium">Tempo médio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dados.por_etapa.map((g) => (
                    <tr key={g.etapa}>
                      <td className="py-2 px-5 text-gray-700">{g.etapa}</td>
                      <td className="py-2 px-5 text-gray-500">
                        {g.total}
                        {g.criticos > 0 && <span className="ml-1 text-red-600">({g.criticos} crít.)</span>}
                      </td>
                      <td className="py-2 px-5"><BarraTempo valor={g.tempo_medio} max={maxEtapa} /></td>
                    </tr>
                  ))}
                  {dados.por_etapa.length === 0 && (
                    <tr><td colSpan={3} className="py-4 px-5 text-center text-gray-400">Nenhum processo em tramitação.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
              <h2 className="text-sm font-bold text-gray-700">Processos mais parados</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[720px]">
                <thead>
                  <tr className="text-left text-gray-400">
                    <th className="py-2 px-5 font-medium">Processo SEI</th>
                    <th className="py-2 px-5 font-medium">Objeto</th>
                    <th className="py-2 px-5 font-medium">Setor</th>
                    <th className="py-2 px-5 font-medium">Fase</th>
                    <th className="py-2 px-5 font-medium">Dias parado</th>
                    <th className="py-2 px-5 font-medium"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {dados.top_criticos.map((p, i) => (
                    <tr key={`${p.numero_sei}-${i}`}>
                      <td className="py-2 px-5 font-mono text-xs">{p.numero_sei}</td>
                      <td className="py-2 px-5 text-gray-700">{p.objeto}</td>
                      <td className="py-2 px-5 text-gray-500">{p.setor}</td>
                      <td className="py-2 px-5 text-gray-500">{p.fase_atual || '—'}</td>
                      <td className="py-2 px-5">
                        <span className="tabular-nums font-semibold text-gray-700 mr-2">{p.dias_na_fase}d</span>
                        <Selo classificacao={p.dias_na_fase >= dados.limiar_dias_critico ? 'critico'
                          : p.dias_na_fase >= dados.limiar_dias_atencao ? 'atencao' : 'normal'} />
                      </td>
                      <td className="py-2 px-5 text-right">
                        {p.etapa_atual && p.etapa_registro_id && ROTA_ETAPA[p.etapa_atual] && (
                          <Link to={ROTA_ETAPA[p.etapa_atual](p.etapa_registro_id)} className="text-xs text-blue-600 hover:underline">
                            Ver
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                  {dados.top_criticos.length === 0 && (
                    <tr><td colSpan={6} className="py-4 px-5 text-center text-gray-400">Nenhum processo com data de referência para calcular tempo parado.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
