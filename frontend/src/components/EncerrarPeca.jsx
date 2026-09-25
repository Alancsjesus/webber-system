import { useState } from 'react'
import api from '../services/api'
import useAuthStore from '../stores/authStore'

/**
 * Encerramento sem prosseguimento de ETP, TR ou Mapa de Preços.
 * Tira a peça do fluxo (para de contar tempo de construção e sai do Painel de
 * Tramitação) com categoria e motivo registrados no histórico. Reabertura só
 * pelo admin. Ver backend core/encerramento.py.
 */
export const MOTIVOS_ENCERRAMENTO = [
  { value: 'enc_desistencia', label: 'Demanda desistida pela unidade demandante' },
  { value: 'enc_perda_objeto', label: 'Perda de objeto — necessidade superada' },
  { value: 'enc_sem_orcamento', label: 'Sem disponibilidade orçamentária no exercício' },
  { value: 'enc_substituida', label: 'Substituída por outra contratação', referencia: true },
  { value: 'enc_aproveitada', label: 'Aproveitada em outra contratação (adesão a ARP, outro processo)', referencia: true },
  { value: 'enc_outro', label: 'Outro' },
]

const PAPEIS = ['admin', 'analista', 'gestor_planejamento', 'solicitante', 'responsavel_tecnico']
const FINAIS = ['Encerrado', 'Cancelado', 'Dispensado']

export default function EncerrarPeca({ tipo, url, status, onEncerrado }) {
  const papel = useAuthStore((s) => s.papel)
  const [aberto, setAberto] = useState(false)
  const [categoria, setCategoria] = useState('')
  const [motivo, setMotivo] = useState('')
  const [referencia, setReferencia] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (FINAIS.includes(status) || !PAPEIS.includes(papel)) return null
  const pedeReferencia = MOTIVOS_ENCERRAMENTO.find((m) => m.value === categoria)?.referencia
  const valido = categoria && motivo.trim() && (!pedeReferencia || referencia.trim())

  const fechar = () => { setAberto(false); setCategoria(''); setMotivo(''); setReferencia(''); setErro('') }
  const confirmar = async () => {
    setEnviando(true); setErro('')
    try {
      await api.post(`${url}/encerrar/`, { categoria, motivo, referencia })
      fechar()
      onEncerrado?.()
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível encerrar.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <button onClick={() => setAberto(true)}
        className="border border-gray-300 text-gray-600 hover:bg-gray-50 text-sm font-medium px-4 py-1.5 rounded-lg">
        Encerrar sem prosseguimento
      </button>
      {aberto && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
            <h3 className="text-base font-semibold text-gray-800">Encerrar {tipo} sem prosseguimento</h3>
            <p className="text-xs text-gray-500 mt-1 mb-4">
              Tira a peça do fluxo: ela deixa de contar tempo de construção e sai do Painel de Tramitação.
              Fica registrada no histórico e só o administrador pode reabrir.
            </p>
            <label className="block text-xs font-medium text-gray-600 mb-1">Categoria *</label>
            <select value={categoria} onChange={(e) => setCategoria(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3">
              <option value="">Selecione…</option>
              {MOTIVOS_ENCERRAMENTO.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
            {pedeReferencia && (
              <>
                <label className="block text-xs font-medium text-gray-600 mb-1">Contratação de destino (processo SEI, Ata, procedimento) *</label>
                <input value={referencia} onChange={(e) => setReferencia(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3" />
              </>
            )}
            <label className="block text-xs font-medium text-gray-600 mb-1">Motivo *</label>
            <textarea rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
            {erro && <p className="text-sm text-red-600 mt-2">{erro}</p>}
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={fechar} className="text-sm text-gray-600 px-4 py-2">Voltar</button>
              <button onClick={confirmar} disabled={!valido || enviando}
                className="bg-gray-800 hover:bg-gray-900 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg">
                {enviando ? 'Encerrando…' : 'Encerrar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
