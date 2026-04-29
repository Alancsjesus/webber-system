"""
Endpoints de indicadores para o Dashboard WEBBER.
- GET /api/indicadores/orcamento/   — execução orçamentária por elemento
- GET /api/indicadores/devolucoes/  — taxa de devoluções por tipo de documento
"""
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

        def _item(total, devolvidos):
            return {
                'total':          total,
                'devolvidos':     devolvidos,
                'taxa_devolucao': _pct(devolvidos, total) if total else 0,
            }

        return Response({
            'DFD':  _item(dfd_total,  dfd_dev),
            'ETP':  _item(etp_total,  etp_dev),
            'TR':   _item(tr_total,   tr_dev),
            'Mapa': _item(mapa_total, mapa_dev),
        })
