import { useEffect, useState } from 'react'
import api, { downloadFile } from '../services/api'
import useTramitacaoStore from '../stores/tramitacaoStore'
import DFDPicker from '../components/DFDPicker'
import LoadingSpinner from '../components/LoadingSpinner'

export const pageHelp = {
  titulo: 'Painel Gerencial de Tramitação',
  descricao: 'Visão de topo para o gestor da organização: em qual setor/mesa cada processo SEI está agora, com objeto, fonte(s) de recurso e a fase atual. Diferente do Gestor de Contrato (que acompanha execução pós-contrato) — aqui é "onde cada processo está parado".',
  acoes: [
    { label: 'Novo processo', texto: 'Cadastra um processo em tramitação. Não exige DFD/TR/Procedimento existente — cobre desde a fase inicial na unidade demandante.' },
    { label: 'Atualizar fase', texto: 'Registra a mudança de setor/fase de um processo, com data e motivo opcional. Fica guardado no histórico do processo.' },
    { label: 'Exportar PDF/XLSX', texto: 'Gera o relatório gerencial agrupado por setor, no mesmo formato usado hoje fora da plataforma.' },
  ],
  dica: 'A fase é texto livre (o campo sugere valores comuns) porque a rotina real inclui situações que não cabem numa lista fechada, como "Retornou para demandante - ajustes".',
}

const FASES_SUGERIDAS = [
  'SESSÃO', 'CACON', 'SI', 'PCBA', 'SEFAZ', 'PGE', 'GAB',
  'Retornou para demandante - ajustes', 'Emissão de DOD', 'DOD',
]

function fmtData(d) {
  if (!d) return '—'
  const [ano, mes, dia] = d.split('-')
  return `${dia}/${mes}/${ano}`
}

function ModalNovoProcesso({ onClose, onSalvo, fontes }) {
  const criarProcesso = useTramitacaoStore((s) => s.criarProcesso)
  const [form, setForm] = useState({
    numero_sei: '', objeto: '', setor_atual: 'demandante', fase_atual: '',
    data_entrada_fase: new Date().toISOString().slice(0, 10), fontes_recurso: [], dfd: null,
  })
  const [dfdLabel, setDfdLabel] = useState('')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState(null)

  const toggleFonte = (id) => {
    setForm((f) => ({
      ...f,
      fontes_recurso: f.fontes_recurso.includes(id)
        ? f.fontes_recurso.filter((x) => x !== id)
        : [...f.fontes_recurso, id],
    }))
  }

  const salvar = async () => {
    if (!form.numero_sei.trim() || !form.objeto.trim()) {
      setErro('Preencha o número SEI e o objeto.')
      return
    }
    setSalvando(true); setErro(null)
    try {
      await criarProcesso(form)
      onSalvo()
    } catch {
      setErro('Não foi possível salvar. Confira os campos.')
    } finally { setSalvando(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="p-5 border-b border-gray-100">
          <h3 className="font-bold text-gray-800">Novo Processo em Tramitação</h3>
        </div>
        <div className="p-5 space-y-4">
          {erro && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{erro}</p>}

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Processo SEI</label>
            <input value={form.numero_sei} onChange={(e) => setForm({ ...form, numero_sei: e.target.value })}
              placeholder="020.16859.2026.0004493-21"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Objeto</label>
            <textarea value={form.objeto} onChange={(e) => setForm({ ...form, objeto: e.target.value })} rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Setor atual</label>
              <select value={form.setor_atual} onChange={(e) => setForm({ ...form, setor_atual: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {SETOR_CHOICES.map(([codigo, label]) => (
                  <option key={codigo} value={codigo}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Data de entrada na fase</label>
              <input type="date" value={form.data_entrada_fase}
                onChange={(e) => setForm({ ...form, data_entrada_fase: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fase</label>
            <input list="fases-sugeridas" value={form.fase_atual}
              onChange={(e) => setForm({ ...form, fase_atual: e.target.value })}
              placeholder="Ex: SESSÃO, CACON, ou uma descrição livre"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <datalist id="fases-sugeridas">
              {FASES_SUGERIDAS.map((f) => <option key={f} value={f} />)}
            </datalist>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">DFD vinculado (opcional)</label>
            <DFDPicker value={form.dfd} valueLabel={dfdLabel}
              onChange={(id, dfd) => { setForm({ ...form, dfd: id }); setDfdLabel(dfd ? dfd.numero_sei : '') }} />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fontes de recurso</label>
            <div className="flex flex-wrap gap-2">
              {fontes.map((f) => (
                <label key={f.id}
                  className={`text-xs px-2 py-1 rounded-full border cursor-pointer ${
                    form.fontes_recurso.includes(f.id)
                      ? 'bg-blue-50 border-blue-300 text-blue-700'
                      : 'bg-gray-50 border-gray-200 text-gray-600'
                  }`}>
                  <input type="checkbox" className="hidden"
                    checked={form.fontes_recurso.includes(f.id)}
                    onChange={() => toggleFonte(f.id)} />
                  {f.nome}
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="p-5 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="text-sm text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>
          <button onClick={salvar} disabled={salvando}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {salvando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ModalAtualizarFase({ processo, onClose, onSalvo }) {
  const mudarFase = useTramitacaoStore((s) => s.mudarFase)
  const [setor, setSetor] = useState(processo.setor_atual)
  const [fase, setFase] = useState('')
  const [data, setData] = useState(new Date().toISOString().slice(0, 10))
  const [motivo, setMotivo] = useState('')
  const [salvando, setSalvando] = useState(false)

  const salvar = async () => {
    setSalvando(true)
    try {
      await mudarFase(processo.id, { setor_atual: setor, fase_atual: fase, data_entrada_fase: data, motivo })
      onSalvo()
    } finally { setSalvando(false) }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
        <div className="p-5 border-b border-gray-100">
          <h3 className="font-bold text-gray-800">Atualizar Fase</h3>
          <p className="text-xs text-gray-500 mt-0.5 font-mono">{processo.numero_sei}</p>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Novo setor</label>
              <select value={setor} onChange={(e) => setSetor(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {SETOR_CHOICES.map(([codigo, label]) => (
                  <option key={codigo} value={codigo}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Data</label>
              <input type="date" value={data} onChange={(e) => setData(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Fase</label>
            <input list="fases-sugeridas-modal" value={fase} onChange={(e) => setFase(e.target.value)}
              placeholder="Ex: SESSÃO, CACON, ou uma descrição livre"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <datalist id="fases-sugeridas-modal">
              {FASES_SUGERIDAS.map((f) => <option key={f} value={f} />)}
            </datalist>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo (opcional)</label>
            <input value={motivo} onChange={(e) => setMotivo(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>
        <div className="p-5 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="text-sm text-gray-600 px-4 py-2 rounded-lg hover:bg-gray-50">Cancelar</button>
          <button onClick={salvar} disabled={salvando}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg">
            {salvando ? 'Salvando...' : 'Confirmar'}
          </button>
        </div>
      </div>
    </div>
  )
}

const SETOR_CHOICES = [
  ['casa_civil', 'Casa Civil'],
  ['ccc', 'CCC'],
  ['cfcr', 'CFCR'],
  ['clic', 'CLIC'],
  ['demandante', 'Demandante'],
  ['pge', 'PGE'],
  ['saeb_coe', 'SAEB/COE'],
  ['saeb_dm', 'SAEB/DM'],
  ['sefaz', 'SEFAZ'],
  ['ssp_gab', 'SSP/GAB'],
]

export default function TramitacaoPainel() {
  const { painel, loading, error, fetchPainel } = useTramitacaoStore()
  const [fontes, setFontes] = useState([])
  const [modalNovo, setModalNovo] = useState(false)
  const [processoEditando, setProcessoEditando] = useState(null)
  const [exportando, setExportando] = useState(false)

  useEffect(() => {
    fetchPainel()
    api.get('/orcamento/fonte-recurso/', { params: { page_size: 100 } })
      .then(({ data }) => setFontes(data.results ?? data))
      .catch(() => {})
  }, [])

  const exportar = async (formato) => {
    setExportando(true)
    try {
      const ext = formato === 'pdf' ? 'pdf' : 'xlsx'
      await downloadFile(`/tramitacao/painel/?export=${formato}`, `PainelTramitacao.${ext}`)
    } catch {
      alert('Não foi possível exportar. Tente novamente.')
    } finally { setExportando(false) }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Painel Gerencial de Tramitação</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Onde cada processo SEI está agora — visão de topo da organização.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => exportar('pdf')} disabled={exportando}
            className="bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-3 py-2 rounded-lg">
            Exportar PDF
          </button>
          <button onClick={() => exportar('xlsx')} disabled={exportando}
            className="bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-700 text-sm font-medium px-3 py-2 rounded-lg">
            Exportar XLSX
          </button>
          <button onClick={() => setModalNovo(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
            + Novo processo
          </button>
        </div>
      </div>

      {loading ? <LoadingSpinner /> : error ? (
        <p className="text-sm text-red-500">{error}</p>
      ) : !painel ? null : (
        <>
          <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 inline-block">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-1">Total de processos</p>
            <p className="text-lg font-bold text-gray-800">{painel.total_geral}</p>
          </div>

          {painel.grupos.length === 0 && (
            <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 text-sm text-gray-500">
              Nenhum processo em tramitação cadastrado ainda.
            </div>
          )}

          <div className="space-y-6">
            {painel.grupos.map((g) => (
              <div key={g.setor}>
                <h2 className="text-sm font-bold text-gray-700 mb-2">
                  {g.setor_display} <span className="text-gray-400 font-normal">(Total: {g.total})</span>
                </h2>
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-400 bg-gray-50 border-b border-gray-100">
                        <th className="py-2 px-4 font-medium">Processo SEI</th>
                        <th className="py-2 px-4 font-medium">Objeto</th>
                        <th className="py-2 px-4 font-medium">Fonte(s)</th>
                        <th className="py-2 px-4 font-medium">Fase</th>
                        <th className="py-2 px-4 font-medium"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {g.itens.map((p) => (
                        <tr key={p.id} className="border-b border-gray-50 last:border-0">
                          <td className="py-2 px-4 font-mono text-xs">{p.numero_sei}</td>
                          <td className="py-2 px-4">{p.objeto}</td>
                          <td className="py-2 px-4 text-xs text-gray-500">
                            {p.fontes_recurso_nomes?.length ? p.fontes_recurso_nomes.join(', ') : '—'}
                          </td>
                          <td className="py-2 px-4 text-xs text-gray-500">
                            {(p.fase_atual || g.setor_display)} - {fmtData(p.data_entrada_fase)}
                          </td>
                          <td className="py-2 px-4 text-right">
                            <button onClick={() => setProcessoEditando(p)}
                              className="text-xs text-blue-600 hover:underline">Atualizar fase</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {modalNovo && (
        <ModalNovoProcesso fontes={fontes} onClose={() => setModalNovo(false)}
          onSalvo={() => { setModalNovo(false); fetchPainel() }} />
      )}
      {processoEditando && (
        <ModalAtualizarFase processo={processoEditando} onClose={() => setProcessoEditando(null)}
          onSalvo={() => { setProcessoEditando(null); fetchPainel() }} />
      )}
    </div>
  )
}
