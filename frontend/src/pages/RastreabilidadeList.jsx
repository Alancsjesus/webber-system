import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useRastreabilidadeStore from '../stores/rastreabilidadeStore'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo:    'Rastreabilidade de Processos',
  descricao: 'Visão gerencial de cada necessidade e sua posição na cadeia de contratação: Necessidade → DFD → ETP → TR → Procedimento → Contrato.',
  acoes: [
    { label: 'Buscar necessidade', texto: 'Pesquisa pelo título ou parte do título da necessidade de planejamento.' },
    { label: 'Buscar por SEI',     texto: 'Localiza qualquer processo pelo número SEI, independente de qual documento (DFD, ETP, TR ou Contrato) ele foi registrado.' },
    { label: 'Filtro Exercício',   texto: 'Restringe a lista ao exercício fiscal selecionado.' },
    { label: 'Filtro Prioridade',  texto: 'Filtra por prioridade (Alta, Média, Baixa) da necessidade.' },
    { label: 'Filtro Etapa',       texto: 'Mostra apenas processos parados em uma etapa específica da cadeia.' },
    { label: 'Ver cadeia',         texto: 'Abre a linha do tempo completa da necessidade selecionada, com todos os documentos e responsáveis.' },
  ],
  dica: 'Use "Buscar por SEI" para localizar rapidamente um processo a partir de qualquer número de processo SEI, mesmo sem saber a qual necessidade ele pertence.',
  baseLegal: 'Lei 14.133/2021 — Art. 12 (planejamento e controle das contratações).',
}
// ─────────────────────────────────────────────────────────────────────────────

const ETAPAS = ['Necessidade', 'DFD', 'ETP', 'TR', 'Procedimento', 'Contrato']
const ETAPA_CORES = {
  Necessidade:  { dot: 'bg-slate-400',  badge: 'bg-slate-100 text-slate-700' },
  DFD:          { dot: 'bg-blue-400',   badge: 'bg-blue-100 text-blue-700' },
  ETP:          { dot: 'bg-indigo-400', badge: 'bg-indigo-100 text-indigo-700' },
  TR:           { dot: 'bg-violet-400', badge: 'bg-violet-100 text-violet-700' },
  Procedimento: { dot: 'bg-amber-400',  badge: 'bg-amber-100 text-amber-700' },
  Contrato:     { dot: 'bg-green-400',  badge: 'bg-green-100 text-green-700' },
}
const PRIORIDADE_BADGE = {
  Alta:  'bg-red-100 text-red-700',
  Média: 'bg-amber-100 text-amber-700',
  Baixa: 'bg-gray-100 text-gray-600',
}

const fmtValor = (v) =>
  v ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—'

function ProgressoEtapas({ item }) {
  const presentes = [
    'Necessidade',
    item.tem_dfd         && 'DFD',
    item.tem_etp         && 'ETP',
    item.tem_tr          && 'TR',
    item.tem_procedimento && 'Procedimento',
    item.tem_contrato    && 'Contrato',
  ].filter(Boolean)

  return (
    <div className="flex items-center gap-0.5">
      {ETAPAS.map((etapa, i) => {
        const presente = presentes.includes(etapa)
        const atual    = item.etapa_atual === etapa
        const cor      = ETAPA_CORES[etapa]
        return (
          <div key={etapa} className="flex items-center gap-0.5">
            {i > 0 && <span className={`h-px w-3 ${presente ? 'bg-gray-300' : 'bg-gray-100'}`} />}
            <div
              title={etapa}
              className={`
                w-2.5 h-2.5 rounded-full
                ${presente ? cor.dot : 'bg-gray-100 border border-gray-200'}
                ${atual ? 'ring-2 ring-offset-1 ring-blue-400' : ''}
              `}
            />
          </div>
        )
      })}
    </div>
  )
}

function SearchInput({ value, onChange, placeholder, icon }) {
  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">{icon}</span>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 w-64"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs"
        >
          ✕
        </button>
      )}
    </div>
  )
}

export default function RastreabilidadeList() {
  const navigate = useNavigate()
  const { lista, loading, error, count, pageSize, fetchLista } =
    useRastreabilidadeStore()

  // Valores de digitação imediata
  const [buscaInput, setBuscaInput]   = useState('')
  const [seiInput, setSeiInput]       = useState('')
  // Selects aplicados imediatamente
  const [exercicio, setExercicio]     = useState('')
  const [prioridade, setPrioridade]   = useState('')
  const [etapa, setEtapa]             = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  // Valores debounced (enviados ao backend)
  const busca = useDebouncedValue(buscaInput).trim()
  const sei   = useDebouncedValue(seiInput).trim()

  // Ao trocar filtros, volta pra página 1
  useEffect(() => { setCurrentPage(1) }, [busca, sei, exercicio, prioridade, etapa])

  // Dispara fetch sempre que algum filtro ou página mudar
  useEffect(() => {
    const params = { page: currentPage, page_size: pageSize }
    if (busca)      params.busca     = busca
    if (sei)        params.sei       = sei
    if (exercicio)  params.exercicio = exercicio
    if (prioridade) params.prioridade = prioridade
    if (etapa)      params.etapa     = etapa
    fetchLista(params)
  }, [busca, sei, exercicio, prioridade, etapa, currentPage])

  const temFiltroAtivo = buscaInput || seiInput || exercicio || prioridade || etapa

  const limparFiltros = () => {
    setBuscaInput(''); setSeiInput('')
    setExercicio(''); setPrioridade(''); setEtapa('')
    setCurrentPage(1)
  }

  const exercicioAtual = new Date().getFullYear()

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-5">

      {/* Cabeçalho */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Rastreabilidade de Processos</h1>
        <p className="text-sm text-gray-500 mt-1">
          Acompanhe onde cada necessidade está na cadeia de contratação.
        </p>
      </div>

      {/* Barra de busca + filtros */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 space-y-3">
        {/* Linha 1: buscas textuais */}
        <div className="flex flex-wrap gap-3">
          <SearchInput
            value={buscaInput}
            onChange={v => { setBuscaInput(v) }}
            placeholder="Buscar por necessidade..."
            icon="🔎"
          />
          <SearchInput
            value={seiInput}
            onChange={v => { setSeiInput(v) }}
            placeholder="Nº SEI (qualquer documento)..."
            icon="#"
          />
        </div>

        {/* Linha 2: selects */}
        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={exercicio}
            onChange={e => setExercicio(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">Todos os exercícios</option>
            {[exercicioAtual, exercicioAtual - 1, exercicioAtual - 2].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>

          <select
            value={prioridade}
            onChange={e => setPrioridade(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">Todas as prioridades</option>
            <option value="Alta">Alta</option>
            <option value="Média">Média</option>
            <option value="Baixa">Baixa</option>
          </select>

          <select
            value={etapa}
            onChange={e => setEtapa(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
          >
            <option value="">Todas as etapas</option>
            {ETAPAS.map(e => <option key={e} value={e}>{e}</option>)}
          </select>

          {temFiltroAtivo && (
            <button
              onClick={limparFiltros}
              className="text-sm text-gray-500 hover:text-gray-700 underline"
            >
              Limpar filtros
            </button>
          )}
        </div>
      </div>

      {/* Conteúdo */}
      {loading && <LoadingSpinner />}
      {error   && <p className="text-red-600 text-sm">{error}</p>}

      {!loading && !error && lista.length === 0 && (
        <EmptyState mensagem="Nenhuma necessidade encontrada para os filtros selecionados." />
      )}

      {!loading && !error && lista.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          {/* Cabeçalho da tabela */}
          <div className="px-5 py-3 border-b border-gray-100 flex flex-wrap items-center justify-between gap-2">
            <span className="text-sm font-medium text-gray-600">
              {count} necessidade{count !== 1 ? 's' : ''}
              {temFiltroAtivo && <span className="text-blue-600"> (filtrado)</span>}
            </span>
            <div className="flex items-center gap-3 text-xs text-gray-400">
              {ETAPAS.map(e => (
                <span key={e} className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full ${ETAPA_CORES[e].dot}`} />
                  {e}
                </span>
              ))}
            </div>
          </div>

          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead>
              <tr className="text-xs text-gray-500 bg-gray-50 border-b border-gray-100">
                <th className="text-left px-5 py-3 font-medium">Necessidade</th>
                <th className="text-left px-4 py-3 font-medium">Exercício</th>
                <th className="text-left px-4 py-3 font-medium">Valor Estimado</th>
                <th className="text-left px-4 py-3 font-medium">Progresso</th>
                <th className="text-left px-4 py-3 font-medium">Etapa Atual</th>
                <th className="text-left px-4 py-3 font-medium">Dias</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {lista.map(item => {
                const cores  = ETAPA_CORES[item.etapa_atual] || ETAPA_CORES.Necessidade
                const priCls = PRIORIDADE_BADGE[item.prioridade] || PRIORIDADE_BADGE.Média
                return (
                  <tr
                    key={item.id}
                    className="hover:bg-blue-50/40 transition-colors cursor-pointer"
                    onClick={() => navigate(`/rastreabilidade/${item.id}`)}
                  >
                    <td className="px-5 py-4">
                      <p className="font-medium text-gray-800 leading-tight">{item.titulo}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${priCls}`}>
                          {item.prioridade}
                        </span>
                        <span className="text-xs text-gray-400">{item.responsavel}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-gray-600">{item.exercicio_fiscal}</td>
                    <td className="px-4 py-4 text-gray-700 font-medium tabular-nums">
                      {fmtValor(item.valor_estimado)}
                    </td>
                    <td className="px-4 py-4">
                      <ProgressoEtapas item={item} />
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full ${cores.badge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${cores.dot}`} />
                        {item.etapa_atual}
                      </span>
                      <p className="text-xs text-gray-400 mt-0.5">{item.status}</p>
                    </td>
                    <td className="px-4 py-4 text-gray-500 tabular-nums">
                      {item.dias_em_aberto != null ? `${item.dias_em_aberto}d` : '—'}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <button
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                        onClick={e => { e.stopPropagation(); navigate(`/rastreabilidade/${item.id}`) }}
                      >
                        Ver cadeia →
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          </div>

          <Pagination
            page={currentPage}
            count={count}
            pageSize={pageSize}
            itemLabel="necessidade(s)"
            onPage={setCurrentPage}
          />
        </div>
      )}
    </div>
  )
}
