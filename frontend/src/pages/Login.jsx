import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import HCaptcha from '@hcaptcha/react-hcaptcha'
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

const HCAPTCHA_SITE_KEY = import.meta.env.VITE_HCAPTCHA_SITE_KEY || '10000000-ffff-ffff-ffff-000000000001'

export default function Login() {
  const [username, setUsername]         = useState('')
  const [password, setPassword]         = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [captchaToken, setCaptchaToken] = useState('')
  const [confirmed, setConfirmed]       = useState(false)
  const captchaRef = useRef(null)

  const { login, loading, error, isAuthenticated,
          orgaoSigla, orgaoNome, unidadeNome, tipoUnidade, papel } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated && !confirmed) navigate('/', { replace: true })
  }, [])

  const errorMessage = () => {
    if (!error) return null
    if (typeof error === 'string' && error.includes('429')) {
      return 'Muitas tentativas. Aguarde 1 minuto e tente novamente.'
    }
    return typeof error === 'string' ? error : 'Usuário ou senha inválidos.'
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await login(username, password, captchaToken)
    if (useAuthStore.getState().isAuthenticated) {
      setConfirmed(true)
    } else {
      // Resetar CAPTCHA após falha para exigir nova verificação
      captchaRef.current?.resetCaptcha()
      setCaptchaToken('')
    }
  }

  // Painel de confirmação pós-login
  if (confirmed && isAuthenticated) {
    const tipo = tipoUnidade
    return (
      <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
          <WatermarkLogo />
        </div>
        <div className="absolute bottom-8 left-0 right-0 flex flex-col items-center pointer-events-none select-none" style={{ opacity: 0.30 }}>
          <span style={{ fontFamily: 'Georgia, serif', letterSpacing: '0.35em', fontSize: '1.05rem', color: '#1e3a5f', fontWeight: 'bold' }}>WEBBER</span>
          <span style={{ fontFamily: 'Arial, sans-serif', letterSpacing: '0.18em', fontSize: '0.6rem', color: '#1e3a5f', marginTop: '2px' }}>GESTÃO DE CONTRATAÇÕES</span>
        </div>
        <div className="relative z-10 bg-white/92 backdrop-blur-sm rounded-2xl shadow-lg w-full max-w-md p-8 text-center">
          <div className="w-14 h-14 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
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
            onClick={() => navigate('/', { replace: true })}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
          >
            Continuar para o sistema →
          </button>
        </div>
      </div>
    )
  }

  const msg = errorMessage()


  return (
    <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 overflow-hidden">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
        <WatermarkLogo />
      </div>
      <div className="absolute bottom-8 left-0 right-0 flex flex-col items-center pointer-events-none select-none" style={{ opacity: 0.30 }}>
        <span style={{ fontFamily: 'Georgia, serif', letterSpacing: '0.35em', fontSize: '1.05rem', color: '#1e3a5f', fontWeight: 'bold' }}>WEBBER</span>
        <span style={{ fontFamily: 'Arial, sans-serif', letterSpacing: '0.18em', fontSize: '0.6rem', color: '#1e3a5f', marginTop: '2px' }}>GESTÃO DE CONTRATAÇÕES</span>
      </div>
      <div className="relative z-10 bg-white/92 backdrop-blur-sm rounded-2xl shadow-lg w-full max-w-md p-8">

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-800 leading-tight">Webber</h1>
            <p className="text-xs text-gray-400">Sistema de planejamento e contratações</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Usuário */}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">
              Usuário
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              autoComplete="username"
              className="w-full border border-gray-300 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
            />
          </div>

          {/* Senha */}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">
              Senha
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                className="w-full border border-gray-300 rounded-xl px-3.5 py-2.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition"
                aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
              >
                {showPassword ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* hCaptcha — em dev, o backend já ignora o token (HCAPTCHA_BYPASS=True) */}
          {import.meta.env.DEV ? (
            <DevCaptchaBypass onToken={setCaptchaToken} active={!!captchaToken} />
          ) : (
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5 uppercase tracking-wide">
                Verificação de segurança
              </label>
              <div className="flex justify-center">
                <HCaptcha
                  ref={captchaRef}
                  sitekey={HCAPTCHA_SITE_KEY}
                  onVerify={(token) => setCaptchaToken(token)}
                  onExpire={() => setCaptchaToken('')}
                  size="normal"
                  theme="light"
                />
              </div>
            </div>
          )}

          {/* Erro */}
          {msg && (
            <div className="flex items-start gap-2 text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-3.5 py-2.5">
              <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.834-1.964-.834-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span>{msg}</span>
            </div>
          )}

          {/* Botão */}
          <button
            type="submit"
            disabled={loading || !captchaToken}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Verificando...
              </>
            ) : 'Entrar'}
          </button>
        </form>

        {/* Rodapé */}
        <p className="mt-5 text-center text-xs text-gray-400">
          Esqueceu a senha?{' '}
          <span className="text-gray-500 font-medium">Contate o administrador do sistema.</span>
        </p>
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

function DevCaptchaBypass({ onToken, active }) {
  // Auto-seta token ao montar — HCAPTCHA_BYPASS=True no backend aceita qualquer valor
  useEffect(() => { onToken('dev-bypass') }, [])

  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-dashed border-amber-300 bg-amber-50 px-4 py-2.5">
      <div className={`w-4 h-4 rounded flex-shrink-0 flex items-center justify-center ${active ? 'bg-amber-400' : 'bg-amber-200'}`}>
        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <span className="text-xs text-amber-700 font-medium">CAPTCHA desativado em desenvolvimento</span>
    </div>
  )
}

function WatermarkLogo() {
  // ── Anel externo: 8 ticks a cada 45° ──
  const outerTicks = Array.from({ length: 8 }, (_, i) => {
    const deg = i * 45
    const major = deg % 90 === 0
    const a = (deg * Math.PI) / 180
    return {
      key: deg,
      x1: 100 + 91 * Math.sin(a), y1: 100 - 91 * Math.cos(a),
      x2: 100 + (major ? 79 : 86) * Math.sin(a), y2: 100 - (major ? 79 : 86) * Math.cos(a),
      sw: major ? 2.4 : 1.2,
    }
  })

  // ── Anel interno: 16 ticks a cada 22.5° ──
  const innerTicks = Array.from({ length: 16 }, (_, i) => {
    const a = (i * 22.5 * Math.PI) / 180
    return {
      key: i,
      x1: 100 + 73 * Math.sin(a), y1: 100 - 73 * Math.cos(a),
      x2: 100 + 69 * Math.sin(a), y2: 100 - 69 * Math.cos(a),
    }
  })

  // ── Chevrons apontando para fora — 6 a cada 60° ──
  const chevrons = Array.from({ length: 6 }, (_, i) => {
    const θ = (i * 60 * Math.PI) / 180
    const la = θ - (10 * Math.PI) / 180
    const ra = θ + (10 * Math.PI) / 180
    const f = n => n.toFixed(1)
    const tip   = [100 + 70 * Math.sin(θ),  100 - 70 * Math.cos(θ)]
    const left  = [100 + 66 * Math.sin(la), 100 - 66 * Math.cos(la)]
    const right = [100 + 66 * Math.sin(ra), 100 - 66 * Math.cos(ra)]
    return {
      key: i,
      pts: `${f(left[0])},${f(left[1])} ${f(tip[0])},${f(tip[1])} ${f(right[0])},${f(right[1])}`,
    }
  })

  // ── Engrenagem: polígono de 18 pontos (6 dentes × 3 pontos) ──
  const rT = 7, rR = 5, hw = (15 * Math.PI) / 180
  const f = n => n.toFixed(1)
  const gearPts = Array.from({ length: 6 }, (_, i) => {
    const θ = (i * 60 * Math.PI) / 180
    return [
      `${f(100 + rT * Math.sin(θ - hw))},${f(146 - rT * Math.cos(θ - hw))}`,
      `${f(100 + rT * Math.sin(θ + hw))},${f(146 - rT * Math.cos(θ + hw))}`,
      `${f(100 + rR * Math.sin(θ + 2 * hw))},${f(146 - rR * Math.cos(θ + 2 * hw))}`,
    ]
  }).flat().join(' ')

  return (
    <>
      <style>{`
        @keyframes wm-spin-cw  { from { transform: rotate(0deg);   } to { transform: rotate(360deg);  } }
        @keyframes wm-spin-ccw { from { transform: rotate(0deg);   } to { transform: rotate(-360deg); } }
        .wm-outer { animation: wm-spin-cw  90s linear infinite; }
        .wm-inner { animation: wm-spin-ccw 60s linear infinite; }
      `}</style>
      <svg
        width="700" height="700" viewBox="0 0 200 200"
        opacity="0.10"
        aria-hidden="true"
      >
        {/* ── Anel externo — sentido horário (90s) ── */}
        <g style={{ transformOrigin: '100px 100px' }} className="wm-outer">
          <circle cx="100" cy="100" r="91" fill="none" stroke="#1e3a5f" strokeWidth="2"/>
          <circle cx="100" cy="100" r="85" fill="none" stroke="#1e3a5f" strokeWidth="0.5"/>
          {outerTicks.map(t => (
            <line key={t.key} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
                  stroke="#1e3a5f" strokeWidth={t.sw}/>
          ))}
          {[0, 90, 180, 270].map(deg => {
            const a = (deg * Math.PI) / 180
            const cx = 100 + 91 * Math.sin(a), cy = 100 - 91 * Math.cos(a)
            return <polygon key={deg} fill="#1e3a5f"
              points={`${cx},${cy-5} ${cx+3.5},${cy} ${cx},${cy+5} ${cx-3.5},${cy}`}/>
          })}
          {[45, 135, 225, 315].map(deg => {
            const a = (deg * Math.PI) / 180
            const cx = 100 + 91 * Math.sin(a), cy = 100 - 91 * Math.cos(a)
            return <polygon key={deg} fill="#1e3a5f"
              points={`${cx},${cy-3} ${cx+2},${cy} ${cx},${cy+3} ${cx-2},${cy}`}/>
          })}
        </g>

        {/* ── Anel interno — sentido anti-horário (60s) ── */}
        <g style={{ transformOrigin: '100px 100px' }} className="wm-inner">
          <circle cx="100" cy="100" r="73" fill="none" stroke="#1e3a5f" strokeWidth="1.5"/>
          <circle cx="100" cy="100" r="64" fill="none" stroke="#1e3a5f"
                  strokeWidth="0.8" strokeDasharray="4 3"/>
          {innerTicks.map(t => (
            <line key={t.key} x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
                  stroke="#1e3a5f" strokeWidth="0.8"/>
          ))}
          {chevrons.map(c => (
            <polyline key={c.key} points={c.pts}
                      fill="none" stroke="#1e3a5f" strokeWidth="1.2"/>
          ))}
        </g>

        {/* ── Centro estático ── */}

        {/* Ícone de edifício institucional */}
        <circle cx="100" cy="50" r="9.5" fill="none" stroke="#1e3a5f" strokeWidth="1.4"/>
        <polygon points="93,47 107,47 100,42" fill="#1e3a5f"/>
        <rect x="93" y="47" width="14" height="7" fill="#1e3a5f"/>
        <rect x="97.5" y="50" width="5" height="4" fill="white"/>

        {/* W limpo — 5 pontos */}
        <path d="M 46,62 L 70,104 L 100,72 L 130,104 L 154,62"
              fill="none" stroke="#1e3a5f" strokeWidth="11"
              strokeLinejoin="round" strokeLinecap="round"/>
        <path d="M 50,62 L 72,100 L 100,70 L 128,100 L 150,62"
              fill="none" stroke="#dbeafe" strokeWidth="3"
              strokeLinejoin="round" strokeLinecap="round"/>

        {/* Linha separadora */}
        <line x1="72" y1="113" x2="128" y2="113" stroke="#1e3a5f" strokeWidth="1"/>

        {/* Linhas de documento */}
        <line x1="76" y1="120" x2="124" y2="120" stroke="#1e3a5f" strokeWidth="1.1"/>
        <line x1="76" y1="126" x2="116" y2="126" stroke="#1e3a5f" strokeWidth="1.1"/>
        <line x1="76" y1="132" x2="124" y2="132" stroke="#1e3a5f" strokeWidth="1.1"/>

        {/* Ícone de engrenagem (gestão) */}
        <circle cx="100" cy="146" r="9.5" fill="none" stroke="#1e3a5f" strokeWidth="1.4"/>
        <polygon points={gearPts} fill="#1e3a5f"/>
        <circle cx="100" cy="146" r="2.8" fill="white"/>
      </svg>
    </>
  )
}
