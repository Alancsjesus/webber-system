import { CHROME, ETAPA, fmtBRL, fmtBRLCompacto, fmtPct } from './tokens'

/**
 * Etapas em sequência comparadas com a primeira (ex.: Dotado → Indicado →
 * Descentralizado → Concedido). Substitui o "funil" de trapézios, cuja área
 * distorce a proporção. Barras horizontais a partir da mesma linha de base,
 * rampa ordinal (mais escuro = mais adiante), valor e % da 1ª etapa no rótulo.
 */
export default function BarrasEtapas({ etapas, vazio = 'Sem valores no período.' }) {
  const base = Number(etapas[0]?.valor) || 0
  const max = Math.max(0, ...etapas.map((e) => Number(e.valor) || 0))
  if (max === 0) return <p className="text-xs text-gray-400">{vazio}</p>
  const passo = (i) => ETAPA[Math.round((i / Math.max(1, etapas.length - 1)) * (ETAPA.length - 1))]
  return (
    <ul className="space-y-2.5">
      {etapas.map((e, i) => {
        const v = Number(e.valor) || 0
        return (
          <li key={e.nome} className="grid grid-cols-[7.5rem_1fr] items-center gap-3" title={`${e.nome}: ${fmtBRL(v)}`}>
            <span className="text-xs text-gray-600 truncate">{e.nome}</span>
            <div className="flex items-center gap-2 min-w-0">
              <div className="flex-1 h-3.5 rounded-r" style={{ background: CHROME.trilho }}>
                {v > 0 && (
                  <div className="h-full rounded-r" style={{ width: `${(v / max) * 100}%`, minWidth: 2, background: passo(i) }} />
                )}
              </div>
              <span className="text-xs text-gray-800 font-semibold tabular-nums whitespace-nowrap w-28 text-right">
                {fmtBRLCompacto(v)}
                {i > 0 && base > 0 && <span className="font-normal text-gray-400"> · {fmtPct(v, base)}</span>}
              </span>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
