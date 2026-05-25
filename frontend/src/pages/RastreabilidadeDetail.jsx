import { useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import useRastreabilidadeStore from '../stores/rastreabilidadeStore'
import LoadingSpinner from '../components/LoadingSpinner'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo:    'Linha do Tempo da Necessidade',
  descricao: 'Exibe cada etapa da cadeia de contratação — de qual necessidade originou até o contrato firmado — com status, responsável, data e link para cada documento.',
  acoes: [
    { label: 'Acessar documento', texto: 'Cada etapa tem um link que abre o documento correspondente (DFD, ETP, TR, etc.) para leitura detalhada ou gestão.' },
    { label: 'Voltar à lista',    texto: 'Retorna para a lista geral de rastreabilidade.' },
  ],
  fluxo: [
    { status: 'Necessidade',   descricao: 'Identificação da necessidade de contratação pelo departamento solicitante.' },
    { status: 'DFD',           descricao: 'Documento de Formalização de Demanda — valida a necessidade e autoriza o planejamento.' },
    { status: 'ETP',           descricao: 'Estudo Técnico Preliminar — analisa mercado, viabilidade e define a estratégia.' },
    { status: 'TR',            descricao: 'Termo de Referência — especifica objeto, critérios e condições de contratação.' },
    { status: 'Procedimento',  descricao: 'Licitação ou contratação direta — processo público de seleção do fornecedor.' },
    { status: 'Contrato',      descricao: 'Instrumento contratual firmado com o fornecedor selecionado.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Arts. 6º, 18, 72 (cadeia de planejamento e contratação).',
}
// ─────────────────────────────────────────────────────────────────────────────

const ETAPA_CONFIG = {
  Necessidade:  { cor: 'slate',  icone: '📋' },
  DFD:          { cor: 'blue',   icone: '📄' },
  ETP:          { cor: 'indigo', icone: '🔍' },
  TR:           { cor: 'violet', icone: '📝' },
  Procedimento: { cor: 'amber',  icone: '⚖️' },
  Contrato:     { cor: 'green',  icone: '✅' },
}

const COR_TAILWIND = {
  slate:  { ring: 'ring-slate-400',  bg: 'bg-slate-50',  border: 'border-slate-200', badge: 'bg-slate-100 text-slate-700',  dot: 'bg-slate-400',  line: 'bg-slate-200'  },
  blue:   { ring: 'ring-blue-400',   bg: 'bg-blue-50',   border: 'border-blue-200',  badge: 'bg-blue-100 text-blue-700',   dot: 'bg-blue-400',   line: 'bg-blue-200'   },
  indigo: { ring: 'ring-indigo-400', bg: 'bg-indigo-50', border: 'border-indigo-200',badge: 'bg-indigo-100 text-indigo-700',dot: 'bg-indigo-400', line: 'bg-indigo-200' },
  violet: { ring: 'ring-violet-400', bg: 'bg-violet-50', border: 'border-violet-200',badge: 'bg-violet-100 text-violet-700',dot: 'bg-violet-400', line: 'bg-violet-200' },
  amber:  { ring: 'ring-amber-400',  bg: 'bg-amber-50',  border: 'border-amber-200', badge: 'bg-amber-100 text-amber-700',  dot: 'bg-amber-400',  line: 'bg-amber-200'  },
  green:  { ring: 'ring-green-400',  bg: 'bg-green-50',  border: 'border-green-200', badge: 'bg-green-100 text-green-700',  dot: 'bg-green-400',  line: 'bg-green-200'  },
}

const fmtValor = (v) =>
  v ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : null

const fmtData = (s) =>
  s ? new Date(s).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' }) : null

const PRIORIDADE_BADGE = {
  Alta:  'bg-red-100 text-red-700',
  Média: 'bg-amber-100 text-amber-700',
  Baixa: 'bg-gray-100 text-gray-600',
}

function InfoLinha({ label, valor }) {
  if (!valor) return null
  return (
    <div className="flex items-start gap-2 text-sm">
      <span className="text-gray-400 min-w-max">{label}</span>
      <span className="text-gray-700 font-medium">{valor}</span>
    </div>
  )
}

function EtapaCard({ step, isLast, isAtual }) {
  const cfg  = ETAPA_CONFIG[step.etapa] || ETAPA_CONFIG.Necessidade
  const cors = COR_TAILWIND[cfg.cor]

  return (
    <div className="flex gap-4">
      {/* Linha vertical + ícone */}
      <div className="flex flex-col items-center">
        <div className={`
          w-10 h-10 rounded-full flex items-center justify-center text-lg
          ring-2 ${cors.ring} bg-white shadow-sm z-10
          ${isAtual ? 'shadow-md' : ''}
        `}>
          {step.concluida ? '✓' : cfg.icone}
        </div>
        {!isLast && <div className={`w-0.5 flex-1 mt-1 ${cors.line}`} />}
      </div>

      {/* Conteúdo */}
      <div className={`
        flex-1 mb-6 rounded-xl border p-4
        ${cors.bg} ${cors.border}
        ${isAtual ? `ring-1 ${cors.ring}` : ''}
      `}>
        {/* Cabeçalho da etapa */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {step.etapa}
              </span>
              {isAtual && (
                <span className="text-xs px-1.5 py-0.5 rounded-full bg-blue-600 text-white font-medium">
                  Etapa atual
                </span>
              )}
            </div>
            <p className="text-sm font-medium text-gray-700 mt-0.5">{step.label}</p>
          </div>

          <span className={`text-xs px-2 py-1 rounded-full font-medium whitespace-nowrap ${cors.badge}`}>
            {step.status}
          </span>
        </div>

        {/* Detalhes */}
        <div className="space-y-1">
          {step.objeto && step.etapa !== 'Necessidade' && (
            <InfoLinha label="Documento" valor={step.objeto} />
          )}
          {step.numero_sei && <InfoLinha label="SEI"           valor={step.numero_sei} />}
          {step.numero     && <InfoLinha label="Número"        valor={step.numero} />}
          {step.modalidade && <InfoLinha label="Modalidade"    valor={step.modalidade} />}
          {step.valor      && <InfoLinha label="Valor"         valor={fmtValor(step.valor)} />}
          {step.responsavel && <InfoLinha label="Responsável"  valor={step.responsavel} />}
          {step.data       && <InfoLinha label="Data"          valor={fmtData(step.data)} />}
          {step.vigencia_fim && <InfoLinha label="Vigência até" valor={fmtData(step.vigencia_fim)} />}
        </div>

        {/* Link para o documento */}
        {step.url && step.id && (
          <div className="mt-3 pt-3 border-t border-white/60">
            <Link
              to={step.url}
              className="text-xs font-medium text-blue-600 hover:text-blue-800 hover:underline"
            >
              Abrir {step.etapa} →
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default function RastreabilidadeDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { detalhe, loading, error, fetchDetalhe } = useRastreabilidadeStore()

  useEffect(() => {
    fetchDetalhe(id)
  }, [id])

  if (loading) return <div className="p-8"><LoadingSpinner /></div>
  if (error)   return <div className="p-8 text-red-600 text-sm">{error}</div>
  if (!detalhe) return null

  const priBadge = PRIORIDADE_BADGE[detalhe.prioridade] || PRIORIDADE_BADGE.Média

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">

      {/* Voltar */}
      <button
        onClick={() => navigate('/rastreabilidade')}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 transition-colors"
      >
        ← Rastreabilidade
      </button>

      {/* Cabeçalho da necessidade */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide mb-1">
              Necessidade #{detalhe.id} · {detalhe.exercicio_fiscal}
            </p>
            <h1 className="text-xl font-bold text-gray-800">{detalhe.titulo}</h1>
            {detalhe.descricao && (
              <p className="text-sm text-gray-500 mt-2 leading-relaxed">{detalhe.descricao}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${priBadge}`}>
              {detalhe.prioridade}
            </span>
            <span className="text-lg font-bold text-gray-800">
              {detalhe.valor_estimado
                ? Number(detalhe.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                : '—'}
            </span>
          </div>
        </div>

        {/* Resumo */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-6 text-sm text-gray-600">
          <div>
            <span className="text-gray-400">Responsável</span>
            <p className="font-medium">{detalhe.responsavel || '—'}</p>
          </div>
          <div>
            <span className="text-gray-400">Aberto há</span>
            <p className="font-medium">{detalhe.dias_em_aberto != null ? `${detalhe.dias_em_aberto} dias` : '—'}</p>
          </div>
          <div>
            <span className="text-gray-400">Etapa atual</span>
            <p className="font-medium text-blue-700">{detalhe.etapa_atual}</p>
          </div>
          <div>
            <span className="text-gray-400">Status</span>
            <p className="font-medium">{detalhe.status}</p>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-sm font-semibold text-gray-600 mb-6 uppercase tracking-wide">
          Cadeia de Contratação
        </h2>

        {detalhe.cadeia && detalhe.cadeia.length > 0 ? (
          <div>
            {detalhe.cadeia.map((step, i) => (
              <EtapaCard
                key={`${step.etapa}-${step.id ?? i}`}
                step={step}
                isLast={i === detalhe.cadeia.length - 1}
                isAtual={step.etapa === detalhe.etapa_atual && !step.concluida}
              />
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">Nenhuma etapa registrada.</p>
        )}
      </div>
    </div>
  )
}
