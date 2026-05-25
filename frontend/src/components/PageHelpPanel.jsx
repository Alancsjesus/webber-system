import { useState, useEffect, useRef } from 'react'
import { useLocation, matchPath } from 'react-router-dom'
import { helpContent } from '../help/helpContent'

function findHelp(pathname) {
  // Tentativa de match exato primeiro
  if (helpContent[pathname]) return helpContent[pathname]
  // Match com parâmetros dinâmicos (:id)
  for (const pattern of Object.keys(helpContent)) {
    if (matchPath(pattern, pathname)) return helpContent[pattern]
  }
  return null
}

export default function PageHelpPanel() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const panelRef = useRef(null)
  const help = findHelp(pathname)

  // Fecha ao pressionar Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Fecha ao clicar fora do painel
  useEffect(() => {
    if (!open) return
    const handler = (e) => { if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  // Fecha ao mudar de rota
  useEffect(() => { setOpen(false) }, [pathname])

  if (!help) return null

  return (
    <>
      {/* Botão flutuante */}
      <button
        onClick={() => setOpen(v => !v)}
        className="fixed bottom-6 right-6 z-40 w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg flex items-center justify-center text-sm font-bold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2"
        aria-label="Abrir ajuda desta página"
        title="Ajuda desta página"
      >
        ?
      </button>

      {/* Overlay escuro (mobile) */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 md:bg-transparent"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Painel lateral */}
      <div
        ref={panelRef}
        className={[
          'fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out',
          open ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
        role="dialog"
        aria-label="Ajuda da página"
      >
        {/* Cabeçalho */}
        <div className="flex items-start justify-between px-5 py-4 border-b border-gray-100 bg-blue-600 text-white">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-blue-200 mb-0.5">Ajuda contextual</p>
            <h2 className="text-sm font-bold leading-snug">{help.titulo}</h2>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="mt-0.5 ml-3 text-blue-200 hover:text-white transition-colors focus:outline-none"
            aria-label="Fechar ajuda"
          >
            ✕
          </button>
        </div>

        {/* Corpo */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {/* Descrição */}
          <p className="text-sm text-gray-600 leading-relaxed">{help.descricao}</p>

          {/* Ações */}
          {help.acoes && help.acoes.length > 0 && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">Ações disponíveis</p>
              <ul className="space-y-3">
                {help.acoes.map((acao, i) => (
                  <li key={i} className="flex gap-2.5">
                    <span className="mt-0.5 flex-shrink-0 w-5 h-5 rounded bg-blue-100 text-blue-700 text-[10px] font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <div>
                      <p className="text-xs font-semibold text-gray-800">{acao.label}</p>
                      <p className="text-xs text-gray-500 leading-relaxed mt-0.5">{acao.texto}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Fluxo / etapas */}
          {help.fluxo && (
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">Fluxo de status</p>
              <ol className="relative border-l border-blue-200 space-y-3 pl-4">
                {help.fluxo.map((etapa, i) => (
                  <li key={i}>
                    <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-blue-500" />
                    <p className="text-xs font-semibold text-gray-800">{etapa.status}</p>
                    {etapa.descricao && (
                      <p className="text-xs text-gray-500 leading-relaxed">{etapa.descricao}</p>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Dica extra */}
          {help.dica && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-600 mb-1">Dica</p>
              <p className="text-xs text-amber-800 leading-relaxed">{help.dica}</p>
            </div>
          )}

          {/* Base legal */}
          {help.baseLegal && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2.5">
              <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-1">Base legal</p>
              <p className="text-xs text-gray-600 leading-relaxed">{help.baseLegal}</p>
            </div>
          )}
        </div>

        {/* Rodapé */}
        <div className="px-5 py-3 border-t border-gray-100">
          <a
            href="/ajuda"
            className="text-xs text-blue-600 hover:underline font-medium"
          >
            Ver documentação completa →
          </a>
        </div>
      </div>
    </>
  )
}
