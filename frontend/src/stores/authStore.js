import { create } from 'zustand'
import axios from 'axios'

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return {}
  }
}

function getFieldFromToken(field) {
  const token = localStorage.getItem('access_token')
  if (!token) return null
  return parseJwt(token)[field] || null
}

const DEFAULT_FLAGS = {
  modulo_planejamento_ativo: true,
  modulo_orcamento_ativo:    true,
  modulo_etp_ativo:          true,
  modulo_mapa_ativo:         true,
  dfd_exige_planejamento:    false,
}

function getFlagsFromToken() {
  const token = localStorage.getItem('access_token')
  if (!token) return DEFAULT_FLAGS
  return parseJwt(token)['flags'] || DEFAULT_FLAGS
}

const useAuthStore = create((set) => ({
  user:          null,
  papel:         getFieldFromToken('papel'),
  orgId:         getFieldFromToken('orgao_id') || getFieldFromToken('org_id'),
  orgaoSigla:    getFieldFromToken('orgao_sigla'),
  orgaoNome:     getFieldFromToken('orgao_nome'),
  unidadeId:     getFieldFromToken('unidade_id'),
  unidadeSigla:  getFieldFromToken('unidade_sigla'),
  unidadeNome:   getFieldFromToken('unidade_nome'),
  tipoUnidade:   getFieldFromToken('tipo_unidade'),
  tipoOrg:       getFieldFromToken('tipo_unidade') || 'demandante',
  flags:         getFlagsFromToken(),
  isAuthenticated: !!localStorage.getItem('access_token'),
  error:         null,
  loading:       false,

  login: async (username, password, captchaToken = '') => {
    set({ loading: true, error: null })
    try {
      const { data } = await axios.post('/api/token/', { username, password, captcha_token: captchaToken })
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      const p = parseJwt(data.access)
      set({
        isAuthenticated: true,
        papel:        p.papel         || null,
        orgId:        p.orgao_id      || p.org_id || null,
        orgaoSigla:   p.orgao_sigla   || null,
        orgaoNome:    p.orgao_nome    || null,
        unidadeId:    p.unidade_id    || null,
        unidadeSigla: p.unidade_sigla || null,
        unidadeNome:  p.unidade_nome  || null,
        tipoUnidade:  p.tipo_unidade  || null,
        tipoOrg:      p.tipo_unidade  || 'demandante',
        flags:        p.flags         || DEFAULT_FLAGS,
        loading: false,
      })
    } catch (err) {
      const status = err.response?.status
      let msg
      if (status === 429) {
        msg = '429'
      } else if (status === 400 && err.response?.data?.captcha) {
        msg = 'Verificação CAPTCHA inválida. Tente novamente.'
      } else {
        msg = err.response?.data?.detail || 'Credenciais inválidas. Tente novamente.'
      }
      set({ error: msg, loading: false })
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({
      isAuthenticated: false,
      user: null, papel: null,
      orgId: null, orgaoSigla: null, orgaoNome: null,
      unidadeId: null, unidadeSigla: null, unidadeNome: null,
      tipoUnidade: null, tipoOrg: 'demandante',
      flags: DEFAULT_FLAGS,
    })
  },
}))

export default useAuthStore
