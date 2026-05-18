import { useEffect, useRef, useState } from 'react'
import api from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'

const ACOES = [
  { value: '',              label: 'Todos os eventos' },
  { value: 'created',       label: '+ Criação de registro' },
  { value: 'deleted',       label: '✕ Exclusão de registro' },
  { value: 'value_changed', label: '$ Alteração de valor' },
  { value: 'sei_changed',   label: '# Vinculação / alteração de SEI' },
  { value: 'login',         label: '→ Login de usuário' },
  { value: 'updated',       label: '~ Atualização' },
]

const ACAO_STYLE = {
  created:       { bg: 'bg-green-100',  text: 'text-green-700',  dot: 'bg-green-500',  label: '+ Criado'    },
  deleted:       { bg: 'bg-red-100',    text: 'text-red-600',    dot: 'bg-red-500',    label: '✕ Excluído'  },
  value_changed: { bg: 'bg-amber-100',  text: 'text-amber-700',  dot: 'bg-amber-400',  label: '$ Valor'     },
  sei_changed:   { bg: 'bg-blue-100',   text: 'text-blue-700',   dot: 'bg-blue-500',   label: '# SEI'       },
  login:         { bg: 'bg-purple-100', text: 'text-purple-700', dot: 'bg-purple-500', label: '→ Login'     },
  updated:       { bg: 'bg-gray-100',   text: 'text-gray-600',   dot: 'bg-gray-400',   label: '~ Alterado'  },
}

const MODULOS = [
  { value: '',                               label: 'Todos os módulos' },
  { value: 'modulo_demanda.DFD',             label: 'DFD' },
  { value: 'modulo_etp.ETP',                 label: 'ETP' },
  { value: 'modulo_tr.TR',                   label: 'Termo de Referência' },
  { value: 'modulo_licitacao.Procedimento',  label: 'Procedimento (Licitação)' },
  { value: 'modulo_contrato.Contrato',       label: 'Contrato' },
  { value: 'modulo_planejamento.NecessidadePlanejamento', label: 'Necessidade de Planejamento' },
  { value: 'User',                           label: 'Usuários (login)' },
]

const fmtDt = (s) => s
  ? new Date(s).toLocaleString('pt-BR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' })
  : '—'

export default function AuditoriaList() {
  const debounceRef = useRef(null)

  const [logs, setLogs]         = useState([])
  const [loading, setLoading]   = useState(true)
  const [total, setTotal]       = useState(0)
  const [page, setPage]         = useState(1)

  const [busca, setBusca]       = useState('')
  const [acao, setAcao]         = useState('')
  const [modelo, setModelo]     = useState('')
  const [usuario, setUsuario]   = useState('')
  const [dataIni, setDataIni]   = useState('')
  const [dataFim, setDataFim]   = useState('')

  const [exportando, setExportando] = useState(false)

  const PAGE_SIZE = 50
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const buildParams = (p = page) => {
    const params = { page_size: PAGE_SIZE, page: p }
    if (busca)   params.busca    = busca
    if (acao)    params.acao     = acao
    if (modelo)  params.modelo   = modelo
    if (usuario) params.usuario  = usuario
    if (dataIni) params.data_ini = dataIni
    if (dataFim) params.data_fim = dataFim
    return params
  }

  const load = (p = page) => {
    setLoading(true)
    api.get('/core/auditoria/', { params: buildParams(p) })
      .then(({ data }) => {
        setLogs(data.results ?? data)
        setTotal(data.count ?? (data.results ?? data).length)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => { setPage(1); load(1) }, busca ? 350 : 0)
    return () => clearTimeout(debounceRef.current)
  }, [busca, acao, modelo, usuario, dataIni, dataFim])

  useEffect(() => { load(page) }, [page])

  const handleExport = async () => {
    setExportando(true)
    try {
      const resp = await api.get('/core/auditoria/export/pdf/', {
        params: buildParams(1),
        responseType: 'blob',
      })
      const url  = URL.createObjectURL(new Blob([resp.data], { type: 'application/pdf' }))
      const a    = document.createElement('a')
      a.href     = url
      a.download = `Auditoria_${new Date().toISOString().slice(0,10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* silencioso */ }
    finally { setExportando(false) }
  }

  const limparFiltros = () => {
    setBusca(''); setAcao(''); setModelo(''); setUsuario(''); setDataIni(''); setDataFim('')
  }
  const temFiltro = busca || acao || modelo || usuario || dataIni || dataFim

  return (
    <div className="p-6 max-w-6xl space-y-4">
      {/* Cabeçalho */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Auditoria e Controle</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Trilha de auditoria — criações, exclusões, alterações de valor e SEI, logins.
            {total > 0 && <span className="ml-1 font-medium text-gray-500">{total.toLocaleString('pt-BR')} registros</span>}
          </p>
        </div>
        <button onClick={handleExport} disabled={exportando || total === 0}
          className="flex items-center gap-1.5 border border-gray-300 text-gray-600 hover:bg-gray-50 disabled:opacity-40 text-sm font-medium px-3 py-2 rounded-lg">
          {exportando ? 'Gerando...' : '↓ Exportar PDF'}
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-3">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
            <input value={busca} onChange={e => setBusca(e.target.value)}
              placeholder="Buscar na descrição ou objeto..."
              className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <input type="text" value={usuario} onChange={e => setUsuario(e.target.value)}
            placeholder="Usuário"
            className="w-36 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <div className="flex gap-3 flex-wrap">
          <select value={acao} onChange={e => { setAcao(e.target.value); setPage(1) }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            {ACOES.map(a => <option key={a.value} value={a.value}>{a.label}</option>)}
          </select>
          <select value={modelo} onChange={e => { setModelo(e.target.value); setPage(1) }}
            className="flex-1 min-w-48 border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            {MODULOS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
          </select>
          <input type="date" value={dataIni} onChange={e => { setDataIni(e.target.value); setPage(1) }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input type="date" value={dataFim} onChange={e => { setDataFim(e.target.value); setPage(1) }}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {temFiltro && (
            <button onClick={limparFiltros}
              className="text-xs text-gray-400 hover:text-red-500 px-2 py-2 rounded-lg hover:bg-red-50 border border-transparent hover:border-red-200">
              ✕ Limpar
            </button>
          )}
        </div>
      </div>

      {/* Timeline */}
      {loading ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12"><LoadingSpinner /></div>
      ) : logs.length === 0 ? (
        <EmptyState icon="search" title="Nenhum evento encontrado"
          description={temFiltro ? 'Tente ajustar os filtros.' : 'Nenhum evento de auditoria registrado ainda.'} />
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          {/* Cabeçalho da tabela */}
          <div className="grid grid-cols-[2rem_8.5rem_7rem_2.5rem_1fr_8rem] gap-x-3 px-5 py-2.5 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
            <span></span>
            <span>Data / Hora</span>
            <span>Módulo</span>
            <span>Tipo</span>
            <span>Descrição</span>
            <span>Usuário</span>
          </div>

          <div className="divide-y divide-gray-100">
            {logs.map(lg => {
              const st = ACAO_STYLE[lg.acao] || ACAO_STYLE.updated
              const mod = lg.modelo.split('.').pop()
              return (
                <div key={lg.id} className="grid grid-cols-[2rem_8.5rem_7rem_2.5rem_1fr_8rem] gap-x-3 px-5 py-3 items-start hover:bg-slate-50 transition-colors">
                  {/* Dot */}
                  <div className="flex items-center justify-center pt-1">
                    <span className={`w-2 h-2 rounded-full shrink-0 ${st.dot}`} />
                  </div>

                  {/* Data */}
                  <div className="text-xs text-gray-500 font-mono leading-tight pt-0.5">
                    {fmtDt(lg.criado_em)}
                  </div>

                  {/* Módulo */}
                  <div className="text-xs text-gray-600 truncate pt-0.5" title={lg.modelo}>
                    {mod}
                    {lg.objeto_repr && (
                      <p className="text-[10px] text-gray-400 truncate mt-0.5">{lg.objeto_repr}</p>
                    )}
                  </div>

                  {/* Badge tipo */}
                  <div className="pt-0.5">
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${st.bg} ${st.text} whitespace-nowrap`}>
                      {st.label}
                    </span>
                  </div>

                  {/* Descrição */}
                  <div className="text-sm text-gray-800 leading-snug">
                    {lg.descricao || lg.objeto_repr || '—'}
                    {/* Diff antes/depois */}
                    {(lg.antes_json || lg.depois_json) && (
                      <div className="mt-1 flex gap-2 text-[10px] font-mono flex-wrap">
                        {lg.antes_json && (
                          <span className="bg-red-50 text-red-600 px-1.5 py-0.5 rounded border border-red-100">
                            — {JSON.stringify(lg.antes_json)}
                          </span>
                        )}
                        {lg.depois_json && (
                          <span className="bg-green-50 text-green-600 px-1.5 py-0.5 rounded border border-green-100">
                            + {JSON.stringify(lg.depois_json)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Usuário */}
                  <div className="text-xs text-gray-500 truncate pt-0.5" title={lg.usuario_nome}>
                    {lg.usuario_nome}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Paginação */}
          <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between bg-gray-50">
            <span className="text-xs text-gray-500">
              {total.toLocaleString('pt-BR')} evento{total !== 1 ? 's' : ''}
              {' · '}página <strong>{page}</strong> de <strong>{totalPages || 1}</strong>
            </span>
            <div className="flex items-center gap-1">
              <button onClick={() => setPage(1)} disabled={page === 1}
                className="px-2 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30">«</button>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                className="px-3 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30">‹</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const start = Math.max(1, Math.min(page - 2, totalPages - 4))
                const pg = start + i
                if (pg < 1 || pg > totalPages) return null
                return (
                  <button key={pg} onClick={() => setPage(pg)}
                    className={`px-3 py-1 text-xs border rounded-lg ${pg === page ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-200 hover:bg-white'}`}>
                    {pg}
                  </button>
                )
              })}
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                className="px-3 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30">›</button>
              <button onClick={() => setPage(totalPages)} disabled={page >= totalPages}
                className="px-2 py-1 text-xs border border-gray-200 rounded-lg hover:bg-white disabled:opacity-30">»</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
