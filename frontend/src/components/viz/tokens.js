// Tokens de visualização — única fonte de cor dos painéis/gráficos.
// Cada cor faz UM trabalho (validado com o script de paleta do guia de dataviz):
//  - ETAPA: rampa ordinal de um só matiz (azul), mais escuro = etapa mais avançada.
//    Validada --ordinal contra fundo branco (extremo claro 2,11:1).
//  - SERIE: identidade de séries nominais, em ordem fixa (nunca por posição/valor).
//  - STATUS: significado reservado (bom/atenção/grave/crítico) — sempre com rótulo/ícone.
//  - CHROME: grade, eixos e textos — texto nunca usa a cor da série.

export const ETAPA = ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b'] // 1ª etapa → última

export const SERIE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']

export const STATUS = {
  bom: '#0ca30c',
  atencao: '#fab219',
  grave: '#ec835a',
  critico: '#d03b3b',
  neutro: '#c3c2b7',
}

export const CHROME = {
  grade: '#e5e7eb',
  eixo: '#9ca3af',
  texto: '#374151',
  textoSec: '#6b7280',
  trilho: '#f3f4f6',
}

export const fmtBRL = (v) =>
  Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// R$ 1,2 mi / R$ 350 mil — para rótulos compactos (o valor exato fica no tooltip/tabela)
export const fmtBRLCompacto = (v) => {
  const n = Number(v || 0)
  const abs = Math.abs(n)
  if (abs >= 1e9) return `R$ ${(n / 1e9).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} bi`
  if (abs >= 1e6) return `R$ ${(n / 1e6).toLocaleString('pt-BR', { maximumFractionDigits: 1 })} mi`
  if (abs >= 1e4) return `R$ ${(n / 1e3).toLocaleString('pt-BR', { maximumFractionDigits: 0 })} mil`
  return fmtBRL(n)
}

export const fmtPct = (parte, todo) => {
  const t = Number(todo) || 0
  if (!t) return '0%'
  const p = (Number(parte) / t) * 100
  return `${p.toLocaleString('pt-BR', { maximumFractionDigits: p > 0 && p < 1 ? 1 : 0 })}%`
}

// Eixos/grade recessivos para recharts: linha sólida fina, nunca tracejada.
export const EIXO_PROPS = {
  tick: { fontSize: 11, fill: CHROME.textoSec },
  axisLine: { stroke: CHROME.grade },
  tickLine: false,
}
export const GRADE_PROPS = { stroke: CHROME.grade, strokeDasharray: undefined }
export const TOOLTIP_PROPS = {
  contentStyle: { fontSize: 12, borderRadius: 8, border: `1px solid ${CHROME.grade}`, boxShadow: '0 4px 12px rgba(0,0,0,.08)' },
  labelStyle: { color: CHROME.texto, fontWeight: 600 },
  cursor: { fill: 'rgba(0,0,0,.04)' },
}
