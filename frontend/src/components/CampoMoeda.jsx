import { useState, useEffect } from 'react'
import { formatarMoeda, mascaraMoedaDigitada } from '../utils/currencyMask'

/**
 * Input controlado para valores em Real (R$), com máscara de milhar/centavos
 * aplicada durante a digitação (mesmo espírito de CampoSei/formatarNumeroSei).
 * `value` é o número (ou string numérica) vindo do state do formulário;
 * `onChange` recebe sempre um Number, ou '' quando o campo é limpo.
 */
export default function CampoMoeda({ value, onChange, placeholder, className = '', disabled = false, name, required = false, permiteNegativo = false }) {
  const [texto, setTexto] = useState(() => formatarMoeda(value))

  // Mantém o texto exibido em sincronia quando o valor muda por fora
  // (ex: carregamento inicial do formulário em modo edição).
  useEffect(() => {
    setTexto(formatarMoeda(value))
  }, [value])

  const handleChange = (e) => {
    const { texto: novoTexto, valor } = mascaraMoedaDigitada(e.target.value, { permiteNegativo })
    setTexto(novoTexto)
    onChange(valor)
  }

  return (
    <input
      type="text"
      inputMode="decimal"
      name={name}
      value={texto}
      onChange={handleChange}
      placeholder={placeholder || 'R$ 0,00'}
      disabled={disabled}
      required={required}
      className={className || 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50'}
    />
  )
}
