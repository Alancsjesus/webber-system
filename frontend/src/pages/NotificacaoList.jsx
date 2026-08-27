import { useEffect, useState } from 'react'
import useNotificacaoContratualStore from '../stores/notificacaoContratualStore'
import useAuthStore from '../stores/authStore'
import LoadingSpinner from '../components/LoadingSpinner'
import Pagination from '../components/Pagination'
import ContratoPicker from '../components/ContratoPicker'
import CampoSei, { NumeroSeiTexto } from '../components/CampoSei'
import useDebouncedValue from '../hooks/useDebouncedValue'

const PAGE_SIZE = 20

const CATEGORIA_OPTS = [
  { value: 'aquisicao', label: 'Aquisição' },
  { value: 'obra',      label: 'Obra' },
  { value: 'servico',   label: 'Serviço' },
]

const STATUS_OPTS = [
  { value: 'andamento', label: 'Em Andamento' },
  { value: 'cpa',       label: 'Em CPA' },
  { value: 'concluido', label: 'Concluído' },
]

const STATUS_CLS = {
  andamento: 'bg-blue-100 text-blue-700',
  cpa:       'bg-amber-100 text-amber-700',
  concluido: 'bg-green-100 text-green-700',
}

const FORM_VAZIO = {
  contrato: '', categoria_objeto: 'aquisicao',
  numero_processo_sei: '', numero_sei_comunicacao: '', numero_sei_notificacao: '',
  data_notificacao: '', resumo_fato: '', observacoes: '',
}

// ─── Ajuda Contextual ─────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Notificações Contratuais',
  descricao: 'Controle de notificações formais enviadas às empresas contratadas (atraso, ausência de garantia, paralisação, alegações finais etc.) — substitui o controle manual em planilha, com numeração interna automática por órgão/exercício.',
  acoes: [
    { label: '+ Nova Notificação', texto: 'Vincula a um contrato existente. Processo SEI, Nº Comunicação e Nº da Notificação são independentes: nem toda notificação tem os três preenchidos desde o início.' },
    { label: 'Status (inline)',    texto: 'Em Andamento: acompanhamento inicial. Em CPA: encaminhada à Coordenação/Comissão de Processos Administrativos para possível apuração/sanção. Concluído: caso encerrado.' },
    { label: 'Filtros',            texto: 'Combine Status, Tipo (Aquisição/Obra/Serviço) e Exercício, ou busque por número, resumo, contrato, fornecedor ou qualquer um dos números de SEI.' },
  ],
  dica: 'O número de controle (ex: NOT-CCC-001/2026) é gerado automaticamente por órgão executor e exercício — não precisa ser preenchido manualmente.',
  baseLegal: 'Lei 14.133/2021 — fiscalização e aplicação de sanções na execução contratual.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function NotificacaoList() {
  const { notificacoes, total, loading, fetchNotificacoes, createNotificacao, updateNotificacao } = useNotificacaoContratualStore()
  const seiBaseUrl = useAuthStore((s) => s.seiBaseUrl)

  const [searchInput, setSearchInput] = useState('')
  const [page, setPage] = useState(1)
  const [filtros, setFiltros] = useState({ status: '', categoria_objeto: '', exercicio: '' })
  const search = useDebouncedValue(searchInput)

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState(FORM_VAZIO)
  const [contratoLabel, setContratoLabel] = useState('')
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => { setPage(1) }, [search, filtros])

  useEffect(() => {
    const params = { page, page_size: PAGE_SIZE }
    if (search) params.search = search
    for (const [k, v] of Object.entries(filtros)) if (v !== '') params[k] = v
    fetchNotificacoes(params)
  }, [search, filtros, page])

  const set = (k, v) => setForm((p) => ({ ...p, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.contrato) errs.contrato = 'Selecione um contrato'
    if (!form.resumo_fato) errs.resumo_fato = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }
    setSaving(true)
    try {
      await createNotificacao({ ...form, contrato: Number(form.contrato) })
      setShowForm(false)
      setForm(FORM_VAZIO)
      setContratoLabel('')
      setErrors({})
      fetchNotificacoes({ page, page_size: PAGE_SIZE })
    } catch (err) {
      const d = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(d)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  const handleStatusChange = async (notificacao, status) => {
    await updateNotificacao(notificacao.id, { status })
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Notificações Contratuais</h1>
          <p className="text-sm text-gray-500 mt-0.5">Controle de notificações enviadas às empresas contratadas</p>
        </div>
        <button onClick={() => setShowForm((v) => !v)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
          {showForm ? 'Cancelar' : '+ Nova Notificação'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Contrato *" error={errors.contrato}>
              <ContratoPicker
                value={form.contrato}
                valueLabel={contratoLabel}
                onChange={(id, contrato) => {
                  set('contrato', id || '')
                  setContratoLabel(contrato ? `${contrato.numero} — ${contrato.objeto?.slice(0, 50) || ''}` : '')
                }}
              />
            </Field>
            <Field label="Tipo" error={errors.categoria_objeto}>
              <select value={form.categoria_objeto} onChange={(e) => set('categoria_objeto', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {CATEGORIA_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Processo SEI" error={errors.numero_processo_sei}>
              <CampoSei value={form.numero_processo_sei} onChange={(v) => set('numero_processo_sei', v)} />
            </Field>
            <Field label="Nº Comunicação (SEI)" error={errors.numero_sei_comunicacao}>
              <CampoSei value={form.numero_sei_comunicacao} onChange={(v) => set('numero_sei_comunicacao', v)} />
            </Field>
            <Field label="Nº da Notificação (SEI)" error={errors.numero_sei_notificacao}>
              <CampoSei value={form.numero_sei_notificacao} onChange={(v) => set('numero_sei_notificacao', v)} />
            </Field>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Field label="Data da Notificação" error={errors.data_notificacao}>
              <input type="date" value={form.data_notificacao} onChange={(e) => set('data_notificacao', e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </Field>
          </div>

          <Field label="Resumo do Fato *" error={errors.resumo_fato}>
            <textarea rows={2} value={form.resumo_fato} onChange={(e) => set('resumo_fato', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </Field>

          <Field label="Observação" error={errors.observacoes}>
            <textarea rows={2} value={form.observacoes} onChange={(e) => set('observacoes', e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </Field>

          <button type="submit" disabled={saving}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Salvando...' : 'Salvar notificação'}
          </button>
        </form>
      )}

      <div className="flex flex-wrap gap-3 mb-4 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Buscar</label>
          <input type="text" value={searchInput} onChange={(e) => setSearchInput(e.target.value)}
            placeholder="número, resumo, contrato, fornecedor, SEI..."
            className="w-72 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
          <select value={filtros.status} onChange={(e) => setFiltros((p) => ({ ...p, status: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos</option>
            {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Tipo</label>
          <select value={filtros.categoria_objeto} onChange={(e) => setFiltros((p) => ({ ...p, categoria_objeto: e.target.value }))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="">Todos</option>
            {CATEGORIA_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Exercício</label>
          <input type="number" value={filtros.exercicio} onChange={(e) => setFiltros((p) => ({ ...p, exercicio: e.target.value }))}
            className="w-24 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && (
        notificacoes.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma notificação encontrada.</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs min-w-[1500px]">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Nº Controle</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Contrato</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Tipo</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Processo SEI</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Nº Comunicação</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Nº Notificação</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Data</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Resumo do Fato</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Fornecedor</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">CNPJ</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Status</th>
                    <th className="text-left px-3 py-2 font-medium text-gray-500">Observação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {notificacoes.map((n) => (
                    <tr key={n.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-mono text-gray-500 whitespace-nowrap">{n.numero}</td>
                      <td className="px-3 py-2 text-gray-700 max-w-[160px] truncate" title={n.contrato_numero}>{n.contrato_numero}</td>
                      <td className="px-3 py-2 text-gray-600">{n.categoria_objeto_display}</td>
                      <td className="px-3 py-2"><NumeroSeiTexto valor={n.numero_processo_sei} seiBaseUrl={seiBaseUrl} className="font-mono text-xs text-gray-600" /></td>
                      <td className="px-3 py-2"><NumeroSeiTexto valor={n.numero_sei_comunicacao} seiBaseUrl={seiBaseUrl} className="font-mono text-xs text-gray-600" /></td>
                      <td className="px-3 py-2"><NumeroSeiTexto valor={n.numero_sei_notificacao} seiBaseUrl={seiBaseUrl} className="font-mono text-xs text-gray-600" /></td>
                      <td className="px-3 py-2 text-gray-600 whitespace-nowrap">{n.data_notificacao ? new Date(n.data_notificacao + 'T00:00').toLocaleDateString('pt-BR') : '—'}</td>
                      <td className="px-3 py-2 text-gray-700 max-w-[260px] truncate" title={n.resumo_fato}>{n.resumo_fato}</td>
                      <td className="px-3 py-2 text-gray-600 max-w-[160px] truncate" title={n.fornecedor_nome || ''}>{n.fornecedor_nome || <span className="text-gray-300">—</span>}</td>
                      <td className="px-3 py-2 font-mono text-gray-500">{n.fornecedor_documento || <span className="text-gray-300">—</span>}</td>
                      <td className="px-3 py-2">
                        <select value={n.status} onChange={(e) => handleStatusChange(n, e.target.value)}
                          className={`px-2 py-1 rounded-full text-[10px] font-medium border-0 focus:outline-none focus:ring-2 focus:ring-blue-500 ${STATUS_CLS[n.status] || 'bg-gray-100 text-gray-600'}`}>
                          {STATUS_OPTS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      </td>
                      <td className="px-3 py-2 text-gray-600 max-w-[200px] truncate" title={n.observacoes || ''}>{n.observacoes || <span className="text-gray-300">—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="px-3">
              <Pagination page={page} count={total} pageSize={PAGE_SIZE} itemLabel="notificação(ões)" onPage={setPage} />
            </div>
          </div>
        )
      )}
    </div>
  )
}

function Field({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}
