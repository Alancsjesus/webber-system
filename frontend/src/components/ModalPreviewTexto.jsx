import { useEffect, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from './LoadingSpinner'

/**
 * Modal de pré-visualização do texto gerado (Sprint C5 — Engine de Geração de Texto).
 * Busca GET `${endpoint}gerar-texto/` e lista as seções renderizadas, com botão de copiar.
 */
export default function ModalPreviewTexto({ open, onClose, endpoint }) {
  const [secoes, setSecoes]   = useState([])
  const [loading, setLoading] = useState(false)
  const [erro, setErro]       = useState(null)
  const [copiado, setCopiado] = useState(null)

  useEffect(() => {
    if (!open) return
    setLoading(true); setErro(null)
    api.get(`${endpoint}gerar-texto/`)
      .then(({ data }) => setSecoes(data || []))
      .catch(() => setErro('Não foi possível gerar o texto. Verifique se há seções configuradas.'))
      .finally(() => setLoading(false))
  }, [open, endpoint])

  if (!open) return null

  const copiar = (texto, idx) => {
    navigator.clipboard.writeText(texto)
    setCopiado(idx)
    setTimeout(() => setCopiado(null), 1500)
  }

  const copiarTudo = () => {
    const tudo = secoes.map(s => `${s.titulo.toUpperCase()}\n\n${s.texto}`).join('\n\n---\n\n')
    navigator.clipboard.writeText(tudo)
    setCopiado('all')
    setTimeout(() => setCopiado(null), 1500)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h3 className="text-base font-semibold text-gray-800">Pré-visualização do texto</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {loading && <LoadingSpinner />}
          {erro && <p className="text-sm text-red-600">{erro}</p>}
          {!loading && !erro && secoes.length === 0 && (
            <p className="text-sm text-gray-400 italic text-center py-8">
              Nenhuma seção com conteúdo gerado ainda. Preencha os campos do documento ou configure os
              modelos de texto em Configurações → Estrutura de Artefatos.
            </p>
          )}
          {secoes.map((s, idx) => (
            <div key={s.secao_id} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="flex items-center justify-between bg-gray-50 px-3 py-2 border-b border-gray-200">
                <span className="text-xs font-semibold text-gray-600 uppercase">{s.titulo}</span>
                <button onClick={() => copiar(s.texto, idx)}
                  className="text-[11px] text-blue-600 hover:text-blue-800 font-medium">
                  {copiado === idx ? 'Copiado!' : 'Copiar'}
                </button>
              </div>
              <p className="px-3 py-2 text-sm text-gray-700 whitespace-pre-wrap">{s.texto}</p>
            </div>
          ))}
        </div>

        {secoes.length > 0 && (
          <div className="px-6 py-3 border-t border-gray-200 flex justify-end">
            <button onClick={copiarTudo}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg">
              {copiado === 'all' ? 'Copiado!' : 'Copiar tudo'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
