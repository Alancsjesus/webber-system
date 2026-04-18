import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

const TIPO_UNIDADE_LABEL = {
  demandante:  'Unidade Demandante',
  licitante:   'Unidade Licitante',
  contratante: 'Unidade Contratante',
}

const TIPO_UNIDADE_CLS = {
  demandante:  'bg-purple-100 text-purple-700 border-purple-200',
  licitante:   'bg-blue-100 text-blue-700 border-blue-200',
  contratante: 'bg-green-100 text-green-700 border-green-200',
}

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  const { login, loading, error, isAuthenticated,
          orgaoSigla, orgaoNome, unidadeNome, tipoUnidade, papel } = useAuthStore()
  const navigate = useNavigate()

  // Se já estava autenticado ao entrar na página, redireciona direto
  useEffect(() => {
    if (isAuthenticated && !confirmed) navigate('/demanda/dfd', { replace: true })
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    await login(username, password)
    if (useAuthStore.getState().isAuthenticated) {
      setConfirmed(true)   // mostra painel de confirmação antes de redirecionar
    }
  }

  // Painel de confirmação pós-login
  if (confirmed && isAuthenticated) {
    const tipo = tipoUnidade
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white rounded-xl shadow-md w-full max-w-sm p-8 text-center">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">✓</span>
          </div>
          <h2 className="text-lg font-bold text-gray-800 mb-1">Acesso autorizado</h2>
          <p className="text-sm text-gray-500 mb-5">Você está conectado como:</p>

          <div className="text-left bg-gray-50 rounded-xl border border-gray-200 p-4 space-y-3 mb-6">
            <Row label="Usuário" value={username} />
            <Row label="Perfil"  value={papel?.replace(/_/g, ' ')} caps />
            <div className="border-t border-gray-100 pt-3">
              <Row label="Órgão"   value={orgaoSigla ? `${orgaoSigla} — ${orgaoNome}` : '—'} bold />
              <Row label="Unidade" value={unidadeNome || '—'} />
              {tipo && (
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-400">Tipo</span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${TIPO_UNIDADE_CLS[tipo] || 'bg-gray-100 text-gray-600'}`}>
                    {TIPO_UNIDADE_LABEL[tipo] || tipo}
                  </span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => navigate('/demanda/dfd', { replace: true })}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-lg text-sm transition-colors"
          >
            Continuar para o sistema →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white rounded-xl shadow-md w-full max-w-sm p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">Webber</h1>
        <p className="text-sm text-gray-500 mb-6">Sistema de planejamento e contratações</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Usuário</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-sm transition-colors"
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Row({ label, value, bold, caps }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-400">{label}</span>
      <span className={`text-sm text-gray-700 ${bold ? 'font-semibold' : ''} ${caps ? 'capitalize' : ''}`}>
        {value}
      </span>
    </div>
  )
}
