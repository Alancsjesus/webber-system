"""
GET /api/calendario/
Agrega eventos de contratação do órgão em uma linha do tempo.

Parâmetros de query:
  ano  (int)  — exercício fiscal; default: ano corrente
  mes  (int)  — opcional, filtra apenas esse mês (1-12)
  tipo (str)  — 'procedimento' | 'contrato' | 'necessidade' | 'dfd' | 'execucao' | omitir para todos
"""
from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant


def _urgencia(dias):
    """Classifica dias restantes até o prazo em 3 níveis — None = fora de destaque."""
    if dias is None:
        return None
    if dias < 0:
        return 'vencido'
    if dias <= 15:
        return 'urgente'
    if dias <= 30:
        return 'atencao'
    return None


CORES_URGENCIA = {'vencido': '#DC3545', 'urgente': '#FD7E14', 'atencao': '#FFC107'}


class CalendarioContratacaoView(APIView):
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_licitacao.models import Procedimento
        from modulo_contrato.models import Contrato, CronogramaEntrega, Pagamento
        from modulo_planejamento.models import NecessidadePlanejamento
        from modulo_demanda.models import DFD

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
                        'urgencia':   None,
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
                dias      = (c.data_vigencia_fim - hoje).days
                urgencia  = _urgencia(dias)
                eventos.append({
                    'id':         f'cont-{c.pk}',
                    'tipo':       'contrato',
                    'subtipo':    'vencimento',
                    'titulo':     f'Vencimento: {c.numero}',
                    'descricao':  c.objeto[:80] if c.objeto else '',
                    'data':       c.data_vigencia_fim.isoformat(),
                    'cor':        CORES_URGENCIA.get(urgencia, '#6C757D'),
                    'link':       f'/contratos/{c.pk}',
                    'status':     c.status,
                    'modalidade': '',
                    'urgencia':   urgencia,
                    'alerta':     urgencia is not None,
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
                    'urgencia':   None,
                    'alerta':     False,
                })

        # ── DFD — prazo de necessidade (pendente) ─────────────────────────────
        if not tipo_filtro or tipo_filtro == 'dfd':
            qs_d = DFD.objects.filter(
                org_id=org_id,
                prazo_necessidade__isnull=False,
            ).exclude(status__in=['Aprovada', 'Rejeitada'])
            if mes:
                qs_d = qs_d.filter(prazo_necessidade__month=mes)
            else:
                qs_d = qs_d.filter(prazo_necessidade__year=ano)

            for d in qs_d.only('id', 'numero_sei', 'descricao', 'status', 'prazo_necessidade'):
                dias     = (d.prazo_necessidade - hoje).days
                urgencia = _urgencia(dias)
                eventos.append({
                    'id':         f'dfd-{d.pk}',
                    'tipo':       'dfd',
                    'subtipo':    'prazo_necessidade',
                    'titulo':     f'Prazo DFD: {d.numero_sei}',
                    'descricao':  d.descricao[:80] if d.descricao else '',
                    'data':       d.prazo_necessidade.isoformat(),
                    'cor':        CORES_URGENCIA.get(urgencia, '#0DCAF0'),
                    'link':       f'/demanda/dfd/{d.pk}',
                    'status':     d.status,
                    'modalidade': '',
                    'urgencia':   urgencia,
                    'alerta':     urgencia is not None,
                    'dias_restantes': dias,
                })

        # ── Execução de Contrato — entregas e pagamentos pendentes (C1) ────────
        if not tipo_filtro or tipo_filtro == 'execucao':
            qs_ce = CronogramaEntrega.objects.filter(
                org_id=org_id,
                data_realizada__isnull=True,
                data_prevista__isnull=False,
            ).select_related('contrato')
            if mes:
                qs_ce = qs_ce.filter(data_prevista__month=mes)
            else:
                qs_ce = qs_ce.filter(data_prevista__year=ano)

            for ce in qs_ce.only('id', 'numero', 'descricao', 'data_prevista',
                                  'contrato__id', 'contrato__numero'):
                dias     = (ce.data_prevista - hoje).days
                urgencia = _urgencia(dias)
                eventos.append({
                    'id':         f'entrega-{ce.pk}',
                    'tipo':       'execucao',
                    'subtipo':    'entrega',
                    'titulo':     f'Entrega {ce.numero}: {ce.contrato.numero}',
                    'descricao':  ce.descricao[:80] if ce.descricao else '',
                    'data':       ce.data_prevista.isoformat(),
                    'cor':        CORES_URGENCIA.get(urgencia, '#20C997'),
                    'link':       f'/contratos/{ce.contrato_id}',
                    'status':     'pendente',
                    'modalidade': '',
                    'urgencia':   urgencia,
                    'alerta':     urgencia is not None,
                    'dias_restantes': dias,
                })

            qs_pg = Pagamento.objects.filter(
                org_id=org_id,
                data_pagamento__isnull=True,
                data_vencimento__isnull=False,
            ).select_related('contrato')
            if mes:
                qs_pg = qs_pg.filter(data_vencimento__month=mes)
            else:
                qs_pg = qs_pg.filter(data_vencimento__year=ano)

            for pg in qs_pg.only('id', 'numero', 'valor_pago', 'data_vencimento',
                                  'contrato__id', 'contrato__numero'):
                dias     = (pg.data_vencimento - hoje).days
                urgencia = _urgencia(dias)
                eventos.append({
                    'id':         f'pagamento-{pg.pk}',
                    'tipo':       'execucao',
                    'subtipo':    'pagamento',
                    'titulo':     f'Pagamento {pg.numero}: {pg.contrato.numero}',
                    'descricao':  f'R$ {pg.valor_pago:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'),
                    'data':       pg.data_vencimento.isoformat(),
                    'cor':        CORES_URGENCIA.get(urgencia, '#6610F2'),
                    'link':       f'/contratos/{pg.contrato_id}',
                    'status':     'pendente',
                    'modalidade': '',
                    'urgencia':   urgencia,
                    'alerta':     urgencia is not None,
                    'dias_restantes': dias,
                })

        eventos.sort(key=lambda e: e['data'])

        return Response({
            'ano':           ano,
            'mes':           mes,
            'total_eventos': len(eventos),
            'eventos':       eventos,
        })
