import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import usePlanoAplicacaoStore from '../stores/planoAplicacaoStore'
import useAuthStore from '../stores/authStore'
import api, { downloadFile } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import CampoMoeda from '../components/CampoMoeda'
import { STATUS_PLANO_CLS, NATUREZA_PLANO_CLS } from './FespPlanoList'
import { formatarMoeda } from '../utils/currencyMask'

const TABS_BASE = ['Dados Gerais', 'Metas Específicas', 'Conselho Gestor', 'Execução Financeira']

// Extrai uma mensagem legível de um erro de API do DRF — seja {"detail": "..."}
// ou {"campo": ["msg1", "msg2"]}. Usado para nunca deixar um botão "morrer" em
// silêncio quando o backend rejeita a operação.
function extrairErro(err, padrao = 'Erro ao executar operação.') {
  const data = err?.response?.data
  if (!data) return padrao
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  const partes = Object.entries(data).map(([campo, msgs]) => {
    const texto = Array.isArray(msgs) ? msgs.join(' ') : String(msgs)
    return `${campo}: ${texto}`
  })
  return partes.length ? partes.join(' | ') : padrao
}

export default function FespPlanoDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const papel = useAuthStore((s) => s.papel)

  const {
    current, loading, error,
    fetchPlano, updatePlano, deletePlano,
    submeterConselho, aprovarConselho, devolver, reabrir, homologar, aprovar, publicar, encerrar, cancelar,
  } = usePlanoAplicacaoStore()

  const [tab, setTab] = useState('Dados Gerais')
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)
  const [actionMsg, setActionMsg] = useState(null)
  const [modal, setModal] = useState(null) // 'aprovar' | 'devolver' | 'homologar' | 'cancelar' | 'encerrar'

  useEffect(() => { fetchPlano(id); setTab('Dados Gerais') }, [id])

  useEffect(() => {
    if (current) {
      setForm({
        ementa: current.ementa,
        descricao: current.descricao || '',
        declaracao_nao_pessoal: current.declaracao_nao_pessoal,
        declaracao_nao_unidade_administrativa: current.declaracao_nao_unidade_administrativa,
        declaracao_sem_contingenciamento: current.declaracao_sem_contingenciamento,
        responsavel_gestao_nome: current.responsavel_gestao_nome || '',
        responsavel_gestao_email: current.responsavel_gestao_email || '',
        responsavel_gestao_cargo: current.responsavel_gestao_cargo || '',
        responsavel_gestao_telefone: current.responsavel_gestao_telefone || '',
        responsavel_elaboracao_nome: current.responsavel_elaboracao_nome || '',
        responsavel_elaboracao_email: current.responsavel_elaboracao_email || '',
        responsavel_elaboracao_cargo: current.responsavel_elaboracao_cargo || '',
        responsavel_elaboracao_telefone: current.responsavel_elaboracao_telefone || '',
        diagnostico: current.diagnostico || '',
        meta_geral: current.meta_geral || '',
        justificativa: current.justificativa || '',
        valor_originario_investimento: current.valor_originario_investimento,
        valor_originario_custeio: current.valor_originario_custeio,
        valor_suplementar_investimento: current.valor_suplementar_investimento,
        valor_suplementar_custeio: current.valor_suplementar_custeio,
        valor_rendimento_investimento: current.valor_rendimento_investimento,
        valor_rendimento_custeio: current.valor_rendimento_custeio,
      })
    }
  }, [current])

  const set = (field, value) => setForm((p) => ({ ...p, [field]: value }))

  const handleSave = async () => {
    setSaving(true)
    setActionMsg(null)
    try {
      await updatePlano(id, {
        ...form,
        valor_originario_investimento: Number(form.valor_originario_investimento || 0),
        valor_originario_custeio: Number(form.valor_originario_custeio || 0),
        valor_suplementar_investimento: Number(form.valor_suplementar_investimento || 0),
        valor_suplementar_custeio: Number(form.valor_suplementar_custeio || 0),
        valor_rendimento_investimento: Number(form.valor_rendimento_investimento || 0),
        valor_rendimento_custeio: Number(form.valor_rendimento_custeio || 0),
      })
      setEditing(false)
    } catch (err) {
      setActionMsg({ type: 'error', text: extrairErro(err, 'Erro ao salvar o plano.') })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Excluir este plano de aplicação? Esta ação não pode ser desfeita.')) return
    setSaving(true)
    setActionMsg(null)
    try {
      await deletePlano(id)
      navigate('/fesp/planos')
    } catch (err) {
      setActionMsg({ type: 'error', text: extrairErro(err, 'Erro ao excluir o plano.') })
      setSaving(false)
    }
  }

  const act = async (fn, ...args) => {
    setSaving(true)
    setActionMsg(null)
    try {
      await fn(...args)
      setActionMsg({ type: 'success', text: 'Operação realizada com sucesso.' })
      setModal(null)
    } catch (err) {
      const data = err.response?.data
      const bloqueadores = data?.bloqueadores
      const msg = bloqueadores?.length ? `${data.detail} ${bloqueadores.join(' ')}` : (data?.detail || 'Erro ao executar operação.')
      setActionMsg({ type: 'error', text: msg })
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-8"><LoadingSpinner message="Carregando plano de aplicação..." /></div>
  if (error) return <div className="p-8 text-sm text-red-600 bg-red-50 rounded-lg m-8">{error}</div>
  if (!current || !form) return null

  const s = current.status
  const usaRitoConselho = current.natureza === 'fesp'
  const podeHomologar = usaRitoConselho && s === 'aprovado_conselho' && ['admin', 'ordenador'].includes(papel)
  const checklist = current.checklist
  const tabs = usaRitoConselho ? TABS_BASE : TABS_BASE.filter((t) => t !== 'Conselho Gestor')

  return (
    <div className="p-6 lg:p-8 max-w-4xl">
      <button onClick={() => navigate(-1)} className="text-sm text-gray-400 hover:text-gray-600 mb-4">← Voltar</button>

      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-800 font-mono">{current.numero}</h1>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${NATUREZA_PLANO_CLS[current.natureza] || ''}`}>
              {current.natureza_display}
            </span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_PLANO_CLS[s] || ''}`}>
              {current.status_display}
            </span>
          </div>
          <p className="text-sm text-gray-500 mt-1">{current.ementa} — Exercício {current.exercicio_fiscal}</p>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          <Link to={`/fesp/planos/${id}/consolidacao`}
            className="border border-yellow-300 text-yellow-700 hover:bg-yellow-50 text-sm px-4 py-1.5 rounded-lg">
            Consolidação de Itens
          </Link>
          <button
            onClick={() => downloadFile(`/fesp/plano-aplicacao/${id}/export/pdf/`, `PlanoAplicacao_${current.numero}.pdf`)}
            className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
            Baixar PDF
          </button>
          {s === 'elaboracao' && !editing && (
            <button onClick={() => setEditing(true)} className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
              Editar
            </button>
          )}
          {usaRitoConselho && s === 'elaboracao' && (
            <button onClick={() => act(submeterConselho, id)} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Submeter ao Conselho
            </button>
          )}
          {!usaRitoConselho && s === 'elaboracao' && (
            <button onClick={() => act(aprovar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Aprovar
            </button>
          )}
          {usaRitoConselho && s === 'submetido_conselho' && (
            <>
              <button onClick={() => setModal('aprovar')} className="bg-green-600 hover:bg-green-700 text-white text-sm px-4 py-1.5 rounded-lg">
                Aprovar (Conselho)
              </button>
              <button onClick={() => setModal('devolver')} className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
                Devolver
              </button>
            </>
          )}
          {usaRitoConselho && s === 'aprovado_conselho' && (
            <button onClick={() => setModal('devolver')} className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Devolver
            </button>
          )}
          {usaRitoConselho && s === 'devolvido' && (
            <button onClick={() => act(reabrir, id)} disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Reabrir para Ajustes
            </button>
          )}
          {podeHomologar && (
            <button onClick={() => setModal('homologar')} className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-1.5 rounded-lg">
              Registrar Homologação
            </button>
          )}
          {(s === 'homologado' || s === 'aprovado') && (
            <button onClick={() => act(publicar, id)} disabled={saving}
              className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
              Publicar
            </button>
          )}
          {s === 'publicado' && (
            <button onClick={() => act(encerrar, id)} disabled={saving}
              className="border border-purple-300 text-purple-600 hover:bg-purple-50 text-sm px-4 py-1.5 rounded-lg">
              Encerrar
            </button>
          )}
          {['elaboracao'].includes(s) && (
            <button onClick={() => setModal('cancelar')} className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Cancelar
            </button>
          )}
          {s === 'elaboracao' && (
            <button onClick={handleDelete} className="border border-red-300 text-red-500 hover:bg-red-50 text-sm px-4 py-1.5 rounded-lg">
              Excluir
            </button>
          )}
        </div>
      </div>

      {actionMsg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm ${actionMsg.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {actionMsg.text}
        </div>
      )}

      {checklist && s === 'elaboracao' && (
        <div className={`mb-5 rounded-lg border px-4 py-3 text-sm ${checklist.pode_submeter ? 'bg-green-50 border-green-200 text-green-700' : 'bg-amber-50 border-amber-200 text-amber-800'}`}>
          <p className="font-medium mb-1">
            Completude: {checklist.score}/{checklist.total} ({checklist.percentual}%)
            {checklist.pode_submeter ? ' — pronto para submissão' : ' — pendências para submeter ao Conselho'}
          </p>
          {checklist.bloqueadores.length > 0 && (
            <ul className="list-disc list-inside space-y-0.5">
              {checklist.bloqueadores.map((b) => <li key={b.campo}>{b.descricao}: {b.detalhe}</li>)}
            </ul>
          )}
        </div>
      )}

      {modal === 'devolver' && <MotivoModal titulo="Devolver ao Elaborador" onConfirm={(m) => act(devolver, id, m)} onClose={() => setModal(null)} saving={saving} />}
      {modal === 'cancelar' && <MotivoModal titulo="Cancelar Plano" onConfirm={(m) => act(cancelar, id, m)} onClose={() => setModal(null)} saving={saving} />}
      {modal === 'aprovar' && <AprovarConselhoModal onConfirm={(payload) => act(aprovarConselho, id, payload)} onClose={() => setModal(null)} saving={saving} />}
      {modal === 'homologar' && <HomologarModal onConfirm={(payload) => act(homologar, id, payload)} onClose={() => setModal(null)} saving={saving} />}

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-5">
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t ? 'border-yellow-600 text-yellow-700' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 'Dados Gerais' && (
        <DadosGeraisTab current={current} form={form} set={set} editing={editing} saving={saving} onSave={handleSave} onCancelEdit={() => setEditing(false)} />
      )}
      {tab === 'Metas Específicas' && <MetasTab plano={current} />}
      {tab === 'Conselho Gestor' && <ConselhoTab plano={current} />}
      {tab === 'Execução Financeira' && <ExecucaoTab planoId={id} />}
    </div>
  )
}

// ─── Aba: Dados Gerais ──────────────────────────────────────────────────────
function DadosGeraisTab({ current, form, set, editing, saving, onSave, onCancelEdit }) {
  return (
    <div className="space-y-6">
      <Section title="Identificação">
        <Field label="Ementa/Eixo">
          {editing ? <input type="text" value={form.ementa} onChange={(e) => set('ementa', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-700">{current.ementa}</p>}
        </Field>
        <Field label="Descrição">
          {editing ? <textarea rows={2} value={form.descricao} onChange={(e) => set('descricao', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500">{current.descricao || '—'}</p>}
        </Field>
      </Section>

      {current.natureza === 'fesp' && (
        <Section title="Vedações Legais (Lei 14.169/2019, art. 4º, §1º)" subtitle="Atestação de quem elabora o plano — o sistema exige que a pergunta tenha sido respondida, não arbitra o mérito da resposta.">
          <DeclaracaoField label="Nenhum item se destina a folha de pessoal/encargos" field="declaracao_nao_pessoal" form={form} set={set} editing={editing} valor={current.declaracao_nao_pessoal} />
          <DeclaracaoField label="Nenhum item beneficia unidade puramente administrativa" field="declaracao_nao_unidade_administrativa" form={form} set={set} editing={editing} valor={current.declaracao_nao_unidade_administrativa} />
          <DeclaracaoField label="Ciência de que os recursos não estão sujeitos a contingenciamento" field="declaracao_sem_contingenciamento" form={form} set={set} editing={editing} valor={current.declaracao_sem_contingenciamento} />
        </Section>
      )}

      <Section title="Decomposição Financeira (R$)">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase">
                <th className="text-left py-1">Origem</th>
                <th className="text-right py-1">Investimento</th>
                <th className="text-right py-1">Custeio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              <ValorLinha label="Originário" campoInv="valor_originario_investimento" campoCus="valor_originario_custeio" form={form} set={set} editing={editing} current={current} />
              <ValorLinha label="Suplementar" campoInv="valor_suplementar_investimento" campoCus="valor_suplementar_custeio" form={form} set={set} editing={editing} current={current} />
              <ValorLinha label="Rendimento" campoInv="valor_rendimento_investimento" campoCus="valor_rendimento_custeio" form={form} set={set} editing={editing} current={current} />
              <tr>
                <td className="py-2 text-gray-500">Planejado (alocado a itens)</td>
                <td className="py-2 text-right font-semibold text-gray-700">{formatarMoeda(current.valor_planejado_investimento)}</td>
                <td className="py-2 text-right font-semibold text-gray-700">{formatarMoeda(current.valor_planejado_custeio)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <Section title="Responsáveis">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Gestão do Fundo</p>
            <ResponsavelFields prefix="responsavel_gestao" form={form} set={set} editing={editing} current={current} />
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Elaboração</p>
            <ResponsavelFields prefix="responsavel_elaboracao" form={form} set={set} editing={editing} current={current} />
          </div>
        </div>
      </Section>

      <Section title="Narrativa">
        <Field label="Diagnóstico">
          {editing ? <textarea rows={3} value={form.diagnostico} onChange={(e) => set('diagnostico', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500 whitespace-pre-wrap">{current.diagnostico || '—'}</p>}
        </Field>
        <Field label="Meta Geral">
          {editing ? <textarea rows={2} value={form.meta_geral} onChange={(e) => set('meta_geral', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500 whitespace-pre-wrap">{current.meta_geral || '—'}</p>}
        </Field>
        <Field label="Justificativa">
          {editing ? <textarea rows={3} value={form.justificativa} onChange={(e) => set('justificativa', e.target.value)} className={inp()} />
            : <p className="text-sm text-gray-500 whitespace-pre-wrap">{current.justificativa || '—'}</p>}
        </Field>
      </Section>

      {current.numero_ato && (
        <Section title="Ato de Homologação">
          <p className="text-sm text-gray-700">Nº {current.numero_ato} {current.data_ato && `— ${new Date(current.data_ato + 'T00:00').toLocaleDateString('pt-BR')}`}</p>
        </Section>
      )}

      {editing && (
        <div className="flex gap-2">
          <button onClick={onSave} disabled={saving}
            className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
          <button onClick={onCancelEdit} className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
            Cancelar edição
          </button>
        </div>
      )}
    </div>
  )
}

function ValorLinha({ label, campoInv, campoCus, form, set, editing, current }) {
  return (
    <tr>
      <td className="py-2 text-gray-500">{label}</td>
      <td className="py-2 text-right">
        {editing ? <CampoMoeda value={form[campoInv]} onChange={(v) => set(campoInv, v)} className="w-32 border border-gray-300 rounded-lg px-2 py-1 text-sm text-right ml-auto" />
          : formatarMoeda(current[campoInv])}
      </td>
      <td className="py-2 text-right">
        {editing ? <CampoMoeda value={form[campoCus]} onChange={(v) => set(campoCus, v)} className="w-32 border border-gray-300 rounded-lg px-2 py-1 text-sm text-right ml-auto" />
          : formatarMoeda(current[campoCus])}
      </td>
    </tr>
  )
}

function ResponsavelFields({ prefix, form, set, editing, current }) {
  const campos = [
    ['nome', 'Nome'], ['cargo', 'Cargo'], ['email', 'E-mail'], ['telefone', 'Telefone'],
  ]
  return (
    <div className="space-y-2">
      {campos.map(([suf, label]) => {
        const campo = `${prefix}_${suf}`
        return (
          <Field key={campo} label={label}>
            {editing ? <input type="text" value={form[campo]} onChange={(e) => set(campo, e.target.value)} className={inp()} />
              : <p className="text-sm text-gray-500">{current[campo] || '—'}</p>}
          </Field>
        )
      })}
    </div>
  )
}

function DeclaracaoField({ label, field, form, set, editing, valor }) {
  const display = valor === true ? 'Sim' : valor === false ? 'Não' : 'Não respondido'
  const cls = valor === true ? 'text-green-700' : valor === false ? 'text-gray-600' : 'text-amber-600'
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
      <p className="text-sm text-gray-700 flex-1">{label}</p>
      {editing ? (
        <select value={form[field] === null || form[field] === undefined ? '' : String(form[field])}
          onChange={(e) => set(field, e.target.value === '' ? null : e.target.value === 'true')}
          className="border border-gray-300 rounded-lg px-2 py-1 text-sm">
          <option value="">Não respondido</option>
          <option value="true">Sim</option>
          <option value="false">Não</option>
        </select>
      ) : <span className={`text-sm font-medium ${cls}`}>{display}</span>}
    </div>
  )
}

// ─── Aba: Metas Específicas + Itens ─────────────────────────────────────────
function MetasTab({ plano }) {
  const { createMeta, deleteMeta } = usePlanoAplicacaoStore()
  const [showNovaMeta, setShowNovaMeta] = useState(false)
  const [novaMeta, setNovaMeta] = useState({ titulo: '', descricao_meta: '' })
  const [erro, setErro] = useState(null)
  const [salvando, setSalvando] = useState(false)
  const editavel = plano.status === 'elaboracao'

  const handleCriarMeta = async () => {
    if (!novaMeta.titulo.trim()) {
      setErro('Informe o título da meta.')
      return
    }
    setSalvando(true)
    setErro(null)
    try {
      await createMeta({ plano: plano.id, titulo: novaMeta.titulo, descricao_meta: novaMeta.descricao_meta })
      setNovaMeta({ titulo: '', descricao_meta: '' })
      setShowNovaMeta(false)
    } catch (err) {
      setErro(extrairErro(err, 'Erro ao criar a Meta Específica.'))
    } finally {
      setSalvando(false)
    }
  }

  const handleExcluirMeta = async (meta) => {
    if (!confirm(`Excluir a meta "${meta.titulo}" e seus itens?`)) return
    try {
      await deleteMeta(meta.id, plano.id)
    } catch (err) {
      alert(extrairErro(err, 'Erro ao excluir a Meta Específica.'))
    }
  }

  return (
    <div className="space-y-5">
      {(plano.metas_especificas || []).map((meta) => (
        <MetaCard key={meta.id} meta={meta} plano={plano} editavel={editavel}
          onDelete={() => handleExcluirMeta(meta)} />
      ))}

      {(plano.metas_especificas || []).length === 0 && (
        <p className="text-sm text-gray-400">Nenhuma Meta Específica cadastrada.</p>
      )}

      {editavel && (
        showNovaMeta ? (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 space-y-2">
            {erro && <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{erro}</p>}
            <input type="text" placeholder="Título da meta *" value={novaMeta.titulo}
              onChange={(e) => setNovaMeta((p) => ({ ...p, titulo: e.target.value }))}
              className={`w-full border rounded-lg px-3 py-2 text-sm ${erro && !novaMeta.titulo.trim() ? 'border-red-400' : 'border-gray-300'}`} />
            <textarea rows={2} placeholder="Descrição (opcional)" value={novaMeta.descricao_meta}
              onChange={(e) => setNovaMeta((p) => ({ ...p, descricao_meta: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            <div className="flex gap-2">
              <button onClick={handleCriarMeta} disabled={salvando}
                className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
                {salvando ? 'Salvando...' : 'Adicionar Meta'}
              </button>
              <button onClick={() => { setShowNovaMeta(false); setErro(null) }} className="border border-gray-300 text-gray-600 text-sm px-4 py-1.5 rounded-lg">Cancelar</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setShowNovaMeta(true)}
            className="text-sm text-yellow-700 hover:text-yellow-900 font-medium border border-yellow-200 hover:border-yellow-400 px-3 py-1.5 rounded-lg">
            + Nova Meta Específica
          </button>
        )
      )}
    </div>
  )
}

function MetaCard({ meta, plano, editavel, onDelete }) {
  const [showItens, setShowItens] = useState(true)

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-100">
        <button onClick={() => setShowItens((v) => !v)} className="flex items-center gap-2 text-left flex-1">
          <span className="text-xs font-bold text-gray-400">ME {meta.numero}</span>
          <span className="text-sm font-semibold text-gray-800">{meta.titulo}</span>
        </button>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-600">{formatarMoeda(meta.valor_total)}</span>
          {editavel && (
            <button onClick={onDelete} className="text-xs text-red-500 hover:text-red-700">Excluir</button>
          )}
        </div>
      </div>
      {showItens && (
        <div className="p-4">
          {meta.descricao_meta && <p className="text-sm text-gray-500 mb-3">{meta.descricao_meta}</p>}
          <ItensDaMeta meta={meta} plano={plano} editavel={editavel} />
        </div>
      )}
    </div>
  )
}

const NATUREZA_OPTIONS = [
  { value: 'custeio', label: 'Custeio' },
  { value: 'investimento', label: 'Investimento' },
]

function ItensDaMeta({ meta, plano, editavel }) {
  const { createItem, deleteItem, gerarNecessidadeIndividual, fetchPlano } = usePlanoAplicacaoStore()
  const [showNovo, setShowNovo] = useState(false)
  const vazio = { org_beneficiaria: '', instrumento: '', bem_servico: '', codigo_senasp: '', natureza: 'investimento', unidade_medida: '', quantidade: '', valor_unitario_estimado: '', destinacao: '' }
  const [novo, setNovo] = useState(vazio)
  const [orgaos, setOrgaos] = useState([])
  const [instrumentos, setInstrumentos] = useState([])
  const [carregandoOpcoes, setCarregandoOpcoes] = useState(false)
  const [camposInvalidos, setCamposInvalidos] = useState({})
  const [erro, setErro] = useState(null)
  const [salvando, setSalvando] = useState(false)
  const [linhaOcupada, setLinhaOcupada] = useState(null) // id do item com ação em andamento

  useEffect(() => {
    if (showNovo) {
      setCarregandoOpcoes(true)
      Promise.all([
        api.get('/core/orgaos/', { params: { page_size: 50 } }),
        api.get('/fesp/instrumento/', { params: { status: 'vigente', page_size: 50 } }),
      ]).then(([orgResp, instResp]) => {
        setOrgaos(orgResp.data.results ?? orgResp.data)
        setInstrumentos(instResp.data.results ?? instResp.data)
      }).catch((err) => {
        setErro(extrairErro(err, 'Erro ao carregar órgãos/instrumentos.'))
      }).finally(() => setCarregandoOpcoes(false))
    }
  }, [showNovo])

  const itens = meta.itens || []

  const validar = () => {
    const inv = {}
    if (!novo.instrumento) inv.instrumento = true
    if (!novo.org_beneficiaria) inv.org_beneficiaria = true
    if (!novo.bem_servico.trim()) inv.bem_servico = true
    if (!novo.unidade_medida.trim()) inv.unidade_medida = true
    if (!novo.quantidade || Number(novo.quantidade) <= 0) inv.quantidade = true
    if (!novo.valor_unitario_estimado || Number(novo.valor_unitario_estimado) <= 0) inv.valor_unitario_estimado = true
    return inv
  }

  const handleCriar = async () => {
    const inv = validar()
    setCamposInvalidos(inv)
    if (Object.keys(inv).length > 0) {
      setErro('Preencha os campos obrigatórios destacados abaixo.')
      return
    }
    setSalvando(true)
    setErro(null)
    try {
      await createItem({
        meta_especifica: meta.id,
        instrumento: Number(novo.instrumento),
        org_beneficiaria: Number(novo.org_beneficiaria),
        bem_servico: novo.bem_servico,
        codigo_senasp: novo.codigo_senasp,
        destinacao: novo.destinacao,
        natureza: novo.natureza,
        unidade_medida: novo.unidade_medida,
        quantidade: Number(novo.quantidade),
        valor_unitario_estimado: Number(novo.valor_unitario_estimado),
      }, plano.id)
      setNovo(vazio)
      setCamposInvalidos({})
      setShowNovo(false)
    } catch (err) {
      setErro(extrairErro(err, 'Erro ao adicionar o item.'))
    } finally {
      setSalvando(false)
    }
  }

  const handleGerarNecessidade = async (itemId) => {
    setLinhaOcupada(itemId)
    setErro(null)
    try {
      await gerarNecessidadeIndividual(itemId)
      await fetchPlano(plano.id)
    } catch (err) {
      setErro(extrairErro(err, 'Erro ao gerar necessidade a partir deste item.'))
    } finally {
      setLinhaOcupada(null)
    }
  }

  const handleExcluirItem = async (item) => {
    if (!confirm(`Excluir o item "${item.bem_servico}"?`)) return
    setLinhaOcupada(item.id)
    setErro(null)
    try {
      await deleteItem(item.id, plano.id)
    } catch (err) {
      setErro(extrairErro(err, 'Erro ao excluir o item.'))
    } finally {
      setLinhaOcupada(null)
    }
  }

  const campoCls = (campo) =>
    `border rounded-lg px-2 py-1.5 text-xs ${camposInvalidos[campo] ? 'border-red-400 bg-red-50' : 'border-gray-300'}`

  return (
    <div>
      {erro && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-2">{erro}</p>
      )}

      {itens.length > 0 && (
        <div className="overflow-x-auto mb-3">
          <table className="w-full text-xs">
            <thead className="text-gray-400 uppercase">
              <tr>
                <th className="text-left py-1 pr-2">Bem/Serviço</th>
                <th className="text-left py-1 pr-2">Instituição</th>
                <th className="text-left py-1 pr-2">Natureza</th>
                <th className="text-right py-1 pr-2">Qtd</th>
                <th className="text-right py-1 pr-2">Valor Total</th>
                <th className="text-left py-1 pr-2">Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {itens.map((item) => (
                <tr key={item.id}>
                  <td className="py-1.5 pr-2 text-gray-700">{item.bem_servico}</td>
                  <td className="py-1.5 pr-2 text-gray-500">{item.org_beneficiaria_sigla}</td>
                  <td className="py-1.5 pr-2 text-gray-500">{item.natureza_display}</td>
                  <td className="py-1.5 pr-2 text-right text-gray-500">{item.quantidade}</td>
                  <td className="py-1.5 pr-2 text-right text-gray-700 font-medium">{formatarMoeda(item.valor_total_estimado)}</td>
                  <td className="py-1.5 pr-2 text-gray-500">{item.status_display}</td>
                  <td className="py-1.5 text-right space-x-2 whitespace-nowrap">
                    {item.status === 'pendente' && (
                      <button onClick={() => handleGerarNecessidade(item.id)} disabled={linhaOcupada === item.id}
                        className="text-blue-600 hover:text-blue-800 disabled:opacity-50">
                        {linhaOcupada === item.id ? '...' : 'Gerar Necessidade'}
                      </button>
                    )}
                    {editavel && (
                      <button onClick={() => handleExcluirItem(item)} disabled={linhaOcupada === item.id}
                        className="text-red-500 hover:text-red-700 disabled:opacity-50">
                        {linhaOcupada === item.id ? '...' : 'Excluir'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editavel && (
        showNovo ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-2">
            {carregandoOpcoes && <p className="text-xs text-gray-400">Carregando órgãos e instrumentos...</p>}
            {!carregandoOpcoes && instrumentos.length === 0 && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1.5">
                Nenhum instrumento financeiro <strong>vigente</strong> encontrado. Ative um instrumento antes de adicionar itens.
              </p>
            )}
            <div className="grid grid-cols-2 gap-2">
              <select value={novo.instrumento} onChange={(e) => setNovo((p) => ({ ...p, instrumento: e.target.value }))} className={campoCls('instrumento')}>
                <option value="">Instrumento financeiro... *</option>
                {instrumentos.map((i) => <option key={i.id} value={i.id}>{i.numero_instrumento}</option>)}
              </select>
              <select value={novo.org_beneficiaria} onChange={(e) => setNovo((p) => ({ ...p, org_beneficiaria: e.target.value }))} className={campoCls('org_beneficiaria')}>
                <option value="">Instituição beneficiária... *</option>
                {orgaos.map((o) => <option key={o.id} value={o.id}>{o.sigla} — {o.nome}</option>)}
              </select>
            </div>
            <input type="text" placeholder="Bem/Serviço *" value={novo.bem_servico}
              onChange={(e) => setNovo((p) => ({ ...p, bem_servico: e.target.value }))}
              className={`w-full ${campoCls('bem_servico')}`} />
            <div className="grid grid-cols-2 gap-2">
              <input type="text" placeholder="Cód. SENASP (opcional)" value={novo.codigo_senasp}
                onChange={(e) => setNovo((p) => ({ ...p, codigo_senasp: e.target.value }))}
                className={campoCls('codigo_senasp')} />
              <select value={novo.natureza} onChange={(e) => setNovo((p) => ({ ...p, natureza: e.target.value }))} className={campoCls('natureza')}>
                {NATUREZA_OPTIONS.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
              </select>
            </div>
            <input type="text" placeholder="Destinação — unidade(s) específica(s) (opcional)" value={novo.destinacao}
              onChange={(e) => setNovo((p) => ({ ...p, destinacao: e.target.value }))}
              className={`w-full ${campoCls('destinacao')}`} />
            <div className="grid grid-cols-3 gap-2">
              <input type="text" placeholder="Unidade de medida *" value={novo.unidade_medida}
                onChange={(e) => setNovo((p) => ({ ...p, unidade_medida: e.target.value }))}
                className={campoCls('unidade_medida')} />
              <input type="number" min="0.01" step="0.01" placeholder="Quantidade *" value={novo.quantidade}
                onChange={(e) => setNovo((p) => ({ ...p, quantidade: e.target.value }))}
                className={campoCls('quantidade')} />
              <CampoMoeda value={novo.valor_unitario_estimado}
                onChange={(v) => setNovo((p) => ({ ...p, valor_unitario_estimado: v }))}
                className={campoCls('valor_unitario_estimado')} placeholder="Valor unitário *" />
            </div>
            <div className="flex gap-2">
              <button onClick={handleCriar} disabled={salvando}
                className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-xs px-3 py-1.5 rounded-lg">
                {salvando ? 'Salvando...' : 'Adicionar Item'}
              </button>
              <button onClick={() => { setShowNovo(false); setErro(null); setCamposInvalidos({}) }} className="border border-gray-300 text-gray-600 text-xs px-3 py-1.5 rounded-lg">Cancelar</button>
            </div>
          </div>
        ) : (
          <button onClick={() => setShowNovo(true)} className="text-xs text-yellow-700 hover:text-yellow-900 font-medium">+ Adicionar item</button>
        )
      )}
    </div>
  )
}

// ─── Aba: Conselho Gestor ────────────────────────────────────────────────────
function ConselhoTab({ plano }) {
  return (
    <div className="space-y-5">
      {plano.motivo_devolucao_conselho && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <p className="text-sm font-medium text-red-800">Motivo da última devolução</p>
          <p className="text-sm text-red-700 mt-0.5">{plano.motivo_devolucao_conselho}</p>
        </div>
      )}

      {plano.reuniao_aprovacao_detail && (
        <Section title="Reunião de Aprovação">
          <p className="text-sm text-gray-700">Ata nº {plano.reuniao_aprovacao_detail.numero_ata} — {plano.reuniao_aprovacao_detail.tipo === 'ordinaria' ? 'Ordinária' : 'Extraordinária'}</p>
          <p className="text-sm text-gray-500">{new Date(plano.reuniao_aprovacao_detail.data_reuniao + 'T00:00').toLocaleDateString('pt-BR')}</p>
          {plano.reuniao_aprovacao_detail.deliberacao && <p className="text-sm text-gray-600 mt-2">{plano.reuniao_aprovacao_detail.deliberacao}</p>}
          {plano.reuniao_aprovacao_detail.presentes_detail?.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Membros presentes</p>
              <ul className="text-sm text-gray-600 list-disc list-inside">
                {plano.reuniao_aprovacao_detail.presentes_detail.map((m) => (
                  <li key={m.id}>{m.cargo_display} — {m.usuario_nome || '—'}</li>
                ))}
              </ul>
            </div>
          )}
        </Section>
      )}

      <Section title="Histórico de Transições">
        {(plano.historico || []).length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma transição registrada.</p>
        ) : (
          <div className="space-y-2">
            {plano.historico.map((h) => (
              <div key={h.id} className="text-xs text-gray-500 border-l-2 border-gray-200 pl-3">
                <span className="font-medium text-gray-700">{h.status_anterior || '—'} → {h.status_novo}</span>
                {' '}por {h.usuario_nome} em {new Date(h.criado_em).toLocaleString('pt-BR')}
                {h.motivo && <p className="text-gray-400">{h.motivo}</p>}
              </div>
            ))}
          </div>
        )}
      </Section>
    </div>
  )
}

// ─── Aba: Execução Financeira ────────────────────────────────────────────────
const ETAPA_CLS = {
  Necessidade: 'bg-gray-100 text-gray-600',
  DFD: 'bg-blue-100 text-blue-700',
  ETP: 'bg-indigo-100 text-indigo-700',
  TR: 'bg-purple-100 text-purple-700',
  Procedimento: 'bg-orange-100 text-orange-700',
  Contrato: 'bg-green-100 text-green-700',
}

function ExecucaoTab({ planoId }) {
  const { fetchExecucao } = usePlanoAplicacaoStore()
  const [dados, setDados] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchExecucao(planoId).then(setDados).finally(() => setLoading(false))
  }, [planoId])

  if (loading) return <p className="text-sm text-gray-400">Carregando execução financeira...</p>
  if (!dados) return null

  const { resumo, necessidades } = dados

  return (
    <div className="space-y-5">
      <Section title="Resumo de Prestação de Contas">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Resumo label="Necessidades" valor={resumo.total_necessidades} />
          <Resumo label="Valor Planejado" valor={formatarMoeda(resumo.valor_planejado)} />
          <Resumo label="Já em DFD" valor={formatarMoeda(resumo.valor_em_dfd)} />
          <Resumo label="Já Contratado" valor={formatarMoeda(resumo.valor_contratado)} cor="text-green-700" />
        </div>
      </Section>

      <Section title="Necessidades Geradas">
        {necessidades.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma necessidade gerada a partir deste plano ainda.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-xs text-gray-400 uppercase">
                <tr>
                  <th className="text-left py-1">Necessidade</th>
                  <th className="text-left py-1">Órgão</th>
                  <th className="text-right py-1">Valor</th>
                  <th className="text-left py-1">Etapa Atual</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {necessidades.map((n) => (
                  <tr key={n.necessidade_id}>
                    <td className="py-2">
                      <Link to={`/rastreabilidade/${n.necessidade_id}`} className="text-blue-600 hover:underline">{n.titulo}</Link>
                    </td>
                    <td className="py-2 text-gray-500">{n.org_sigla}</td>
                    <td className="py-2 text-right text-gray-700">{formatarMoeda(n.valor_estimado)}</td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ETAPA_CLS[n.etapa_atual] || ''}`}>
                        {n.etapa_atual} ({n.etapa_idx + 1}/{n.total_etapas})
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </div>
  )
}

function Resumo({ label, valor, cor = 'text-gray-800' }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase">{label}</p>
      <p className={`text-lg font-semibold ${cor}`}>{valor}</p>
    </div>
  )
}

// ─── Modais ──────────────────────────────────────────────────────────────────
function MotivoModal({ titulo, onConfirm, onClose, saving }) {
  const [motivo, setMotivo] = useState('')
  return (
    <Modal titulo={titulo} onClose={onClose}>
      <textarea rows={3} placeholder="Motivo (obrigatório)" value={motivo} onChange={(e) => setMotivo(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3" />
      <ModalActions onConfirm={() => onConfirm(motivo)} onClose={onClose} disabled={!motivo.trim() || saving} saving={saving} />
    </Modal>
  )
}

function AprovarConselhoModal({ onConfirm, onClose, saving }) {
  const [form, setForm] = useState({ numero_ata: '', data_reuniao: '', tipo: 'ordinaria', deliberacao: '' })
  return (
    <Modal titulo="Aprovar pelo Conselho Gestor" onClose={onClose}>
      <div className="space-y-2 mb-3">
        <input type="text" placeholder="Número da ata" value={form.numero_ata}
          onChange={(e) => setForm((p) => ({ ...p, numero_ata: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        <input type="date" value={form.data_reuniao}
          onChange={(e) => setForm((p) => ({ ...p, data_reuniao: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        <select value={form.tipo} onChange={(e) => setForm((p) => ({ ...p, tipo: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="ordinaria">Reunião Ordinária</option>
          <option value="extraordinaria">Reunião Extraordinária</option>
        </select>
        <textarea rows={2} placeholder="Deliberação (opcional)" value={form.deliberacao}
          onChange={(e) => setForm((p) => ({ ...p, deliberacao: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>
      <ModalActions onConfirm={() => onConfirm(form)} onClose={onClose} disabled={!form.numero_ata.trim() || !form.data_reuniao || saving} saving={saving} />
    </Modal>
  )
}

function HomologarModal({ onConfirm, onClose, saving }) {
  const [form, setForm] = useState({ numero_ato: '', data_ato: '', numero_processo_sei_ato: '' })
  return (
    <Modal titulo="Registrar Homologação" onClose={onClose}>
      <div className="space-y-2 mb-3">
        <input type="text" placeholder="Número do ato" value={form.numero_ato}
          onChange={(e) => setForm((p) => ({ ...p, numero_ato: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        <input type="date" value={form.data_ato}
          onChange={(e) => setForm((p) => ({ ...p, data_ato: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        <input type="text" placeholder="Nº processo SEI (opcional)" value={form.numero_processo_sei_ato}
          onChange={(e) => setForm((p) => ({ ...p, numero_processo_sei_ato: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>
      <ModalActions onConfirm={() => onConfirm(form)} onClose={onClose} disabled={!form.numero_ato.trim() || !form.data_ato || saving} saving={saving} />
    </Modal>
  )
}

function Modal({ titulo, onClose, children }) {
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-xl p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
        <p className="text-sm font-semibold text-gray-800 mb-3">{titulo}</p>
        {children}
      </div>
    </div>
  )
}

function ModalActions({ onConfirm, onClose, disabled, saving }) {
  return (
    <div className="flex gap-2">
      <button onClick={onConfirm} disabled={disabled}
        className="bg-yellow-600 hover:bg-yellow-700 disabled:opacity-50 text-white text-sm px-4 py-1.5 rounded-lg">
        {saving ? 'Salvando...' : 'Confirmar'}
      </button>
      <button onClick={onClose} className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm px-4 py-1.5 rounded-lg">
        Fechar
      </button>
    </div>
  )
}

// ─── Componentes utilitários ─────────────────────────────────────────────────
function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{title}</p>
      {subtitle && <p className="text-xs text-gray-400 mb-3">{subtitle}</p>}
      <div className="space-y-3 mt-2">{children}</div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      {children}
    </div>
  )
}

function inp() {
  return 'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-500'
}
