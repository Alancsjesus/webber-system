// Máscara de moeda (Real brasileiro) para campos de valor — mesmo espírito
// de seiMask.js: sem dependência externa, formata dígitos digitados/colados.

// Formata um valor numérico (Number ou string numérica) como "R$ 1.234,56".
// Usado tanto para exibição quanto para popular o texto inicial do CampoMoeda.
export function formatarMoeda(valor) {
  if (valor === null || valor === undefined || valor === '') return ''
  const n = Number(valor)
  if (!isFinite(n)) return ''
  return n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

// A partir do texto bruto digitado, trata os últimos 2 dígitos como centavos
// (padrão de campo monetário: "123456" digitado vira R$ 1.234,56) e retorna
// o texto já mascarado junto do valor numérico correspondente.
// `permiteNegativo` habilita o sinal de "-" (ex: aditivo de valor por redução).
export function mascaraMoedaDigitada(raw, { permiteNegativo = false } = {}) {
  const texto_bruto = String(raw || '')
  const negativo = permiteNegativo && /^\s*-/.test(texto_bruto)
  const digitos = texto_bruto.replace(/\D/g, '')
  if (!digitos) return { texto: '', valor: '' }
  const valor = (Number(digitos) / 100) * (negativo ? -1 : 1)
  return { texto: formatarMoeda(valor), valor }
}
