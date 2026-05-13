import { MODULE_COLORS } from '../config/moduleCards.jsx'

export default function ModuleCard({ card, onClick, badge }) {
  const colors = MODULE_COLORS[card.cor] || MODULE_COLORS.gray

  return (
    <button
      onClick={onClick}
      className={[
        'relative flex flex-col items-center justify-center text-center',
        'p-6 rounded-2xl border-2 cursor-pointer w-full',
        'transition-all duration-200',
        'hover:-translate-y-1 hover:shadow-xl hover:shadow-black/50',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20',
        colors.bg, colors.border, colors.hover,
      ].join(' ')}
    >
      {/* Badge contador (aceites pendentes, etc.) */}
      {badge != null && badge > 0 && (
        <span className="absolute top-3 right-3 bg-white/10 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
          {badge > 99 ? '99+' : badge}
        </span>
      )}

      {/* Ícone */}
      <div className={`p-2.5 rounded-xl ${colors.iconBg} ${colors.iconText} mb-3`}>
        {card.icon}
      </div>

      {/* Título */}
      <p className={`text-[15px] font-bold leading-tight ${colors.text}`}>
        {card.label}
      </p>

      {/* Descrição */}
      <p className={`text-xs mt-1.5 opacity-60 max-w-[160px] leading-snug ${colors.text}`}>
        {card.descricao}
      </p>

      {/* CTA */}
      <p className={`text-xs font-semibold mt-4 ${colors.accent}`}>
        Acessar →
      </p>
    </button>
  )
}
