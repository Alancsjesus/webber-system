import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import useDebouncedValue from '../hooks/useDebouncedValue'

/**
 * Autocomplete de Fornecedor por CNPJ/CPF/nome. onChange recebe o id do
 * fornecedor selecionado (ou null se limpo). Se onCriarNovo for passado,
 * mostra um link para cadastrar um fornecedor novo quando a busca não
 * encontra resultados.
 */
export default function FornecedorPicker({ value, valueLabel, onChange, onCriarNovo, placeholder = 'Buscar por CNPJ/CPF ou nome...' }) {
  const [query, setQuery] = useState(valueLabel || '')
  const [resultados, setResultados] = useState([])
  const [aberto, setAberto] = useState(false)
  const [loading, setLoading] = useState(false)
  const search = useDebouncedValue(query)
  const boxRef = useRef(null)

  useEffect(() => { setQuery(valueLabel || '') }, [valueLabel])

  useEffect(() => {
    if (!search || search === valueLabel) { setResultados([]); return }
    setLoading(true)
    api.get('/fornecedores/', { params: { search, ativos: 'true', page_size: 10 } })
      .then(({ data }) => setResultados(data.results ?? data))
      .finally(() => setLoading(false))
  }, [search])

  useEffect(() => {
    const onClickFora = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setAberto(false) }
    document.addEventListener('mousedown', onClickFora)
    return () => document.removeEventListener('mousedown', onClickFora)
  }, [])

  const selecionar = (fornecedor) => {
    setQuery(`${fornecedor.documento} — ${fornecedor.nome_razao_social}`)
    setAberto(false)
    onChange(fornecedor.id, fornecedor)
  }

  const limpar = () => {
    setQuery('')
    onChange(null, null)
  }

  return (
    <div className="relative" ref={boxRef}>
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => { setQuery(e.target.value); setAberto(true); if (value) onChange(null, null) }}
          onFocus={() => setAberto(true)}
          placeholder={placeholder}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {value && (
          <button type="button" onClick={limpar} className="text-xs text-gray-400 hover:text-gray-600 px-2">✕</button>
        )}
      </div>

      {aberto && query && !value && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {loading ? (
            <p className="px-3 py-2 text-xs text-gray-400">Buscando...</p>
          ) : resultados.length === 0 ? (
            <div className="px-3 py-2 text-xs text-gray-400">
              Nenhum fornecedor encontrado.
              {onCriarNovo && (
                <button type="button" onClick={() => onCriarNovo(query)} className="block text-blue-600 hover:underline mt-1">
                  + Cadastrar novo fornecedor
                </button>
              )}
            </div>
          ) : (
            resultados.map(f => (
              <button key={f.id} type="button" onClick={() => selecionar(f)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                <span className="font-mono text-xs text-gray-500">{f.documento}</span>
                <span className="block text-gray-800">{f.nome_razao_social}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
