"""
Endpoints de indicadores para o Dashboard WEBBER.
- GET /api/indicadores/orcamento/    — execução orçamentária por elemento
- GET /api/indicadores/devolucoes/   — taxa de devoluções por tipo de documento
- GET /api/indicadores/agrupamento/  — sugestão de agrupamento por família SIMPAS
"""
from decimal import Decimal
from django.db.models import Sum, Count, Q
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
            .select_related('item_catalogo', 'dfd')
        )

        if familia_filtro:
            qs = qs.filter(item_catalogo__familia=familia_filtro)

        # Agrupa por família
        familias: dict = {}
        for item in qs:
            fam = item.item_catalogo.familia or 'Sem família'
            if fam not in familias:
                familias[fam] = {
                    'familia':        fam,
                    'total_itens':    0,
                    'valor_total':    Decimal('0'),
                    'dfds_ids':       set(),
                    'itens':          [],
                }
            g = familias[fam]
            g['total_itens']  += 1
            g['valor_total']  += item.valor_total_estimado or Decimal('0')
            g['dfds_ids'].add(item.dfd_id)
            g['itens'].append({
                'item_id':        item.id,
                'catalogo_codigo': item.item_catalogo.codigo_interno,
                'catalogo_nome':   item.item_catalogo.nome,
                'dfd_sei':        item.dfd.numero_sei,
                'dfd_status':     item.dfd.status,
                'quantidade':     float(item.quantidade),
                'valor_total':    float(item.valor_total_estimado or 0),
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
