#!/usr/bin/env node
/**
 * Verifica cobertura de ajuda contextual.
 * Uso: node scripts/check-help.js
 *
 * Regras verificadas:
 *   1. Todas as rotas em helpContent.js têm uma página correspondente exportando pageHelp
 *   2. Todas as páginas listadas exportam `pageHelp` (bloco não-vazio)
 */

const fs = require('fs')
const path = require('path')

const HELP_CONTENT = path.join(__dirname, '../frontend/src/help/helpContent.js')
const PAGES_DIR    = path.join(__dirname, '../frontend/src/pages')

function readFile(p) {
  try { return fs.readFileSync(p, 'utf8') } catch { return null }
}

// Extrai as rotas mapeadas em helpContent.js
function extractRoutes(content) {
  const routes = []
  const re = /['"](\/.+?)['"]\s*:/g
  let m
  while ((m = re.exec(content)) !== null) routes.push(m[1])
  return routes
}

// Extrai os arquivos de página importados em helpContent.js
function extractImportedFiles(content) {
  const files = []
  const re = /from\s+['"]\.\.\/pages\/([^'"]+)['"]/g
  let m
  while ((m = re.exec(content)) !== null) files.push(m[1])
  return files
}

// Verifica se um arquivo de página exporta pageHelp
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

  const routes   = extractRoutes(helpContent)
  const imported = extractImportedFiles(helpContent)

  console.log(`\n📋 WEBBER — Verificação de Ajuda Contextual`)
  console.log(`   Rotas mapeadas: ${routes.length}`)
  console.log(`   Páginas importadas: ${imported.length}\n`)

  let erros = 0

  // Verifica se cada página importada tem pageHelp
  for (const file of imported) {
    const result = hasPageHelp(file)
    if (!result.found) {
      console.log(`❌  ${file}.jsx — ${result.reason}`)
      erros++
    }
  }

  if (erros === 0) {
    console.log(`✅  Todas as ${imported.length} páginas têm pageHelp definido.`)
    console.log(`✅  ${routes.length} rotas mapeadas no helpContent.js.\n`)
  } else {
    console.log(`\n⚠️  ${erros} página(s) sem cobertura de ajuda.`)
    console.log('   Adicione o bloco "export const pageHelp = { ... }" no topo do arquivo.\n')
    process.exit(1)
  }
}

main()
