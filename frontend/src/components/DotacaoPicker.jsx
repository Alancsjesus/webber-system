import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import useDebouncedValue from '../hooks/useDebouncedValue'

const fmt = (v) => `R$ ${Number(v || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`

/**
 * Autocomplete de Dotação Orçamentária por ação/elemento/fonte/eixo. Mostra
 * ação, elemento, natureza, fonte e saldo (dotado − indicado) no resultado —
 * ao contrário de um <select> simples, dá contexto suficiente para escolher
 * a dotação certa sem abrir outra tela.
 */
export default function DotacaoPicker({ value, valueLabel, onChange, exercicioFiltro, placeholder = 'Buscar por ação, elemento ou fonte...' }) {
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
    const params = { search, page_size: 10 }
    if (exercicioFiltro) params.exercicio_fiscal = exercicioFiltro
    api.get('/orcamento/dotacao/', { params })
      .then(({ data }) => setResultados(data.results ?? data))
      .finally(() => setLoading(false))
  }, [search])

  useEffect(() => {
    const onClickFora = (e) => { if (boxRef.current && !boxRef.current.contains(e.target)) setAberto(false) }
    document.addEventListener('mousedown', onClickFora)
    return () => document.removeEventListener('mousedown', onClickFora)
  }, [])

  const selecionar = (d) => {
    setQuery(`${d.acao_codigo} / ${d.elemento_codigo} — ${fmt(d.valor_dotado)}`)
    setAberto(false)
    onChange(d.id, d)
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
        <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto">
          {loading ? (
            <p className="px-3 py-2 text-xs text-gray-400">Buscando...</p>
          ) : resultados.length === 0 ? (
            <p className="px-3 py-2 text-xs text-gray-400">Nenhuma dotação encontrada.</p>
          ) : (
            resultados.map(d => {
              const saldo = Number(d.valor_dotado || 0) - Number(d.valor_indicado || 0)
              return (
                <button key={d.id} type="button" onClick={() => selecionar(d)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-gray-700">Ação {d.acao_codigo} — {d.acao_nome}</span>
                    <span className={`text-xs font-semibold ${saldo < 0 ? 'text-red-600' : 'text-green-700'}`}>
                      Saldo {fmt(saldo)}
                    </span>
                  </div>
                  <span className="block text-xs text-gray-500">
                    Elemento {d.elemento_codigo} — {d.elemento_descricao}
                    {d.natureza_formato && <> · Natureza {d.natureza_formato}</>}
                    {' '}· Fonte {d.fonte_codigo} — {d.fonte_nome}
                  </span>
                  <span className="block text-xs text-gray-400">
                    Dotado {fmt(d.valor_dotado)} — Indicado {fmt(d.valor_indicado)}
                  </span>
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}
