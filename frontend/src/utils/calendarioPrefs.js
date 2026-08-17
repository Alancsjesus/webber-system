// Preferência de "destaque" do Calendário (Sprint C6): quais tipos de evento
// o usuário quer ver em cor forte vs. discreto/dessaturado. Padrão por papel,
// com override salvo em localStorage (sem back-end — ver plano da sprint).

export const IMPORTANCIA_PADRAO_POR_PAPEL = {
  fiscal_contrato:     ['execucao', 'contrato'],
  gestor_contrato:     ['execucao', 'contrato'],
  gestor_planejamento: ['dfd', 'necessidade'],
  analista:            ['dfd', 'contrato', 'execucao'],
  ordenador:           ['contrato'],
  admin:               ['dfd', 'contrato', 'execucao', 'necessidade'],
  solicitante:         ['dfd'],
  responsavel_tecnico: ['dfd'],
}

// user_id vem direto do JWT (claim padrão do SimpleJWT) — evita depender de um
// campo extra no authStore só para isto, e mantém a preferência isolada por usuário
// mesmo em máquinas compartilhadas.
function _userId() {
  const token = localStorage.getItem('access_token')
  if (!token) return 'anon'
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.user_id ?? 'anon'
  } catch {
    return 'anon'
  }
}

const _key = () => `webber:calendario:destaques:${_userId()}`

export function getDestaques(papel) {
  try {
    const salvo = localStorage.getItem(_key())
    if (salvo) return JSON.parse(salvo)
  } catch {
    // ignora JSON inválido — cai no padrão do papel
  }
  return IMPORTANCIA_PADRAO_POR_PAPEL[papel] || []
}

export function salvarDestaques(tipos) {
  localStorage.setItem(_key(), JSON.stringify(tipos))
}
