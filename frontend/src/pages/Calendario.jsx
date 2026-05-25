import { useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calendar, dateFnsLocalizer } from 'react-big-calendar'
import { format, parse, startOfWeek, getDay } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import 'react-big-calendar/lib/css/react-big-calendar.css'
import useCalendarioStore from '../stores/calendarioStore'
import LoadingSpinner from '../components/LoadingSpinner'

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Calendário de Contratações',
  descricao: 'Visão calendário de todas as datas relevantes: sessões públicas, publicações, prazos de vigência de contratos e devoluções com prazo.',
  acoes: [
    { label: 'Navegar meses', texto: 'Use as setas para avançar ou retroceder no calendário.' },
    { label: 'Clicar evento', texto: 'Clique em um evento para ir diretamente ao procedimento ou contrato correspondente.' },
  ],
  dica: 'Eventos em vermelho indicam prazos vencidos ou próximos ao vencimento.',
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
  procedimento: { label: 'Procedimento', bg: 'bg-blue-100',   text: 'text-blue-700' },
  contrato:     { label: 'Contrato',     bg: 'bg-red-100',    text: 'text-red-700'  },
  necessidade:  { label: 'Necessidade',  bg: 'bg-purple-100', text: 'text-purple-700' },
}

const TIPO_OPTIONS = [
  { value: '',             label: 'Todos os tipos' },
  { value: 'procedimento', label: 'Procedimentos' },
  { value: 'contrato',     label: 'Contratos' },
  { value: 'necessidade',  label: 'Necessidades' },
]

const ANOS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 + i)

// ── Componente principal ─────────────────────────────────────────────────────
export default function Calendario() {
  const navigate = useNavigate()
  const {
    eventos, loading, error,
    ano, mes, tipoFiltro,
    setAno, setTipoFiltro,
    fetchEventos,
  } = useCalendarioStore()

  useEffect(() => {
    fetchEventos(ano, mes, tipoFiltro)
  }, [ano, mes, tipoFiltro])

  // Converte eventos da API para o formato do react-big-calendar
  const rbcEvents = eventos.map(ev => ({
    id:       ev.id,
    title:    ev.titulo,
    start:    new Date(ev.data + 'T00:00:00'),
    end:      new Date(ev.data + 'T23:59:59'),
    resource: ev,
  }))

  // Estilo por tipo (cor de fundo)
  const eventStyleGetter = useCallback((event) => {
    const cor = event.resource?.cor || '#6B7280'
    return {
      style: {
        backgroundColor: cor,
        borderColor: cor,
        color: '#fff',
        borderRadius: '4px',
        fontSize: '0.75rem',
        padding: '2px 4px',
      },
    }
  }, [])

  // Navegar ao clicar no evento
  const handleSelectEvent = useCallback((event) => {
    const link = event.resource?.link
    if (link) navigate(link)
  }, [navigate])

  // Contratos vencendo em ≤ 30 dias
  const alertas = eventos.filter(ev => ev.alerta)

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
        </div>
      </div>

      {/* Alertas de vencimento */}
      {alertas.length > 0 && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm font-semibold text-red-700 mb-1">
            ⚠ {alertas.length} contrato{alertas.length > 1 ? 's' : ''} vencendo em até 30 dias
          </p>
          <ul className="space-y-0.5">
            {alertas.map(ev => (
              <li key={ev.id} className="text-xs text-red-600">
                <button
                  onClick={() => navigate(ev.link)}
                  className="hover:underline text-left"
                >
                  {ev.titulo} — {new Date(ev.data + 'T00:00:00').toLocaleDateString('pt-BR')}
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
          <span key={tipo} className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${meta.bg} ${meta.text}`}>
            <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: tipo === 'procedimento' ? '#1351B4' : tipo === 'contrato' ? '#DC3545' : '#6F42C1' }} />
            {meta.label}
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-600">
          <span className="w-2 h-2 rounded-full bg-gray-400 inline-block" />
          Contrato vencendo
        </span>
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
