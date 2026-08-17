import { formatarNumeroSei } from '../utils/seiMask'

/**
 * Input controlado para número de processo SEI, com máscara suave
 * (NNN.NNNN.AAAA.NNNNNNN-DD) e link "Abrir no SEI" quando `seiBaseUrl`
 * estiver configurado (ver useAuthStore.seiBaseUrl). Não valida nem bloqueia
 * formatos diferentes — só reformata dígitos puros (Sprint E2).
 */
export default function CampoSei({ value, onChange, seiBaseUrl, placeholder, className = '', disabled = false, name }) {
  const handleChange = (e) => {
    const raw = e.target.value
    const temLetra = /[a-zA-Z]/.test(raw)
    onChange(temLetra ? raw : formatarNumeroSei(raw))
  }

  const url = seiBaseUrl && value ? `${seiBaseUrl}${encodeURIComponent(value)}` : null

  return (
    <div className="flex items-center gap-2">
      <input
        type="text"
        name={name}
        value={value || ''}
        onChange={handleChange}
        placeholder={placeholder || '099.8188.2025.0027815-30'}
        disabled={disabled}
        className={className || 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50'}
      />
      {url && (
        <a href={url} target="_blank" rel="noreferrer"
          className="text-xs text-blue-600 hover:text-blue-800 whitespace-nowrap font-medium shrink-0">
          Abrir no SEI ↗
        </a>
      )}
    </div>
  )
}

/** Exibição somente-leitura: texto formatado + link "Abrir no SEI" quando disponível. */
export function NumeroSeiTexto({ valor, seiBaseUrl, className = 'font-mono text-blue-700' }) {
  if (!valor) return null
  const formatado = formatarNumeroSei(valor)
  const url = seiBaseUrl ? `${seiBaseUrl}${encodeURIComponent(valor)}` : null

  return (
    <span className="inline-flex items-center gap-2">
      <span className={className}>{formatado}</span>
      {url && (
        <a href={url} target="_blank" rel="noreferrer"
          className="text-xs text-blue-600 hover:text-blue-800 font-medium">
          Abrir no SEI ↗
        </a>
      )}
    </span>
  )
}
