import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAtaStore from '../stores/ataStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'

const PAGE_SIZE = 20

const STATUS_CLS = {
  rascunho:  'bg-gray-100 text-gray-600',
  vigente:   'bg-green-100 text-green-700',
  encerrada: 'bg-blue-100 text-blue-700',
  cancelada: 'bg-red-100 text-red-600',
}
const STATUS_LABEL = { rascunho: 'Rascunho', vigente: 'Vigente', encerrada: 'Encerrada', cancelada: 'Cancelada' }
const TIPO_LABEL = { gerenciador: 'Gerenciador', participante: 'Participante', carona: 'Carona' }

const fmt = (v) => Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Atas de Registro de Preços',
  descricao: 'Cadastro de Atas de Registro de Preços — próprias (geradas por procedimento deste órgão) ou de carona (aderidas de ata gerenciada por outro órgão). Permite verificar quais itens de DFDs pendentes já têm saldo disponível numa ata vigente, evitando abrir uma nova licitação desnecessariamente.',
  acoes: [
    { label: '+ Nova Ata',                texto: 'Cadastra uma ata própria ou de carona, com seus itens e quantidades registradas.' },
    { label: 'Confronto de Necessidades', texto: 'Mostra os itens de DFDs pendentes de contratação que já têm saldo disponível em alguma ata vigente deste órgão.' },
    { label: 'Filtros',                   texto: 'Combine status e tipo de origem para refinar a lista.' },
  ],
  dica: 'Só atas com status "Vigente" e saldo disponível entram no confronto de necessidades.',
  baseLegal: 'Lei 14.133/2021 — Art. 82 a 86.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function AtaList() {
  const navigate = useNavigate()
  const { atas, total, loading, fetchAtas, confronto, fetchConfronto } = useAtaStore()
  const [searchInput, setSearchInput] = useState('')
  const [status, setStatus] = useState('')
  const [tipoOrigem, setTipoOrigem] = useState('')
  const [page, setPage] = useState(1)
  const [showConfronto, setShowConfronto] = useState(false)
  const [loadingConfronto, setLoadingConfronto] = useState(false)
  const search = useDebouncedValue(searchInput)

  useEffect(() => { setPage(1) }, [search, status, tipoOrigem])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    if (status) params.status = status
    if (tipoOrigem) params.tipo_origem = tipoOrigem
    fetchAtas(params)
  }, [search, status, tipoOrigem, page])

  const abrirConfronto = async () => {
    setShowConfronto(true)
    setLoadingConfronto(true)
    try { await fetchConfronto() } finally { setLoadingConfronto(false) }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Atas de Registro de Preços</h1>
          <p className="text-sm text-gray-500 mt-0.5">Atas próprias e de carona — Lei 14.133/2021, Art. 82-86</p>
        </div>
        <div className="flex gap-2">
          <button onClick={abrirConfronto}
            className="border border-indigo-300 text-indigo-700 hover:bg-indigo-50 text-sm font-medium px-4 py-2 rounded-lg">
            Confronto de Necessidades
          </button>
          <button onClick={() => navigate('/arp/novo')}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
            + Nova Ata
          </button>
        </div>
      </div>

      {showConfronto && (
        <div className="mb-6 bg-white border border-indigo-200 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 bg-indigo-50 border-b border-indigo-100">
            <p className="text-sm font-semibold text-indigo-800">
              Itens de DFDs pendentes com saldo disponível em ata vigente
            </p>
            <button onClick={() => setShowConfronto(false)} className="text-xs text-indigo-500 hover:text-indigo-700">
              Fechar
            </button>
          </div>
          {loadingConfronto ? (
            <div className="p-6"><LoadingSpinner /></div>
          ) : !confronto || confronto.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">
              Nenhum item pendente com correspondência em ata vigente no momento.
            </p>
          ) : (
            <div className="divide-y divide-gray-100">
              {confronto.map((c) => (
                <div key={c.item_dfd.id} className="px-5 py-3">
                  <p className="text-sm font-medium text-gray-800">
                    {c.item_dfd.catalogo_nome}
                    <span className="text-xs text-gray-400 font-normal ml-2">
                      DFD {c.item_dfd.dfd_numero_sei} · Qtd. {c.item_dfd.quantidade}
                    </span>
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-2">
                    {c.sugestoes.map((s) => (
                      <button key={s.item_ata_id} onClick={() => navigate(`/arp/${s.ata_id}`)}
                        className="text-xs bg-green-50 border border-green-200 text-green-800 hover:bg-green-100 px-2.5 py-1 rounded-lg">
                        Ata {s.ata_numero} — saldo {s.saldo_disponivel} · {fmt(s.valor_unitario_registrado)}/un
                        {s.fornecedor_nome && ` · ${s.fornecedor_nome}`}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-3 mb-5">
        <input
          type="text"
          placeholder="Buscar por número da ata, objeto ou órgão gerenciador..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 min-w-[240px] border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">Todos os status</option>
          {Object.entries(STATUS_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={tipoOrigem} onChange={(e) => setTipoOrigem(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">Todos os tipos de origem</option>
          {Object.entries(TIPO_LABEL).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      {loading ? <LoadingSpinner /> : atas.length === 0 ? (
        <EmptyState icon="document" title="Nenhuma ata cadastrada"
          description={search ? 'Tente ajustar a busca.' : 'Cadastre as atas de registro de preços deste órgão.'} />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Número</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Objeto</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Vigência até</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {atas.map(a => (
                  <tr key={a.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/arp/${a.id}`)}>
                    <td className="px-5 py-3 font-mono text-gray-800">{a.numero_ata}</td>
                    <td className="px-5 py-3 text-gray-700 max-w-xs truncate">{a.objeto}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{TIPO_LABEL[a.tipo_origem]}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[a.status] || ''}`}>
                        {STATUS_LABEL[a.status]}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs">
                      {a.data_vigencia_fim ? new Date(a.data_vigencia_fim).toLocaleDateString('pt-BR') : '—'}
                    </td>
                    <td className="px-5 py-3 text-right">
                      <span className="text-xs text-indigo-600 hover:underline">Ver detalhes</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="ata(s)" onPage={setPage} />
    </div>
  )
}
