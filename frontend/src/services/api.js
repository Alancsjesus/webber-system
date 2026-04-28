import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Injeta o token e corrige Content-Type para FormData
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Quando o payload é FormData, o Axios precisa definir o boundary automaticamente.
  // Remover o Content-Type fixo permite que o browser o gere corretamente.
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

// Se 401, tenta refresh; se falhar, desloga
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
        } catch {
          // refresh expirado — limpa sessão
        }
      }

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

export async function downloadFile(path, filename) {
  const token = localStorage.getItem('access_token')
  const res = await fetch(`/api${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(`Erro ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default api
