import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useTrStore from '../stores/trStore'

const STATUS_CLS = {
  Rascunho:    'bg-gray-100 text-gray-600',
  Submetido:   'bg-blue-100 text-blue-700',
  'Em Análise':'bg-yellow-100 text-yellow-700',
  Devolvido:   'bg-orange-100 text-orange-700',
  Aprovado:    'bg-green-100 text-green-700',
  Cancelado:   'bg-red-100 text-red-700',
}

export default function TRList() {
  const navigate = useNavigate()
  const { trs, total, loading, error, fetchTrs } = useTrStore()
  const [search, setSearch] = useState('')
  const [statusFiltro, setStatusFiltro] = useState('')

  useEffect(() => {
    const params = {}
    if (search) params.search = search
    if (statusFiltro) params.status = statusFiltro
    fetchTrs(params)
  }, [search, statusFiltro])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Termos de Referência</h1>
          <p className="text-sm text-gray-500 mt-0.5">TRs gerados a partir de ETPs aprovados</p>
        </div>
      </div>

      <div className="flex gap-3 mb-5">
        <input type="text" placeholder="Buscar por SEI ou objeto..."
          value={search} onChange={(e) => setSearch(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
        <select value={statusFiltro} onChange={(e) => setStatusFiltro(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500">
          <option value="">Todos os status</option>
          {Object.keys(STATUS_CLS).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>
      )}

      {loading ? (
        <p className="text-sm text-gray-400 text-center py-10">Carregando...</p>
      ) : trs.length === 0 ? (
        <div className="text-center py-16 text-gray-400 text-sm">Nenhum TR encontrado.</div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Nº SEI TR</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">ETP</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">DFD</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Órgão</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Est.</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {trs.map((t) => (
                  <tr key={t.id} onClick={() => navigate(`/analise-tecnica/trs/${t.id}`)}
                    className="hover:bg-gray-50 cursor-pointer">
                    <td className="px-5 py-3 font-medium text-gray-800">{t.numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.etp_numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.dfd_numero_sei}</td>
                    <td className="px-5 py-3 text-gray-500">{t.org_sigla}</td>
                    <td className="px-5 py-3 text-gray-700">
                      {t.estimativa_valor
                        ? Number(t.estimativa_valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                        : '—'}
                    </td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[t.status] || ''}`}>
                        {t.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
