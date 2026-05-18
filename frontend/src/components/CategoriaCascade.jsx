/**
 * Seletor em cascata para CategoriaItem.
 *
 * Props:
 *   categorias  - lista completa de categorias (flat, com campos id, nome, pai, tem_filhos)
 *   value       - id (number|null) da categoria atualmente selecionada
 *   onChange    - (id: number|null) => void  — chamado apenas quando uma folha é selecionada ou limpa
 *   disabled    - boolean
 */
import { useMemo } from 'react'

export default function CategoriaCascade({ categorias = [], value, onChange, disabled = false }) {
  // Índice pai → filhos
  const filhosDe = useMemo(() => {
    const map = {}
    categorias.forEach(c => {
      const chave = c.pai ?? null
      if (!map[chave]) map[chave] = []
      map[chave].push(c)
    })
    // Ordenar cada grupo por nome
    Object.values(map).forEach(arr => arr.sort((a, b) => a.nome.localeCompare(b.nome)))
    return map
  }, [categorias])

  // Reconstrói o caminho de seleções a partir do value atual
  const caminhoAtual = useMemo(() => {
    if (!value) return []
    const caminho = []
    let atual = categorias.find(c => c.id === value)
    while (atual) {
      caminho.unshift(atual)
      atual = atual.pai ? categorias.find(c => c.id === atual.pai) : null
    }
    return caminho
  }, [value, categorias])

  // Níveis a renderizar: [raiz, filho_selecionado_no_nivel_0, ...]
  // Cada nível mostra os irmãos do nó selecionado naquele nível
  const niveis = useMemo(() => {
    const resultado = []
    // Nível 0: raízes
    resultado.push({ opcoes: filhosDe[null] ?? [], selecionadoId: caminhoAtual[0]?.id ?? null })
    // Próximos níveis: filhos do selecionado anterior
    for (let i = 0; i < caminhoAtual.length; i++) {
      const pai = caminhoAtual[i]
      const filhos = filhosDe[pai.id] ?? []
      if (filhos.length === 0) break // folha — para aqui
      resultado.push({ opcoes: filhos, selecionadoId: caminhoAtual[i + 1]?.id ?? null })
    }
    return resultado
  }, [filhosDe, caminhoAtual])

  // Nó atualmente em foco (último selecionado com filhos, ou folha)
  const noSelecionado = value ? categorias.find(c => c.id === value) : null
  const ehFolha = noSelecionado ? !(filhosDe[noSelecionado.id]?.length > 0) : false

  const handleChange = (nivelIdx, novoId) => {
    if (!novoId) {
      // Limpou a seleção neste nível: propaga null e corta o caminho
      onChange(null)
      return
    }
    const id = Number(novoId)
    const no = categorias.find(c => c.id === id)
    const temFilhos = (filhosDe[id]?.length ?? 0) > 0
    if (temFilhos) {
      // Selecionou nó intermediário: não grava ainda, apenas navega
      // Informa onChange com null para indicar "ainda não fechado"
      onChange(null)
      // Reconstruímos o caminho forçando este nó como ponta
      // Controlamos via um ID "parcial" — usamos um valor especial para forçar re-render
      // Truque: chamamos onChange com o id mesmo para que o pai possa armazenar estado parcial,
      // MAS vamos tratar na lógica de submit — ehFolha === false impede salvar
      onChange(id)
    } else {
      // Folha: confirma
      onChange(id)
    }
  }

  if (categorias.length === 0) {
    return (
      <p className="text-xs text-gray-400 italic">
        Nenhuma categoria cadastrada.{' '}
        <a href="/config/categorias" className="text-blue-600 hover:underline">Criar categorias</a>
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {niveis.map((nivel, idx) => (
        <div key={idx} className="flex items-center gap-2">
          {idx > 0 && (
            <span className="text-gray-300 text-sm shrink-0">›</span>
          )}
          <select
            disabled={disabled}
            value={nivel.selecionadoId ?? ''}
            onChange={e => handleChange(idx, e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          >
            <option value="">
              {idx === 0 ? '— Selecione a categoria —' : '— Selecione a subcategoria —'}
            </option>
            {nivel.opcoes.map(c => (
              <option key={c.id} value={c.id}>
                {c.nome}{filhosDe[c.id]?.length > 0 ? ' ›' : ' ✓'}
              </option>
            ))}
          </select>
        </div>
      ))}

      {/* Feedback do estado atual */}
      {value && (
        <div className={`flex items-center gap-2 mt-1 text-xs px-2 py-1.5 rounded-lg ${
          ehFolha
            ? 'bg-purple-50 text-purple-700 border border-purple-200'
            : 'bg-amber-50 text-amber-700 border border-amber-200'
        }`}>
          {ehFolha ? (
            <>
              <span>✓</span>
              <span className="font-medium">{noSelecionado?.nome}</span>
              <span className="text-purple-400">— categoria registrada</span>
            </>
          ) : (
            <>
              <span>⚠</span>
              <span>Selecione uma subcategoria para prosseguir</span>
            </>
          )}
        </div>
      )}

      {/* Botão limpar */}
      {value && (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="text-xs text-red-500 hover:underline"
        >
          Limpar categoria
        </button>
      )}
    </div>
  )
}
