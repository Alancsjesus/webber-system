import { useState, useRef, useEffect } from 'react'

/**
 * Tooltip inline de ajuda contextual.
 * Uso: <HelpTip text="Explica o que este botão faz." />
 * Props:
 *   text      — string ou JSX com o conteúdo do tooltip
 *   position  — "top" | "bottom" | "left" | "right" (default "top")
 *   className — classes extras no container
 */
export default function HelpTip({ text, position = 'top', className = '' }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const posClasses = {
    top:    'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left:   'right-full top-1/2 -translate-y-1/2 mr-2',
    right:  'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  const arrowClasses = {
    top:    'top-full left-1/2 -translate-x-1/2 border-t-gray-200 border-x-transparent border-b-transparent border-4',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-200 border-x-transparent border-t-transparent border-4',
    left:   'left-full top-1/2 -translate-y-1/2 border-l-gray-200 border-y-transparent border-r-transparent border-4',
    right:  'right-full top-1/2 -translate-y-1/2 border-r-gray-200 border-y-transparent border-l-transparent border-4',
  }

  return (
    <span ref={ref} className={`relative inline-flex items-center ${className}`}>
      <button
        type="button"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen(v => !v)}
        className="w-4 h-4 rounded-full bg-gray-200 hover:bg-blue-500 text-gray-600 hover:text-white text-[10px] font-bold flex items-center justify-center transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400"
        aria-label="Ajuda"
      >
        ?
      </button>

      {open && (
        <span className={`absolute z-50 w-64 ${posClasses[position]}`}>
          <span className="block bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 text-xs text-gray-700 leading-relaxed">
            {text}
          </span>
          <span className={`absolute w-0 h-0 ${arrowClasses[position]}`} />
        </span>
      )}
    </span>
  )
}
