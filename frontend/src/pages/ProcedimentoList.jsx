import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useLicitacaoStore from '../stores/licitacaoStore'
import LoadingSpinner from '../components/LoadingSpinner'

const MODALIDADE_LABEL = {
  pregao_eletronico:    'Pregão Eletrônico',
  concorrencia:         'Concorrência',
  dispensa_eletronica:  'Dispensa Eletrônica',
  dispensa_tradicional: 'Dispensa por Valor',
  inexigibilidade:      'Inexigibilidade',
}

const MODALIDADE_CLS = {
  pregao_eletronico:    'bg-blue-100 text-blue-800',
  concorrencia:         'bg-indigo-100 text-indigo-800',
  dispensa_eletronica:  'bg-amber-100 text-amber-800',
  dispensa_tradicional: 'bg-orange-100 text-orange-800',
  inexigibilidade:      'bg-purple-100 text-purple-800',
}

const STATUS_CLS = {
  'Em Instrução':         'bg-gray-100 text-gray-600',
  'Aguardando Aprovação': 'bg-yellow-100 text-yellow-700',
  'Aprovado':             'bg-teal-100 text-teal-700',
  'Publicado':            'bg-blue-100 text-blue-700',
  'Em Sessão':            'bg-indigo-100 text-indigo-700',
  'Homologado':           'bg-green-100 text-green-700',
  'Contratado':           'bg-green-200 text-green-800',
  'Deserto':              'bg-red-100 text-red-600',
  'Fracassado':           'bg-red-100 text-red-700',
  'Revogado':             'bg-gray-200 text-gray-500',
  'Anulado':              'bg-gray-200 text-gray-500',
}

const fmt = v => Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function ProcedimentoList() {
  const navigate  = useNavigate()
  const { procedimentos, total, loading, error, fetchProcedimentos } = useLicitacaoStore()
  const [filtros, setFiltros] = useState({ modalidade: '', status: '', exercicio: '' })

  useEffect(() => {
    const p = {}
    if (filtros.modalidade) p.modalidade = filtros.modalidade
    if (filtros.status)     p.status     = filtros.status
    if (filtros.exercicio)  p.exercicio  = filtros.exercicio
    fetchProcedimentos(p)
  }, [filtros])

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando procedimentos..." /></div>

  return (
    <div className="p-8">
      {/* Cabeçalho */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Licitações e Contratações Diretas</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} procedimento(s) encontrado(s)</p>
        </div>
        <button onClick={() => navigate('/licitacao/novo')}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg text-sm">
          + Novo Procedimento
        </button>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <select value={filtros.modalidade}
          onChange={e => setFiltros(p => ({ ...p, modalidade: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todas as modalidades</option>
          {Object.entries(MODALIDADE_LABEL).map(([v, l]) => (
            <option key={v} value={v}>{l}</option>
          ))}
        </select>
        <select value={filtros.status}
          onChange={e => setFiltros(p => ({ ...p, status: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">Todos os status</option>
          {['Em Instrução','Aguardando Aprovação','Aprovado','Publicado','Em Sessão',
            'Homologado','Contratado','Deserto','Fracassado','Revogado','Anulado'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <input type="number" placeholder="Exercício" value={filtros.exercicio}
          onChange={e => setFiltros(p => ({ ...p, exercicio: e.target.value }))}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-500" />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-lg mb-4">{error}</div>
      )}

      {procedimentos.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">⚖️</p>
          <p className="font-medium text-gray-600">Nenhum procedimento encontrado</p>
          <p className="text-sm mt-1">Clique em "+ Novo Procedimento" para criar o primeiro.</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Número</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Modalidade</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Objeto</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500">Valor Est.</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Abertura</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-center px-4 py-3 font-medium text-gray-500">Tram.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {procedimentos.map(p => (
                <tr key={p.id} onClick={() => navigate(`/licitacao/${p.id}`)}
                  className="hover:bg-blue-50 cursor-pointer transition-colors">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-blue-700">
                    {p.numero}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${MODALIDADE_CLS[p.modalidade] || 'bg-gray-100 text-gray-600'}`}>
                      {MODALIDADE_LABEL[p.modalidade] || p.modalidade}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs truncate" title={p.objeto}>
                    {p.objeto}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-700 font-medium">
                    {p.valor_estimado ? fmt(p.valor_estimado) : '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {p.data_abertura
                      ? new Date(p.data_abertura + 'T12:00').toLocaleDateString('pt-BR')
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_CLS[p.status] || 'bg-gray-100 text-gray-600'}`}>
                      {p.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {p.tramitacoes_pendentes > 0
                      ? <span className="text-xs bg-red-100 text-red-700 font-medium px-1.5 py-0.5 rounded-full">{p.tramitacoes_pendentes}</span>
                      : <span className="text-gray-300 text-xs">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
