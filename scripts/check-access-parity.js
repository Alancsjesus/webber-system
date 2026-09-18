#!/usr/bin/env node
/**
 * Verifica que a matriz de acesso por papel/unidade está em paridade entre
 * os dois arquivos que a duplicam manualmente:
 *   - frontend/src/components/RequireRole.jsx  (bloqueio real de rota)
 *   - frontend/src/components/Layout.jsx       (visibilidade no menu)
 *
 * Já causou incidente real (rota liberada no menu e bloqueada no acesso,
 * ou vice-versa — ver CLAUDE.md, regra adicionada após o bug do C7 em
 * 20/08/2026). Este script não elimina a duplicação (decisão de não tocar
 * na arquitetura agora), só garante que ela não diverge silenciosamente.
 *
 * Uso: node scripts/check-access-parity.js
 */

const fs = require('fs')
const path = require('path')

const REQUIRE_ROLE = path.join(__dirname, '../frontend/src/components/RequireRole.jsx')
const LAYOUT       = path.join(__dirname, '../frontend/src/components/Layout.jsx')

function readFile(p) {
  const content = fs.readFileSync(p, 'utf8')
  return content
}

// Extrai o texto do objeto `const NOME = { ... }` (incluindo as chaves externas),
// contando chaves balanceadas — os valores são arrays simples, sem objetos aninhados.
function extractObjectLiteral(content, varName) {
  const start = content.indexOf(`const ${varName} = {`)
  if (start === -1) throw new Error(`"${varName}" não encontrado`)
  const braceStart = content.indexOf('{', start)
  let depth = 0
  for (let i = braceStart; i < content.length; i++) {
    if (content[i] === '{') depth++
    else if (content[i] === '}') {
      depth--
      if (depth === 0) return content.slice(braceStart, i + 1)
    }
  }
  throw new Error(`chave de fechamento de "${varName}" não encontrada`)
}

// Dentro do texto de um objeto, extrai { chave: [ '/a', '/b', ... ], ... } como
// { chave: Set(['/a','/b']) } — ignora entradas cujo valor não é um array (ex: '*').
function extractRoleMap(objText) {
  const map = {}
  const re = /([A-Za-z_][A-Za-z0-9_]*)\s*:\s*\[([^\]]*)\]/g
  let m
  while ((m = re.exec(objText)) !== null) {
    const [, key, arrText] = m
    const routes = [...arrText.matchAll(/['"]([^'"]*)['"]/g)].map(x => x[1])
    map[key] = new Set(routes)
  }
  return map
}

function setEquals(a, b) {
  if (a.size !== b.size) return false
  for (const v of a) if (!b.has(v)) return false
  return true
}

function diffSets(a, b) {
  const soA = [...a].filter(x => !b.has(x))
  const soB = [...b].filter(x => !a.has(x))
  return { soA, soB }
}

function compareMaps(nameA, mapA, nameB, mapB, label) {
  let ok = true
  const chaves = new Set([...Object.keys(mapA), ...Object.keys(mapB)])
  for (const chave of chaves) {
    const a = mapA[chave]
    const b = mapB[chave]
    if (!a || !b) {
      console.log(`  ✗  [${label}] "${chave}" existe em ${a ? nameA : nameB} mas não em ${a ? nameB : nameA}`)
      ok = false
      continue
    }
    if (!setEquals(a, b)) {
      const { soA, soB } = diffSets(a, b)
      if (soA.length) console.log(`  ✗  [${label}] "${chave}": só em ${nameA} → ${soA.join(', ')}`)
      if (soB.length) console.log(`  ✗  [${label}] "${chave}": só em ${nameB} → ${soB.join(', ')}`)
      ok = false
    }
  }
  return ok
}

const rrContent = readFile(REQUIRE_ROLE)
const lyContent = readFile(LAYOUT)

const rrPapel   = extractRoleMap(extractObjectLiteral(rrContent, 'ACESSO_POR_PAPEL'))
const lyPapel   = extractRoleMap(extractObjectLiteral(lyContent, 'ACESSO_PAPEL'))
const rrUnidade = extractRoleMap(extractObjectLiteral(rrContent, 'ACESSO_EXTRA_POR_UNIDADE'))
const lyUnidade = extractRoleMap(extractObjectLiteral(lyContent, 'ACESSO_UNIDADE'))

console.log('\n📋 WEBBER — Paridade RequireRole.jsx ↔ Layout.jsx')
console.log(`   Papéis em RequireRole: ${Object.keys(rrPapel).length}  |  Papéis em Layout: ${Object.keys(lyPapel).length}`)
console.log(`   Unidades em RequireRole: ${Object.keys(rrUnidade).length}  |  Unidades em Layout: ${Object.keys(lyUnidade).length}\n`)

const okPapel   = compareMaps('RequireRole', rrPapel, 'Layout', lyPapel, 'papel')
const okUnidade = compareMaps('RequireRole', rrUnidade, 'Layout', lyUnidade, 'unidade')

if (okPapel && okUnidade) {
  console.log('✅  As duas matrizes de acesso estão em paridade.\n')
  process.exit(0)
} else {
  console.log('\n⚠️  Divergência encontrada — uma rota pode ficar visível no menu e bloqueada')
  console.log('   no acesso real, ou vice-versa. Sincronize RequireRole.jsx e Layout.jsx.\n')
  process.exit(1)
}
