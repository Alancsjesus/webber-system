import { useState } from 'react'
import api from '../services/api'

/**
 * Bloco "Mesa atual" reaproveitado em DFDDetail/ETPDetail/TRDetail/ProcedimentoDetail.
 * Marca onde o processo está tramitando fisicamente agora (UnidadeOrganizacional ou
 * Orgao já cadastrado) — sinal manual, só preenchido quando o Painel Gerencial de
 * Tramitação não consegue inferir sozinho (TramitacaoExterna ou as FKs fixas de
 * responsabilidade unidade_demandante/licitante/gestora já cobrem a maioria dos casos).
 */
export default function MesaAtualCard({ actionUrl, mesaAtualLabel, dataMesaAtual, onAtualizado }) {
  const [editando, setEditando] = useState(false)
  const [tipo, setTipo] = useState('unidade')
  const [query, setQuery] = useState('')
  const [resultados, setResultados] = useState([])
  const [selecionado, setSelecionado] = useState(null)
  const [data, setData] = useState(new Date().toISOString().slice(0, 10))
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState(null)

  const buscar = async (texto) => {
    setQuery(texto)
    setSelecionado(null)
    if (!texto) { setResultados([]); return }
    const endpoint = tipo === 'unidade' ? '/core/unidades/' : '/core/orgaos/'
    const { data: resp } = await api.get(endpoint, { params: { search: texto, page_size: 10 } })
    setResultados(resp.results ?? resp)
  }

  const salvar = async () => {
    if (!selecionado) { setErro('Selecione uma unidade ou órgão.'); return }
    setSalvando(true); setErro(null)
    try {
      await api.post(actionUrl, { tipo, id: selecionado.id, data })
      setEditando(false)
      setQuery(''); setSelecionado(null); setResultados([])
      onAtualizado?.()
    } catch {
      setErro('Não foi possível salvar a mesa atual.')
    } finally { setSalvando(false) }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs font-semibold text-gray-400 uppercase">Mesa atual</p>
        <button onClick={() => setEditando((v) => !v)} className="text-xs text-blue-600 hover:underline">
          {editando ? 'Cancelar' : mesaAtualLabel ? 'Alterar' : 'Marcar'}
        </button>
      </div>

      {!editando && (
        mesaAtualLabel
          ? <p className="text-sm text-gray-800">{mesaAtualLabel} <span className="text-xs text-gray-400">— {dataMesaAtual}</span></p>
          : <p className="text-sm text-gray-400">Não marcada — o Painel de Tramitação usa a unidade responsável pela etapa automaticamente.</p>
      )}

      {editando && (
        <div className="mt-2 space-y-2">
          {erro && <p className="text-xs text-red-600">{erro}</p>}
          <div className="flex gap-2 text-xs">
            <button onClick={() => { setTipo('unidade'); setResultados([]); setQuery('') }}
              className={`px-2 py-1 rounded-full border ${tipo === 'unidade' ? 'bg-blue-50 border-blue-300 text-blue-700' : 'bg-gray-50 border-gray-200 text-gray-600'}`}>
              Unidade
            </button>
            <button onClick={() => { setTipo('orgao'); setResultados([]); setQuery('') }}
              className={`px-2 py-1 rounded-full border ${tipo === 'orgao' ? 'bg-blue-50 border-blue-300 text-blue-700' : 'bg-gray-50 border-gray-200 text-gray-600'}`}>
              Órgão
            </button>
          </div>
          <input value={query} onChange={(e) => buscar(e.target.value)}
            placeholder="Buscar por sigla/nome..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {resultados.length > 0 && !selecionado && (
            <div className="border border-gray-200 rounded-lg max-h-40 overflow-y-auto">
              {resultados.map((r) => (
                <button key={r.id} type="button"
                  onClick={() => { setSelecionado(r); setQuery(r.sigla || r.nome) }}
                  className="w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 border-b border-gray-100 last:border-0">
                  {r.sigla} — {r.nome}
                </button>
              ))}
            </div>
          )}
          <input type="date" value={data} onChange={(e) => setData(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button onClick={salvar} disabled={salvando}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
            {salvando ? 'Salvando...' : 'Confirmar'}
          </button>
        </div>
      )}
    </div>
  )
}
