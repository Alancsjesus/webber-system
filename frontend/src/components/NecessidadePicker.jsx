import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import useDebouncedValue from '../hooks/useDebouncedValue'

const fmt = (v) => v == null ? '' : `R$ ${Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`

/**
 * Autocomplete de Necessidade de Planejamento por título/descrição/departamento.
 * onChange recebe o id da necessidade selecionada (ou null se limpo). Mostra
 * departamento e valor estimado no resultado para ajudar a diferenciar
 * necessidades com títulos parecidos.
 */
export default function NecessidadePicker({ value, valueLabel, onChange, status = 'Aprovada', placeholder = 'Buscar por título, descrição ou departamento...' }) {
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
    api.get('/planejamento/necessidade/', { params: { search, status, page_size: 10 } })
      .then(({ data }) => setResultados(data.results ?? data))
      .finally(() => setLoading(false))
  }, [search])

  useEffect(() => {
    const onClickFora = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setAberto(false) }
    document.addEventListener('mousedown', onClickFora)
    return () => document.removeEventListener('mousedown', onClickFora)
  }, [])

  const selecionar = (nec) => {
    setQuery(`${nec.titulo} (${nec.exercicio_fiscal})`)
    setAberto(false)
    onChange(nec.id, nec)
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
            <p className="px-3 py-2 text-xs text-gray-400">Nenhuma necessidade encontrada.</p>
          ) : (
            resultados.map(n => (
              <button key={n.id} type="button" onClick={() => selecionar(n)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                <span className="block text-gray-800">{n.titulo} <span className="text-gray-400">({n.exercicio_fiscal})</span></span>
                <span className="block text-xs text-gray-500">
                  {n.departamento_solicitante || '—'}
                  {n.valor_estimado != null && <span className="ml-2 text-gray-400">· {fmt(n.valor_estimado)}</span>}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
