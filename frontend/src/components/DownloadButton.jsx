import { useState } from 'react'

/**
 * Botão de download com feedback de loading e erro inline.
 *
 * Props:
 *   onClick   — função async que faz o download (deve lançar erro em caso de falha)
 *   children  — label do botão
 *   className — classes CSS extras
 *   disabled  — desabilitar externamente
 */
export default function DownloadButton({ onClick, children, className = '', disabled = false }) {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const handleClick = async () => {
    setLoading(true)
    setError(null)
    try {
      await onClick()
    } catch (err) {
      setError(err.message || 'Erro ao baixar arquivo.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <span className="inline-flex flex-col items-start">
      <button
        type="button"
        onClick={handleClick}
        disabled={loading || disabled}
        className={`text-sm px-4 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      >
        {loading ? (
          <span className="flex items-center gap-1.5">
            <svg className="animate-spin h-3 w-3 shrink-0" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Baixando...
          </span>
        ) : children}
      </button>
      {error && (
        <span className="text-xs text-red-600 mt-0.5 whitespace-nowrap">{error}</span>
      )}
    </span>
  )
}
