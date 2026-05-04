/**
 * Modal de devolução com motivo livre + categoria estruturada.
 * Props:
 *   show           - boolean
 *   onClose        - () => void
 *   onConfirm      - (motivo, categoria) => Promise<void>
 *   loading        - boolean
 *   titulo         - string (ex: "Devolver DFD")
 *   categorias     - [{value, label}]
 */
import { useState } from 'react'

export default function ModalDevolver({ show, onClose, onConfirm, loading, titulo, categorias = [] }) {
  const [motivo,    setMotivo]    = useState('')
  const [categoria, setCategoria] = useState('')

  if (!show) return null

  const handleConfirm = async () => {
    if (!motivo.trim()) return
    await onConfirm(motivo, categoria)
    setMotivo('')
    setCategoria('')
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="text-base font-semibold text-gray-800 mb-4">{titulo || 'Devolver documento'}</h3>

        {categorias.length > 0 && (
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Categoria do motivo</label>
            <select value={categoria} onChange={e => setCategoria(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400">
              <option value="">— Selecione (opcional) —</option>
              {categorias.map(c => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        )}

        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-600 mb-1">Motivo detalhado *</label>
          <textarea rows={3} value={motivo} onChange={e => setMotivo(e.target.value)}
            placeholder="Descreva o que precisa ser corrigido..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400" />
        </div>

        <div className="flex gap-2">
          <button onClick={handleConfirm} disabled={!motivo.trim() || loading}
            className="bg-orange-500 hover:bg-orange-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {loading ? 'Processando...' : 'Confirmar devolução'}
          </button>
          <button onClick={() => { onClose(); setMotivo(''); setCategoria('') }}
            className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  )
}

// Choices por tipo de documento
export const MOTIVOS_DFD = [
  { value: 'documentacao_incompleta',  label: 'Documentação incompleta' },
  { value: 'valor_incorreto',          label: 'Valor estimado incorreto' },
  { value: 'areas_inconsistentes',     label: 'Áreas de aplicação inconsistentes' },
  { value: 'especificacao_inadequada', label: 'Especificação inadequada' },
  { value: 'sem_vinculo_orcamentario', label: 'Sem vinculação orçamentária' },
  { value: 'outro',                    label: 'Outro' },
]

export const MOTIVOS_ETP = [
  { value: 'alternativas_insuficientes', label: 'Alternativas insuficientes' },
  { value: 'estimativa_sem_referencia',  label: 'Estimativa de valor sem referência' },
  { value: 'requisitos_incompletos',     label: 'Requisitos técnicos incompletos' },
  { value: 'fontes_inadequadas',         label: 'Fontes de pesquisa inadequadas' },
  { value: 'outro',                      label: 'Outro' },
]

export const MOTIVOS_TR = [
  { value: 'objeto_mal_definido',          label: 'Objeto mal definido' },
  { value: 'criterios_habilitacao_excess', label: 'Critérios de habilitação excessivos' },
  { value: 'obrigacoes_desequilibradas',   label: 'Obrigações desequilibradas' },
  { value: 'prazo_irreal',                 label: 'Prazo irreal' },
  { value: 'outro',                        label: 'Outro' },
]

export const MOTIVOS_MAPA = [
  { value: 'fontes_inadequadas',  label: 'Fontes de pesquisa inadequadas' },
  { value: 'cotacoes_fora_prazo', label: 'Cotações fora do prazo' },
  { value: 'qtd_insuficiente',    label: 'Número insuficiente de cotações' },
  { value: 'metodo_inadequado',   label: 'Método de cálculo inadequado' },
  { value: 'outro',               label: 'Outro' },
]
