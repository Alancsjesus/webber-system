"""
GET /api/calendario/
Agrega eventos de contratação do órgão em uma linha do tempo.

Parâmetros de query:
  ano  (int)  — exercício fiscal; default: ano corrente
  mes  (int)  — opcional, filtra apenas esse mês (1-12)
  tipo (str)  — 'procedimento' | 'contrato' | 'necessidade' | omitir para todos
"""
from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


class CalendarioContratacaoView(APIView):
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_licitacao.models import Procedimento
        from modulo_contrato.models import Contrato
        from modulo_planejamento.models import NecessidadePlanejamento

        org_id = request.org_id
        hoje   = date.today()

        try:
            ano = int(request.query_params.get('ano', hoje.year))
        except (ValueError, TypeError):
            ano = hoje.year

        try:
            mes = int(request.query_params.get('mes', 0)) or None
        except (ValueError, TypeError):
            mes = None

        tipo_filtro = request.query_params.get('tipo', '')

        eventos = []

        # ── Procedimentos ────────────────────────────────────────────────────
        if not tipo_filtro or tipo_filtro == 'procedimento':
            qs = Procedimento.objects.filter(org_id=org_id, exercicio=ano)
            if mes:
                from django.db.models import Q
                qs = qs.filter(
                    Q(data_publicacao__month=mes) |
                    Q(data_abertura__month=mes)   |
                    Q(data_homologacao__month=mes)
                )

            marcos = [
                ('data_publicacao',  'Publicação',   '#1351B4'),
                ('data_abertura',    'Abertura',     '#155724'),
                ('data_homologacao', 'Homologação',  '#856404'),
            ]
            for p in qs.only('id', 'numero', 'status', 'modalidade',
                             'objeto', 'data_publicacao', 'data_abertura',
                             'data_homologacao'):
                for campo, label, cor in marcos:
                    data_ev = getattr(p, campo)
                    if not data_ev:
                        continue
                    if mes and data_ev.month != mes:
                        continue
                    eventos.append({
                        'id':         f'proc-{p.pk}-{campo}',
                        'tipo':       'procedimento',
                        'subtipo':    campo,
                        'titulo':     f'{label}: {p.numero}',
                        'descricao':  p.objeto[:80] if p.objeto else '',
                        'data':       data_ev.isoformat(),
                        'cor':        cor,
                        'link':       f'/licitacao/{p.pk}',
                        'status':     p.status,
                        'modalidade': p.get_modalidade_display(),
                        'alerta':     False,
                    })

        # ── Contratos — vencimentos ───────────────────────────────────────────
        if not tipo_filtro or tipo_filtro == 'contrato':
            qs_c = Contrato.objects.filter(
                org_id=org_id,
                status__in=['Vigente', 'Suspenso'],
                data_vigencia_fim__isnull=False,
            )
            if mes:
                qs_c = qs_c.filter(data_vigencia_fim__month=mes)
            else:
                qs_c = qs_c.filter(data_vigencia_fim__year=ano)

            for c in qs_c.only('id', 'numero', 'objeto', 'status',
                                'data_vigencia_fim', 'exercicio'):
                dias = (c.data_vigencia_fim - hoje).days
                alerta = dias <= 30
                cor = '#DC3545' if alerta else '#6C757D'
                eventos.append({
                    'id':         f'cont-{c.pk}',
                    'tipo':       'contrato',
                    'subtipo':    'vencimento',
                    'titulo':     f'Vencimento: {c.numero}',
                    'descricao':  c.objeto[:80] if c.objeto else '',
                    'data':       c.data_vigencia_fim.isoformat(),
                    'cor':        cor,
                    'link':       f'/contratos/{c.pk}',
                    'status':     c.status,
                    'modalidade': '',
                    'alerta':     alerta,
                    'dias_restantes': dias,
                })

        # ── Necessidades — prazo desejado ─────────────────────────────────────
        if not tipo_filtro or tipo_filtro == 'necessidade':
            qs_n = NecessidadePlanejamento.objects.filter(
                org_id=org_id,
                exercicio_fiscal=ano,
                status__in=['Aprovada', 'DFD Criado'],
                prazo_desejado__isnull=False,
            )
            if mes:
                qs_n = qs_n.filter(prazo_desejado__month=mes)

            for n in qs_n.only('id', 'titulo', 'status', 'prazo_desejado',
                                'valor_estimado'):
                eventos.append({
                    'id':         f'nec-{n.pk}',
                    'tipo':       'necessidade',
                    'subtipo':    'prazo',
                    'titulo':     f'Prazo: {n.titulo[:50]}',
                    'descricao':  n.titulo,
                    'data':       n.prazo_desejado.isoformat(),
                    'cor':        '#6F42C1',
                    'link':       f'/planejamento/necessidades/{n.pk}',
                    'status':     n.status,
                    'modalidade': '',
                    'alerta':     False,
                })

        eventos.sort(key=lambda e: e['data'])

        return Response({
            'ano':           ano,
            'mes':           mes,
            'total_eventos': len(eventos),
            'eventos':       eventos,
        })
