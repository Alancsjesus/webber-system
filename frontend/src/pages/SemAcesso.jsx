import { useNavigate, useLocation } from 'react-router-dom'
import useAuthStore from '../stores/authStore'

const PAPEL_LABEL = {
  admin:               'Administrador',
  analista:            'Analista de Contratações',
  gestor_planejamento: 'Gestor de Planejamento',
  gestor_contrato:     'Gestor de Contrato',
  fiscal_contrato:     'Fiscal de Contrato',
  ordenador:           'Ordenador de Despesas',
  solicitante:         'Solicitante',
  responsavel_tecnico: 'Responsável Técnico',
}

export default function SemAcesso() {
  const navigate  = useNavigate()
  const location  = useLocation()
  const papel     = useAuthStore(s => s.papel)
  const rotaTentada = location.state?.from || ''

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-10 max-w-md w-full text-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-5">
          <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 15v2m0 0v2m0-2h2m-2 0H10m2-6V9m0 0V7m0 2h2m-2 0H10m9 4a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-xl font-bold text-gray-800 mb-2">Acesso não autorizado</h1>
        <p className="text-sm text-gray-500 mb-1">
          Seu perfil <strong className="text-gray-700">{PAPEL_LABEL[papel] || papel}</strong> não tem
          permissão para acessar esta área.
        </p>
        {rotaTentada && (
          <p className="text-xs text-gray-400 mb-5 font-mono">{rotaTentada}</p>
        )}
        <p className="text-xs text-gray-400 mb-6">
          Se você acredita que deveria ter acesso, entre em contato com o administrador do sistema.
        </p>
        <div className="flex gap-3 justify-center">
          <button onClick={() => navigate('/')}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-5 py-2 rounded-lg">
            Ir para o início
          </button>
          <button onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm font-medium px-5 py-2 rounded-lg">
            Voltar
          </button>
        </div>
      </div>
    </div>
  )
}
