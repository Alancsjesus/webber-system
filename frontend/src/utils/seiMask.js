// Máscara suave (best-effort) para número de processo SEI-BA.
// Formato: NNN.NNNN.AAAA.NNNNNNN-DD (ex: 099.8188.2025.0027815-30)
// Não valida nem bloqueia — apenas formata os dígitos digitados/colados.
// Entradas com dígitos além de 20 são truncadas; entradas não numéricas são
// exibidas como vieram (ver CampoSei.jsx), sem forçar o padrão.
export function formatarNumeroSei(valor) {
  const digitos = String(valor || '').replace(/\D/g, '').slice(0, 20)
  let out = ''
  for (let i = 0; i < digitos.length; i++) {
    if (i === 3 || i === 7 || i === 11) out += '.'
    if (i === 18) out += '-'
    out += digitos[i]
  }
  return out
}
