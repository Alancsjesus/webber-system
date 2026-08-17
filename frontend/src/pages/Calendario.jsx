import { useEffect, useCallback, useState, useRef } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import useCalendarioStore from '../stores/calendarioStore'
import useAuthStore from '../stores/authStore'
import { getDestaques, salvarDestaques } from '../utils/calendarioPrefs'
import LoadingSpinner from '../components/LoadingSpinner'

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Calendário de Contratações',
  descricao: 'Visão calendário de todas as datas relevantes: sessões públicas, publicações, prazos de vigência (DFD, contratos), entregas e pagamentos pendentes.',
  acoes: [
    { label: 'Navegar meses', texto: 'Use as setas para avançar ou retroceder no calendário.' },
    { label: 'Clicar evento', texto: 'Clique em um evento para ir diretamente ao documento, contrato ou procedimento correspondente.' },
    { label: 'Passar o mouse', texto: 'Mostra um tooltip com detalhes do evento: descrição, data, status e dias restantes.' },
    { label: '⚙ Personalizar destaques', texto: 'Escolha quais tipos de prazo você quer ver em cor forte. Por padrão, já vem ajustado ao seu papel (ex: fiscal vê entregas/pagamentos em destaque; planejamento vê prazos de DFD). Os demais tipos continuam visíveis, só em tom discreto — para não competir visualmente. Fica salvo neste navegador.' },
  ],
  dica: 'Entre os tipos destacados: vermelho = vencido, laranja = urgente (≤15 dias), âmbar = atenção (≤30 dias). Tipos fora do seu destaque aparecem em cinza, mesmo se urgentes.',
}
// ──────────────────────────────────────────────────────────────────────────────

// ── Localização pt-BR ────────────────────────────────────────────────────────
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 0 }),
  getDay,
  locales: { 'pt-BR': ptBR },
})

const MESSAGES = {
  allDay:     'Dia inteiro',
  previous:   '‹ Anterior',
  next:       'Próximo ›',
  today:      'Hoje',
  month:      'Mês',
  week:       'Semana',
  day:        'Dia',
  agenda:     'Agenda',
  date:       'Data',
  time:       'Hora',
  event:      'Evento',
  noEventsInRange: 'Nenhum evento neste período.',
}

// ── Labels e cores dos tipos ─────────────────────────────────────────────────
const TIPO_META = {
  procedimento: { label: 'Procedimento',          bg: 'bg-blue-100',   text: 'text-blue-700' },
  contrato:     { label: 'Contrato',               bg: 'bg-red-100',    text: 'text-red-700'  },
  necessidade:  { label: 'Necessidade',            bg: 'bg-purple-100', text: 'text-purple-700' },
  dfd:          { label: 'DFD',                    bg: 'bg-cyan-100',   text: 'text-cyan-700' },
  execucao:     { label: 'Execução de Contrato',   bg: 'bg-teal-100',   text: 'text-teal-700' },
}

const TIPO_COR_BASE = {
  procedimento: '#1351B4',
  contrato:     '#DC3545',
  necessidade:  '#6F42C1',
  dfd:          '#0DCAF0',
  execucao:     '#20C997',
}

const TIPO_OPTIONS = [
  { value: '',             label: 'Todos os tipos' },
  { value: 'procedimento', label: 'Procedimentos' },
  { value: 'contrato',     label: 'Contratos' },
  { value: 'necessidade',  label: 'Necessidades' },
  { value: 'dfd',          label: 'DFDs' },
  { value: 'execucao',     label: 'Execução de Contrato' },
]

const URGENCIA_LABEL = { vencido: 'Vencido', urgente: 'Urgente', atencao: 'Atenção' }
const URGENCIA_COR_TEXTO = { vencido: 'text-red-600', urgente: 'text-orange-600', atencao: 'text-amber-600' }

const ANOS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 + i)

// ── Tooltip do evento (via portal, escapa do overflow:hidden das células) ─────
function EventoComTooltip({ event }) {
  const [show, setShow] = useState(false)
  const [pos, setPos]   = useState({ top: 0, left: 0 })
  const ref = useRef(null)
  const ev  = event.resource

  const handleEnter = () => {
    const rect = ref.current?.getBoundingClientRect()
    if (rect) setPos({ top: rect.bottom + 4, left: Math.min(rect.left, window.innerWidth - 280) })
    setShow(true)
  }

  return (
    <div ref={ref} onMouseEnter={handleEnter} onMouseLeave={() => setShow(false)} className="truncate">
      {event.title}
      {show && createPortal(
        <div style={{ position: 'fixed', top: pos.top, left: pos.left, zIndex: 9999 }}
             className="w-64 bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs text-gray-700">
          <p className="font-semibold text-gray-800">{ev.titulo}</p>
          {ev.descricao && <p className="text-gray-500 mt-0.5">{ev.descricao}</p>}
          <p className="text-gray-400 mt-1">{new Date(ev.data + 'T00:00:00').toLocaleDateString('pt-BR')}</p>
          {ev.status && <p className="text-gray-400">Status: {ev.status}</p>}
          {ev.urgencia && (
            <p className={`mt-1 font-semibold ${URGENCIA_COR_TEXTO[ev.urgencia] || 'text-gray-500'}`}>
              {URGENCIA_LABEL[ev.urgencia]}
              {ev.dias_restantes !== undefined && (
                ev.dias_restantes >= 0 ? ` — ${ev.dias_restantes} dia(s) restante(s)` : ` — ${Math.abs(ev.dias_restantes)} dia(s) em atraso`
              )}
            </p>
          )}
        </div>,
        document.body
      )}
    </div>
  )
}

// ── Componente principal ─────────────────────────────────────────────────────
export default function Calendario() {
  const navigate = useNavigate()
  const papel = useAuthStore((s) => s.papel)
  const {
    eventos, loading, error,
    ano, mes, tipoFiltro,
    setAno, setTipoFiltro,
    fetchEventos,
  } = useCalendarioStore()

  const [destaques, setDestaques]         = useState(() => getDestaques(papel))
  const [showPersonalizar, setShowPersonalizar] = useState(false)

  useEffect(() => {
    fetchEventos(ano, mes, tipoFiltro)
  }, [ano, mes, tipoFiltro])

  const toggleDestaque = (tipo) => {
    setDestaques(prev => {
      const novo = prev.includes(tipo) ? prev.filter(t => t !== tipo) : [...prev, tipo]
      salvarDestaques(novo)
      return novo
    })
  }

  // Converte eventos da API para o formato do react-big-calendar
  const rbcEvents = eventos.map(ev => ({
    id:       ev.id,
    title:    ev.titulo,
    start:    new Date(ev.data + 'T00:00:00'),
    end:      new Date(ev.data + 'T23:59:59'),
    resource: ev,
  }))

  // Estilo por tipo: cor de urgência cheia se o tipo está nos destaques do usuário,
  // senão tom discreto/dessaturado — evita poluição visual (ver pageHelp).
  const eventStyleGetter = useCallback((event) => {
    const destacado = destaques.includes(event.resource?.tipo)
    const cor = destacado ? (event.resource?.cor || '#6B7280') : '#D1D5DB'
    return {
      style: {
        backgroundColor: cor,
        borderColor: cor,
        color: destacado ? '#fff' : '#4B5563',
        opacity: destacado ? 1 : 0.7,
        borderRadius: '4px',
        fontSize: '0.75rem',
        padding: '2px 4px',
      },
    }
  }, [destaques])

  // Navegar ao clicar no evento
  const handleSelectEvent = useCallback((event) => {
    const link = event.resource?.link
    if (link) navigate(link)
  }, [navigate])

  // Prazos em destaque vencendo/urgentes (respeita a preferência do usuário)
  const alertas = eventos.filter(ev => ev.alerta && destaques.includes(ev.tipo))

  return (
    <div className="p-6">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Calendário de Contratações</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Linha do tempo de procedimentos, contratos e prazos
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Seletor de ano */}
          <select
            value={ano}
            onChange={e => setAno(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {ANOS.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>

          {/* Filtro de tipo */}
          <select
            value={tipoFiltro}
            onChange={e => setTipoFiltro(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {TIPO_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          {/* Personalizar destaques */}
          <button
            onClick={() => setShowPersonalizar(v => !v)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
          >
            ⚙ Destaques
          </button>
        </div>
      </div>

      {/* Painel de personalização de destaques */}
      {showPersonalizar && (
        <div className="mb-4 bg-white border border-gray-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-gray-600 mb-2">
            Tipos de prazo que você quer ver em cor forte (os demais ficam discretos, em cinza):
          </p>
          <div className="flex flex-wrap gap-2">
            {TIPO_OPTIONS.filter(o => o.value).map(opt => (
              <button key={opt.value} onClick={() => toggleDestaque(opt.value)}
                className={`px-3 py-1 rounded-full text-xs border font-medium transition-colors ${
                  destaques.includes(opt.value)
                    ? 'bg-blue-600 border-blue-600 text-white'
                    : 'bg-white border-gray-300 text-gray-600 hover:border-blue-400'
                }`}>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Alertas de vencimento (só tipos em destaque) */}
      {alertas.length > 0 && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm font-semibold text-red-700 mb-1">
            ⚠ {alertas.length} prazo{alertas.length > 1 ? 's' : ''} vencido{alertas.length > 1 ? 's' : ''} ou próximo{alertas.length > 1 ? 's' : ''} do vencimento
          </p>
          <ul className="space-y-0.5">
            {alertas.map(ev => (
              <li key={ev.id} className="text-xs text-red-600">
                <button
                  onClick={() => navigate(ev.link)}
                  className="hover:underline text-left"
                >
                  <span className="font-semibold">[{TIPO_META[ev.tipo]?.label}]</span> {ev.titulo} — {new Date(ev.data + 'T00:00:00').toLocaleDateString('pt-BR')}
                  {ev.dias_restantes !== undefined && (
                    <span className="ml-1">
                      ({ev.dias_restantes >= 0 ? `${ev.dias_restantes} dias` : 'vencido'})
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Legenda */}
      <div className="flex gap-4 mb-4 flex-wrap">
        {Object.entries(TIPO_META).map(([tipo, meta]) => (
          <span key={tipo} className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${destaques.includes(tipo) ? `${meta.bg} ${meta.text}` : 'bg-gray-50 text-gray-400'}`}>
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: destaques.includes(tipo) ? TIPO_COR_BASE[tipo] : '#D1D5DB' }} />
            {meta.label}
            {!destaques.includes(tipo) && <span className="italic">(discreto)</span>}
          </span>
        ))}
      </div>

      {/* Conteúdo */}
      {loading ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <style>{`
            .rbc-calendar { font-family: inherit; }
            .rbc-header { background: #F8FAFC; font-size: 0.8rem; font-weight: 600; color: #475569; padding: 8px 4px; }
            .rbc-today { background-color: #EFF6FF !important; }
            .rbc-off-range-bg { background-color: #F9FAFB; }
            .rbc-event:focus { outline: none; }
            .rbc-toolbar button { font-size: 0.8rem; border-radius: 6px; }
            .rbc-toolbar button.rbc-active { background-color: #1351B4 !important; border-color: #1351B4 !important; color: #fff !important; }
            .rbc-show-more { font-size: 0.72rem; color: #1351B4; font-weight: 600; }
          `}</style>
          <Calendar
            localizer={localizer}
            events={rbcEvents}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 620, padding: '12px' }}
            culture="pt-BR"
            messages={MESSAGES}
            eventPropGetter={eventStyleGetter}
            onSelectEvent={handleSelectEvent}
            components={{ event: EventoComTooltip }}
            popup
            views={['month', 'agenda']}
            defaultView="month"
            defaultDate={new Date(ano, 0, 1)}
          />
        </div>
      )}

      {/* Totalizador */}
      {!loading && !error && (
        <p className="text-xs text-gray-400 mt-3 text-right">
          {eventos.length} evento{eventos.length !== 1 ? 's' : ''} em {ano}
          {tipoFiltro ? ` · ${TIPO_OPTIONS.find(o => o.value === tipoFiltro)?.label}` : ''}
        </p>
      )}
    </div>
  )
}
