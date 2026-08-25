import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import useAtaStore from '../stores/ataStore'
import FormErrors from '../components/FormErrors'
import FornecedorPicker from '../components/FornecedorPicker'
import CampoMoeda from '../components/CampoMoeda'

function novoItem() {
  return {
    item_catalogo: null, item_catalogo_label: '', objeto: '', unidade_medida: '',
    fornecedor: null, fornecedor_label: '', quantidade_registrada: '', valor_unitario_registrado: '',
  }
}

// ─── Ajuda Contextual ────────────────────────────────────────────────────────
export const pageHelp = {
  titulo: 'Nova Ata de Registro de Preços',
  descricao: 'Cadastra a ata e seus itens registrados. Vincular o item ao catálogo SIMPAS é o que permite que ele apareça no Confronto de Necessidades — sem esse vínculo, o item fica só de registro, sem cruzamento automático.',
  acoes: [
    { label: 'Tipo de origem',        texto: 'Própria: gerada por um Procedimento deste órgão — selecione o procedimento de origem. Carona: ata gerenciada por outro órgão, aderida manualmente — exige número no PNCP e dados do órgão gerenciador.' },
    { label: 'Buscar no catálogo',    texto: 'Vincula o item ao catálogo SIMPAS (pré-preenche descrição e unidade) — necessário para o item entrar no confronto contra DFDs pendentes. Sem catálogo, o item fica só de registro manual.' },
    { label: '+ Adicionar item',      texto: 'Cada item registra quantidade e valor unitário pactuados na ata — o saldo disponível é calculado automaticamente (quantidade registrada menos consumida).' },
    { label: 'Criar ata',             texto: 'Salva a ata como Rascunho. É preciso Ativá-la depois (na tela de detalhe) para que ela entre no confronto de necessidades.' },
  ],
  baseLegal: 'Lei 14.133/2021 — Art. 82 a 86.',
}
// ──────────────────────────────────────────────────────────────────────────────

export default function AtaCreate() {
  const navigate = useNavigate()
  const { createAta, criarItem } = useAtaStore()

  const [form, setForm] = useState({
    tipo_origem: 'propria',
    numero_ata: '',
    procedimento: '',
    numero_pncp: '',
    orgao_gerenciador_nome: '',
    orgao_gerenciador_cnpj: '',
    orgao_gerenciador_uf: '',
    objeto: '',
    data_assinatura: '',
    data_vigencia_inicio: '',
    data_vigencia_fim: '',
    observacoes: '',
  })
  const [procedimentos, setProcedimentos] = useState([])
  const [itens, setItens] = useState([novoItem()])
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  useEffect(() => {
    api.get('/licitacao/procedimento/', { params: { page_size: 100 } })
      .then(({ data }) => {
        const lista = data.results ?? data
        setProcedimentos(Array.isArray(lista) ? lista : [])
      })
      .catch(() => setProcedimentos([]))
  }, [])

  const set = (k, v) => { setForm(p => ({ ...p, [k]: v })); setErrors(p => ({ ...p, [k]: undefined })) }
  const setItem = (idx, field, value) =>
    setItens(prev => { const n = [...prev]; n[idx] = { ...n[idx], [field]: value }; return n })

  const buscarCatalogo = async (idx, query) => {
    if (!query || query.length < 2) return []
    const { data } = await api.get('/core/catalogo/', { params: { search: query, page_size: 8 } })
    return data.results ?? data
  }

  const validate = () => {
    const errs = {}
    if (!form.numero_ata.trim()) errs.numero_ata = 'Campo obrigatório'
    if (!form.objeto.trim()) errs.objeto = 'Campo obrigatório'
    if (form.tipo_origem === 'carona') {
      if (!form.numero_pncp.trim()) errs.numero_pncp = 'Obrigatório para ata de carona'
      if (!form.orgao_gerenciador_nome.trim()) errs.orgao_gerenciador_nome = 'Obrigatório para ata de carona'
    }
    const itensValidos = itens.filter(
      i => i.objeto.trim() && i.unidade_medida.trim() &&
           parseFloat(i.quantidade_registrada) > 0 && parseFloat(i.valor_unitario_registrado) > 0
    )
    if (itensValidos.length === 0) errs.itens = 'Adicione ao menos um item com objeto, unidade, quantidade e valor'
    return { errs, itensValidos }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const { errs, itensValidos } = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const payload = {
        tipo_origem: form.tipo_origem,
        numero_ata: form.numero_ata,
        objeto: form.objeto,
        data_assinatura: form.data_assinatura || null,
        data_vigencia_inicio: form.data_vigencia_inicio || null,
        data_vigencia_fim: form.data_vigencia_fim || null,
        observacoes: form.observacoes,
        ...(form.tipo_origem === 'propria' && form.procedimento ? { procedimento: Number(form.procedimento) } : {}),
        ...(form.tipo_origem === 'carona' ? {
          numero_pncp: form.numero_pncp,
          orgao_gerenciador_nome: form.orgao_gerenciador_nome,
          orgao_gerenciador_cnpj: form.orgao_gerenciador_cnpj,
          orgao_gerenciador_uf: form.orgao_gerenciador_uf,
        } : {}),
      }
      const ata = await createAta(payload)

      await Promise.all(itensValidos.map(item => criarItem(ata.id, {
        item_catalogo: item.item_catalogo || null,
        objeto: item.objeto,
        unidade_medida: item.unidade_medida,
        fornecedor: item.fornecedor || null,
        quantidade_registrada: parseFloat(item.quantidade_registrada),
        valor_unitario_registrado: parseFloat(item.valor_unitario_registrado),
      })))

      navigate(`/arp/${ata.id}`)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      if (!Object.keys(mapped).length) mapped._geral = 'Erro ao criar a ata. Verifique os dados.'
      setErrors(mapped)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>
      <h1 className="text-xl font-bold text-gray-800 mb-6">Nova Ata de Registro de Preços</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />
        {errors._geral && (
          <div className="bg-red-50 border border-red-300 rounded-lg px-4 py-3 text-sm text-red-700">{errors._geral}</div>
        )}

        <Field label="Tipo de origem">
          <div className="flex gap-2">
            {[['propria', 'Ata Própria'], ['carona', 'Carona']].map(([value, label]) => (
              <button key={value} type="button" onClick={() => set('tipo_origem', value)}
                className={`flex-1 border rounded-lg px-3 py-2 text-sm ${form.tipo_origem === value ? 'border-indigo-500 bg-indigo-50 text-indigo-700 font-medium' : 'border-gray-300 text-gray-600'}`}>
                {label}
              </button>
            ))}
          </div>
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Número da ata *" error={errors.numero_ata}>
            <input type="text" value={form.numero_ata} onChange={e => set('numero_ata', e.target.value)}
              className={inp(errors.numero_ata)} />
          </Field>

          {form.tipo_origem === 'propria' ? (
            <Field label="Procedimento de origem (opcional)">
              <select value={form.procedimento} onChange={e => set('procedimento', e.target.value)} className={inp()}>
                <option value="">— Selecione —</option>
                {procedimentos.map(p => <option key={p.id} value={p.id}>{p.numero} — {p.objeto?.slice(0, 40)}</option>)}
              </select>
            </Field>
          ) : (
            <Field label="Número no PNCP *" error={errors.numero_pncp}>
              <input type="text" value={form.numero_pncp} onChange={e => set('numero_pncp', e.target.value)}
                className={inp(errors.numero_pncp)} />
            </Field>
          )}
        </div>

        {form.tipo_origem === 'carona' && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Órgão gerenciador *" error={errors.orgao_gerenciador_nome}>
              <input type="text" value={form.orgao_gerenciador_nome} onChange={e => set('orgao_gerenciador_nome', e.target.value)}
                className={inp(errors.orgao_gerenciador_nome)} />
            </Field>
            <Field label="CNPJ do órgão gerenciador">
              <input type="text" value={form.orgao_gerenciador_cnpj} onChange={e => set('orgao_gerenciador_cnpj', e.target.value)}
                className={inp()} />
            </Field>
            <Field label="UF">
              <input type="text" maxLength={2} value={form.orgao_gerenciador_uf}
                onChange={e => set('orgao_gerenciador_uf', e.target.value.toUpperCase())} className={inp()} />
            </Field>
          </div>
        )}

        <Field label="Objeto *" error={errors.objeto}>
          <textarea rows={3} value={form.objeto} onChange={e => set('objeto', e.target.value)} className={inp(errors.objeto)} />
        </Field>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Data de assinatura">
            <input type="date" value={form.data_assinatura} onChange={e => set('data_assinatura', e.target.value)} className={inp()} />
          </Field>
          <Field label="Início da vigência">
            <input type="date" value={form.data_vigencia_inicio} onChange={e => set('data_vigencia_inicio', e.target.value)} className={inp()} />
          </Field>
          <Field label="Fim da vigência">
            <input type="date" value={form.data_vigencia_fim} onChange={e => set('data_vigencia_fim', e.target.value)} className={inp()} />
          </Field>
        </div>

        {/* Itens */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-700">Itens da ata</p>
            <button type="button" onClick={() => setItens(p => [...p, novoItem()])}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium">+ Adicionar item</button>
          </div>
          {errors.itens && <p className="text-xs text-red-600 mb-2">{errors.itens}</p>}

          <div className="space-y-3">
            {itens.map((item, idx) => (
              <ItemRow key={idx} item={item} idx={idx} setItem={setItem} buscarCatalogo={buscarCatalogo}
                onRemove={() => setItens(p => p.filter((_, i) => i !== idx))} podeRemover={itens.length > 1} />
            ))}
          </div>
        </div>

        <Field label="Observações (opcional)">
          <textarea rows={2} value={form.observacoes} onChange={e => set('observacoes', e.target.value)} className={inp()} />
        </Field>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Salvando...' : 'Criar ata'}
          </button>
          <button type="button" onClick={() => navigate(-1)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 font-medium px-5 py-2 rounded-lg text-sm">
            Cancelar
          </button>
        </div>
      </form>
    </div>
  )
}

function ItemRow({ item, idx, setItem, buscarCatalogo, onRemove, podeRemover }) {
  const [query, setQuery] = useState(item.item_catalogo_label)
  const [resultados, setResultados] = useState([])
  const [aberto, setAberto] = useState(false)

  useEffect(() => {
    if (!query) { setResultados([]); return }
    const t = setTimeout(async () => setResultados(await buscarCatalogo(idx, query)), 300)
    return () => clearTimeout(t)
  }, [query])

  const selecionarCatalogo = (cat) => {
    setItem(idx, 'item_catalogo', cat.id)
    setItem(idx, 'item_catalogo_label', cat.nome)
    setItem(idx, 'objeto', cat.nome)
    setItem(idx, 'unidade_medida', cat.unidade_medida || '')
    setQuery(cat.nome)
    setAberto(false)
  }

  return (
    <div className="border border-gray-200 rounded-lg p-3 bg-gray-50">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-400 uppercase">Item {idx + 1}</span>
        {podeRemover && <button type="button" onClick={onRemove} className="text-xs text-red-400 hover:text-red-600">Remover</button>}
      </div>

      <div className="relative mb-2">
        <label className="block text-xs text-gray-500 mb-0.5">Buscar no catálogo (opcional, recomendado)</label>
        <input type="text" value={query}
          onChange={e => { setQuery(e.target.value); setAberto(true); if (item.item_catalogo) { setItem(idx, 'item_catalogo', null); setItem(idx, 'item_catalogo_label', '') } }}
          onFocus={() => setAberto(true)}
          placeholder="Buscar item do catálogo SIMPAS..."
          className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        {aberto && query && !item.item_catalogo && resultados.length > 0 && (
          <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {resultados.map(cat => (
              <button key={cat.id} type="button" onClick={() => selecionarCatalogo(cat)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 border-b border-gray-100 last:border-0">
                <span className="block text-gray-800">{cat.nome}</span>
                <span className="text-xs text-gray-400 font-mono">{cat.codigo_interno} {cat.codigo_simpas}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-0.5">Objeto / Descrição</label>
          <input type="text" value={item.objeto} onChange={e => setItem(idx, 'objeto', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-0.5">Unidade</label>
          <input type="text" value={item.unidade_medida} onChange={e => setItem(idx, 'unidade_medida', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-0.5">Quantidade registrada</label>
          <input type="number" min="0" step="0.0001" value={item.quantidade_registrada}
            onChange={e => setItem(idx, 'quantidade_registrada', e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-0.5">Valor unitário registrado (R$)</label>
          <CampoMoeda value={item.valor_unitario_registrado} onChange={v => setItem(idx, 'valor_unitario_registrado', v)}
            className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm" />
        </div>
        <div className="col-span-2">
          <label className="block text-xs text-gray-500 mb-0.5">Fornecedor (opcional)</label>
          <FornecedorPicker value={item.fornecedor} valueLabel={item.fornecedor_label}
            onChange={(id, forn) => { setItem(idx, 'fornecedor', id); setItem(idx, 'fornecedor_label', forn ? `${forn.documento} — ${forn.nome_razao_social}` : '') }} />
        </div>
      </div>
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

const inp = (error) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
    error ? 'border-red-400' : 'border-gray-300'
  }`
