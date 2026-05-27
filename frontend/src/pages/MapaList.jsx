import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useMapaStore from '../stores/mapaStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Rascunho:   'bg-gray-100 text-gray-600',
  Finalizado: 'bg-green-100 text-green-700',
  Cancelado:  'bg-red-100 text-red-600',
}

const fmt = (v) =>
  Number(v ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Mapas de Preços — Pesquisa de Mercado',
  descricao: 'Lista as pesquisas de preços realizadas para estimar o valor das contratações. Cada mapa deve conter ao menos 3 fontes válidas por item.',
  acoes: [
    { label: '+ Novo Mapa', texto: 'Cria uma nova pesquisa de preços vinculada a uma necessidade ou procedimento. Defina os itens e colete preços de múltiplas fontes.' },
  ],
  dica: 'Use preços do PNCP (Tipo I) como primeira fonte — são os mais aceitos pelos órgãos de controle.',
  baseLegal: 'Lei 14.133/2021 — Art. 23 e IN SEGES nº 65/2021.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function MapaList() {
  const navigate = useNavigate()
  const { mapas, total, loading, error, fetchMapas } = useMapaStore()
  const [status, setStatus]     = useState('')
  const [exercicio, setExercicio] = useState('')

  useEffect(() => {
    const params = {}
    if (status)    params.status           = status
    if (exercicio) params.exercicio_fiscal = exercicio
    fetchMapas(params)
  }, [status, exercicio])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Mapa Comparativo de Preços</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Pesquisa de preços conforme Decreto Estadual 22.886/2024 — Art. 3º e 8º
          </p>
        </div>
        <button onClick={() => navigate('/pesquisa/mapa/novo')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          + Novo Mapa
        </button>
      </div>

      <div className="flex flex-wrap gap-3 mb-5">
        <input type="number" placeholder="Exercício"
          value={exercicio} onChange={(e) => setExercicio(e.target.value)}
          className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os status</option>
          <option value="Rascunho">Rascunho</option>
          <option value="Finalizado">Finalizado</option>
          <option value="Cancelado">Cancelado</option>
        </select>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {loading && <LoadingSpinner />}

      {!loading && mapas.length === 0 && (
        <EmptyState icon="search" title="Nenhum mapa encontrado"
          description={status || exercicio ? 'Ajuste os filtros.' : 'Inicie a pesquisa de preços criando um novo Mapa Comparativo.'}
          actionLabel={!status && !exercicio ? '+ Novo Mapa' : undefined}
          onAction={!status && !exercicio ? () => navigate('/pesquisa/mapa/novo') : undefined} />
      )}

      {!loading && mapas.length > 0 && (
        <>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[640px]">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Objeto</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">DFD</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Exercício</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Itens</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Fontes</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Valor Total</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {mapas.map((m) => (
                  <tr key={m.id} onClick={() => navigate(`/pesquisa/mapa/${m.id}`)}
                    className="hover:bg-gray-50 cursor-pointer transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-800 max-w-xs truncate">{m.objeto}</td>
                    <td className="px-5 py-3 font-mono text-xs text-blue-700">{m.dfd_numero_sei || '—'}</td>
                    <td className="px-5 py-3 text-gray-600">{m.exercicio_fiscal}</td>
                    <td className="px-5 py-3 text-gray-600 text-center">{m.qtd_itens}</td>
                    <td className="px-5 py-3 text-gray-600 text-center">{m.qtd_fontes}</td>
                    <td className="px-5 py-3 font-semibold text-gray-800">{fmt(m.valor_estimado_total)}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_CLS[m.status] || ''}`}>
                        {m.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3">{total} registro(s)</p>
        </>
      )}
    </div>
  )
}
