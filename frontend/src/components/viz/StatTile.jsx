import { STATUS } from './tokens'

// Indicador (KPI) neutro: rótulo, valor, contexto. Substitui os cards de fundo
// saturado, onde a cor não significava nada (Indicado e Empenhado ambos azuis,
// "Valor Estimado" âmbar...). Cor só aparece quando carrega ESTADO (tom), e
// sempre acompanhada de ícone — nunca sozinha.
const TONS = {
  neutro: null,
  bom: { cor: STATUS.bom, icone: '✓', texto: 'text-green-700' },
  atencao: { cor: STATUS.atencao, icone: '!', texto: 'text-amber-700' },
  critico: { cor: STATUS.critico, icone: '!', texto: 'text-red-700' },
}

export default function StatTile({ label, value, sub, tom = 'neutro', onClick, children }) {
  const t = TONS[tom]
  const Tag = onClick ? 'button' : 'div'
  return (
    <Tag
      onClick={onClick}
      className={`text-left w-full bg-white rounded-xl border border-gray-200 p-4 relative overflow-hidden
        ${onClick ? 'hover:border-gray-300 hover:shadow-sm transition focus:outline-none focus:ring-2 focus:ring-blue-500' : ''}`}
    >
      {t && <span className="absolute left-0 top-0 bottom-0 w-1" style={{ background: t.cor }} aria-hidden />}
      <p className="text-xs font-medium text-gray-500 flex items-center gap-1.5">
        {t && (
          <span
            className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full text-[9px] font-bold text-white"
            style={{ background: t.cor }}
            aria-hidden
          >
            {t.icone}
          </span>
        )}
        {label}
      </p>
      <p className="text-2xl font-semibold text-gray-900 mt-1 leading-tight break-words">{value}</p>
      {sub && <p className={`text-xs mt-1 ${t ? t.texto : 'text-gray-500'}`}>{sub}</p>}
      {children && <div className="mt-3">{children}</div>}
    </Tag>
  )
}
