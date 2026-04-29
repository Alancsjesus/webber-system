import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useContratoStore from '../stores/contratoStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'

const STATUS_CLS = {
  Vigente:    'bg-green-100 text-green-700',
  Encerrado:  'bg-gray-100 text-gray-500',
  Suspenso:   'bg-yellow-100 text-yellow-700',
  Rescindido: 'bg-red-100 text-red-600',
}

const fmt = (v) => Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

export default function ContratoList() {
  const navigate = useNavigate()
  const { contratos, loading, fetchContratos } = useContratoStore()

  useEffect(() => { fetchContratos() }, [])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Contratos</h1>
          <p className="text-sm text-gray-500 mt-0.5">Contratos, apostilas e aditivos do órgão</p>
        </div>
        <button onClick={() => navigate('/contratos/novo')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Novo contrato
        </button>
      </div>

      {loading ? <LoadingSpinner /> : contratos.length === 0 ? (
        <EmptyState icon="document" title="Nenhum contrato cadastrado"
          description="Registre os contratos celebrados pelo órgão." />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Número</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Objeto</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Origem</th>
                <th className="text-right px-5 py-3 font-medium text-gray-500">Valor</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Vigência até</th>
                <th className="text-left px-5 py-3 font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {contratos.map(c => (
                <tr key={c.id} className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/contratos/${c.id}`)}>
                  <td className="px-5 py-3 font-mono font-semibold text-gray-800">{c.numero}</td>
                  <td className="px-5 py-3 text-gray-700 max-w-xs truncate">{c.objeto}</td>
                  <td className="px-5 py-3 text-gray-500">{c.tipo_origem_display}</td>
                  <td className="px-5 py-3 text-right font-semibold text-gray-800">{fmt(c.valor_contrato)}</td>
                  <td className="px-5 py-3 text-gray-500">
                    {c.data_vigencia_fim ? new Date(c.data_vigencia_fim).toLocaleDateString('pt-BR') : '—'}
                  </td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[c.status] || 'bg-gray-100 text-gray-500'}`}>
                      {c.status}
                    </span>
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
