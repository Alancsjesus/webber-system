import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useInstrumentoFinanceiroStore from '../stores/instrumentoFinanceiroStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'
import { formatarMoeda } from '../utils/currencyMask'

const PAGE_SIZE = 20

export const TIPO_INSTRUMENTO_OPTIONS = [
  { value: 'fesp', label: 'FESP — Fundo Estadual de Segurança Pública' },
  { value: 'emenda_parlamentar', label: 'Emenda Parlamentar' },
  { value: 'convenio', label: 'Convênio' },
  { value: 'contrato_repasse', label: 'Contrato de Repasse' },
  { value: 'transferencia_fundo_a_fundo', label: 'Transferência Fundo a Fundo' },
  { value: 'financiamento', label: 'Financiamento' },
]

export const STATUS_INSTRUMENTO_CLS = {
  rascunho: 'bg-gray-100 text-gray-600',
  vigente: 'bg-green-100 text-green-700',
  encerrado: 'bg-blue-100 text-blue-700',
  cancelado: 'bg-red-100 text-red-600',
}

export const pageHelp = {
  titulo: 'Instrumentos Financeiros',
  descricao: 'Cadastre os instrumentos jurídicos de origem de recursos extraordinários — FESP, emendas parlamentares, convênios, contratos de repasse, transferências fundo a fundo e financiamentos.',
  acoes: [
    { label: '+ Novo Instrumento', texto: 'Cadastra o instrumento com tipo, número externo, objeto, órgão concedente e valores pactuados.' },
  ],
  fluxo: [
    { status: 'Rascunho', descricao: 'Instrumento cadastrado, ainda não vigente.' },
    { status: 'Vigente', descricao: 'Instrumento ativo — pode financiar itens de um Plano de Aplicação.' },
    { status: 'Encerrado', descricao: 'Vigência finalizada.' },
  ],
  dica: 'Um Plano de Aplicação pode reunir itens financiados por mais de um instrumento (ex: FESP + uma emenda parlamentar no mesmo exercício).',
  baseLegal: 'Lei Estadual 14.169/2019 (FESP).',
}

export default function FespInstrumentoList() {
  const navigate = useNavigate()
  const { instrumentos, total, loading, error, fetchInstrumentos } = useInstrumentoFinanceiroStore()
  const [searchInput, setSearchInput] = useState('')
  const [tipo, setTipo] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const search = useDebouncedValue(searchInput)

  useEffect(() => { setPage(1) }, [search, tipo, status])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (tipo) params.tipo_instrumento = tipo
    if (status) params.status = status
    fetchInstrumentos(params)
  }, [search, tipo, status, page])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Instrumentos Financeiros</h1>
          <p className="text-sm text-gray-500 mt-0.5">FESP, emendas parlamentares, convênios, repasses e financiamentos</p>
        </div>
        <button
          onClick={() => navigate('/fesp/instrumentos/novo')}
          className="bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Novo instrumento
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por número, objeto, órgão concedente..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />
        <select value={tipo} onChange={(e) => setTipo(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500">
          <option value="">Todos os tipos</option>
          {TIPO_INSTRUMENTO_OPTIONS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
        </select>
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500">
          <option value="">Todos os status</option>
          <option value="rascunho">Rascunho</option>
          <option value="vigente">Vigente</option>
          <option value="encerrado">Encerrado</option>
          <option value="cancelado">Cancelado</option>
        </select>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && (
        <>
          {instrumentos.length === 0 ? (
            <EmptyState
              icon="currency"
              title="Nenhum instrumento financeiro encontrado"
              description={search || tipo || status ? 'Tente ajustar os filtros.' : 'Cadastre o primeiro instrumento (FESP, emenda, convênio...) para começar a montar um Plano de Aplicação.'}
              actionLabel={!search && !tipo && !status ? '+ Novo instrumento' : undefined}
              onAction={!search && !tipo && !status ? () => navigate('/fesp/instrumentos/novo') : undefined}
            />
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm min-w-[720px]">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Número</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Objeto</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Pactuado</th>
                      <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {instrumentos.map((i) => (
                      <tr key={i.id} onClick={() => navigate(`/fesp/instrumentos/${i.id}`)}
                        className="hover:bg-gray-50 cursor-pointer transition-colors">
                        <td className="px-5 py-3 text-gray-700">{i.tipo_instrumento_display}</td>
                        <td className="px-5 py-3 font-medium text-gray-800 font-mono">{i.numero_instrumento}</td>
                        <td className="px-5 py-3 text-gray-500 max-w-sm truncate">{i.objeto}</td>
                        <td className="px-5 py-3 text-gray-700">{formatarMoeda(i.valor_total_pactuado)}</td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_INSTRUMENTO_CLS[i.status] || ''}`}>
                            {i.status_display}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="instrumento(s)" onPage={setPage} />
        </>
      )}
    </div>
  )
}
