import { useState } from 'react'
import { CHROME, ETAPA, STATUS } from './tokens'

/**
 * Parte-do-todo em uma barra horizontal empilhada (substitui roscas pequenas).
 * itens: [{ label, valor, cor }] — na ordem do fluxo (rascunho → ... → final).
 * A legenda traz a contagem de cada parte, então a cor nunca é o único canal.
 */
export default function DistribuicaoBar({ itens, unidade = '', vazio = 'Sem dados.' }) {
  const [hover, setHover] = useState(null)
  const total = itens.reduce((a, i) => a + (Number(i.valor) || 0), 0)
  if (total === 0) return <p className="text-xs text-gray-400">{vazio}</p>
  const pct = (v) => `${Math.round((v / total) * 100)}%`
  return (
    <div>
      <div className="flex w-full h-3 rounded overflow-hidden" style={{ gap: 2 }} role="img"
        aria-label={itens.map((i) => `${i.label}: ${i.valor}`).join('; ')}>
        {itens.filter((i) => i.valor > 0).map((i) => (
          <div key={i.label} style={{ flexGrow: i.valor, flexBasis: 0, minWidth: 3, background: i.cor }}
            className={`h-full transition-opacity ${hover && hover !== i.label ? 'opacity-40' : ''}`}
            onMouseEnter={() => setHover(i.label)} onMouseLeave={() => setHover(null)}
            title={`${i.label}: ${i.valor}${unidade} (${pct(i.valor)})`} />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-3 gap-y-1 mt-2.5">
        {itens.map((i) => (
          <li key={i.label} onMouseEnter={() => setHover(i.label)} onMouseLeave={() => setHover(null)}
            className={`inline-flex items-center gap-1.5 text-xs ${i.valor ? 'text-gray-600' : 'text-gray-300'}`}>
            <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: i.valor ? i.cor : CHROME.trilho }} />
            {i.label} <b className={i.valor ? 'text-gray-800 font-semibold tabular-nums' : 'font-normal'}>{i.valor}</b>
          </li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Cor de status de documento por SIGNIFICADO, igual em todos os painéis:
 * início (rascunho) = neutro; em trâmite = rampa azul (mais escuro = mais adiante);
 * concluído bem = bom; devolvido = atenção; rejeitado/cancelado = crítico.
 */
export function corStatusDoc(status) {
  const s = (status || '').toLowerCase()
  if (/cancel|rejeit|rescind/.test(s)) return STATUS.critico
  if (/devolv|suspens/.test(s)) return STATUS.atencao
  if (/aprovad|conclu|vigente|dfd criado|homolog/.test(s)) return STATUS.bom
  if (/execu/.test(s)) return ETAPA[3]
  if (/an[aá]lise/.test(s)) return ETAPA[2]
  if (/submet|proposta/.test(s)) return ETAPA[1]
  if (/encerrad/.test(s)) return '#6b7280'
  return STATUS.neutro // rascunho, identificada, etc.
}
