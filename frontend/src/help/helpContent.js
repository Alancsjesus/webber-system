/**
 * Agregador central de ajuda contextual.
 *
 * REGRA DE MANUTENÇÃO:
 *   Sempre que uma página ganhar, remover ou alterar um botão/ação/campo relevante,
 *   o bloco `export const pageHelp` naquela página deve ser atualizado na mesma operação.
 *   Páginas novas devem exportar `pageHelp` e ter a rota registrada aqui.
 *
 *   Para validar cobertura: node scripts/check-help.js
 */

import { pageHelp as dashboardHelp }          from '../pages/Dashboard'
import { pageHelp as painelHelp }             from '../pages/Painel'
import { pageHelp as necessidadeListHelp }    from '../pages/NecessidadeList'
import { pageHelp as necessidadeDetailHelp }  from '../pages/NecessidadeDetail'
import { pageHelp as dfdListHelp }            from '../pages/DFDList'
import { pageHelp as dfdDetailHelp }          from '../pages/DFDDetail'
import { pageHelp as etpListHelp }            from '../pages/ETPList'
import { pageHelp as etpDetailHelp }          from '../pages/ETPDetail'
import { pageHelp as trListHelp }             from '../pages/TRList'
import { pageHelp as trDetailHelp }           from '../pages/TRDetail'
import { pageHelp as orcamentoListHelp }      from '../pages/OrcamentoList'
import { pageHelp as relatorioIndicacoesHelp } from '../pages/RelatorioIndicacoes'
import { pageHelp as painelOrcamentoHelp }    from '../pages/PainelOrcamento'
import { pageHelp as mapaListHelp }           from '../pages/MapaList'
import { pageHelp as mapaDetailHelp }         from '../pages/MapaDetail'
import { pageHelp as pncpListHelp }           from '../pages/PNCPList'
import { pageHelp as procedimentoListHelp }   from '../pages/ProcedimentoList'
import { pageHelp as procedimentoDetailHelp } from '../pages/ProcedimentoDetail'
import { pageHelp as contratoListHelp }       from '../pages/ContratoList'
import { pageHelp as contratoDetailHelp }     from '../pages/ContratoDetail'
import { pageHelp as planoComprasHelp }       from '../pages/PlanoCompras'
import { pageHelp as calendarioHelp }         from '../pages/Calendario'
import { pageHelp as auditoriaHelp }              from '../pages/AuditoriaList'
import { pageHelp as rastreabilidadeListHelp }    from '../pages/RastreabilidadeList'
import { pageHelp as rastreabilidadeDetailHelp }  from '../pages/RastreabilidadeDetail'

/**
 * Mapeamento rota → objeto pageHelp.
 * Padrões com :param são resolvidos via matchPath (react-router-dom) no PageHelpPanel.
 */
export const helpContent = {
  '/':                          dashboardHelp,
  '/painel':                    painelHelp,

  '/planejamento/necessidades':       necessidadeListHelp,
  '/planejamento/necessidades/:id':   necessidadeDetailHelp,

  '/demanda/dfd':               dfdListHelp,
  '/demanda/dfd/:id':           dfdDetailHelp,

  '/etp/etps':                  etpListHelp,
  '/etp/etps/:id':              etpDetailHelp,

  '/analise-tecnica/trs':       trListHelp,
  '/analise-tecnica/trs/:id':   trDetailHelp,

  '/orcamento/dotacoes':        orcamentoListHelp,
  '/orcamento/relatorio-indicacoes': relatorioIndicacoesHelp,
  '/orcamento/painel':          painelOrcamentoHelp,

  '/pesquisa/mapa':             mapaListHelp,
  '/pesquisa/mapa/:id':         mapaDetailHelp,
  '/pesquisa/pncp':             pncpListHelp,

  '/licitacao':                 procedimentoListHelp,
  '/licitacao/:id':             procedimentoDetailHelp,

  '/contratos':                 contratoListHelp,
  '/contratos/:id':             contratoDetailHelp,

  '/plano-compras':             planoComprasHelp,
  '/calendario':                calendarioHelp,
  '/auditoria':                 auditoriaHelp,

  '/rastreabilidade':           rastreabilidadeListHelp,
  '/rastreabilidade/:id':       rastreabilidadeDetailHelp,
}
