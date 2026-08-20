import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useFornecedorStore from '../stores/fornecedorStore'
import EmptyState from '../components/EmptyState'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import useDebouncedValue from '../hooks/useDebouncedValue'

const PAGE_SIZE = 20

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Fornecedores',
  descricao: 'Cadastro único de fornecedores (pessoa física ou jurídica) do sistema, compartilhado entre todos os órgãos. Permite verificar se um fornecedor já teve relação anterior com a administração — cotações, licitações vencidas, contratos executados.',
  acoes: [
    { label: '+ Novo Fornecedor', texto: 'Cadastra um fornecedor por CNPJ (pessoa jurídica) ou CPF (pessoa física), com validação de dígito verificador.' },
    { label: 'Buscar',            texto: 'Busca pelo documento, razão social ou nome fantasia.' },
    { label: 'Ver histórico',     texto: 'Na tela de detalhe, mostra todas as cotações, licitações e contratos já vinculados a este fornecedor.' },
  ],
  dica: 'Antes de selecionar um fornecedor numa nova cotação ou licitação, consulte o histórico dele para verificar relações anteriores com a administração.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FornecedorList() {
  const navigate = useNavigate()
  const { fornecedores, total, loading, fetchFornecedores } = useFornecedorStore()
  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(1)
  const search = useDebouncedValue(searchInput)

  useEffect(() => { setPage(1) }, [search])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    fetchFornecedores(params)
  }, [search, page])

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Fornecedores</h1>
          <p className="text-sm text-gray-500 mt-0.5">Cadastro único de fornecedores, PJ e PF</p>
        </div>
        <button onClick={() => navigate('/fornecedores/novo')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          + Novo fornecedor
        </button>
      </div>

      <div className="mb-5">
        <input
          type="text"
          placeholder="Buscar por CNPJ/CPF, razão social ou nome fantasia..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="w-full sm:w-96 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {loading ? <LoadingSpinner /> : fornecedores.length === 0 ? (
        <EmptyState icon="document" title="Nenhum fornecedor cadastrado"
          description={search ? 'Tente ajustar a busca.' : 'Cadastre os fornecedores que participam de cotações, licitações e contratos.'} />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Documento</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Nome / Razão social</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Tipo</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500">Situação</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {fornecedores.map(f => (
                  <tr key={f.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/fornecedores/${f.id}`)}>
                    <td className="px-5 py-3 font-mono text-gray-800">{f.documento}</td>
                    <td className="px-5 py-3 text-gray-700">
                      {f.nome_razao_social}
                      {f.nome_fantasia && <span className="text-gray-400"> ({f.nome_fantasia})</span>}
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs">{f.tipo_pessoa === 'PJ' ? 'Pessoa Jurídica' : 'Pessoa Física'}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${f.ativo ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {f.ativo ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right">
                      <span className="text-xs text-blue-600 hover:underline">Ver detalhes</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="fornecedor(es)" onPage={setPage} />
    </div>
  )
}
