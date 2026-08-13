import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import useDebouncedValue from '../hooks/useDebouncedValue'

const TIPO_CLS = {
  DFD: 'bg-blue-100 text-blue-700',
  ETP: 'bg-indigo-100 text-indigo-700',
  TR: 'bg-violet-100 text-violet-700',
  Procedimento: 'bg-amber-100 text-amber-700',
  Contrato: 'bg-green-100 text-green-700',
  Necessidade: 'bg-slate-100 text-slate-700',
}

export default function CommandPalette({ open, onClose }) {
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [resultados, setResultados] = useState([])
  const [loading, setLoading] = useState(false)
  const [ativo, setAtivo] = useState(0)
  const inputRef = useRef(null)
  const q = useDebouncedValue(input, 300)

  useEffect(() => {
    if (open) {
      setInput(''); setResultados([]); setAtivo(0)
      setTimeout(() => inputRef.current?.focus(), 0)
    }
  }, [open])

  useEffect(() => {
    if (!open || q.trim().length < 2) { setResultados([]); return }
    setLoading(true)
    api.get('/busca-global/', { params: { q: q.trim() } })
      .then(({ data }) => { setResultados(data.resultados || []); setAtivo(0) })
      .catch(() => setResultados([]))
      .finally(() => setLoading(false))
  }, [q, open])

  useEffect(() => {
    if (!open) return
    const handler = (e) => {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key === 'ArrowDown') { e.preventDefault(); setAtivo(a => Math.min(a + 1, resultados.length - 1)) }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setAtivo(a => Math.max(a - 1, 0)) }
      if (e.key === 'Enter' && resultados[ativo]) { e.preventDefault(); ir(resultados[ativo]) }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, resultados, ativo])

  const ir = (r) => {
    navigate(r.url)
    onClose()
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 bg-black/40 flex items-start justify-center pt-24 z-50" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100">
          <span className="text-gray-400">🔎</span>
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Buscar DFD, ETP, TR, procedimento, contrato, necessidade..."
            className="flex-1 text-sm focus:outline-none"
          />
          <kbd className="text-[10px] text-gray-400 border border-gray-200 rounded px-1.5 py-0.5">Esc</kbd>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {loading && <p className="px-4 py-6 text-xs text-gray-400 text-center italic">Buscando...</p>}

          {!loading && q.trim().length >= 2 && resultados.length === 0 && (
            <p className="px-4 py-6 text-xs text-gray-400 text-center italic">Nenhum resultado para "{q}".</p>
          )}

          {!loading && q.trim().length < 2 && (
            <p className="px-4 py-6 text-xs text-gray-400 text-center italic">Digite ao menos 2 caracteres.</p>
          )}

          {!loading && resultados.map((r, i) => (
            <button
              key={`${r.tipo}-${r.id}`}
              onClick={() => ir(r)}
              onMouseEnter={() => setAtivo(i)}
              className={`w-full text-left px-4 py-2.5 flex items-center gap-3 border-b border-gray-50 last:border-0 transition-colors ${
                i === ativo ? 'bg-blue-50' : 'hover:bg-gray-50'
              }`}
            >
              <span className={`shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded ${TIPO_CLS[r.tipo] || 'bg-gray-100 text-gray-600'}`}>
                {r.tipo}
              </span>
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-gray-800 truncate">{r.label}</span>
                {r.sublabel && <span className="block text-xs text-gray-400 truncate">{r.sublabel}</span>}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
