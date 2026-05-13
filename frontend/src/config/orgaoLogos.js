export const ORGAO_LOGOS = {
  SSP: { brasao: '/logos/sspba_brasao.png', escudo: '/logos/sspba_escudo.png' },
}

export const getOrgaoLogo = (sigla, tipo = 'brasao') =>
  ORGAO_LOGOS[sigla]?.[tipo] ?? null
