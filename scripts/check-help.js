#!/usr/bin/env node
/**
 * Verifica cobertura de ajuda contextual.
 * Uso: node scripts/check-help.js
 *
 * Regras verificadas:
 *   1. Toda página em frontend/src/pages/**\/*.jsx (exceto as na denylist abaixo)
 *      exporta `pageHelp`.
 *   2. Toda página que exporta `pageHelp` está registrada em helpContent.js.
 *   3. Toda rota registrada em helpContent.js aponta para um arquivo existente
 *      que de fato exporta `pageHelp`.
 *
 * Antes só verificava as páginas já importadas em helpContent.js — uma página
 * nunca registrada lá passava despercebida (0 pageHelp, 0 alerta). Agora varre
 * o diretório inteiro, então o próprio "não registrado" também é reportado.
 */

const fs = require('fs')
const path = require('path')

const HELP_CONTENT = path.join(__dirname, '../frontend/src/help/helpContent.js')
const PAGES_DIR    = path.join(__dirname, '../frontend/src/pages')

// Páginas que legitimamente não precisam de ajuda contextual: pré-autenticação
// ou telas de erro/estado sem ações de domínio (Login, SemAcesso), ou arquivos
// em pages/ que não são rotas próprias — subcomponentes de outra página
// (DashboardAnalytics é renderizado dentro de Dashboard.jsx, que já tem pageHelp).
const DENYLIST = new Set(['Login', 'SemAcesso', 'DashboardAnalytics'])

function readFile(p) {
  try { return fs.readFileSync(p, 'utf8') } catch { return null }
}

// Lista todos os .jsx sob PAGES_DIR, recursivo, como caminhos relativos sem extensão
// (ex: 'DFDList', 'config/AcaoAdmin').
function listPageFiles(dir, prefix = '') {
  let out = []
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name
    if (entry.isDirectory()) {
      out = out.concat(listPageFiles(path.join(dir, entry.name), rel))
    } else if (entry.isFile() && entry.name.endsWith('.jsx')) {
      out.push(rel.replace(/\.jsx$/, ''))
    }
  }
  return out
}

function extractRoutes(content) {
  const routes = []
  const re = /['"](\/.+?)['"]\s*:/g
  let m
  while ((m = re.exec(content)) !== null) routes.push(m[1])
  return routes
}

function extractImportedFiles(content) {
  const files = []
  const re = /from\s+['"]\.\.\/pages\/([^'"]+)['"]/g
  let m
  while ((m = re.exec(content)) !== null) files.push(m[1])
  return files
}

function hasPageHelp(filename) {
  const fullPath = path.join(PAGES_DIR, `${filename}.jsx`)
  const content = readFile(fullPath)
  if (!content) return { found: false, reason: 'arquivo não encontrado' }
  if (!content.includes('export const pageHelp')) return { found: false, reason: 'pageHelp não exportado' }
  return { found: true }
}

function main() {
  const helpContent = readFile(HELP_CONTENT)
  if (!helpContent) {
    console.error('❌ Arquivo helpContent.js não encontrado em:', HELP_CONTENT)
    process.exit(1)
  }

  const routes       = extractRoutes(helpContent)
  const imported      = extractImportedFiles(helpContent)
  const importedSet   = new Set(imported)
  const allPages       = listPageFiles(PAGES_DIR).filter(f => !DENYLIST.has(f))

  console.log(`\n📋 WEBBER — Verificação de Ajuda Contextual`)
  console.log(`   Páginas em pages/ (exceto denylist): ${allPages.length}`)
  console.log(`   Rotas mapeadas em helpContent.js: ${routes.length}`)
  console.log(`   Páginas importadas em helpContent.js: ${imported.length}\n`)

  let erros = 0
  const semPageHelp = []
  const semRegistro  = []

  for (const file of allPages) {
    const result = hasPageHelp(file)
    if (!result.found) {
      semPageHelp.push(file)
      erros++
    } else if (!importedSet.has(file)) {
      semRegistro.push(file)
      erros++
    }
  }

  // Também valida os imports já existentes em helpContent.js (arquivo pode ter
  // sido renomeado/removido sem atualizar o import).
  for (const file of imported) {
    if (allPages.includes(file)) continue // já coberto acima
    const result = hasPageHelp(file)
    if (!result.found) {
      console.log(`❌  ${file}.jsx (importado em helpContent.js) — ${result.reason}`)
      erros++
    }
  }

  if (semPageHelp.length) {
    console.log(`❌  ${semPageHelp.length} página(s) sem "export const pageHelp":`)
    for (const f of semPageHelp) console.log(`     - ${f}.jsx`)
    console.log('')
  }

  if (semRegistro.length) {
    console.log(`⚠️  ${semRegistro.length} página(s) com pageHelp definido mas NÃO registrado em helpContent.js:`)
    for (const f of semRegistro) console.log(`     - ${f}.jsx`)
    console.log('')
  }

  if (erros === 0) {
    console.log(`✅  Todas as ${allPages.length} páginas têm pageHelp definido e registrado.\n`)
  } else {
    console.log(`⚠️  ${erros} problema(s) de cobertura de ajuda contextual.`)
    console.log('   Página sem pageHelp: adicione "export const pageHelp = { ... }" no topo do arquivo.')
    console.log('   Página sem registro: adicione o import + entrada de rota em helpContent.js.\n')
    process.exit(1)
  }
}

main()
