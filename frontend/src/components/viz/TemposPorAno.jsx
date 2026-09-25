import { useEffect, useMemo, useState } from 'react'
import api from '../../services/api'
import { CHROME, ETAPA } from './tokens'

/**
 * Corte temporal: tempo de construção das peças e das fases do procedimento
 * comparado entre dois anos (mediana em dias). Dados de
 * GET /tramitacao/tempos-por-ano/ — definições em modulo_tramitacao/tempos.py.
 * Menor é melhor: queda aparece como ▼ (verde), alta como ▲ (vermelho).
 */
const COR_A = ETAPA[1]
const COR_B = ETAPA[3]

function Variacao({ a, b }) {
  if (a == null || b == null) return <span className="text-gray-300">—</span>
  const dif = Math.round((b - a) * 10) / 10
  if (dif === 0) return <span className="text-gray-500">=</span>
  const pct = a > 0 ? Math.round((dif / a) * 100) : null
  const melhor = dif < 0
  return (
    <span className={`font-semibold tabular-nums ${melhor ? 'text-green-700' : 'text-red-700'}`}
      title={melhor ? 'Mais rápido que no ano anterior' : 'Mais lento que no ano anterior'}>
      {melhor ? '▼' : '▲'} {dif > 0 ? '+' : ''}{dif.toLocaleString('pt-BR')} d{pct != null && ` (${pct > 0 ? '+' : ''}${pct}%)`}
    </span>
  )
}

function BarrasPar({ a, b, max }) {
  const w = (v) => (v == null || !max ? 0 : Math.max(2, (v / max) * 100))
  return (
    <div className="space-y-1 w-full min-w-[120px]">
      {[[a, COR_A], [b, COR_B]].map(([v, cor], i) => (
        <div key={i} className="h-2 rounded-r" style={{ background: CHROME.trilho }}>
          {v != null && <div className="h-full rounded-r" style={{ width: `${w(v)}%`, background: cor }} />}
        </div>
      ))}
    </div>
  )
}

const fmtDias = (v) => (v == null ? '—' : `${v.toLocaleString('pt-BR')} d`)

export default function TemposPorAno() {
  const [dados, setDados] = useState(null)
  const [erro, setErro] = useState(null)
  const [anoA, setAnoA] = useState(null)
  const [anoB, setAnoB] = useState(null)

  useEffect(() => {
    api.get('/tramitacao/tempos-por-ano/')
      .then(({ data }) => {
        setDados(data)
        const anos = data.anos
        setAnoB(anos[anos.length - 1] ?? null)
        setAnoA(anos[anos.length - 2] ?? anos[anos.length - 1] ?? null)
      })
      .catch(() => setErro('Não foi possível carregar os tempos por ano.'))
  }, [])

  const max = useMemo(() => {
    if (!dados) return 0
    return Math.max(0, ...dados.metricas.flatMap((m) => [m.por_ano[anoA]?.mediana ?? 0, m.por_ano[anoB]?.mediana ?? 0]))
  }, [dados, anoA, anoB])

  if (erro) return <p className="text-sm text-red-600">{erro}</p>
  if (!dados) return <p className="text-sm text-gray-400">Carregando…</p>
  if (!dados.anos.length) return <p className="text-sm text-gray-400">Ainda não há peças ou processos concluídos para medir.</p>

  const Sel = ({ valor, set }) => (
    <select value={valor ?? ''} onChange={(e) => set(Number(e.target.value))}
      className="border border-gray-300 rounded-lg px-2 py-1 text-sm">
      {dados.anos.map((a) => <option key={a} value={a}>{a}</option>)}
    </select>
  )

  const linhas = [
    { titulo: 'Construção das peças', grupo: 'peca' },
    { titulo: 'Fases do procedimento', grupo: 'procedimento' },
  ]

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-bold text-gray-700">Tempo de instrução por ano</h2>
          <p className="text-xs text-gray-500 mt-0.5">Mediana em dias, no ano em que a peça ou fase foi concluída. Peças encerradas sem prosseguimento ficam fora da mediana.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: COR_A }} /><Sel valor={anoA} set={setAnoA} />
          <span className="text-gray-400">×</span>
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: COR_B }} /><Sel valor={anoB} set={setAnoB} />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[860px]">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
              <th className="py-2 px-5 font-medium">Peça / fase</th>
              <th className="py-2 px-3 font-medium text-right">{anoA}</th>
              <th className="py-2 px-3 font-medium text-right">{anoB}</th>
              <th className="py-2 px-3 font-medium w-40">Comparação</th>
              <th className="py-2 px-3 font-medium text-right">Variação</th>
              <th className="py-2 px-3 font-medium text-right" title="Concluídas no ano de referência (n da mediana)">Concluídas</th>
              <th className="py-2 px-3 font-medium text-right" title="Média de devoluções até a aprovação">Devoluções</th>
              <th className="py-2 px-3 font-medium text-right" title="Encerradas/canceladas sem prosseguimento no ano">Encerradas</th>
              <th className="py-2 px-5 font-medium text-right" title="Estoque atual: quantidade e idade mediana">Em andamento</th>
            </tr>
          </thead>
          {linhas.map(({ titulo, grupo }) => (
            <tbody key={grupo} className="divide-y divide-gray-50">
              <tr><td colSpan={9} className="px-5 pt-3 pb-1 text-xs font-semibold text-gray-400 uppercase tracking-wide">{titulo}</td></tr>
              {dados.metricas.filter((m) => m.grupo === grupo).map((m) => {
                const a = m.por_ano[anoA] || {}
                const b = m.por_ano[anoB] || {}
                return (
                  <tr key={m.chave} className="hover:bg-gray-50">
                    <td className="py-2 px-5 text-gray-700" title={m.definicao}>{m.rotulo}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-gray-700">{fmtDias(a.mediana)}</td>
                    <td className="py-2 px-3 text-right tabular-nums font-semibold text-gray-900">{fmtDias(b.mediana)}</td>
                    <td className="py-2 px-3"><BarrasPar a={a.mediana} b={b.mediana} max={max} /></td>
                    <td className="py-2 px-3 text-right"><Variacao a={a.mediana} b={b.mediana} /></td>
                    <td className="py-2 px-3 text-right tabular-nums text-gray-600">{a.n ?? 0} → {b.n ?? 0}</td>
                    <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                      {grupo === 'peca' ? `${a.devolucoes_media ?? '—'} → ${b.devolucoes_media ?? '—'}` : '—'}
                    </td>
                    <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                      {grupo === 'peca' ? `${a.encerradas ?? 0} → ${b.encerradas ?? 0}` : '—'}
                    </td>
                    <td className="py-2 px-5 text-right tabular-nums text-gray-600">
                      {m.em_andamento ? `${m.em_andamento.n}${m.em_andamento.idade_mediana != null ? ` · ${m.em_andamento.idade_mediana} d` : ''}` : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          ))}
        </table>
      </div>
      <p className="text-[11px] text-gray-400 px-5 py-2 border-t border-gray-100">
        Peças: da criação à primeira aprovação. Fase preparatória: do DFD à aprovação do procedimento. Fase externa: da publicação à homologação.
        Ciclo total: do DFD à assinatura do contrato. Amostras pequenas (poucas concluídas) oscilam muito — veja a coluna Concluídas.
      </p>
    </div>
  )
}
