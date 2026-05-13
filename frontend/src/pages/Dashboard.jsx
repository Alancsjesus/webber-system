import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../stores/authStore'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import OrgaoHero from '../components/OrgaoHero'
import ModuleGrid from '../components/ModuleGrid'
import DashboardAnalytics from './DashboardAnalytics'

// ── Abas ──────────────────────────────────────────────────────────────────────

function TabBar({ active, onChange }) {
  const tabs = [
    { id: 'modulos',   label: 'Módulos' },
    { id: 'analytics', label: 'Analytics' },
  ]
  return (
    <div className="flex gap-1 -mx-6 px-6 mt-4">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={[
            'px-4 py-2 text-sm font-semibold border-b-2 transition-colors',
            active === t.id
              ? 'text-white border-white'
              : 'text-gray-500 border-transparent hover:text-gray-300',
          ].join(' ')}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ── Banner: sistema vazio ─────────────────────────────────────────────────────

function OnboardingBanner({ navigate }) {
  return (
    <div className="mx-0 mt-4 bg-blue-950 border border-blue-800 rounded-xl p-4">
      <div className="flex items-start gap-3">
        <span className="text-blue-400 text-lg mt-0.5">🚀</span>
        <div>
          <p className="text-sm font-semibold text-blue-200 mb-1.5">Bem-vindo ao WEBBER System!</p>
          <p className="text-xs text-blue-400 mb-3">O sistema está pronto. Siga os passos abaixo para começar:</p>
          <ol className="space-y-1.5">
            {[
              { step: '1', label: 'Configure os órgãos e unidades', path: '/config/orgaos', cta: 'Ir para Configurações' },
              { step: '2', label: 'Cadastre as ações orçamentárias', path: '/config/acoes', cta: 'Ir para Ações' },
              { step: '3', label: 'Crie a primeira necessidade de planejamento', path: '/planejamento/necessidades/nova', cta: 'Nova Necessidade' },
            ].map(({ step, label, path, cta }) => (
              <li key={step} className="flex items-center gap-2 text-xs text-blue-300">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-800 text-blue-200 font-bold flex items-center justify-center text-[10px]">{step}</span>
                <span className="flex-1">{label}</span>
                <button onClick={() => navigate(path)} className="text-blue-400 hover:text-blue-200 font-medium hover:underline">{cta} →</button>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  )
}

// ── Banner: aceites pendentes ─────────────────────────────────────────────────

function AceitesBanner({ count, navigate }) {
  return (
    <button
      onClick={() => navigate('/planejamento/aceite')}
      className="w-full flex items-center gap-3 mt-4 bg-amber-950 border border-amber-800 rounded-xl px-4 py-3 text-left hover:bg-amber-900 transition-colors"
    >
      <span className="text-amber-400 text-lg">⚠</span>
      <div>
        <p className="text-sm font-semibold text-amber-200">
          {count} necessidade{count > 1 ? 's' : ''} de órgão{count > 1 ? 's' : ''} filho{count > 1 ? 's' : ''} aguardando aceite
        </p>
        <p className="text-xs text-amber-500">Clique para revisar e aceitar/recusar</p>
      </div>
      <span className="ml-auto text-amber-500 text-lg">›</span>
    </button>
  )
}

// ── Dashboard principal ────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate()

  const papel       = useAuthStore(s => s.papel)
  const tipoUnidade = useAuthStore(s => s.tipoUnidade)
  const orgaoSigla  = useAuthStore(s => s.orgaoSigla)
  const orgaoNome   = useAuthStore(s => s.orgaoNome)
  const unidadeNome = useAuthStore(s => s.unidadeNome)
  const flags       = useAuthStore(s => s.flags)

  const [activeTab, setActiveTab] = useState('modulos')
  const [stats, setStats]         = useState(null)
  const [indOrc, setIndOrc]       = useState(null)
  const [indDev, setIndDev]       = useState(null)
  const [indAgrup, setIndAgrup]   = useState(null)
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    api.get('/dashboard/stats/')
      .then(({ data }) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false))

    api.get('/indicadores/orcamento/')
      .then(({ data }) => setIndOrc(data))
      .catch(() => {})

    api.get('/indicadores/devolucoes/')
      .then(({ data }) => setIndDev(data))
      .catch(() => {})

    api.get('/indicadores/agrupamento/')
      .then(({ data }) => setIndAgrup(data))
      .catch(() => {})
  }, [])

  const showAnalyticsTab  = ['admin', 'analista', 'gestor_planejamento'].includes(papel)
  const aceitesPendentes  = stats?.aceites_pendentes ?? 0
  const systemIsEmpty     = !loading && stats &&
    (stats.necessidades?.total ?? 0) === 0 &&
    (stats.dfds?.total ?? 0) === 0

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-gray-950">
        <LoadingSpinner message="Carregando..." />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 text-white overflow-hidden">

      {/* ── ZONA A: cabeçalho institucional ──────────────────────────── */}
      <div className="flex-none px-6 pt-6 pb-0 border-b border-gray-800">
        <OrgaoHero
          orgaoSigla={orgaoSigla}
          orgaoNome={orgaoNome}
          unidadeNome={unidadeNome}
          tipoUnidade={tipoUnidade}
          papel={papel}
        />

        {systemIsEmpty && <OnboardingBanner navigate={navigate} />}
        {aceitesPendentes > 0 && <AceitesBanner count={aceitesPendentes} navigate={navigate} />}

        {showAnalyticsTab && (
          <TabBar active={activeTab} onChange={setActiveTab} />
        )}
      </div>

      {/* ── ZONA B: conteúdo ─────────────────────────────────────────── */}
      {activeTab === 'modulos' || !showAnalyticsTab ? (
        <ModuleGrid
          papel={papel}
          tipoUnidade={tipoUnidade}
          flags={flags}
          stats={stats}
        />
      ) : (
        <DashboardAnalytics
          stats={stats}
          indOrc={indOrc}
          indDev={indDev}
          indAgrup={indAgrup}
        />
      )}

    </div>
  )
}
