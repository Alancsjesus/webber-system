import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export const pageHelp = {
  titulo: 'Indicadores de Tramitação',
  descricao: 'Onde estão os gargalos: tempo médio de permanência na etapa/fase atual de cada processo, por setor e por etapa (DFD/ETP/TR/Procedimento), a partir dos mesmos dados do Painel Gerencial de Tramitação. "Crítico" e "Em atenção" usam limiares configuráveis (Parâmetros do Sistema: tramitacao_dias_atencao/tramitacao_dias_critico — padrão 15/30 dias).',
  acoes: [
    { label: 'Filtros', texto: 'Restringe a análise por setor, etapa e período (data de entrada na fase atual). Sem filtro, mostra todos os processos abertos.' },
    { label: 'Cards de topo', texto: 'Visão geral: total de processos, quantos estão críticos/em atenção, tempo médio geral e qual etapa concentra o maior tempo médio.' },
    { label: 'Gráficos por setor/etapa', texto: 'Comparação visual do tempo médio — a barra mais alta é onde vale investigar primeiro. Cor segue o mesmo limiar dos cards (verde/âmbar/vermelho).' },
    { label: 'Processos mais parados', texto: 'Os 10 processos com mais dias na fase atual, com link direto para abrir o registro (quando não é um item manual).' },
    { label: 'Duração de processos concluídos', texto: 'Mede o ciclo completo (início do Procedimento até assinatura do Contrato) de processos já concluídos, não o tempo parado dos que estão em andamento. Segmentado por modalidade, natureza do objeto e passagem por órgão externo (Casa Civil, PGE, SEFAZ) — uma média única esconderia a diferença entre uma compra simples e uma que exige mais trâmite.' },
  ],
}

const ROTA_ETAPA = {
  DFD: (id) => `/demanda/dfd/${id}`,
  ETP: (id) => `/etp/etps/${id}`,
  TR: (id) => `/analise-tecnica/trs/${id}`,
  Procedimento: (id) => `/licitacao/${id}`,
}

const ETAPA_OPCOES = [
  { value: '', label: 'Todas as etapas' },
  { value: 'DFD', label: 'DFD' },
  { value: 'ETP', label: 'ETP' },
  { value: 'TR', label: 'TR' },
  { value: 'Procedimento', label: 'Procedimento' },
  { value: 'manual', label: 'Manual (sem DFD)' },
]

const COR_NORMAL = '#22C55E'
const COR_ATENCAO = '#F59E0B'
const COR_CRITICO = '#DC2626'

function corPorTempo(tempoMedio, limiarAtencao, limiarCritico) {
  if (tempoMedio == null) return '#CBD5E1'
  if (tempoMedio >= limiarCritico) return COR_CRITICO
  if (tempoMedio >= limiarAtencao) return COR_ATENCAO
  return COR_NORMAL
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

function GraficoTempoMedio({ titulo, dados, chaveLabel, limiarAtencao, limiarCritico }) {
  const linhas = dados.map((g) => ({ nome: g[chaveLabel], tempo_medio: g.tempo_medio ?? 0, total: g.total, criticos: g.criticos }))
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h2 className="text-sm font-bold text-gray-700">{titulo}</h2>
      </div>
      {linhas.length === 0 ? (
        <p className="text-sm text-gray-400 p-5">Nenhum processo em tramitação.</p>
      ) : (
        <div style={{ width: '100%', height: Math.max(160, linhas.length * 40) }} className="py-3">
          <ResponsiveContainer>
            <BarChart data={linhas} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94A3B8' }} unit="d" />
              <YAxis type="category" dataKey="nome" width={110} tick={{ fontSize: 11, fill: '#475569' }} />
              <Tooltip
                formatter={(value, name) => [name === 'tempo_medio' ? `${value} dias` : value, name === 'tempo_medio' ? 'Tempo médio' : name]}
                labelStyle={{ color: '#334155', fontWeight: 600 }}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
              />
              <Bar dataKey="tempo_medio" radius={[0, 4, 4, 0]} maxBarSize={22}>
                {linhas.map((l, i) => (
                  <Cell key={i} fill={corPorTempo(l.tempo_medio, limiarAtencao, limiarCritico)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <table className="w-full text-sm border-t border-gray-100">
        <tbody className="divide-y divide-gray-50">
          {dados.map((g) => (
            <tr key={g[chaveLabel]}>
              <td className="py-1.5 px-5 text-gray-600 text-xs">{g[chaveLabel]}</td>
              <td className="py-1.5 px-5 text-gray-400 text-xs text-right">
                {g.total} processo{g.total !== 1 ? 's' : ''}
                {g.criticos > 0 && <span className="ml-1 text-red-600">({g.criticos} crít.)</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DonutClassificacao({ total, criticos, atencao }) {
  const normal = Math.max(0, total - criticos - atencao)
  const dados = [
    { nome: 'Normal', valor: normal, cor: COR_NORMAL },
    { nome: 'Em atenção', valor: atencao, cor: COR_ATENCAO },
    { nome: 'Crítico', valor: criticos, cor: COR_CRITICO },
  ].filter((d) => d.valor > 0)

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h2 className="text-sm font-bold text-gray-700">Distribuição por situação</h2>
      </div>
      {total === 0 ? (
        <p className="text-sm text-gray-400 p-5">Nenhum processo em tramitação.</p>
      ) : (
        <div className="flex items-center gap-4 p-4">
          <div style={{ width: 120, height: 120 }} className="shrink-0">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={dados} dataKey="valor" nameKey="nome" innerRadius={34} outerRadius={56} paddingAngle={2}>
                  {dados.map((d, i) => <Cell key={i} fill={d.cor} />)}
                </Pie>
                <Tooltip formatter={(value, name) => [`${value} processos`, name]} contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-col gap-1.5 text-sm">
            {dados.map((d) => (
              <span key={d.nome} className="flex items-center gap-2 text-gray-600">
                <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: d.cor }} />
                {d.nome}: <b className="text-gray-800">{d.valor}</b>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const COR_DURACAO = '#6366F1'

function GraficoDuracaoPorGrupo({ titulo, dados, chaveLabel }) {
  const comAmostra = dados.filter((g) => g.amostra_suficiente)
  const semAmostra = dados.filter((g) => !g.amostra_suficiente)
  const linhas = comAmostra.map((g) => ({ nome: g[chaveLabel], duracao_media: g.duracao_media, min: g.duracao_min, max: g.duracao_max, n: g.quantidade_amostra }))
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h2 className="text-sm font-bold text-gray-700">{titulo}</h2>
      </div>
      {linhas.length === 0 ? (
        <p className="text-sm text-gray-400 p-5">Ainda não há amostra suficiente (mínimo 3 processos concluídos) em nenhum grupo.</p>
      ) : (
        <div style={{ width: '100%', height: Math.max(120, linhas.length * 42) }} className="py-3">
          <ResponsiveContainer>
            <BarChart data={linhas} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94A3B8' }} unit="d" />
              <YAxis type="category" dataKey="nome" width={130} tick={{ fontSize: 11, fill: '#475569' }} />
              <Tooltip
                formatter={(value, _name, item) => [`${value}d (mín. ${item.payload.min} · máx. ${item.payload.max} · n=${item.payload.n})`, 'Duração média']}
                labelStyle={{ color: '#334155', fontWeight: 600 }}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
              />
              <Bar dataKey="duracao_media" radius={[0, 4, 4, 0]} maxBarSize={22} fill={COR_DURACAO} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      {semAmostra.length > 0 && (
        <p className="text-xs text-gray-400 px-5 py-2 border-t border-gray-100">
          Ainda sem amostra suficiente: {semAmostra.map((g) => g[chaveLabel]).join(', ')}
        </p>
      )}
    </div>
  )
}

const COR_SEM_EXTERNA = '#6366F1'
const COR_COM_EXTERNA = '#C026D3'

function GraficoDuracaoModalidadeSegmentado({ duracaoPorModalidade, impactoTramitacaoExterna }) {
  const impactoPorModalidade = Object.fromEntries(impactoTramitacaoExterna.map((g) => [g.modalidade, g]))
  const linhas = []
  const semAmostra = []
  for (const m of duracaoPorModalidade) {
    if (!m.amostra_suficiente) { semAmostra.push(m.modalidade_label); continue }
    const impacto = impactoPorModalidade[m.modalidade]
    const temSegmentacao = impacto && impacto.sem_tramitacao_externa.amostra_suficiente && impacto.com_tramitacao_externa.amostra_suficiente
    if (temSegmentacao) {
      linhas.push({ nome: `${m.modalidade_label} — sem trâmite externo`, duracao_media: impacto.sem_tramitacao_externa.duracao_media, cor: COR_SEM_EXTERNA })
      linhas.push({ nome: `${m.modalidade_label} — com trâmite externo`, duracao_media: impacto.com_tramitacao_externa.duracao_media, cor: COR_COM_EXTERNA })
    } else {
      linhas.push({ nome: m.modalidade_label, duracao_media: m.duracao_media, min: m.duracao_min, max: m.duracao_max, cor: COR_SEM_EXTERNA })
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-gray-700">Duração média por modalidade</h2>
        <div className="flex items-center gap-3 text-[10px] text-gray-500">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: COR_SEM_EXTERNA }} /> sem trâmite externo</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: COR_COM_EXTERNA }} /> com trâmite externo</span>
        </div>
      </div>
      {linhas.length === 0 ? (
        <p className="text-sm text-gray-400 p-5">Ainda não há amostra suficiente (mínimo 3 processos concluídos) em nenhuma modalidade.</p>
      ) : (
        <div style={{ width: '100%', height: Math.max(120, linhas.length * 38) }} className="py-3">
          <ResponsiveContainer>
            <BarChart data={linhas} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#94A3B8' }} unit="d" />
              <YAxis type="category" dataKey="nome" width={190} tick={{ fontSize: 11, fill: '#475569' }} />
              <Tooltip
                formatter={(value) => [`${value}d`, 'Duração média']}
                labelStyle={{ color: '#334155', fontWeight: 600 }}
                contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #E2E8F0' }}
              />
              <Bar dataKey="duracao_media" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {linhas.map((l, i) => <Cell key={i} fill={l.cor} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <p className="text-xs text-gray-400 px-5 py-2 border-t border-gray-100">
        Quando a modalidade tem amostra suficiente nos dois grupos, a média geral é substituída pelas
        duas médias separadas — misturar as duas esconderia justamente o efeito do trâmite externo.
        {semAmostra.length > 0 && ` Ainda sem amostra suficiente: ${semAmostra.join(', ')}.`}
      </p>
    </div>
  )
}

function TabelaImpactoTramitacaoExterna({ dados }) {
  const relevantes = dados.filter((g) => g.com_tramitacao_externa.amostra_suficiente || g.sem_tramitacao_externa.amostra_suficiente)
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
        <h2 className="text-sm font-bold text-gray-700">Impacto de tramitação externa (Casa Civil, PGE, SEFAZ...)</h2>
      </div>
      {relevantes.length === 0 ? (
        <p className="text-sm text-gray-400 p-5">Ainda não há amostra suficiente para comparar.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400">
              <th className="py-2 px-5 font-medium">Modalidade</th>
              <th className="py-2 px-5 font-medium text-right">Sem trâmite externo</th>
              <th className="py-2 px-5 font-medium text-right">Com trâmite externo</th>
              <th className="py-2 px-5 font-medium text-right">Impacto medido</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {relevantes.map((g) => (
              <tr key={g.modalidade}>
                <td className="py-2 px-5 text-gray-700">{g.modalidade_label}</td>
                <td className="py-2 px-5 text-right text-gray-600 tabular-nums">
                  {g.sem_tramitacao_externa.amostra_suficiente ? `${g.sem_tramitacao_externa.duracao_media}d` : '— sem amostra'}
                </td>
                <td className="py-2 px-5 text-right text-gray-600 tabular-nums">
                  {g.com_tramitacao_externa.amostra_suficiente ? `${g.com_tramitacao_externa.duracao_media}d` : '— sem amostra'}
                </td>
                <td className="py-2 px-5 text-right tabular-nums">
                  {g.impacto_dias != null ? (
                    <span className={`font-semibold ${g.impacto_dias > 0 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {g.impacto_dias > 0 ? '+' : ''}{g.impacto_dias}d
                    </span>
                  ) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default function TramitacaoIndicadores() {
  const [dados, setDados] = useState(null)
  const [setoresDisponiveis, setSetoresDisponiveis] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filtros, setFiltros] = useState({ setor: '', etapa: '', data_inicio: '', data_fim: '' })

  const carregar = (comFiltro) => {
    setLoading(true); setError(null)
    const params = {}
    if (comFiltro.setor) params.setor = comFiltro.setor
    if (comFiltro.etapa) params.etapa = comFiltro.etapa
    if (comFiltro.data_inicio) params.data_inicio = comFiltro.data_inicio
    if (comFiltro.data_fim) params.data_fim = comFiltro.data_fim
    api.get('/tramitacao/indicadores/', { params })
      .then(({ data }) => setDados(data))
      .catch(() => setError('Não foi possível carregar os indicadores de tramitação.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/tramitacao/indicadores/')
      .then(({ data }) => setSetoresDisponiveis(data.por_setor.map((g) => g.setor)))
      .catch(() => {})
    carregar(filtros)
  }, [])

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

      <div className="flex flex-wrap items-end gap-3 mb-6 bg-white border border-gray-200 rounded-xl p-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Setor</label>
          <select value={filtros.setor} onChange={(e) => setFiltros({ ...filtros, setor: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos os setores</option>
            {setoresDisponiveis.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Etapa</label>
          <select value={filtros.etapa} onChange={(e) => setFiltros({ ...filtros, etapa: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm min-w-[160px] focus:outline-none focus:ring-2 focus:ring-blue-500">
            {ETAPA_OPCOES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Entrada na fase — de</label>
          <input type="date" value={filtros.data_inicio} onChange={(e) => setFiltros({ ...filtros, data_inicio: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">até</label>
          <input type="date" value={filtros.data_fim} onChange={(e) => setFiltros({ ...filtros, data_fim: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <button onClick={() => carregar(filtros)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
          Aplicar
        </button>
        {(filtros.setor || filtros.etapa || filtros.data_inicio || filtros.data_fim) && (
          <button
            onClick={() => { const f = { setor: '', etapa: '', data_inicio: '', data_fim: '' }; setFiltros(f); carregar(f) }}
            className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1.5">
            Limpar
          </button>
        )}
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

          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-1">
              <DonutClassificacao total={dados.total_processos} criticos={dados.processos_criticos} atencao={dados.processos_atencao} />
            </div>
            <div className="lg:col-span-2 grid sm:grid-cols-2 gap-6">
              <GraficoTempoMedio titulo="Tempo médio por setor" dados={dados.por_setor} chaveLabel="setor"
                limiarAtencao={dados.limiar_dias_atencao} limiarCritico={dados.limiar_dias_critico} />
              <GraficoTempoMedio titulo="Tempo médio por etapa" dados={dados.por_etapa} chaveLabel="etapa"
                limiarAtencao={dados.limiar_dias_atencao} limiarCritico={dados.limiar_dias_critico} />
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

          <div className="mt-8 mb-4">
            <h2 className="text-base font-bold text-gray-800">Duração de processos concluídos</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Diferente do restante desta página (que mede quanto tempo processos EM ANDAMENTO estão
              parados na etapa atual), isto mede o ciclo completo — do início do Procedimento até a
              assinatura do Contrato — de processos já concluídos. Segmentado por modalidade, natureza
              do objeto e passagem por órgão externo, porque uma média única mistura processos de
              complexidade muito diferente (ex.: compra de material de escritório vs. aquisição de
              viaturas que tramita pela Casa Civil) e esconde exatamente o sinal que importa para
              planejar. Amostra mínima de 3 processos concluídos por grupo — abaixo disso, nada é
              estimado.
            </p>
          </div>
          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            <GraficoDuracaoModalidadeSegmentado
              duracaoPorModalidade={dados.duracao_por_modalidade}
              impactoTramitacaoExterna={dados.impacto_tramitacao_externa}
            />
            <GraficoDuracaoPorGrupo titulo="Duração média por natureza do objeto (via TR)" dados={dados.duracao_por_tipo_objeto} chaveLabel="tipo_objeto_label" />
          </div>
          <TabelaImpactoTramitacaoExterna dados={dados.impacto_tramitacao_externa} />
        </>
      )}
    </div>
  )
}
