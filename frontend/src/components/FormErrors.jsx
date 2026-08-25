/**
 * Exibe um banner de resumo de erros de validação do formulário.
 * Passa errors = { campo: 'mensagem', ... }
 * Também rola para o primeiro campo com erro.
 */
import { useEffect } from 'react'

const LABEL_MAP = {
  titulo:                   'Título',
  descricao:                'Descrição',
  departamento_solicitante: 'Departamento solicitante',
  valor_estimado:           'Valor estimado',
  area_aplicacao:           'Áreas de atuação',
  exercicio_fiscal:         'Exercício fiscal',
  prazo_desejado:           'Prazo desejado',
  prazo_necessidade:        'Prazo da necessidade',
  numero_sei:               'Número SEI',
  justificativa_sem_planejamento: 'Justificativa',
  itens:                    'Itens da demanda',
  objeto:                   'Objeto da pesquisa',
  acao:                     'Ação orçamentária',
  elemento_despesa:         'Elemento de despesa',
  natureza_despesa:         'Natureza de despesa',
  fonte_recurso:            'Fonte de recurso',
  valor_dotado:             'Valor dotado',
  dfd:                      'DFD de origem',
}

export default function FormErrors({ errors }) {
  const entries = Object.entries(errors).filter(([, v]) => v)

  useEffect(() => {
    if (entries.length === 0) return
    const firstKey = entries[0][0]
    const el = document.querySelector(`[name="${firstKey}"], #field-${firstKey}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [entries.length])

  if (entries.length === 0) return null

  return (
    <div className="mb-5 bg-red-50 border border-red-300 rounded-xl px-5 py-4">
      <p className="text-sm font-semibold text-red-800 mb-2">
        Corrija os campos obrigatórios antes de continuar:
      </p>
      <ul className="space-y-1">
        {entries.map(([key, msg]) => (
          <li key={key} className="flex items-start gap-2 text-sm text-red-700">
            <span className="mt-0.5 shrink-0">•</span>
            <span>
              <span className="font-medium">{LABEL_MAP[key] || key}:</span> {msg}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
