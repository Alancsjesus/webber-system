import { useState } from 'react'
import { CHROME, ETAPA, fmtBRL, fmtPct } from './tokens'

/**
 * Barra de etapas ACUMULATIVAS (ex.: Indicado ⊇ Empenhado ⊇ Liquidado ⊇ Pago;
 * Contratado ⊇ Medido ⊇ Pago). Cada etapa contém a seguinte, então a barra
 * mostra os INCREMENTOS — pago | liquidado a pagar | empenhado a liquidar — e o
 * trilho cinza é o que ainda não iniciou. Os segmentos somam exatamente a base.
 *
 * Cor: rampa ordinal de um só matiz, mais escuro = mais avançado.
 *
 * props:
 *   base    — valor total (100% da barra), ex.: indicado
 *   etapas  — da MAIS avançada para a menos: [{ label, valor }] com valores
 *             acumulados (pago, liquidado, empenhado)
 *   resto   — rótulo do trilho (ex.: 'A empenhar')
 *   compacto — versão de célula de tabela (sem legenda; % da 1ª etapa ao lado)
 */
export function segmentosEtapas(base, etapas, resto) {
  const b = Math.max(0, Number(base) || 0)
  const n = etapas.length
  let anterior = 0
  const segs = etapas.map((e, i) => {
    const acumulado = Math.min(b, Math.max(anterior, Number(e.valor) || 0))
    const valor = acumulado - anterior
    anterior = acumulado
    // mais avançada = passo mais escuro da rampa
    return { label: e.label, valor, acumulado, cor: ETAPA[ETAPA.length - 1 - i] ?? ETAPA[0], idx: n - i }
  })
  segs.push({ label: resto, valor: Math.max(0, b - anterior), cor: CHROME.trilho, trilho: true })
  return { base: b, segs }
}

function Barra({ base, segs, altura, onHover }) {
  return (
    <div className="flex w-full overflow-hidden rounded" style={{ height: altura, gap: 2 }} role="img"
      aria-label={segs.map((s) => `${s.label}: ${fmtBRL(s.valor)} (${fmtPct(s.valor, base)})`).join('; ')}>
      {segs.filter((s) => s.valor > 0).map((s) => (
        <div
          key={s.label}
          className="h-full first:rounded-l last:rounded-r transition-opacity"
          style={{ flexGrow: s.valor, flexBasis: 0, minWidth: 2, background: s.cor, boxShadow: s.trilho ? `inset 0 0 0 1px ${CHROME.grade}` : undefined }}
          onMouseEnter={() => onHover?.(s)}
          onMouseLeave={() => onHover?.(null)}
          title={`${s.label}: ${fmtBRL(s.valor)} (${fmtPct(s.valor, base)})`}
        />
      ))}
    </div>
  )
}

export function EtapasLegenda({ etapas, resto, className = '' }) {
  const { segs } = segmentosEtapas(1, etapas.map((e) => ({ ...e, valor: 0 })), resto)
  return (
    <div className={`flex flex-wrap gap-x-3 gap-y-1 text-xs text-gray-500 ${className}`}>
      {segs.map((s) => (
        <span key={s.label} className="inline-flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: s.cor, boxShadow: s.trilho ? `inset 0 0 0 1px ${CHROME.grade}` : undefined }} />
          {s.label}
        </span>
      ))}
    </div>
  )
}

export default function EtapasBar({ base, etapas, resto, compacto = false }) {
  const [hover, setHover] = useState(null)
  const { base: b, segs } = segmentosEtapas(base, etapas, resto)
  if (b === 0) return <p className="text-xs text-gray-400">Sem valor de referência.</p>
  const principal = segs[0]

  if (compacto) {
    return (
      <div className="flex items-center gap-2 min-w-[180px]">
        <div className="flex-1"><Barra base={b} segs={segs} altura={10} /></div>
        <span className="text-xs font-semibold text-gray-700 tabular-nums w-10 text-right" title={`${principal.label}: ${fmtPct(principal.acumulado, b)} da base`}>
          {fmtPct(principal.acumulado, b)}
        </span>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <p className="text-sm text-gray-600">
          <span className="text-2xl font-semibold text-gray-900 mr-1.5">{fmtPct(principal.acumulado, b)}</span>
          {principal.label.toLowerCase()}
        </p>
        <p className="text-xs text-gray-500 h-4">
          {hover ? <>{hover.label}: <b className="text-gray-800">{fmtBRL(hover.valor)}</b> ({fmtPct(hover.valor, b)})</> : `base ${fmtBRL(b)}`}
        </p>
      </div>
      <Barra base={b} segs={segs} altura={14} onHover={setHover} />
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2 mt-3">
        {segs.map((s) => (
          <div key={s.label} className="min-w-0">
            <dt className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="inline-block w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: s.cor, boxShadow: s.trilho ? `inset 0 0 0 1px ${CHROME.grade}` : undefined }} />
              <span className="truncate">{s.label}</span>
            </dt>
            <dd className="text-sm font-semibold text-gray-800 tabular-nums">
              {fmtBRL(s.valor)} <span className="text-xs font-normal text-gray-400">{fmtPct(s.valor, b)}</span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
