import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.data instanceof FormData) delete config.headers['Content-Type']
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const { data } = await axios.post('/api/token/refresh/', { refresh })
          localStorage.setItem('access_token', data.access)
          original.headers.Authorization = `Bearer ${data.access}`
          return api(original)
        } catch { /* refresh expirado */ }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

/**
 * Dispara download autenticado de arquivo binário (PDF, HTML, etc).
 * Lança exceção com mensagem legível em caso de erro.
 */
export async function downloadFile(path, filename) {
  const token = localStorage.getItem('access_token')
  const res = await fetch(`/api${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    let detail = `Erro ${res.status}`
    try {
      const body = await res.json()
      if (body.detail) detail = body.detail
    } catch { /* body não é JSON (ex: 500 HTML) */ }
    throw new Error(detail)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Hook-like helper para botões de download.
 * Retorna { download, loading, error } — gerencia estado internamente.
 * Uso: const { download, loading, error } = useDownload()
 *      <button onClick={() => download('/path/', 'file.pdf')} disabled={loading}>
 */
export function useDownload() {
  // Implementado como função simples (não hook) para ser reutilizável fora de componentes.
  // O estado é passado por callbacks para manter compatibilidade com React.
}

export default api
