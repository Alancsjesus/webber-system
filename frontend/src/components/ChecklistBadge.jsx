import { useState, useEffect, useCallback } from 'react'
import api from '../services/api'

const ENDPOINT = {
  dfd: (id) => `/demanda/dfd/${id}/checklist/`,
  etp: (id) => `/etp/etp/${id}/checklist/`,
  tr:  (id) => `/tr/tr/${id}/checklist/`,
}

/**
 * Badge de completude do checklist SSP-BA para DFD, ETP ou TR.
 *
 * Props:
 *   tipo       — 'dfd' | 'etp' | 'tr'
 *   id         — pk do artefato
 *   status     — status atual do artefato (controla se exibe botão de submissão)
 *   onRefresh  — callback opcional chamado após refresh do checklist
 */
export default function ChecklistBadge({ tipo, id, status, onRefresh }) {
  const [resultado, setResultado]   = useState(null)
  const [loading, setLoading]       = useState(false)
  const [open, setOpen]             = useState(false)
  const [erro, setErro]             = useState(null)

  const carregar = useCallback(async () => {
    if (!id || !tipo || !ENDPOINT[tipo]) return
    setLoading(true)
    setErro(null)
    try {
      const { data } = await api.get(ENDPOINT[tipo](id))
      setResultado(data)
      onRefresh?.(data)
    } catch (e) {
      setErro('Não foi possível carregar o checklist.')
    } finally {
      setLoading(false)
    }
  }, [id, tipo, onRefresh])

  useEffect(() => { carregar() }, [carregar])

  if (!resultado && !loading && !erro) return null

  const { score = 0, total = 0, percentual = 0, pode_submeter = true, bloqueadores = [], avisos = [] } = resultado || {}

  const cor = !resultado ? 'gray'
    : bloqueadores.length > 0 ? 'red'
    : avisos.length > 0 ? 'yellow'
    : 'green'

  const badgeCls = {
    red:    'bg-red-100 text-red-700 border-red-300',
    yellow: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    green:  'bg-green-100 text-green-700 border-green-300',
    gray:   'bg-gray-100 text-gray-500 border-gray-200',
  }[cor]

  const icone = {
    red:    '✗',
    yellow: '⚠',
    green:  '✓',
    gray:   '…',
  }[cor]

  return (
    <>
      <button
        type="button"
        onClick={() => { setOpen(true); if (!resultado) carregar() }}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold transition-opacity ${badgeCls} ${loading ? 'opacity-50' : 'hover:opacity-80'}`}
        title="Ver checklist SSP-BA"
      >
        <span>{icone}</span>
        <span>{loading ? '…' : `${score}/${total}`}</span>
        <span className="text-[10px] font-normal opacity-70">checklist</span>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setOpen(false)}>
          <div
            className="relative bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <div>
                <h3 className="font-semibold text-gray-900">Checklist SSP-BA</h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {score}/{total} itens preenchidos ({percentual}%)
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={carregar}
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  Atualizar
                </button>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="text-gray-400 hover:text-gray-600 text-xl leading-none"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Status banner */}
            <div className={`mx-5 mt-3 rounded-lg px-3 py-2 text-sm font-medium ${
              pode_submeter
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {pode_submeter
                ? '✓ Todos os campos obrigatórios estão preenchidos.'
                : `✗ ${bloqueadores.length} campo(s) obrigatório(s) pendente(s) — submissão bloqueada.`}
            </div>

            {/* Body */}
            <div className="overflow-y-auto px-5 py-4 flex-1 space-y-4">
              {erro && <p className="text-sm text-red-500">{erro}</p>}

              {bloqueadores.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-red-600 mb-2">
                    Bloqueadores ({bloqueadores.length})
                  </h4>
                  <ul className="space-y-2">
                    {bloqueadores.map((r) => (
                      <li key={r.campo} className="bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                        <p className="text-sm font-medium text-red-800">{r.descricao}</p>
                        {r.detalhe && <p className="text-xs text-red-600 mt-0.5">{r.detalhe}</p>}
                        {r.base_legal && (
                          <p className="text-[10px] text-red-400 mt-1">Base: {r.base_legal}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {avisos.length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold uppercase tracking-wide text-yellow-600 mb-2">
                    Recomendados ({avisos.length})
                  </h4>
                  <ul className="space-y-2">
                    {avisos.map((r) => (
                      <li key={r.campo} className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2">
                        <p className="text-sm font-medium text-yellow-800">{r.descricao}</p>
                        {r.detalhe && <p className="text-xs text-yellow-600 mt-0.5">{r.detalhe}</p>}
                        {r.base_legal && (
                          <p className="text-[10px] text-yellow-400 mt-1">Base: {r.base_legal}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {bloqueadores.length === 0 && avisos.length === 0 && !loading && (
                <div className="text-center py-6 text-green-600">
                  <p className="text-2xl">✓</p>
                  <p className="text-sm font-medium mt-1">Checklist completo!</p>
                  <p className="text-xs text-gray-500 mt-0.5">Todos os campos foram preenchidos.</p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t bg-gray-50 rounded-b-2xl">
              <p className="text-[10px] text-gray-400 text-center">
                Baseado no Checklist SSP-BA · Decreto Estadual 22.598/2024 · Lei 14.133/2021
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
