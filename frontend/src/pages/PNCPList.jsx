import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

const STATUS_CLS = {
  pendente:     'bg-gray-100 text-gray-500',
  em_andamento: 'bg-yellow-100 text-yellow-700',
  concluida:    'bg-green-100 text-green-700',
  erro:         'bg-red-100 text-red-600',
}
const STATUS_LABEL = {
  pendente:     'Pendente',
  em_andamento: 'Em andamento',
  concluida:    'Concluída',
  erro:         'Erro',
}
const fmt = (v) => v != null ? Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—'
const fmtDate = (s) => s ? new Date(s + 'T00:00:00').toLocaleDateString('pt-BR') : '—'

export default function PNCPList() {
  const navigate = useNavigate()
  const [list, setList]       = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    api.get('/pncp/importacoes/', { params: { page_size: 100 } })
      .then(({ data }) => setList(data.results ?? data))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6 max-w-5xl">
      {/* Cabeçalho */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-800">Importações PNCP</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Histórico de consultas ao Portal Nacional de Contratações Públicas realizadas pelo órgão.
          As importações são iniciadas dentro de cada Mapa Comparativo de Preços.
        </p>
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : list.length === 0 ? (
        <EmptyState
          icon="search"
          title="Nenhuma importação PNCP encontrada"
          description="As importações são iniciadas na aba de Itens e Preços de um Mapa Comparativo."
          actionLabel="Ir para Pesquisa de Preços"
          onAction={() => navigate('/pesquisa/mapa')}
        />
      ) : (
        <div className="space-y-3">
          {list.map(imp => {
            const open = expanded === imp.id
            const totalReg = imp.registros?.length ?? 0
            const importados = imp.registros?.filter(r => r.importado).length ?? 0
            return (
              <div key={imp.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                {/* Linha resumo */}
                <button
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors text-left"
                  onClick={() => setExpanded(open ? null : imp.id)}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${STATUS_CLS[imp.status] || 'bg-gray-100 text-gray-500'}`}>
                      {STATUS_LABEL[imp.status] || imp.status}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {imp.termo_busca || 'Busca sem filtro de termo'}
                        {imp.cnpj_orgao_referencia && (
                          <span className="ml-2 text-xs text-gray-400 font-mono">{imp.cnpj_orgao_referencia}</span>
                        )}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        UF: {imp.uf} · Período: {fmtDate(imp.periodo_inicio)} a {fmtDate(imp.periodo_fim)}
                        {' · '}Tipo fonte: {imp.tipo_fonte}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 ml-4">
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {imp.total_consultados} consultados · {imp.total_importados} importados
                      </p>
                      <p className="text-[10px] text-gray-400">
                        {new Date(imp.created_at).toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    {imp.mapa && (
                      <button
                        onClick={e => { e.stopPropagation(); navigate(`/pesquisa/mapa/${imp.mapa}`) }}
                        className="text-xs text-blue-600 hover:underline shrink-0"
                      >
                        Ver Mapa
                      </button>
                    )}
                    <span className={`text-gray-400 text-xs transition-transform duration-200 ${open ? 'rotate-90' : ''}`}>›</span>
                  </div>
                </button>

                {/* Erro */}
                {imp.erro_mensagem && (
                  <div className="px-5 py-2 bg-red-50 border-t border-red-100 text-xs text-red-600">
                    {imp.erro_mensagem}
                  </div>
                )}

                {/* Registros expandidos */}
                {open && imp.registros && imp.registros.length > 0 && (
                  <div className="border-t border-gray-100">
                    <div className="px-5 py-2 bg-gray-50 flex items-center justify-between">
                      <span className="text-xs font-medium text-gray-600">
                        {totalReg} registro{totalReg !== 1 ? 's' : ''} · {importados} importado{importados !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-gray-50 border-b border-gray-100">
                          <tr>
                            <th className="text-left px-4 py-2 font-medium text-gray-500">Objeto</th>
                            <th className="text-left px-4 py-2 font-medium text-gray-500">Órgão</th>
                            <th className="text-left px-4 py-2 font-medium text-gray-500">Modalidade</th>
                            <th className="text-right px-4 py-2 font-medium text-gray-500">Valor Unit.</th>
                            <th className="text-right px-4 py-2 font-medium text-gray-500">Qtd</th>
                            <th className="text-center px-4 py-2 font-medium text-gray-500">Importado</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {imp.registros.map(r => (
                            <tr key={r.id} className={`hover:bg-gray-50 ${r.importado ? 'bg-green-50/30' : ''}`}>
                              <td className="px-4 py-2 max-w-xs">
                                <p className="truncate text-gray-800" title={r.objeto}>{r.objeto}</p>
                                <p className="text-[10px] text-gray-400 font-mono">{r.numero_pncp}</p>
                              </td>
                              <td className="px-4 py-2 text-gray-600 max-w-[160px]">
                                <p className="truncate" title={r.orgao_nome}>{r.orgao_nome || '—'}</p>
                                <p className="text-[10px] text-gray-400">{r.uf}</p>
                              </td>
                              <td className="px-4 py-2 text-gray-500">{r.modalidade || '—'}</td>
                              <td className="px-4 py-2 text-right font-medium text-gray-700">{fmt(r.valor_unitario)}</td>
                              <td className="px-4 py-2 text-right text-gray-500">{r.quantidade ?? '—'} {r.unidade_medida}</td>
                              <td className="px-4 py-2 text-center">
                                {r.importado
                                  ? <span className="text-green-600 font-medium">✓</span>
                                  : <span className="text-gray-300">—</span>
                                }
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {open && (!imp.registros || imp.registros.length === 0) && (
                  <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400 italic">
                    Nenhum registro retornado nesta importação.
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
