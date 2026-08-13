"""
Busca global — localiza rapidamente um registro pelo número SEI, número ou objeto,
em qualquer módulo da cadeia de contratação, sem precisar saber em qual lista está.
"""
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

LIMITE_POR_TIPO = 5


def _dfd(qs):
    return [
        {
            'tipo': 'DFD', 'id': o.id,
            'label': o.numero_sei or f'DFD #{o.id}',
            'sublabel': (o.descricao or '')[:80],
            'url': f'/demanda/dfd/{o.id}',
        }
        for o in qs
    ]


def _etp(qs):
    return [
        {
            'tipo': 'ETP', 'id': o.id,
            'label': o.numero_sei or f'ETP #{o.id}',
            'sublabel': (o.dfd.numero_sei if o.dfd_id else '') or '',
            'url': f'/etp/etps/{o.id}',
        }
        for o in qs
    ]


def _tr(qs):
    return [
        {
            'tipo': 'TR', 'id': o.id,
            'label': o.numero_sei or f'TR #{o.id}',
            'sublabel': (o.objeto_contratacao or '')[:80],
            'url': f'/analise-tecnica/trs/{o.id}',
        }
        for o in qs
    ]


def _procedimento(qs):
    return [
        {
            'tipo': 'Procedimento', 'id': o.id,
            'label': o.numero or f'Procedimento #{o.id}',
            'sublabel': (o.objeto or '')[:80],
            'url': f'/licitacao/{o.id}',
        }
        for o in qs
    ]


def _contrato(qs):
    return [
        {
            'tipo': 'Contrato', 'id': o.id,
            'label': o.numero or f'Contrato #{o.id}',
            'sublabel': (o.objeto or '')[:80],
            'url': f'/contratos/{o.id}',
        }
        for o in qs
    ]


def _necessidade(qs):
    return [
        {
            'tipo': 'Necessidade', 'id': o.id,
            'label': o.titulo,
            'sublabel': f'Exercício {o.exercicio_fiscal}',
            'url': f'/planejamento/necessidades/{o.id}',
        }
        for o in qs
    ]


class BuscaGlobalView(APIView):
    """
    GET /api/busca-global/?q=<termo>

    Busca por termo em DFD, ETP, TR, Procedimento, Contrato e Necessidade,
    restrita ao órgão do usuário autenticado. Retorna no máximo 5 resultados
    por tipo, ordenados pelos mais recentes.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if len(q) < 2:
            return Response({'resultados': []})

        org_id = request.org_id
        resultados = []

        from modulo_demanda.models import DFD
        resultados += _dfd(
            DFD.objects.filter(org_id=org_id)
            .filter(Q(numero_sei__icontains=q) | Q(descricao__icontains=q))
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        from modulo_etp.models import ETP
        resultados += _etp(
            ETP.objects.filter(org_id=org_id)
            .filter(Q(numero_sei__icontains=q))
            .select_related('dfd')
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        from modulo_tr.models import TR
        resultados += _tr(
            TR.objects.filter(org_id=org_id)
            .filter(Q(numero_sei__icontains=q) | Q(objeto_contratacao__icontains=q))
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        from modulo_licitacao.models import Procedimento
        resultados += _procedimento(
            Procedimento.objects.filter(org_id=org_id)
            .filter(Q(numero__icontains=q) | Q(objeto__icontains=q))
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        from modulo_contrato.models import Contrato
        resultados += _contrato(
            Contrato.objects.filter(org_id=org_id)
            .filter(Q(numero__icontains=q) | Q(objeto__icontains=q))
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        from modulo_planejamento.models import NecessidadePlanejamento
        resultados += _necessidade(
            NecessidadePlanejamento.objects.filter(org_id=org_id)
            .filter(Q(titulo__icontains=q))
            .order_by('-created_at')[:LIMITE_POR_TIPO]
        )

        return Response({'resultados': resultados})
