import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import useDebouncedValue from '../hooks/useDebouncedValue'

/**
 * Autocomplete de DFD por número SEI/descrição. onChange recebe o id do
 * DFD selecionado (ou null se limpo). Evita listas longas quando há vários
 * DFDs parecidos — busca no backend em vez de carregar tudo de uma vez.
 */
export default function DFDPicker({ value, valueLabel, onChange, status = 'Aprovada', placeholder = 'Buscar por número SEI ou descrição...' }) {
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
    api.get('/demanda/dfd/', { params: { search, status, page_size: 10 } })
      .then(({ data }) => setResultados(data.results ?? data))
      .finally(() => setLoading(false))
  }, [search])

  useEffect(() => {
    const onClickFora = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setAberto(false) }
    document.addEventListener('mousedown', onClickFora)
    return () => document.removeEventListener('mousedown', onClickFora)
  }, [])

  const selecionar = (dfd) => {
    setQuery(`${dfd.numero_sei} — ${dfd.descricao?.slice(0, 50) || ''}`)
    setAberto(false)
    onChange(dfd.id, dfd)
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
            <p className="px-3 py-2 text-xs text-gray-400">Nenhum DFD encontrado.</p>
          ) : (
            resultados.map(d => (
              <button key={d.id} type="button" onClick={() => selecionar(d)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                <span className="font-mono text-xs text-gray-500">{d.numero_sei}</span>
                <span className="block text-gray-800">{d.descricao?.slice(0, 80)}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
