import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useOrcamentoStore from '../stores/orcamentoStore'
import CampoMoeda from '../components/CampoMoeda'

const STATUS_OPTIONS = ['Proposta', 'Em Análise', 'Aprovada', 'Em Execução', 'Concluída', 'Cancelada']

const STATUS_CLS = {
  Proposta:      'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'Em Execução': 'bg-blue-100 text-blue-700',
  Concluída:     'bg-purple-100 text-purple-700',
  Cancelada:     'bg-red-100 text-red-700',
}

const NECES_STATUS_CLS = {
  Identificada:  'bg-gray-100 text-gray-600',
  'Em Análise':  'bg-yellow-100 text-yellow-700',
  Aprovada:      'bg-green-100 text-green-700',
  'DFD Criado':  'bg-blue-100 text-blue-700',
  Cancelada:     'bg-red-100 text-red-700',
}

export default function OrcamentoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const {
    current, loading, error,
    fetchDotacao, updateDotacao, deleteDotacao,
    fetchAcoes, fetchElementos, fetchNaturezas, fetchFontes,
    acoes, elementos, naturezas, fontes,
    vincularNecessidade, desvincularNecessidade, fetchNecessidadesDisponiveis,
  } = useOrcamentoStore()

  const [editing, setEditing]         = useState(false)
  const [form, setForm]               = useState(null)
  const [saving, setSaving]           = useState(false)
  const [formErrors, setFormErrors]   = useState({})
  const [showVincular, setShowVincular] = useState(false)
  const [disponiveis, setDisponiveis] = useState([])
  const [diagnostico, setDiagnostico] = useState(null)
  const [loadingDisp, setLoadingDisp] = useState(false)
  const [loadingVinculo, setLoadingVinculo] = useState(null)

  useEffect(() => { fetchDotacao(id) }, [id])

  useEffect(() => {
    if (current) {
      setForm({
        exercicio_fiscal: current.exercicio_fiscal,
        acao: current.acao,
        elemento_despesa: current.elemento_despesa,
        natureza_despesa: current.natureza_despesa || '',
        fonte_recurso: current.fonte_recurso,
        valor_dotado: current.valor_dotado,
        valor_indicado: current.valor_indicado ?? 0,
        valor_descentralizado: current.valor_descentralizado ?? 0,
        valor_concedido: current.valor_concedido ?? 0,
        status: current.status,
        eixo: current.eixo || '',
        objetivo_estrategico: current.objetivo_estrategico || '',
        observacoes: current.observacoes || '',
      })
      if (current.elemento_despesa) fetchNaturezas(current.elemento_despesa)
    }
  }, [current])

  useEffect(() => {
    if (editing) {
      fetchAcoes()
      fetchElementos()
      fetchFontes()
    }
  }, [editing])

  const set = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setFormErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = {
        exercicio_fiscal: Number(form.exercicio_fiscal),
        acao:             Number(form.acao),
        fonte_recurso:    Number(form.fonte_recurso),
        // Natureza contém o elemento — backend auto-preenche elemento a partir da natureza
        ...(form.natureza_despesa
          ? { natureza_despesa: Number(form.natureza_despesa) }
          : { elemento_despesa: Number(form.elemento_despesa) }),
        valor_dotado: Number(form.valor_dotado),
        valor_indicado: Number(form.valor_indicado),
        valor_descentralizado: Number(form.valor_descentralizado),
        valor_concedido: Number(form.valor_concedido),
        status: form.status,
        eixo: form.eixo,
        objetivo_estrategico: form.objetivo_estrategico,
        observacoes: form.observacoes,
      }
      await updateDotacao(id, payload)
      setEditing(false)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) {
        mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      }
      setFormErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Deseja excluir esta dotação? Esta ação não pode ser desfeita.')) return
    await deleteDotacao(id)
    navigate('/orcamento/dotacoes')
  }

  const handleAbrirVincular = async () => {
    setShowVincular(true)
    setLoadingDisp(true)
    setDiagnostico(null)
    try {
      const { items, diagnostico: diag } = await fetchNecessidadesDisponiveis(id)
      setDisponiveis(items)
      setDiagnostico(diag)
    } finally {
      setLoadingDisp(false)
    }
  }

  const handleVincular = async (necessidadeId) => {
    setLoadingVinculo(necessidadeId)
    try {
      await vincularNecessidade(id, necessidadeId)
      setDisponiveis((prev) => prev.filter((n) => n.id !== necessidadeId))
    } finally {
      setLoadingVinculo(null)
    }
  }

  const handleDesvincular = async (necessidadeId) => {
    setLoadingVinculo(necessidadeId)
    try {
      await desvincularNecessidade(id, necessidadeId)
    } finally {
      setLoadingVinculo(null)
    }
  }

  if (loading) {
    return <div className="p-8 text-sm text-gray-400">Carregando...</div>
  }

  if (error) {
    return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  }

  if (!current || !form) return null

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-gray-400 hover:text-gray-600 mb-4 inline-flex items-center gap-1"
      >
        ← Voltar
      </button>

      {/* Cabeçalho */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">
            {current.acao_codigo} — {current.acao_nome}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Exercício {current.exercicio_fiscal}</p>
          <span className={`mt-1 inline-block px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || 'bg-gray-100 text-gray-600'}`}>
            {current.status}
          </span>
        </div>
        <div className="flex gap-2">
          {!editing ? (
            <>
              <button
                onClick={() => setEditing(true)}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors"
              >
                Editar
              </button>
              <button
                onClick={handleDelete}
                className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg transition-colors"
              >
                Excluir
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg transition-colors"
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
              <button
                onClick={() => { setEditing(false); setFormErrors({}) }}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg transition-colors"
              >
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>

      <div className="space-y-5">
        {/* Exercício fiscal */}
        <DetailField label="Exercício fiscal" error={formErrors.exercicio_fiscal}>
          {editing ? (
            <input type="number" min="2020" max="2050" value={form.exercicio_fiscal}
              onChange={(e) => set('exercicio_fiscal', e.target.value)}
              className={inputCls(formErrors.exercicio_fiscal)} />
          ) : (
            <p className="text-sm text-gray-700">{current.exercicio_fiscal}</p>
          )}
        </DetailField>

        {/* Status */}
        <DetailField label="Status" error={formErrors.status}>
          {editing ? (
            <select value={form.status}
              onChange={(e) => set('status', e.target.value)}
              className={inputCls(formErrors.status)}>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          ) : (
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CLS[current.status] || ''}`}>
              {current.status}
            </span>
          )}
        </DetailField>

        {/* Ação */}
        <DetailField label="Ação orçamentária" error={formErrors.acao}>
          {editing ? (
            <select value={form.acao}
              onChange={(e) => set('acao', e.target.value)}
              className={inputCls(formErrors.acao)}>
              <option value="">Selecione...</option>
              {acoes.map((a) => (
                <option key={a.id} value={a.id}>{a.codigo} — {a.nome}</option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-gray-700">
              {current.acao_codigo} — {current.acao_nome}
              <span className="ml-2 text-xs text-gray-400">({current.acao_tipo})</span>
            </p>
          )}
        </DetailField>

        {/* Natureza de Despesa — campo primário; Elemento é derivado */}
        <DetailField label="Natureza de despesa" error={formErrors.natureza_despesa}>
          {editing ? (
            <>
              <select value={form.natureza_despesa}
                onChange={(e) => { set('natureza_despesa', e.target.value); fetchNaturezas() }}
                className={inputCls(formErrors.natureza_despesa)}>
                <option value="">Selecione uma natureza...</option>
                {naturezas.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.formato} — {n.descricao} (El. {String(n.elemento_codigo).padStart(2,'0')})
                  </option>
                ))}
              </select>
              {form.natureza_despesa && (() => {
                const nat = naturezas.find(n => String(n.id) === String(form.natureza_despesa))
                return nat
                  ? <p className="text-xs text-blue-600 mt-1">Elemento derivado: {String(nat.elemento_codigo).padStart(2,'0')} — {nat.elemento_descricao}</p>
                  : null
              })()}
            </>
          ) : (
            <div>
              <p className="text-sm text-gray-700">
                {current.natureza_formato
                  ? <><span className="font-mono font-semibold text-blue-700">{current.natureza_formato}</span> — {current.natureza_descricao}</>
                  : <span className="text-gray-400">—</span>}
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                Elemento: {current.elemento_codigo} — {current.elemento_descricao}
              </p>
            </div>
          )}
        </DetailField>

        {/* Fonte de Recurso */}
        <DetailField label="Fonte de recurso" error={formErrors.fonte_recurso}>
          {editing ? (
            <select value={form.fonte_recurso}
              onChange={(e) => set('fonte_recurso', e.target.value)}
              className={inputCls(formErrors.fonte_recurso)}>
              <option value="">Selecione...</option>
              {fontes.map((f) => (
                <option key={f.id} value={f.id}>{f.codigo} — {f.nome} ({f.tipo})</option>
              ))}
            </select>
          ) : (
            <p className="text-sm text-gray-700">
              {current.fonte_codigo} — {current.fonte_nome}
            </p>
          )}
        </DetailField>

        {/* Pipeline de Valores */}
        <div className="bg-gray-50 rounded-xl border border-gray-200 p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase mb-3">Pipeline Orçamentário</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { key: 'valor_dotado',        label: 'Dotado',         color: 'text-gray-800' },
              { key: 'valor_indicado',      label: 'Indicado',       color: 'text-blue-700' },
              { key: 'valor_descentralizado', label: 'Descentralizado', color: 'text-amber-700' },
              { key: 'valor_concedido',     label: 'Concedido',      color: 'text-green-700' },
            ].map(({ key, label, color }) => (
              <div key={key}>
                <p className="text-xs text-gray-500 mb-1">{label}</p>
                {editing ? (
                  <CampoMoeda value={form[key]}
                    onChange={(v) => set(key, v)}
                    className={inputCls(formErrors[key])} />
                ) : (
                  <p className={`text-sm font-semibold ${color}`}>
                    {Number(current[key] ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Eixo */}
        <DetailField label="Eixo" error={formErrors.eixo}>
          {editing ? (
            <input type="text" value={form.eixo}
              onChange={(e) => set('eixo', e.target.value)}
              className={inputCls()} />
          ) : (
            <p className="text-sm text-gray-500">{current.eixo || '—'}</p>
          )}
        </DetailField>

        {/* Objetivo estratégico */}
        <DetailField label="Objetivo estratégico" error={formErrors.objetivo_estrategico}>
          {editing ? (
            <input type="text" value={form.objetivo_estrategico}
              onChange={(e) => set('objetivo_estrategico', e.target.value)}
              className={inputCls()} />
          ) : (
            <p className="text-sm text-gray-500">{current.objetivo_estrategico || '—'}</p>
          )}
        </DetailField>

        {/* Observações */}
        <DetailField label="Observações" error={formErrors.observacoes}>
          {editing ? (
            <textarea rows={2} value={form.observacoes}
              onChange={(e) => set('observacoes', e.target.value)}
              className={inputCls()} />
          ) : (
            <p className="text-sm text-gray-500">{current.observacoes || '—'}</p>
          )}
        </DetailField>

        {/* Metadados */}
        <div className="pt-4 border-t border-gray-100 text-xs text-gray-400 space-y-1">
          <p>Criado em: {new Date(current.created_at).toLocaleString('pt-BR')}</p>
          <p>Atualizado em: {new Date(current.updated_at).toLocaleString('pt-BR')}</p>
        </div>

        {/* Necessidades Vinculadas */}
        <div className="pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-semibold text-gray-400 uppercase">
              Necessidades Vinculadas ({(current.necessidades_detail || []).length})
            </p>
            {!showVincular && (
              <button
                onClick={handleAbrirVincular}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium border border-blue-200 hover:border-blue-400 px-3 py-1 rounded-lg transition-colors"
              >
                + Vincular necessidade
              </button>
            )}
          </div>

          {(current.necessidades_detail || []).length === 0 && !showVincular && (
            <p className="text-sm text-gray-400">Nenhuma necessidade vinculada.</p>
          )}

          {(current.necessidades_detail || []).length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-3">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Título</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Status</th>
                    <th className="text-left px-4 py-2 font-medium text-gray-500">Valor</th>
                    <th className="px-4 py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {current.necessidades_detail.map((n) => (
                    <tr key={n.id}>
                      <td className="px-4 py-2 font-medium text-gray-800 max-w-xs truncate">{n.titulo}</td>
                      <td className="px-4 py-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${NECES_STATUS_CLS[n.status] || ''}`}>
                          {n.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-gray-600 text-xs">
                        {Number(n.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button
                          onClick={() => handleDesvincular(n.id)}
                          disabled={loadingVinculo === n.id}
                          className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                        >
                          {loadingVinculo === n.id ? '...' : 'Desvincular'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Painel de vincular */}
          {showVincular && (
            <div className="mt-2 bg-gray-50 border border-gray-200 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-semibold text-gray-700">Vincular Necessidade</p>
                <button
                  onClick={() => setShowVincular(false)}
                  className="text-xs text-gray-400 hover:text-gray-600"
                >
                  Fechar
                </button>
              </div>

              {loadingDisp && (
                <p className="text-sm text-gray-400">Carregando...</p>
              )}

              {!loadingDisp && disponiveis.length === 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                  <p className="text-sm font-medium text-amber-800 mb-0.5">
                    Nenhuma necessidade disponível para vinculação
                  </p>
                  {diagnostico && (
                    <p className="text-xs text-amber-700">{diagnostico}</p>
                  )}
                </div>
              )}

              {!loadingDisp && disponiveis.length > 0 && (
                <div className="space-y-2">
                  {disponiveis.map((n) => (
                    <div key={n.id}
                      className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-3 py-2"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-800">{n.titulo}</p>
                        <p className="text-xs text-gray-400">
                          {n.departamento_solicitante} •{' '}
                          {Number(n.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </p>
                      </div>
                      <button
                        onClick={() => handleVincular(n.id)}
                        disabled={loadingVinculo === n.id}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium border border-blue-200 hover:border-blue-400 px-3 py-1 rounded-lg disabled:opacity-50 transition-colors"
                      >
                        {loadingVinculo === n.id ? '...' : 'Vincular'}
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function DetailField({ label, error, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{label}</p>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

function inputCls(error) {
  return `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
}
