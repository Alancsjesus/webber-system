function somenteDigitos(valor) {
  return (valor || '').replace(/\D/g, '')
}

export function mascararDocumento(valor, tipoPessoa) {
  const d = somenteDigitos(valor)
  if (tipoPessoa === 'PF') {
    return d
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return d
    .slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

export function validarCNPJ(valor) {
  const d = somenteDigitos(valor)
  if (d.length !== 14 || /^(\d)\1{13}$/.test(d)) return false

  const calcularDV = (base, pesos) => {
    const soma = base.split('').reduce((acc, dig, i) => acc + Number(dig) * pesos[i], 0)
    const resto = soma % 11
    return resto < 2 ? '0' : String(11 - resto)
  }
  const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
  const dv1 = calcularDV(d.slice(0, 12), pesos1)
  const dv2 = calcularDV(d.slice(0, 12) + dv1, pesos2)
  return d.slice(12) === dv1 + dv2
}

export function validarCPF(valor) {
  const d = somenteDigitos(valor)
  if (d.length !== 11 || /^(\d)\1{10}$/.test(d)) return false

  const calcularDV = (base) => {
    const n = base.length + 1
    const soma = base.split('').reduce((acc, dig, i) => acc + Number(dig) * (n - i), 0)
    const resto = (soma * 10) % 11
    return resto === 10 ? '0' : String(resto)
  }
  const dv1 = calcularDV(d.slice(0, 9))
  const dv2 = calcularDV(d.slice(0, 9) + dv1)
  return d.slice(9) === dv1 + dv2
}

export function validarDocumento(valor, tipoPessoa) {
  return tipoPessoa === 'PF' ? validarCPF(valor) : validarCNPJ(valor)
}
