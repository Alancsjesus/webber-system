import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import useTrStore from '../stores/trStore'
import FormErrors from '../components/FormErrors'

// ── Helpers ───────────────────────────────────────────────────────────────────

const TIPO_OBJETO_LABEL = {
  bens:                'Bens',
  servicos:            'Serviços Comuns',
  servicos_engenharia: 'Serviços de Engenharia',
  obras:               'Obras',
  hibrido:             'Híbrido — Bens e Serviços',
}

// Mapeia tipos legados do ETP para os choices do TR
const MAPA_TIPO_ETP = {
  bens:                 'bens',
  material:             'bens',
  servicos:             'servicos',
  servico_continuo:     'servicos',
  servico_nao_continuo: 'servicos',
  servicos_engenharia:  'servicos_engenharia',
  obras:                'obras',
}
const mapearTipoEtp = (t) => MAPA_TIPO_ETP[t] || ''

const ehBens     = (t) => ['bens', 'hibrido'].includes(t)
const ehServicos = (t) => ['servicos', 'servicos_engenharia', 'hibrido'].includes(t)

const TIPO_PRAZO_OPTS = [
  { value: '',            label: '— Selecione —' },
  { value: 'escopo',      label: 'Por Escopo — Entrega única (Art. 105)' },
  { value: 'continuo',    label: 'Contínuo — Serviço continuado (Art. 106/107)' },
  { value: 'emergencial', label: 'Emergencial — Contratação direta emergência (Art. 75, VIII)' },
  { value: 'direta_108',  label: 'Contratação Direta Art. 108' },
]
const INSTRUMENTO_OPTS = [
  { value: '',         label: '— Selecione —' },
  { value: 'contrato', label: 'Assinatura do Contrato' },
  { value: 'afm',      label: 'AFM — Autorização de Fornecimento de Material' },
  { value: 'aps',      label: 'APS — Autorização de Prestação de Serviços' },
]
const EXAME_OPTS = [
  { value: 'nenhum',        label: 'Não será exigido exame de adequação' },
  { value: 'amostra',       label: 'Amostra' },
  { value: 'conformidade',  label: 'Exame de conformidade' },
  { value: 'prova_conceito',label: 'Prova de conceito' },
  { value: 'certificacao',  label: 'Certificação CONMETRO' },
  { value: 'teste',         label: 'Teste específico' },
]
const VISTORIA_OPTS = [
  { value: 'nao',        label: 'Não será exigida vistoria prévia' },
  { value: 'obrigatoria',label: 'Vistoria obrigatória com agendamento' },
  { value: 'facultativa',label: 'Vistoria facultativa (declaração em substituição)' },
]
const SUBCONTR_OPTS = [
  { value: 'nao',    label: 'Não será admitida subcontratação' },
  { value: 'parcial',label: 'Subcontratação parcial permitida' },
]
const HAB_ESFERA_OPTS = [
  { value: 'estadual', label: 'Estadual / Distrital' },
  { value: 'municipal',label: 'Municipal / Distrital' },
  { value: 'ambos',    label: 'Estadual e Municipal' },
]

function gerarRedacao(tipo, meses, instrumento) {
  const inst = INSTRUMENTO_OPTS.find(i => i.value === instrumento)?.label || 'assinatura do Contrato'
  if (tipo === 'escopo')
    return `O prazo de vigência do Contrato é de 30 dias, a contar da data da ${inst}, observado o artigo 105 da Lei Federal nº 14.133/2021.`
  if (tipo === 'continuo')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 5 anos), a contar da data da ${inst}, prorrogável até atingir o limite de 10 anos, na forma dos artigos 106 e 107 da Lei Federal nº 14.133/2021.`
  if (tipo === 'emergencial')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses, podendo ser prorrogado, desde que o prazo total não ultrapasse 1 (um) ano, observado o art. 75, inc. VIII, da Lei Federal nº 14.133/2021.`
  if (tipo === 'direta_108')
    return `O prazo de vigência do Contrato é de ${meses || '___'} meses (máximo de 10 anos), a contar da data da ${inst}, nos termos do artigo 108 da Lei Federal nº 14.133/2021.`
  return ''
}

// ── Componentes UI ────────────────────────────────────────────────────────────

function F({ label, error, hint, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-400 mb-1">{hint}</p>}
      {children}
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  )
}

function Secao({ titulo, tag, cor = 'teal', children }) {
  const cores = {
    teal:   'border-teal-200 bg-teal-700',
    blue:   'border-blue-200 bg-blue-700',
    purple: 'border-purple-200 bg-purple-700',
    indigo: 'border-indigo-200 bg-indigo-700',
  }
  const [borda, fundo] = (cores[cor] || cores.teal).split(' ')
  return (
    <div className={`border ${borda} rounded-xl overflow-hidden`}>
      <div className={`${fundo} text-white px-4 py-2 flex items-center gap-2`}>
        <span className="text-sm font-semibold uppercase tracking-wide">{titulo}</span>
        {tag && <span className="ml-auto text-xs bg-white/20 px-2 py-0.5 rounded-full">{tag}</span>}
      </div>
      <div className="p-4 space-y-4">{children}</div>
    </div>
  )
}

function Toggle({ label, checked, onChange, hint }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <button type="button"
        onClick={onChange}
        className={`mt-0.5 w-10 h-5 rounded-full flex items-center transition-colors shrink-0 ${checked ? 'bg-blue-600' : 'bg-gray-300'}`}>
        <span className={`w-4 h-4 bg-white rounded-full shadow transition-transform mx-0.5 ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
      </button>
      <div>
        <span className="text-sm text-gray-700">{label}</span>
        {hint && <p className="text-xs text-gray-400 mt-0.5">{hint}</p>}
      </div>
    </label>
  )
}

const inp = (err) =>
  `w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 ${err ? 'border-red-400' : 'border-gray-300'}`
const sel = () =>
  'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500'

// ── Formulário principal ──────────────────────────────────────────────────────

export default function TRCreate() {
  const navigate = useNavigate()
  const location = useLocation()
  const etp = location.state?.etp
  const { createTr } = useTrStore()

  const tipoEtp = mapearTipoEtp(etp?.etp_tipo_objeto || etp?.tipo_objeto || '')

  const [form, setForm] = useState({
    tipo_objeto:             tipoEtp,
    contratacao_delegada:    false,
    sistema_registro_precos: false,

    objeto_contratacao:     etp?.dfd_descricao || etp?.necessidade_contratacao || '',
    justificativa:          etp?.justificativa_solucao  || '',
    requisitos_contratacao: etp?.requisitos_contratacao || '',
    obrigacoes_contratada:  '',
    obrigacoes_contratante: '',
    criterios_selecao:      '',
    criterios_medicao:      '',

    tipo_prazo_vigencia: '',
    prazo_meses:         '',
    instrumento_inicio:  '',
    prazo_observacao:    '',
    local_entrega:       etp?.dfd_local_entrega || '',
    garantia_contrato:   '',
    estimativa_valor:    etp?.estimativa_valor  || '',

    req_sustentabilidade:           false,
    req_sustentabilidade_criterios: etp?.sustentabilidade || '',
    req_indicacao_marca:            false,
    req_indicacao_marca_justific:   '',
    req_exame_adequacao:            'nenhum',
    req_exame_descricao:            '',
    req_vistoria:                   'nao',
    req_vistoria_detalhes:          '',
    req_subcontratacao:             'nao',
    req_subcontratacao_descricao:   '',
    req_subcontratacao_mep:         false,
    req_garantia_proposta:          false,
    req_garantia_contratacao:       false,
    req_garantia_percentual:        '',
    req_garantia_modalidade:        '',

    hab_fiscal_esfera: ['servicos','servicos_engenharia'].includes(tipoEtp) ? 'municipal' : 'estadual',

    bens_nao_luxo:               true,
    bens_reserva_cota:           etp?.etp_reserva_cota_me_epp || false,
    bens_reserva_cota_percentual: 25,
    bens_carta_solidariedade:    false,
    bens_validade_pereciveis:    '',
    bens_garantia_tecnica_prazo: '',
    bens_garantia_tecnica_det:   '',

    serv_transicao_contratual: false,
    serv_transicao_descricao:  '',
    serv_regime_execucao:      '',
    serv_materiais:            '',
    serv_qualificacao_tecnica: etp?.requisitos_contratacao || '',
    serv_parcelas_relevancia:  '',

    observacoes: '',
  })

  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState({})

  if (!etp) {
    return (
      <div className="p-8">
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          Nenhum ETP selecionado. Acesse esta página a partir de um ETP aprovado.
        </p>
        <button onClick={() => navigate(-1)} className="mt-4 text-sm text-blue-600 hover:underline">← Voltar</button>
      </div>
    )
  }

  const set   = (f, v) => { setForm(p => ({ ...p, [f]: v })); setErrors(p => ({ ...p, [f]: undefined })) }
  const isBens    = ehBens(form.tipo_objeto)
  const isServico = ehServicos(form.tipo_objeto)
  const tipo      = form.tipo_prazo_vigencia
  const precisaMeses = ['continuo','emergencial','direta_108'].includes(tipo)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!form.objeto_contratacao.trim()) errs.objeto_contratacao = 'Campo obrigatório'
    if (Object.keys(errs).length) { setErrors(errs); return }

    setSaving(true)
    try {
      const payload = {
        etp: etp.id,
        tipo_objeto: form.tipo_objeto,
        contratacao_delegada: form.contratacao_delegada,
        sistema_registro_precos: form.sistema_registro_precos,
        objeto_contratacao: form.objeto_contratacao,
        justificativa: form.justificativa,
        requisitos_contratacao: form.requisitos_contratacao,
        obrigacoes_contratada: form.obrigacoes_contratada,
        obrigacoes_contratante: form.obrigacoes_contratante,
        criterios_selecao: form.criterios_selecao,
        criterios_medicao: form.criterios_medicao,
        tipo_prazo_vigencia: form.tipo_prazo_vigencia || '',
        prazo_meses: form.prazo_meses ? Number(form.prazo_meses) : null,
        instrumento_inicio: form.instrumento_inicio || '',
        prazo_observacao: form.prazo_observacao,
        local_entrega: form.local_entrega,
        garantia_contrato: form.garantia_contrato,
        estimativa_valor: form.estimativa_valor ? Number(form.estimativa_valor) : null,
        req_sustentabilidade: form.req_sustentabilidade,
        req_sustentabilidade_criterios: form.req_sustentabilidade_criterios,
        req_indicacao_marca: form.req_indicacao_marca,
        req_indicacao_marca_justific: form.req_indicacao_marca_justific,
        req_exame_adequacao: form.req_exame_adequacao,
        req_exame_descricao: form.req_exame_descricao,
        req_vistoria: form.req_vistoria,
        req_vistoria_detalhes: form.req_vistoria_detalhes,
        req_subcontratacao: form.req_subcontratacao,
        req_subcontratacao_descricao: form.req_subcontratacao_descricao,
        req_subcontratacao_mep: form.req_subcontratacao_mep,
        req_garantia_proposta: form.req_garantia_proposta,
        req_garantia_contratacao: form.req_garantia_contratacao,
        req_garantia_percentual: form.req_garantia_percentual ? Number(form.req_garantia_percentual) : null,
        req_garantia_modalidade: form.req_garantia_modalidade,
        hab_fiscal_esfera: form.hab_fiscal_esfera,
        ...(isBens ? {
          bens_nao_luxo: form.bens_nao_luxo,
          bens_reserva_cota: form.bens_reserva_cota,
          bens_reserva_cota_percentual: Number(form.bens_reserva_cota_percentual) || 25,
          bens_carta_solidariedade: form.bens_carta_solidariedade,
          bens_validade_pereciveis: form.bens_validade_pereciveis,
          bens_garantia_tecnica_prazo: form.bens_garantia_tecnica_prazo ? Number(form.bens_garantia_tecnica_prazo) : null,
          bens_garantia_tecnica_det: form.bens_garantia_tecnica_det,
        } : {}),
        ...(isServico ? {
          serv_transicao_contratual: form.serv_transicao_contratual,
          serv_transicao_descricao: form.serv_transicao_descricao,
          serv_regime_execucao: form.serv_regime_execucao,
          serv_materiais: form.serv_materiais,
          serv_qualificacao_tecnica: form.serv_qualificacao_tecnica,
          serv_parcelas_relevancia: form.serv_parcelas_relevancia,
        } : {}),
        observacoes: form.observacoes,
      }
      const tr = await createTr(payload)
      navigate(`/analise-tecnica/trs/${tr.id}`)
    } catch (err) {
      const data = err.response?.data || {}
      const mapped = {}
      for (const [k, v] of Object.entries(data)) mapped[k] = Array.isArray(v) ? v.join(' ') : String(v)
      setErrors(mapped)
    } finally { setSaving(false) }
  }

  return (
    <div className="p-6 max-w-3xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      <h1 className="text-xl font-bold text-gray-800 mb-1">Nova Minuta — Termo de Referência</h1>
      <div className="flex items-center gap-3 text-sm text-gray-500 mb-5 flex-wrap">
        <span>ETP: <span className="font-mono font-semibold text-teal-700">{etp.numero_sei}</span></span>
        <span>·</span>
        <span>DFD: <span className="font-mono font-semibold">{etp.dfd_numero_sei}</span></span>
        <span>·</span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
          isBens && isServico ? 'bg-orange-100 text-orange-700' :
          isBens             ? 'bg-blue-100 text-blue-700' :
          isServico          ? 'bg-purple-100 text-purple-700' :
                               'bg-gray-100 text-gray-600'
        }`}>{TIPO_OBJETO_LABEL[form.tipo_objeto] || 'Tipo não definido'}</span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormErrors errors={errors} />

        {/* Seção 1 — Condições Gerais */}
        <Secao titulo="1. Condições Gerais" cor="teal">
          <div className="grid grid-cols-2 gap-4">
            <F label="Tipo de objeto">
              <select value={form.tipo_objeto} onChange={e => set('tipo_objeto', e.target.value)} className={sel()}>
                <option value="">— Selecione —</option>
                <option value="bens">Bens — Aquisição de materiais/equipamentos</option>
                <option value="servicos">Serviços Comuns</option>
                <option value="servicos_engenharia">Serviços de Engenharia</option>
                <option value="hibrido">Híbrido — Bens e Serviços</option>
                <option value="obras">Obras</option>
              </select>
            </F>
            <F label="Esfera de habilitação fiscal">
              <select value={form.hab_fiscal_esfera} onChange={e => set('hab_fiscal_esfera', e.target.value)} className={sel()}>
                {HAB_ESFERA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </F>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Toggle label="Contratação Delegada" checked={form.contratacao_delegada} onChange={() => set('contratacao_delegada', !form.contratacao_delegada)} />
            <Toggle label="Sistema de Registro de Preços (ARP)" checked={form.sistema_registro_precos} onChange={() => set('sistema_registro_precos', !form.sistema_registro_precos)} />
          </div>
        </Secao>

        {/* Seções 2–3 — Objeto e Fundamentação */}
        <Secao titulo="2–3. Objeto, Fundamentação e Solução" cor="teal">
          <F label="Objeto da contratação *" error={errors.objeto_contratacao}>
            <textarea rows={3} value={form.objeto_contratacao} onChange={e => set('objeto_contratacao', e.target.value)}
              placeholder="Descreva o objeto a ser contratado..." className={inp(errors.objeto_contratacao)} />
          </F>
          <F label="Justificativa da contratação" hint="Pré-populada do ETP — pode ser editada">
            <textarea rows={3} value={form.justificativa} onChange={e => set('justificativa', e.target.value)} className={inp()} />
          </F>
          <F label="Requisitos da contratação" hint="Pré-populados do ETP — pode ser editado">
            <textarea rows={3} value={form.requisitos_contratacao} onChange={e => set('requisitos_contratacao', e.target.value)} className={inp()} />
          </F>
        </Secao>

        {/* Seção 4 — Requisitos parametrizáveis */}
        <Secao titulo="4. Requisitos da Contratação" cor="indigo">
          {/* 4.1 Sustentabilidade */}
          <Toggle label="4.1 Exige critérios de sustentabilidade (art. 11, IV)"
            checked={form.req_sustentabilidade} onChange={() => set('req_sustentabilidade', !form.req_sustentabilidade)} />
          {form.req_sustentabilidade && (
            <F label="Critérios de sustentabilidade" hint="Pré-populados do ETP se houver">
              <textarea rows={2} value={form.req_sustentabilidade_criterios} onChange={e => set('req_sustentabilidade_criterios', e.target.value)} className={inp()} />
            </F>
          )}

          {/* 4.2 Marca */}
          <Toggle label="4.2 Indicação de marca ou modelo (requer justificativa técnica, art. 41, I)"
            checked={form.req_indicacao_marca} onChange={() => set('req_indicacao_marca', !form.req_indicacao_marca)} />
          {form.req_indicacao_marca && (
            <F label="Justificativa da indicação de marca">
              <textarea rows={2} value={form.req_indicacao_marca_justific} onChange={e => set('req_indicacao_marca_justific', e.target.value)} className={inp()} />
            </F>
          )}

          {/* 4.3 Exame de adequação */}
          <F label="4.3 Exame de adequação do objeto (art. 17, §3º)">
            <select value={form.req_exame_adequacao} onChange={e => set('req_exame_adequacao', e.target.value)} className={sel()}>
              {EXAME_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </F>
          {form.req_exame_adequacao !== 'nenhum' && (
            <F label="Critérios e aspectos a avaliar">
              <textarea rows={2} value={form.req_exame_descricao} onChange={e => set('req_exame_descricao', e.target.value)} className={inp()} />
            </F>
          )}

          {/* 4.4 Vistoria */}
          <F label="4.4 Vistoria prévia (art. 63, §2º)">
            <select value={form.req_vistoria} onChange={e => set('req_vistoria', e.target.value)} className={sel()}>
              {VISTORIA_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </F>
          {form.req_vistoria !== 'nao' && (
            <F label="Detalhes da vistoria (endereço, horário, responsável)">
              <textarea rows={2} value={form.req_vistoria_detalhes} onChange={e => set('req_vistoria_detalhes', e.target.value)} className={inp()} />
            </F>
          )}

          {/* 4.5 Subcontratação */}
          <F label="4.5 Subcontratação">
            <select value={form.req_subcontratacao} onChange={e => set('req_subcontratacao', e.target.value)} className={sel()}>
              {SUBCONTR_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </F>
          {form.req_subcontratacao === 'parcial' && (
            <>
              <F label="Parcelas permitidas e condições">
                <textarea rows={2} value={form.req_subcontratacao_descricao} onChange={e => set('req_subcontratacao_descricao', e.target.value)} className={inp()} />
              </F>
              <Toggle label="Obrigatório subcontratar ME/EPP (art. 48, II, LC 123/2006)"
                checked={form.req_subcontratacao_mep} onChange={() => set('req_subcontratacao_mep', !form.req_subcontratacao_mep)} />
            </>
          )}

          {/* 4.6 Garantia */}
          <div className="grid grid-cols-2 gap-4">
            <Toggle label="4.6.1 Garantia de proposta (art. 58)"
              checked={form.req_garantia_proposta} onChange={() => set('req_garantia_proposta', !form.req_garantia_proposta)} />
            <Toggle label="4.6.2 Garantia da contratação (art. 96)"
              checked={form.req_garantia_contratacao} onChange={() => set('req_garantia_contratacao', !form.req_garantia_contratacao)} />
          </div>
          {form.req_garantia_contratacao && (
            <div className="grid grid-cols-2 gap-4">
              <F label="Percentual (%) — máx. 5%; até 10% justificado (art. 98)">
                <input type="number" min="1" max="10" step="0.5" value={form.req_garantia_percentual}
                  onChange={e => set('req_garantia_percentual', e.target.value)} className={inp()} placeholder="Ex: 5" />
              </F>
              <F label="Modalidade preferencial">
                <select value={form.req_garantia_modalidade} onChange={e => set('req_garantia_modalidade', e.target.value)} className={sel()}>
                  <option value="">Qualquer modalidade (art. 96, §1º)</option>
                  <option value="caucao_dinheiro">Caução em dinheiro</option>
                  <option value="seguro_garantia">Seguro-garantia</option>
                  <option value="fianca_bancaria">Fiança bancária</option>
                  <option value="titulos">Títulos da dívida pública</option>
                </select>
              </F>
            </div>
          )}
        </Secao>

        {/* Seção BENS — condicional */}
        {isBens && (
          <Secao titulo="Bens — Seção Específica" tag="BENS" cor="blue">
            <Toggle label="Objeto não se enquadra como bem de luxo (art. 20, Lei 14.133/2021)"
              checked={form.bens_nao_luxo} onChange={() => set('bens_nao_luxo', !form.bens_nao_luxo)} />
            <Toggle label="Reserva de cota ME/EPP para bens divisíveis (art. 48, III, LC 123/2006)"
              checked={form.bens_reserva_cota} onChange={() => set('bens_reserva_cota', !form.bens_reserva_cota)}
              hint="Pré-selecionado conforme ETP" />
            {form.bens_reserva_cota && (
              <F label="Percentual da cota (máx. 25%)">
                <input type="number" min="1" max="25" value={form.bens_reserva_cota_percentual}
                  onChange={e => set('bens_reserva_cota_percentual', e.target.value)}
                  className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </F>
            )}
            <Toggle label="Exige carta de solidariedade do fabricante (para licitantes revendedores/distribuidores)"
              checked={form.bens_carta_solidariedade} onChange={() => set('bens_carta_solidariedade', !form.bens_carta_solidariedade)} />
            <F label="Validade mínima de produtos perecíveis (deixe em branco se não se aplica)">
              <input value={form.bens_validade_pereciveis} onChange={e => set('bens_validade_pereciveis', e.target.value)}
                placeholder="Ex: mínimo de 12 meses a contar da entrega" className={inp()} />
            </F>
            <div className="grid grid-cols-2 gap-4">
              <F label="Prazo de garantia técnica (meses)">
                <input type="number" min="1" value={form.bens_garantia_tecnica_prazo}
                  onChange={e => set('bens_garantia_tecnica_prazo', e.target.value)}
                  placeholder="Ex: 12" className={inp()} />
              </F>
              <F label="Detalhes da garantia e assistência técnica">
                <textarea rows={2} value={form.bens_garantia_tecnica_det}
                  onChange={e => set('bens_garantia_tecnica_det', e.target.value)} className={inp()} />
              </F>
            </div>
          </Secao>
        )}

        {/* Seção SERVIÇOS — condicional */}
        {isServico && (
          <Secao titulo="Serviços — Seção Específica" tag="SERVIÇOS" cor="purple">
            <Toggle label="Exige transição contratual com transferência de conhecimento e tecnologia"
              checked={form.serv_transicao_contratual} onChange={() => set('serv_transicao_contratual', !form.serv_transicao_contratual)} />
            {form.serv_transicao_contratual && (
              <F label="Descrição da transição contratual">
                <textarea rows={2} value={form.serv_transicao_descricao} onChange={e => set('serv_transicao_descricao', e.target.value)} className={inp()} />
              </F>
            )}
            <F label="Regime de execução" hint="Cronograma, horário, frequência e forma de realização dos serviços">
              <textarea rows={3} value={form.serv_regime_execucao} onChange={e => set('serv_regime_execucao', e.target.value)} className={inp()} />
            </F>
            <F label="Materiais e equipamentos a disponibilizar pela contratada">
              <textarea rows={2} value={form.serv_materiais} onChange={e => set('serv_materiais', e.target.value)} className={inp()} />
            </F>
            <F label="Qualificação técnica exigida" hint="Pré-populada dos requisitos do ETP">
              <textarea rows={3} value={form.serv_qualificacao_tecnica} onChange={e => set('serv_qualificacao_tecnica', e.target.value)} className={inp()} />
            </F>
            <F label="Parcelas de maior relevância ou valor significativo">
              <textarea rows={2} value={form.serv_parcelas_relevancia} onChange={e => set('serv_parcelas_relevancia', e.target.value)}
                placeholder="Ex: Instalação e configuração inicial — mínimo 30% do valor total" className={inp()} />
            </F>
          </Secao>
        )}

        {/* Seção 5 — Prazo e execução */}
        <Secao titulo={isServico ? '5. Regime de Execução e Prazo de Vigência' : '5. Forma de Entrega e Prazo de Vigência'} cor="teal">
          <F label="Forma de execução do contrato">
            <select value={form.tipo_prazo_vigencia}
              onChange={e => { set('tipo_prazo_vigencia', e.target.value); set('prazo_observacao', gerarRedacao(e.target.value, form.prazo_meses, form.instrumento_inicio)) }}
              className={sel()}>
              {TIPO_PRAZO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </F>
          {precisaMeses && (
            <F label={`Prazo em meses ${tipo === 'continuo' ? '(máx. 60)' : tipo === 'emergencial' ? '(máx. 12)' : '(máx. 120)'}`}>
              <input type="number" min="1" max={tipo === 'continuo' ? 60 : tipo === 'emergencial' ? 12 : 120}
                value={form.prazo_meses}
                onChange={e => { set('prazo_meses', e.target.value); set('prazo_observacao', gerarRedacao(tipo, e.target.value, form.instrumento_inicio)) }}
                className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            </F>
          )}
          {['escopo','continuo','direta_108'].includes(tipo) && (
            <F label="Instrumento de início da vigência">
              <select value={form.instrumento_inicio}
                onChange={e => { set('instrumento_inicio', e.target.value); set('prazo_observacao', gerarRedacao(tipo, form.prazo_meses, e.target.value)) }}
                className={sel()}>
                {INSTRUMENTO_OPTS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </F>
          )}
          {form.prazo_observacao && (
            <div className="bg-teal-50 border border-teal-200 rounded-lg p-3">
              <p className="text-xs font-semibold text-teal-700 mb-1">Redação gerada (Lei 14.133/2021):</p>
              <p className="text-xs text-teal-800 leading-relaxed">{form.prazo_observacao}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <F label="Estimativa de valor (R$)">
              <input type="number" min="0" step="0.01" value={form.estimativa_valor}
                onChange={e => set('estimativa_valor', e.target.value)} className={inp()} />
            </F>
            <F label={isServico ? 'Local de execução' : 'Local de entrega'}>
              <input value={form.local_entrega} onChange={e => set('local_entrega', e.target.value)} className={inp()} />
            </F>
          </div>
          <F label="Garantia contratual">
            <textarea rows={2} value={form.garantia_contrato} onChange={e => set('garantia_contrato', e.target.value)} className={inp()} />
          </F>
        </Secao>

        {/* Seção 6 — Obrigações e Critérios */}
        <Secao titulo="6. Obrigações e Critérios" cor="teal">
          <div className="grid grid-cols-2 gap-4">
            <F label="Obrigações da contratada">
              <textarea rows={4} value={form.obrigacoes_contratada} onChange={e => set('obrigacoes_contratada', e.target.value)} className={inp()} />
            </F>
            <F label="Obrigações da contratante">
              <textarea rows={4} value={form.obrigacoes_contratante} onChange={e => set('obrigacoes_contratante', e.target.value)} className={inp()} />
            </F>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <F label="Critérios de seleção do fornecedor">
              <textarea rows={2} value={form.criterios_selecao} onChange={e => set('criterios_selecao', e.target.value)} className={inp()} />
            </F>
            <F label={isServico ? 'Critérios de medição / pagamento por resultados' : 'Critérios de medição e pagamento'}>
              <textarea rows={2} value={form.criterios_medicao} onChange={e => set('criterios_medicao', e.target.value)} className={inp()} />
            </F>
          </div>
          <F label="Observações gerais">
            <textarea rows={2} value={form.observacoes} onChange={e => set('observacoes', e.target.value)} className={inp()} />
          </F>
        </Secao>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={saving}
            className="bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm">
            {saving ? 'Criando...' : 'Criar Minuta TR'}
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
