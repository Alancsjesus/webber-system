import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import useFornecedorStore from '../stores/fornecedorStore'
import LoadingSpinner from '../components/LoadingSpinner'
import { mascararDocumento, validarDocumento } from '../utils/documentoValidator'
import api from '../services/api'

const fmt = (v) => v == null ? '—' : Number(v).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
const fmtData = (v) => v ? new Date(v).toLocaleDateString('pt-BR') : '—'

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Fornecedor — Detalhe',
  descricao: 'Cadastro do fornecedor e seu histórico consolidado de relação com a administração (cotações, licitações e contratos), independente de qual órgão registrou cada um.',
  acoes: [
    { label: 'Aviso de relação anterior', texto: 'Aparece quando o fornecedor já teve pelo menos uma cotação, licitação ou contrato registrado — útil para verificar histórico antes de uma nova contratação.' },
    { label: 'Abas Cotações/Licitações/Contratos', texto: 'Lista, por categoria, todos os registros já vinculados a este fornecedor em qualquer órgão da plataforma.' },
    { label: 'Editar',                    texto: 'Altera os dados cadastrais — CNPJ/CPF continua validado por dígito verificador.' },
    { label: 'Famílias SIMPAS',           texto: 'Famílias de item que este fornecedor atende. Ao criar uma Solicitação de Cotação (Parâmetro V) para uma família, o sistema mostra todos os fornecedores marcados com ela como destinatários do disparo.' },
  ],
}
// ──────────────────────────────────────────────────────────────────────────────

export default function FornecedorDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { current, historico, loading, fetchFornecedor, fetchHistorico, updateFornecedor, addFamilia, deleteFamilia } = useFornecedorStore()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(null)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)
  const [aba, setAba] = useState('cotacoes')

  useEffect(() => {
    fetchFornecedor(id)
    fetchHistorico(id)
  }, [id])

  if (loading || !current) return <LoadingSpinner />

  const startEdit = () => {
    setForm({ ...current })
    setEditing(true)
  }

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }

  const handleSave = async () => {
    const errs = {}
    if (!validarDocumento(form.documento, form.tipo_pessoa)) {
      errs.documento = form.tipo_pessoa === 'PF' ? 'CPF inválido' : 'CNPJ inválido'
    }
    if (!form.nome_razao_social.trim()) errs.nome_razao_social = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      await updateFornecedor(id, form)
      setEditing(false)
    } catch (err) {
      const d = err.response?.data || {}
      setErrors(Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v.join(' ') : String(v)])))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <button onClick={() => navigate('/fornecedores')} className="text-sm text-blue-600 hover:underline mb-4">
        ← Voltar para Fornecedores
      </button>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-800">{current.nome_razao_social}</h1>
          <p className="text-sm text-gray-500 mt-0.5 font-mono">{current.documento} · {current.tipo_pessoa === 'PJ' ? 'Pessoa Jurídica' : 'Pessoa Física'}</p>
        </div>
        {!editing && (
          <button onClick={startEdit} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
            Editar
          </button>
        )}
      </div>

      {historico && (
        <div className={`mb-6 px-4 py-3 rounded-lg text-sm ${historico.ja_teve_relacao ? 'bg-amber-50 border border-amber-200 text-amber-800' : 'bg-gray-50 border border-gray-200 text-gray-500'}`}>
          {historico.ja_teve_relacao
            ? 'Este fornecedor já teve relação anterior com a administração — confira as abas abaixo.'
            : 'Nenhum histórico de cotação, licitação ou contrato registrado para este fornecedor ainda.'}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
        {editing ? (
          <div className="space-y-4">
            <DetailField label="Documento" error={errors.documento}>
              <input value={form.documento} onChange={e => set('documento', mascararDocumento(e.target.value, form.tipo_pessoa))}
                className={inp(errors.documento)} />
            </DetailField>
            <DetailField label="Nome / Razão social" error={errors.nome_razao_social}>
              <input value={form.nome_razao_social} onChange={e => set('nome_razao_social', e.target.value)} className={inp(errors.nome_razao_social)} />
            </DetailField>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <DetailField label="Nome fantasia">
                <input value={form.nome_fantasia} onChange={e => set('nome_fantasia', e.target.value)} className={inp()} />
              </DetailField>
              <DetailField label="E-mail">
                <input value={form.email} onChange={e => set('email', e.target.value)} className={inp()} />
              </DetailField>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <DetailField label="Telefone">
                <input value={form.telefone} onChange={e => set('telefone', e.target.value)} className={inp()} />
              </DetailField>
              <DetailField label="Situação">
                <select value={form.ativo ? 'true' : 'false'} onChange={e => set('ativo', e.target.value === 'true')} className={inp()}>
                  <option value="true">Ativo</option>
                  <option value="false">Inativo</option>
                </select>
              </DetailField>
            </div>
            <DetailField label="Observações">
              <textarea rows={3} value={form.observacoes} onChange={e => set('observacoes', e.target.value)} className={inp()} />
            </DetailField>
            <div className="flex gap-2">
              <button onClick={handleSave} disabled={saving}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {saving ? 'Salvando...' : 'Salvar alterações'}
              </button>
              <button onClick={() => setEditing(false)} className="border border-gray-300 text-gray-600 text-sm px-4 py-2 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
            </div>
          </div>
        ) : (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Nome fantasia</dt><dd className="text-gray-700">{current.nome_fantasia || '—'}</dd></div>
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Porte</dt><dd className="text-gray-700">{current.porte_empresa || '—'}</dd></div>
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">E-mail</dt><dd className="text-gray-700">{current.email || '—'}</dd></div>
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Telefone</dt><dd className="text-gray-700">{current.telefone || '—'}</dd></div>
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Município/UF</dt><dd className="text-gray-700">{current.municipio ? `${current.municipio}/${current.uf}` : '—'}</dd></div>
            <div><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Situação</dt><dd className="text-gray-700">{current.ativo ? 'Ativo' : 'Inativo'}</dd></div>
            {current.observacoes && (
              <div className="sm:col-span-2"><dt className="text-gray-400 text-xs uppercase font-semibold mb-0.5">Observações</dt><dd className="text-gray-700 whitespace-pre-wrap">{current.observacoes}</dd></div>
            )}
          </dl>
        )}
      </div>

      <FamiliasFornecedor
        fornecedorId={current.id}
        familias={current.familias || []}
        onAdd={(f) => addFamilia(current.id, f)}
        onDelete={(familiaId) => deleteFamilia(current.id, familiaId)}
      />

      <div className="border-b border-gray-200 mb-4 flex gap-4">
        {[
          ['cotacoes', `Cotações (${historico?.cotacoes.length ?? 0})`],
          ['licitacoes', `Licitações (${historico?.resultados_licitacao.length ?? 0})`],
          ['contratos', `Contratos (${historico?.contratos.length ?? 0})`],
        ].map(([key, label]) => (
          <button key={key} onClick={() => setAba(key)}
            className={`pb-2 text-sm font-medium border-b-2 ${aba === key ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}>
            {label}
          </button>
        ))}
      </div>

      {aba === 'cotacoes' && (
        <ListaHistorico
          itens={historico?.cotacoes}
          vazio="Nenhuma resposta de cotação registrada para este fornecedor."
          colunas={['Mapa', 'Família', 'Resposta em', 'Recusou', 'Valor']}
          render={(c) => [c.mapa_id, c.familia_simpas || '—', fmtData(c.data_resposta), c.recusou ? 'Sim' : 'Não', fmt(c.valor_respondido)]}
        />
      )}
      {aba === 'licitacoes' && (
        <ListaHistorico
          itens={historico?.resultados_licitacao}
          vazio="Nenhuma licitação vencida por este fornecedor."
          colunas={['Procedimento', 'Resultado', 'Valor final']}
          render={(r) => [r.procedimento_numero, r.resultado, fmt(r.valor_final)]}
        />
      )}
      {aba === 'contratos' && (
        <ListaHistorico
          itens={historico?.contratos}
          vazio="Nenhum contrato executado por este fornecedor."
          colunas={['Número', 'Objeto', 'Status', 'Valor', 'Vigência']}
          render={(ct) => [ct.numero, ct.objeto?.slice(0, 60), ct.status, fmt(ct.valor_contrato), `${fmtData(ct.data_vigencia_inicio)} – ${fmtData(ct.data_vigencia_fim)}`]}
          onClick={(ct) => navigate(`/contratos/${ct.id}`)}
        />
      )}
    </div>
  )
}

function FamiliasFornecedor({ fornecedorId, familias, onAdd, onDelete }) {
  const [sugestoes, setSugestoes] = useState([])
  const [novaFamilia, setNovaFamilia] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/core/catalogo/familias/').then(({ data }) => setSugestoes(data)).catch(() => {})
  }, [])

  const handleAdd = async () => {
    const valor = novaFamilia.trim()
    if (!valor) return
    setSaving(true)
    try { await onAdd(valor); setNovaFamilia('') } finally { setSaving(false) }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
      <p className="text-sm font-semibold text-gray-700 mb-1">Famílias SIMPAS atendidas</p>
      <p className="text-xs text-gray-400 mb-3">
        Usado para selecionar destinatários ao disparar uma Solicitação de Cotação (Parâmetro V).
      </p>
      <div className="flex flex-wrap gap-2 mb-3">
        {familias.length === 0 && <span className="text-xs text-gray-400">Nenhuma família cadastrada ainda.</span>}
        {familias.map((f) => (
          <span key={f.id} className="inline-flex items-center gap-1.5 bg-blue-50 text-blue-700 text-xs font-medium px-2.5 py-1 rounded-full">
            {f.familia_simpas}
            <button onClick={() => onDelete(f.id)} className="text-blue-400 hover:text-blue-700">✕</button>
          </span>
        ))}
      </div>
      <div className="flex gap-2">
        <input list="familias-sugestoes" value={novaFamilia} onChange={(e) => setNovaFamilia(e.target.value)}
          placeholder="Ex: 42.40"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <datalist id="familias-sugestoes">
          {sugestoes.map((f) => <option key={f} value={f} />)}
        </datalist>
        <button onClick={handleAdd} disabled={saving || !novaFamilia.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
          Adicionar
        </button>
      </div>
    </div>
  )
}

function ListaHistorico({ itens, vazio, colunas, render, onClick }) {
  if (!itens || itens.length === 0) {
    return <p className="text-sm text-gray-400 py-6 text-center">{vazio}</p>
  }
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[560px]">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>{colunas.map(c => <th key={c} className="text-left px-5 py-3 font-medium text-gray-500">{c}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {itens.map((item, i) => (
              <tr key={item.id ?? i} className={onClick ? 'hover:bg-gray-50 cursor-pointer' : ''} onClick={() => onClick?.(item)}>
                {render(item).map((v, j) => <td key={j} className="px-5 py-3 text-gray-700">{v}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function DetailField({ label, error, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}
const inp = (err) => `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${err ? 'border-red-400' : 'border-gray-300'}`
