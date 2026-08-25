import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import usePlanoStore from '../stores/planoStore'
import LoadingSpinner from '../components/LoadingSpinner'
import { formatarMoeda } from '../utils/currencyMask'

const STATUS_BADGE = {
  rascunho:  'bg-yellow-100 text-yellow-700',
  publicado: 'bg-green-100 text-green-700',
}

const ANOS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 + i)

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Plano de Compras / PCA',
  descricao: 'Lista os Planos de Contratações Anuais (PCA) do órgão, um por exercício fiscal.',
  acoes: [
    { label: '+ Novo Plano', texto: 'Cria um novo PCA para o exercício selecionado e abre direto a tela de detalhe para começar a vincular necessidades.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 12, VII.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function PlanoList() {
  const navigate = useNavigate()
  const { planos, loading, error, fetchPlanos, criarPlano } = usePlanoStore()
  const [criando, setCriando] = useState(false)
  const [form,    setForm]    = useState({ exercicio_fiscal: new Date().getFullYear(), descricao: '' })
  const [showForm, setShowForm] = useState(false)
  const [erroCriar, setErroCriar] = useState(null)

  useEffect(() => { fetchPlanos() }, [])

  const handleCriar = async (e) => {
    e.preventDefault()
    setCriando(true)
    setErroCriar(null)
    try {
      const novo = await criarPlano(form)
      await fetchPlanos()
      navigate(`/planejamento/pca/${novo.id}`)
    } catch (err) {
      setErroCriar(err?.response?.data?.detail || JSON.stringify(err?.response?.data) || 'Erro ao criar plano.')
    } finally {
      setCriando(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Plano de Compras / PCA</h1>
          <p className="text-sm text-gray-500 mt-0.5">Planos de Contratações Anuais por exercício</p>
        </div>
        <button
          onClick={() => setShowForm(p => !p)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg"
        >
          + Novo Plano
        </button>
      </div>

      {/* Formulário de criação */}
      {showForm && (
        <form onSubmit={handleCriar} className="bg-white rounded-xl border border-gray-200 p-5 mb-5 space-y-3">
          <h2 className="font-semibold text-gray-700 text-sm">Novo Plano / PCA</h2>
          {erroCriar && <p className="text-red-600 text-xs">{erroCriar}</p>}
          <div className="flex gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Exercício fiscal</label>
              <select
                value={form.exercicio_fiscal}
                onChange={e => setForm(p => ({ ...p, exercicio_fiscal: Number(e.target.value) }))}
                className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              >
                {ANOS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs text-gray-500 mb-1">Descrição (opcional)</label>
              <input
                value={form.descricao}
                onChange={e => setForm(p => ({ ...p, descricao: e.target.value }))}
                placeholder="Ex: PCA 2026 — SSP"
                className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
              />
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <button type="button" onClick={() => setShowForm(false)}
              className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
              Cancelar
            </button>
            <button type="submit" disabled={criando}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg disabled:opacity-50">
              {criando ? 'Criando…' : 'Criar e abrir PCA'}
            </button>
          </div>
        </form>
      )}

      {/* Lista */}
      {loading ? (
        <div className="flex justify-center py-16"><LoadingSpinner /></div>
      ) : error ? (
        <div className="text-red-600 text-sm p-4">{error}</div>
      ) : planos.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
          Nenhum plano cadastrado ainda.
        </div>
      ) : (
        <div className="space-y-2">
          {planos.map(plano => (
            <div
              key={plano.id}
              onClick={() => navigate(`/planejamento/pca/${plano.id}`)}
              className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between hover:border-blue-300 hover:shadow-sm cursor-pointer transition-all"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-800">{plano.orgao_sigla} — {plano.exercicio_fiscal}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[plano.status_pca] || 'bg-gray-100 text-gray-500'}`}>
                    {plano.status_pca === 'publicado' ? 'Publicado' : 'Rascunho'}
                  </span>
                </div>
                {plano.descricao && <p className="text-sm text-gray-500 mt-0.5">{plano.descricao}</p>}
                <p className="text-xs text-gray-400 mt-1">
                  {plano.itens?.length || 0} itens
                  {plano.dotacao_total ? ` · Dotação: ${formatarMoeda(plano.dotacao_total)}` : ''}
                  {plano.dotacao_utilizada ? ` · Utilizado: ${formatarMoeda(plano.dotacao_utilizada)}` : ''}
                </p>
              </div>
              <span className="text-gray-400 text-lg">→</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
