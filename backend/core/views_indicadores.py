"""
Endpoints de indicadores para o Dashboard WEBBER.
- GET /api/indicadores/orcamento/    — execução orçamentária por elemento
- GET /api/indicadores/devolucoes/   — taxa de devoluções por tipo de documento
- GET /api/indicadores/agrupamento/  — sugestão de agrupamento por família SIMPAS
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q, Exists, OuterRef
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


def _pct(parte, total):
    if not total or total == 0:
        return 0
    return round(float(parte) / float(total) * 100, 1)


class IndicadoresOrcamentoView(APIView):
    """
    Execução orçamentária do exercício corrente.
    Agrega DotacaoOrcamentaria por elemento de despesa.
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_orcamento.models import DotacaoOrcamentaria
        from core.models import ParametroSistema

        org_id = request.org_id

        # Exercício corrente via parâmetro (fallback: ano atual)
        exercicio_str = ParametroSistema.get('exercicio_fiscal_corrente')
        try:
            exercicio = int(exercicio_str) if exercicio_str else None
        except (ValueError, TypeError):
            exercicio = None

        qs = DotacaoOrcamentaria.objects.filter(org_id=org_id)
        if exercicio:
            qs = qs.filter(exercicio_fiscal=exercicio)

        # Totais gerais
        totais_raw = qs.aggregate(
            dotado=Sum('valor_dotado'),
            indicado=Sum('valor_indicado'),
            descentralizado=Sum('valor_descentralizado'),
            concedido=Sum('valor_concedido'),
        )
        dotado        = float(totais_raw['dotado']        or 0)
        indicado      = float(totais_raw['indicado']      or 0)
        descentralizado = float(totais_raw['descentralizado'] or 0)
        concedido     = float(totais_raw['concedido']     or 0)

        totais = {
            'dotado':             dotado,
            'indicado':           indicado,
            'descentralizado':    descentralizado,
            'concedido':          concedido,
            'pct_indicado':       _pct(indicado, dotado),
            'pct_descentralizado':_pct(descentralizado, dotado),
            'pct_concedido':      _pct(concedido, dotado),
        }

        # Por elemento de despesa
        por_elem_raw = (
            qs.values(
                'elemento_despesa__codigo',
                'elemento_despesa__descricao',
            )
            .annotate(
                dotado=Sum('valor_dotado'),
                indicado=Sum('valor_indicado'),
                descentralizado=Sum('valor_descentralizado'),
                concedido=Sum('valor_concedido'),
            )
            .order_by('-dotado')
        )

        por_elemento = []
        for row in por_elem_raw:
            d = float(row['dotado'] or 0)
            i = float(row['indicado'] or 0)
            por_elemento.append({
                'elemento_codigo':    row['elemento_despesa__codigo'],
                'elemento_descricao': row['elemento_despesa__descricao'] or '—',
                'dotado':             d,
                'indicado':           i,
                'descentralizado':    float(row['descentralizado'] or 0),
                'concedido':          float(row['concedido'] or 0),
                'pct_indicado':       _pct(i, d),
            })

        # Por ação orçamentária
        por_acao_raw = (
            qs.values('acao__codigo', 'acao__nome')
            .annotate(dotado=Sum('valor_dotado'), indicado=Sum('valor_indicado'))
            .order_by('-dotado')[:5]
        )
        por_acao = [
            {
                'acao_codigo': r['acao__codigo'],
                'acao_nome':   (r['acao__nome'] or '')[:50],
                'dotado':      float(r['dotado'] or 0),
                'indicado':    float(r['indicado'] or 0),
                'pct_indicado':_pct(float(r['indicado'] or 0), float(r['dotado'] or 0)),
            }
            for r in por_acao_raw
        ]

        return Response({
            'exercicio':    exercicio,
            'totais':       totais,
            'por_elemento': por_elemento,
            'por_acao':     por_acao,
        })


class IndicadoresDevolucoesView(APIView):
    """
    Taxa de devoluções por tipo de documento no exercício corrente.
    Consulta os históricos de DFD, ETP, TR e Mapa de Preços.
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import DFD, HistoricoTramitacao
        from modulo_etp.models import ETP, HistoricoETP
        from modulo_tr.models import TR, HistoricoTR
        from modulo_mapa_precos.models import MapaComparativoPrecos, HistoricoMapa

        org_id = request.org_id

        def _stats_doc(Model, HistoricoModel, status_devolvido, fk_field):
            total     = Model.objects.filter(org_id=org_id).count()
            devolvidos = (
                HistoricoModel.objects
                .filter(**{f'{fk_field}__org_id': org_id, 'status_novo': status_devolvido})
                .values(fk_field)
                .distinct()
                .count()
            )
            return {
                'total':           total,
                'devolvidos':      devolvidos,
                'taxa_devolucao':  _pct(devolvidos, total) if total else 0,
            }

        # DFD usa org_id diretamente
        dfd_total = DFD.objects.filter(org_id=org_id).count()
        dfd_dev   = (
            HistoricoTramitacao.objects
            .filter(dfd__org_id=org_id, status_novo='Devolvida')
            .values('dfd').distinct().count()
        )

        etp_total = ETP.objects.filter(org_id=org_id).count()
        etp_dev   = (
            HistoricoETP.objects
            .filter(etp__org_id=org_id, status_novo='Devolvido')
            .values('etp').distinct().count()
        )

        tr_total  = TR.objects.filter(org_id=org_id).count()
        tr_dev    = (
            HistoricoTR.objects
            .filter(tr__org_id=org_id, status_novo='Devolvido')
            .values('tr').distinct().count()
        )

        mapa_total = MapaComparativoPrecos.objects.filter(org_id=org_id).count()
        mapa_dev   = (
            HistoricoMapa.objects
            .filter(mapa__org_id=org_id, status_novo='Devolvido')
            .values('mapa').distinct().count()
        )

        def _por_categoria(qs):
            from django.db.models import Count
            cats = (qs.filter(categoria_motivo__gt='')
                      .values('categoria_motivo')
                      .annotate(total=Count('id'))
                      .order_by('-total'))
            return {c['categoria_motivo']: c['total'] for c in cats}

        def _item(total, devolvidos, por_cat):
            return {
                'total':          total,
                'devolvidos':     devolvidos,
                'taxa_devolucao': _pct(devolvidos, total) if total else 0,
                'por_categoria':  por_cat,
            }

        dfd_cats  = _por_categoria(HistoricoTramitacao.objects.filter(dfd__org_id=org_id, status_novo='Devolvida'))
        etp_cats  = _por_categoria(HistoricoETP.objects.filter(etp__org_id=org_id, status_novo='Devolvido'))
        tr_cats   = _por_categoria(HistoricoTR.objects.filter(tr__org_id=org_id, status_novo='Devolvido'))
        mapa_cats = _por_categoria(HistoricoMapa.objects.filter(mapa__org_id=org_id, status_novo='Devolvido'))

        return Response({
            'DFD':  _item(dfd_total,  dfd_dev,  dfd_cats),
            'ETP':  _item(etp_total,  etp_dev,  etp_cats),
            'TR':   _item(tr_total,   tr_dev,   tr_cats),
            'Mapa': _item(mapa_total, mapa_dev, mapa_cats),
        })


class IndicadoresAgrupamentoView(APIView):
    """
    Sugestão de agrupamento de itens por família SIMPAS.
    Analisa ItemDFD com item_catalogo em DFDs não aprovados, agrupa por família
    e sugere modalidade de aquisição com base no limite de dispensa configurado.

    GET /api/indicadores/agrupamento/
    Parâmetros opcionais: ?familia=42.40  (filtra família específica)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from modulo_demanda.models import ItemDFD
        from core.models import ParametroSistema

        org_id = request.org_id

        # Limite de dispensa configurado
        limite_str = ParametroSistema.get('valor_limite_dispensa_etp', '62000.00')
        try:
            limite_dispensa = Decimal(str(limite_str))
        except Exception:
            limite_dispensa = Decimal('62000.00')

        familia_filtro = request.query_params.get('familia')

        # Busca itens com catálogo vinculado, de DFDs não aprovados
        qs = (
            ItemDFD.objects
            .filter(
                dfd__org_id=org_id,
                item_catalogo__isnull=False,
            )
            .exclude(dfd__status__in=['Aprovada', 'Rejeitada', 'Cancelada'])
            .select_related('item_catalogo__categoria__pai', 'dfd')
        )

        if familia_filtro:
            qs = qs.filter(item_catalogo__familia=familia_filtro)

        # Agrupa por família
        familias: dict = {}
        for item in qs:
            fam = item.item_catalogo.familia or 'Sem família'
            cat = item.item_catalogo.categoria
            cat_path = cat.caminho_completo if cat else None
            if fam not in familias:
                familias[fam] = {
                    'familia':        fam,
                    'categoria_path': cat_path,
                    'total_itens':    0,
                    'valor_total':    Decimal('0'),
                    'dfds_ids':       set(),
                    'itens':          [],
                }
            elif cat_path and not familias[fam]['categoria_path']:
                familias[fam]['categoria_path'] = cat_path
            g = familias[fam]
            g['total_itens']  += 1
            g['valor_total']  += item.valor_total_estimado or Decimal('0')
            g['dfds_ids'].add(item.dfd_id)
            g['itens'].append({
                'item_id':         item.id,
                'catalogo_codigo': item.item_catalogo.codigo_interno,
                'catalogo_nome':   item.item_catalogo.nome,
                'categoria_path':  cat_path,
                'dfd_sei':         item.dfd.numero_sei,
                'dfd_status':      item.dfd.status,
                'quantidade':      float(item.quantidade),
                'valor_total':     float(item.valor_total_estimado or 0),
            })

        resultado = []
        for fam, g in sorted(familias.items()):
            valor = g['valor_total']
            qtd_dfds = len(g['dfds_ids'])
            # Sugestão de modalidade
            if valor > limite_dispensa:
                sugestao    = 'pregao_eletronico'
                sugestao_label = 'Pregão Eletrônico'
                sugestao_motivo = f'Valor total R$ {float(valor):,.2f} supera o limite de dispensa (R$ {float(limite_dispensa):,.2f})'
            elif qtd_dfds > 1:
                sugestao    = 'dispensa_agrupada'
                sugestao_label = 'Dispensa por Valor (agrupada)'
                sugestao_motivo = f'{qtd_dfds} DFDs com itens da mesma família — agrupamento recomendado'
            else:
                sugestao    = 'dispensa_valor'
                sugestao_label = 'Dispensa por Valor'
                sugestao_motivo = f'Valor total R$ {float(valor):,.2f} dentro do limite de dispensa'

            resultado.append({
                'familia':         fam,
                'categoria_path':  g['categoria_path'],
                'total_itens':     g['total_itens'],
                'total_dfds':      qtd_dfds,
                'valor_total':     float(valor),
                'sugestao':        sugestao,
                'sugestao_label':  sugestao_label,
                'sugestao_motivo': sugestao_motivo,
                'itens':           g['itens'],
            })

        return Response({
            'limite_dispensa': float(limite_dispensa),
            'familias':        resultado,
            'total_familias':  len(resultado),
        })


class PlanoComprasView(APIView):
    """
    Relatório de Plano de Compras por família SIMPAS.
    Consolida todos os itens de DFD com catálogo vinculado,
    agrupados por família, com detalhe de itens e sugestão de modalidade.

    GET /api/indicadores/plano-compras/
    Parâmetros opcionais:
      ?exercicio=2026          — filtra por exercício do DFD (via dotação)
      ?status=Rascunho,Aprovada — filtra por status do DFD (default: todos exceto Cancelada/Rejeitada)
      ?familia=42.40            — filtra uma família específica
      ?incluir_executados=true — inclui itens cujo DFD já tem Contrato (por padrão
                                  saem da lista — já foram executados)
      ?export=pdf               — exporta em PDF em vez de retornar JSON (não usar
                                   "format": é reservado pela negociação de conteúdo do DRF)
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import ItemDFD
        from modulo_contrato.models import Contrato
        from core.models import ParametroSistema

        org_id = request.org_id

        limite_str = ParametroSistema.get('valor_limite_dispensa_etp', '62000.00')
        try:
            limite_dispensa = Decimal(str(limite_str))
        except Exception:
            limite_dispensa = Decimal('62000.00')

        # Filtros
        familia_filtro = request.query_params.get('familia')
        status_param   = request.query_params.get('status', '')
        status_list    = [s.strip() for s in status_param.split(',') if s.strip()] if status_param else None
        exercicio      = request.query_params.get('exercicio')
        incluir_executados = request.query_params.get('incluir_executados') == 'true'

        # Base query — itens com catálogo. "Executado" = o DFD do item já tem
        # ao menos um Contrato vinculado (mesma demanda percorreu a cadeia
        # inteira) — por padrão sai da lista de pendências do Plano de Compras
        # para a demanda não ficar eternamente pedindo aquisição já feita.
        qs = ItemDFD.objects.filter(
            dfd__org_id=org_id,
            item_catalogo__isnull=False,
        ).exclude(
            dfd__status__in=['Rejeitada', 'Cancelada']
        ).annotate(
            executado=Exists(Contrato.objects.filter(dfd_id=OuterRef('dfd_id')))
        ).select_related('item_catalogo__categoria__pai', 'dfd__org_id')

        total_itens_executados = qs.filter(executado=True).count()
        if not incluir_executados:
            qs = qs.filter(executado=False)

        if status_list:
            qs = qs.filter(dfd__status__in=status_list)
        if familia_filtro:
            qs = qs.filter(item_catalogo__familia=familia_filtro)

        # Agrupar por família
        familias: dict = {}
        for item in qs:
            fam  = item.item_catalogo.familia or 'Sem família'
            cat = item.item_catalogo.categoria
            cat_path = cat.caminho_completo if cat else None
            if fam not in familias:
                familias[fam] = {
                    'familia':        fam,
                    'categoria_path': cat_path,
                    'total_itens':    0,
                    'qtd_total':      Decimal('0'),
                    'valor_total':    Decimal('0'),
                    'dfds_ids':       set(),
                    'status_counts':  {},
                    'itens':          [],
                }
            elif cat_path and not familias[fam]['categoria_path']:
                familias[fam]['categoria_path'] = cat_path
            g = familias[fam]
            g['total_itens'] += 1
            g['qtd_total']   += item.quantidade
            valor_item = item.quantidade * item.valor_unitario_estimado
            g['valor_total'] += valor_item
            g['dfds_ids'].add(item.dfd_id)
            st = item.dfd.status
            g['status_counts'][st] = g['status_counts'].get(st, 0) + 1
            g['itens'].append({
                'item_id':          item.id,
                'catalogo_codigo':  item.item_catalogo.codigo_interno,
                'catalogo_simpas':  item.item_catalogo.codigo_simpas,
                'catalogo_nome':    item.item_catalogo.nome,
                'categoria_path':   cat_path,
                'unidade_medida':   item.item_catalogo.unidade_medida or item.unidade_medida,
                'dfd_sei':          item.dfd.numero_sei,
                'dfd_status':       item.dfd.status,
                'quantidade':       float(item.quantidade),
                'valor_unitario':   float(item.valor_unitario_estimado),
                'valor_total':      float(valor_item),
                'executado':        item.executado,
            })

        # Consolidar por item dentro da família
        resultado = []
        for fam, g in sorted(familias.items()):
            valor = g['valor_total']
            qtd_dfds = len(g['dfds_ids'])

            # Consolidar itens iguais (mesmo simpas) somando qtd
            itens_consolidados: dict = {}
            for it in g['itens']:
                key = it['catalogo_simpas'] or it['catalogo_codigo']
                if key not in itens_consolidados:
                    itens_consolidados[key] = {
                        **it,
                        'dfds': [it['dfd_sei']],
                        'quantidade_total': it['quantidade'],
                        'valor_total_consolidado': it['valor_total'],
                        # Todos os ItemDFD de origem consolidados nesta linha —
                        # 'item_id' acima é só o primeiro; sem esta lista, o
                        # DFD agrupado criado a partir daqui não teria como
                        # registrar a proveniência dos demais (ver
                        # DFDViewSet.iniciar_de_familia / core.VinculoRastreabilidade).
                        'item_ids': [it['item_id']],
                    }
                else:
                    itens_consolidados[key]['quantidade_total'] += it['quantidade']
                    itens_consolidados[key]['valor_total_consolidado'] += it['valor_total']
                    itens_consolidados[key]['item_ids'].append(it['item_id'])
                    if it['dfd_sei'] not in itens_consolidados[key]['dfds']:
                        itens_consolidados[key]['dfds'].append(it['dfd_sei'])

            # Sugestão de modalidade
            if valor > limite_dispensa:
                sugestao       = 'pregao_eletronico'
                sugestao_label = 'Pregão Eletrônico'
            elif qtd_dfds > 1:
                sugestao       = 'dispensa_agrupada'
                sugestao_label = 'Dispensa Agrupada'
            else:
                sugestao       = 'dispensa_valor'
                sugestao_label = 'Dispensa por Valor'

            resultado.append({
                'familia':            fam,
                'categoria_path':     g['categoria_path'],
                'total_itens':        g['total_itens'],
                'total_dfds':         qtd_dfds,
                'qtd_total':          float(g['qtd_total']),
                'valor_total':        float(valor),
                'status_counts':      g['status_counts'],
                'sugestao':           sugestao,
                'sugestao_label':     sugestao_label,
                'itens_consolidados': list(itens_consolidados.values()),
            })

        # Totais gerais
        total_geral = sum(float(g['valor_total']) for g in familias.values())

        dados = {
            'exercicio':       exercicio,
            'limite_dispensa': float(limite_dispensa),
            'total_familias':  len(resultado),
            'valor_total':     total_geral,
            'familias':        resultado,
            'incluir_executados':     incluir_executados,
            'total_itens_executados': total_itens_executados,
        }

        # Nome do param é "export", não "format" — "format" é reservado pelo DRF
        # (URL_FORMAT_OVERRIDE / negociação de conteúdo) e um valor não reconhecido
        # como renderer (ex: "pdf") faz o DRF responder 404 antes de chegar aqui.
        if request.query_params.get('export') == 'pdf':
            from exportacao.pdf_utils import gerar_pdf_plano_compras, resposta_pdf
            from core.models import Orgao
            orgao = Orgao.objects.filter(pk=org_id).first()
            org_nome  = orgao.nome  if orgao else 'WEBER-E'
            org_sigla = orgao.sigla if orgao else None
            pdf = gerar_pdf_plano_compras(dados, org_nome, org_sigla)
            nome = f'PlanoCompras{"-" + str(exercicio) if exercicio else ""}.pdf'
            return resposta_pdf(pdf, nome)


class IndicadoresReconciliacaoView(APIView):
    """
    Painel de reconciliação de rastreabilidade (épico C-Trace) — audita ativamente
    o que os campos de saldo/vínculo (ItemDFD.quantidade_comprometida/migrada,
    core.VinculoRastreabilidade) não bloqueiam sozinhos, só registram:

    1. `duplicados` — mesmo item de catálogo + mesma unidade demandante presente
       em 2+ DFDs ativos, nenhum deles migrado (status_execucao != 'migrado') nem
       ligado por um VinculoRastreabilidade — candidato a pedido de compra
       duplicado que ninguém percebeu (agrupamento que deveria ter sido feito,
       mas não foi).
    2. `orfaos` — itens com quantidade_comprometida > 0 cujo(s) TR(s) de destino
       só têm Procedimentos Revogados/Anulados (ou tiveram todos cancelados) —
       o item ficou "preso" num comprometimento morto porque nada libera
       automaticamente o saldo quando um Procedimento é revogado/anulado
       (ver ItemLoteTR, sinal em modulo_tr/models.py). Fica invisível até esta
       checagem: o item não aparece mais em nenhuma tela de pendência porque
       "tecnicamente" está comprometido, mas a demanda real segue sem atender.

    GET /api/indicadores/reconciliacao/
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import ItemDFD
        from modulo_licitacao.models import Procedimento

        org_id = request.org_id

        # ── 1. Duplicidade sem vínculo registrado ──────────────────────────
        qs = (
            ItemDFD.objects
            .filter(dfd__org_id=org_id, item_catalogo__isnull=False)
            .exclude(dfd__status__in=['Rejeitada', 'Cancelada'])
            .select_related('item_catalogo', 'dfd__unidade_demandante')
        )
        grupos = {}
        for item in qs:
            if item.status_execucao == 'migrado':
                continue  # já rastreado como origem de um agrupamento — não é duplicidade
            chave = (item.item_catalogo_id, item.dfd.unidade_demandante_id)
            grupos.setdefault(chave, []).append(item)

        duplicados = []
        for (catalogo_id, unidade_id), itens_grupo in grupos.items():
            dfds_distintos = {i.dfd_id for i in itens_grupo}
            if len(dfds_distintos) < 2:
                continue
            duplicados.append({
                'item_catalogo_id':    catalogo_id,
                'catalogo_nome':       itens_grupo[0].item_catalogo.nome,
                'unidade_demandante':  itens_grupo[0].dfd.unidade_demandante.nome
                                        if itens_grupo[0].dfd.unidade_demandante else None,
                'quantidade_total':    float(sum(i.quantidade for i in itens_grupo)),
                'valor_total':         float(sum(i.valor_total_estimado for i in itens_grupo)),
                'itens': [
                    {
                        'item_id':   i.id,
                        'dfd_id':    i.dfd_id,
                        'dfd_sei':   i.dfd.numero_sei,
                        'dfd_status': i.dfd.status,
                        'quantidade': float(i.quantidade),
                        'status_execucao': i.status_execucao,
                    }
                    for i in itens_grupo
                ],
            })
        duplicados.sort(key=lambda d: -d['valor_total'])

        # ── 2. Itens órfãos (comprometidos num Procedimento morto) ─────────
        comprometidos = (
            ItemDFD.objects
            .filter(dfd__org_id=org_id, quantidade_comprometida__gt=0)
            .select_related('dfd')
            .prefetch_related('lotes_tr__lote__tr')
        )
        orfaos = []
        for item in comprometidos:
            tr_ids = {
                lt.lote.tr_id for lt in item.lotes_tr.all()
                if lt.lote.modalidade != 'cota_me_epp'
            }
            if not tr_ids:
                continue
            tem_tr_ativo = False
            for tr_id in tr_ids:
                procs = Procedimento.objects.filter(tr_id=tr_id)
                if not procs.exists():
                    tem_tr_ativo = True  # TR ainda não virou Procedimento — normal, não é órfão
                    break
                if procs.exclude(status__in=['Revogado', 'Anulado']).exists():
                    tem_tr_ativo = True
                    break
            if not tem_tr_ativo:
                orfaos.append({
                    'item_id':   item.id,
                    'objeto':    item.objeto,
                    'dfd_id':    item.dfd_id,
                    'dfd_sei':   item.dfd.numero_sei,
                    'quantidade_comprometida': float(item.quantidade_comprometida),
                    'valor_comprometido':      float(item.quantidade_comprometida * item.valor_unitario_estimado),
                })
        orfaos.sort(key=lambda o: -o['valor_comprometido'])

        return Response({
            'duplicados': duplicados,
            'orfaos':     orfaos,
            'resumo': {
                'total_grupos_duplicados': len(duplicados),
                'valor_total_duplicados':  sum(d['valor_total'] for d in duplicados),
                'total_itens_orfaos':      len(orfaos),
                'valor_total_orfaos':      sum(o['valor_comprometido'] for o in orfaos),
            },
        })

        return Response(dados)
