import { useNavigate } from 'react-router-dom'
import ModuleCard from './ModuleCard'
import { buildModuleCards } from '../config/moduleCards.jsx'

export default function ModuleGrid({ papel, tipoUnidade, flags, stats }) {
  const navigate = useNavigate()
  const cards    = buildModuleCards(papel, tipoUnidade, flags)

  // Badge dinâmico por módulo a partir dos stats do dashboard
  function getBadge(cardId) {
    if (!stats) return undefined
    if (cardId === 'aceite')      return stats.aceites_pendentes || undefined
    if (cardId === 'necessidades') return stats.necessidades?.pendentes || undefined
    if (cardId === 'dfds')        return stats.dfds?.pendentes || undefined
    if (cardId === 'etps')        return stats.etps?.pendentes || undefined
    return undefined
  }

  if (cards.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-gray-600 text-sm">Nenhum módulo disponível para este perfil.</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5 p-6">
        {cards.map(card => (
          <ModuleCard
            key={card.id}
            card={card}
            badge={getBadge(card.id)}
            onClick={() => navigate(card.to)}
          />
        ))}
      </div>
    </div>
  )
}
