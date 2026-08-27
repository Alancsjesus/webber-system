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
import { pageHelp as necessidadeCreateHelp }  from '../pages/NecessidadeCreate'
import { pageHelp as dfdListHelp }            from '../pages/DFDList'
import { pageHelp as dfdDetailHelp }          from '../pages/DFDDetail'
import { pageHelp as dfdCreateHelp }          from '../pages/DFDCreate'
import { pageHelp as etpListHelp }            from '../pages/ETPList'
import { pageHelp as etpDetailHelp }          from '../pages/ETPDetail'
import { pageHelp as etpCreateHelp }          from '../pages/ETPCreate'
import { pageHelp as trListHelp }             from '../pages/TRList'
import { pageHelp as trDetailHelp }           from '../pages/TRDetail'
import { pageHelp as trCreateHelp }           from '../pages/TRCreate'
import { pageHelp as orcamentoListHelp }      from '../pages/OrcamentoList'
import { pageHelp as relatorioIndicacoesHelp } from '../pages/RelatorioIndicacoes'
import { pageHelp as painelOrcamentoHelp }    from '../pages/PainelOrcamento'
import { pageHelp as orcamentoCreateHelp }    from '../pages/OrcamentoCreate'
import { pageHelp as orcamentoDetailHelp }    from '../pages/OrcamentoDetail'
import { pageHelp as indicacaoListHelp }      from '../pages/IndicacaoList'
import { pageHelp as indicacaoCreateHelp }    from '../pages/IndicacaoCreate'
import { pageHelp as indicacaoDetailHelp }    from '../pages/IndicacaoDetail'
import { pageHelp as pcaDetailHelp }          from '../pages/PCADetail'
import { pageHelp as planoListHelp }          from '../pages/PlanoList'
import { pageHelp as mapaListHelp }           from '../pages/MapaList'
import { pageHelp as mapaDetailHelp }         from '../pages/MapaDetail'
import { pageHelp as mapaCreateHelp }         from '../pages/MapaCreate'
import { pageHelp as pncpListHelp }           from '../pages/PNCPList'
import { pageHelp as procedimentoListHelp }   from '../pages/ProcedimentoList'
import { pageHelp as procedimentoDetailHelp } from '../pages/ProcedimentoDetail'
import { pageHelp as procedimentoCreateHelp } from '../pages/ProcedimentoCreate'
import { pageHelp as contratoListHelp }       from '../pages/ContratoList'
import { pageHelp as contratoDetailHelp }     from '../pages/ContratoDetail'
import { pageHelp as notificacaoListHelp }    from '../pages/NotificacaoList'
import { pageHelp as painelContratosHelp }    from '../pages/PainelContratos'
import { pageHelp as contratoCreateHelp }     from '../pages/ContratoCreate'
import { pageHelp as fornecedorCreateHelp }   from '../pages/FornecedorCreate'
import { pageHelp as fornecedorDetailHelp }   from '../pages/FornecedorDetail'
import { pageHelp as prepararAquisicaoHelp }  from '../pages/PrepararAquisicao'
import { pageHelp as aceiteNecessidadesHelp } from '../pages/AceiteNecessidades'
import { pageHelp as ajudaHelp }              from '../pages/Ajuda'
import { pageHelp as orgaoAdminHelp }         from '../pages/config/OrgaoAdmin'
import { pageHelp as unidadeAdminHelp }       from '../pages/config/UnidadeAdmin'
import { pageHelp as usuarioAdminHelp }       from '../pages/config/UsuarioAdmin'
import { pageHelp as acaoAdminHelp }          from '../pages/config/AcaoAdmin'
import { pageHelp as elementoAdminHelp }      from '../pages/config/ElementoAdmin'
import { pageHelp as naturezaAdminHelp }      from '../pages/config/NaturezaAdmin'
import { pageHelp as fonteAdminHelp }         from '../pages/config/FonteAdmin'
import { pageHelp as subFonteAdminHelp }      from '../pages/config/SubFonteAdmin'
import { pageHelp as tipoAcaoAdminHelp }      from '../pages/config/TipoAcaoAdmin'
import { pageHelp as tipoFonteAdminHelp }     from '../pages/config/TipoFonteAdmin'
import { pageHelp as parametroAdminHelp }     from '../pages/config/ParametroAdmin'
import { pageHelp as perfilAdminHelp }        from '../pages/config/PerfilAdmin'
import { pageHelp as areaAdminHelp }          from '../pages/config/AreaAdmin'
import { pageHelp as artefatoAdminHelp }      from '../pages/config/ArtefatoAdmin'
import { pageHelp as catalogoAdminHelp }      from '../pages/config/CatalogoAdmin'
import { pageHelp as categoriaAdminHelp }     from '../pages/config/CategoriaAdmin'
import { pageHelp as importarCatalogoAdminHelp } from '../pages/config/ImportarCatalogoAdmin'
import { pageHelp as composicaoConselhoAdminHelp } from '../pages/config/ComposicaoConselhoAdmin'
import { pageHelp as planoComprasHelp }       from '../pages/PlanoCompras'
import { pageHelp as calendarioHelp }         from '../pages/Calendario'
import { pageHelp as auditoriaHelp }              from '../pages/AuditoriaList'
import { pageHelp as rastreabilidadeListHelp }    from '../pages/RastreabilidadeList'
import { pageHelp as rastreabilidadeDetailHelp }  from '../pages/RastreabilidadeDetail'
import { pageHelp as fornecedorListHelp }         from '../pages/FornecedorList'
import { pageHelp as ataListHelp }                from '../pages/AtaList'
import { pageHelp as ataCreateHelp }              from '../pages/AtaCreate'
import { pageHelp as ataDetailHelp }              from '../pages/AtaDetail'
import { pageHelp as fespPlanoListHelp }          from '../pages/FespPlanoList'
import { pageHelp as fespPlanoCreateHelp }        from '../pages/FespPlanoCreate'
import { pageHelp as fespPlanoDetailHelp }        from '../pages/FespPlanoDetail'
import { pageHelp as fespConselhoHelp }           from '../pages/FespConselhoPainel'
import { pageHelp as fespInstrumentoListHelp }    from '../pages/FespInstrumentoList'
import { pageHelp as fespInstrumentoCreateHelp }  from '../pages/FespInstrumentoCreate'
import { pageHelp as fespInstrumentoDetailHelp }  from '../pages/FespInstrumentoDetail'
import { pageHelp as fespConsolidacaoHelp }       from '../pages/FespConsolidacao'
import { pageHelp as fespPainelExecucaoHelp }     from '../pages/FespPainelExecucao'
import { pageHelp as fespRelatorioItensHelp }     from '../pages/FespRelatorioItens'

/**
 * Mapeamento rota → objeto pageHelp.
 * Padrões com :param são resolvidos via matchPath (react-router-dom) no PageHelpPanel.
 */
export const helpContent = {
  '/':                          dashboardHelp,
  '/painel':                    painelHelp,

  '/planejamento/necessidades':       necessidadeListHelp,
  '/planejamento/necessidades/nova':  necessidadeCreateHelp,
  '/planejamento/necessidades/:id':   necessidadeDetailHelp,

  '/demanda/dfd':               dfdListHelp,
  '/demanda/dfd/novo':          dfdCreateHelp,
  '/demanda/dfd/:id':           dfdDetailHelp,

  '/etp/etps':                  etpListHelp,
  '/etp/etps/novo':             etpCreateHelp,
  '/etp/etps/:id':              etpDetailHelp,

  '/analise-tecnica/trs':       trListHelp,
  '/analise-tecnica/trs/novo':  trCreateHelp,
  '/analise-tecnica/trs/:id':   trDetailHelp,

  '/orcamento/dotacoes':        orcamentoListHelp,
  '/orcamento/dotacoes/nova':   orcamentoCreateHelp,
  '/orcamento/dotacoes/:id':    orcamentoDetailHelp,
  '/orcamento/indicacoes':      indicacaoListHelp,
  '/orcamento/indicacoes/nova': indicacaoCreateHelp,
  '/orcamento/indicacoes/:id':  indicacaoDetailHelp,
  '/orcamento/relatorio-indicacoes': relatorioIndicacoesHelp,
  '/orcamento/painel':          painelOrcamentoHelp,

  '/planejamento/planos':       planoListHelp,
  '/planejamento/pca/:id':      pcaDetailHelp,

  '/pesquisa/mapa':             mapaListHelp,
  '/pesquisa/mapa/novo':        mapaCreateHelp,
  '/pesquisa/mapa/:id':         mapaDetailHelp,
  '/pesquisa/pncp':             pncpListHelp,

  '/licitacao':                 procedimentoListHelp,
  '/licitacao/novo':            procedimentoCreateHelp,
  '/licitacao/:id':             procedimentoDetailHelp,

  '/contratos':                 contratoListHelp,
  '/contratos/novo':            contratoCreateHelp,
  '/contratos/notificacoes':    notificacaoListHelp,
  '/contratos/painel':          painelContratosHelp,
  '/contratos/:id':             contratoDetailHelp,

  '/fornecedores/novo':         fornecedorCreateHelp,
  '/fornecedores/:id':          fornecedorDetailHelp,

  '/aquisicao/preparar':        prepararAquisicaoHelp,
  '/planejamento/aceite':       aceiteNecessidadesHelp,

  '/plano-compras':             planoComprasHelp,
  '/calendario':                calendarioHelp,
  '/auditoria':                 auditoriaHelp,

  '/rastreabilidade':           rastreabilidadeListHelp,
  '/rastreabilidade/:id':       rastreabilidadeDetailHelp,

  '/fornecedores':              fornecedorListHelp,
  '/arp':                       ataListHelp,
  '/arp/novo':                  ataCreateHelp,
  '/arp/:id':                   ataDetailHelp,
  '/fesp/planos':               fespPlanoListHelp,
  '/fesp/planos/novo':          fespPlanoCreateHelp,
  '/fesp/planos/:id':           fespPlanoDetailHelp,
  '/fesp/planos/:id/consolidacao': fespConsolidacaoHelp,
  '/fesp/conselho':             fespConselhoHelp,
  '/fesp/instrumentos':         fespInstrumentoListHelp,
  '/fesp/instrumentos/novo':    fespInstrumentoCreateHelp,
  '/fesp/instrumentos/:id':     fespInstrumentoDetailHelp,
  '/fesp/execucao':             fespPainelExecucaoHelp,
  '/fesp/relatorio-itens':      fespRelatorioItensHelp,

  '/ajuda':                     ajudaHelp,

  '/config/orgaos':             orgaoAdminHelp,
  '/config/unidades':           unidadeAdminHelp,
  '/config/usuarios':           usuarioAdminHelp,
  '/config/perfis':             perfilAdminHelp,
  '/config/parametros':         parametroAdminHelp,
  '/config/areas':              areaAdminHelp,
  '/config/acoes':              acaoAdminHelp,
  '/config/elementos':          elementoAdminHelp,
  '/config/naturezas':          naturezaAdminHelp,
  '/config/fontes':             fonteAdminHelp,
  '/config/subfontes':          subFonteAdminHelp,
  '/config/tipo-acao':          tipoAcaoAdminHelp,
  '/config/tipo-fonte':         tipoFonteAdminHelp,
  '/config/artefatos':          artefatoAdminHelp,
  '/config/catalogo':           catalogoAdminHelp,
  '/config/catalogo/importar':  importarCatalogoAdminHelp,
  '/config/categorias':         categoriaAdminHelp,
  '/config/conselho-fesp':      composicaoConselhoAdminHelp,
}
