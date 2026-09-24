from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsMultiTenant
from .models import Contrato, Apostila, Aditivo, CronogramaEntrega, Medicao, Pagamento, Notificacao
from .serializers import (
    ContratoSerializer, ApostilaSerializer, AditivoSerializer,
    CronogramaEntregaSerializer, MedicaoSerializer, PagamentoSerializer,
    NotificacaoSerializer,
)

PAPEIS_GESTORES = ['admin', 'gestor_contrato', 'analista', 'ordenador']


def _dec(valor):
    from decimal import Decimal
    return Decimal(str(valor if valor not in (None, '') else '0'))


def _validar_ateste(request, contrato, dados, medicao_atual=None):
    """
    Ateste (aprovar/rejeitar medição) é ato do fiscal designado no contrato
    (Lei 14.133, art. 117) — também na criação, senão um POST já "aprovado"
    pulava a exigência de parecer. Retorna campos a gravar junto.
    """
    from datetime import date
    from django.db.models import Sum
    from rest_framework.exceptions import PermissionDenied, ValidationError
    novo = dados.get('status')
    atual = medicao_atual.status if medicao_atual else 'pendente'
    if novo not in ('aprovada', 'rejeitada') or novo == atual:
        return {}
    if contrato.fiscal_contrato_id is None:
        raise ValidationError({'status': 'Designe o fiscal do contrato antes de atestar medições.'})
    if request.user.pk != contrato.fiscal_contrato_id and getattr(request, 'papel', None) != 'admin':
        raise PermissionDenied('Apenas o fiscal designado no contrato pode atestar (aprovar/rejeitar) a medição.')
    parecer = dados.get('parecer_fiscal', medicao_atual.parecer_fiscal if medicao_atual else '')
    if not (parecer or '').strip():
        raise ValidationError({'parecer_fiscal': 'Parecer do fiscal é obrigatório para atestar a medição — atesto sem parecer é irregularidade recorrente em auditorias de execução contratual.'})
    if novo == 'aprovada':
        valor = _dec(dados.get('valor_medido', medicao_atual.valor_medido if medicao_atual else 0))
        outras = contrato.medicoes.filter(status='aprovada')
        if medicao_atual:
            outras = outras.exclude(pk=medicao_atual.pk)
        ja_medido = outras.aggregate(t=Sum('valor_medido'))['t'] or 0
        if ja_medido + valor > contrato.valor_contrato:
            raise ValidationError({'valor_medido': f'Medições aprovadas (R$ {ja_medido + valor:,.2f}) superariam o valor do contrato (R$ {contrato.valor_contrato:,.2f}).'})
    return {'fiscal_responsavel': request.user, 'data_aprovacao': date.today()}


def _validar_pagamento(contrato, dados, pagamento_atual=None):
    """
    Pagamento só após liquidação: medição vinculada e atestada, dentro do valor
    medido; e, havendo DOD aprovada para o DFD do contrato, o nº de empenho
    precisa existir (não cancelado) na execução orçamentária dessa DOD.
    """
    from datetime import date
    from django.db.models import Sum
    from rest_framework.exceptions import ValidationError

    def campo(nome):
        if nome in dados:
            return dados[nome]
        return getattr(pagamento_atual, nome, None) if pagamento_atual else None

    status_novo = campo('status') or 'pendente'
    if status_novo == 'cancelado':
        return {}
    medicao_id = dados.get('medicao', pagamento_atual.medicao_id if pagamento_atual else None)
    medicao = contrato.medicoes.filter(pk=medicao_id).first() if medicao_id else None
    extras = {}
    if medicao is not None:
        outros = medicao.pagamentos.exclude(status='cancelado')
        if pagamento_atual:
            outros = outros.exclude(pk=pagamento_atual.pk)
        ja_pago = outros.aggregate(t=Sum('valor_pago'))['t'] or 0
        valor = _dec(campo('valor_pago'))
        if ja_pago + valor > medicao.valor_medido:
            raise ValidationError({'valor_pago': f'Pagamentos da medição {medicao.numero} (R$ {ja_pago + valor:,.2f}) superariam o valor medido (R$ {medicao.valor_medido:,.2f}).'})
    if status_novo != 'pago':
        return extras
    if medicao is None or medicao.status != 'aprovada':
        raise ValidationError({'medicao': 'Pagamento só pode ser efetivado com medição vinculada e atestada pelo fiscal (liquidação da despesa — Lei 4.320/64, art. 63).'})
    if not campo('numero_nota_fiscal'):
        raise ValidationError({'numero_nota_fiscal': 'Informe a nota fiscal liquidada.'})
    if contrato.dfd_id and contrato.dfd.indicacoes.filter(status='Aprovada').exists():
        from modulo_orcamento.models import EmpenhoOrcamentario
        numero = (campo('numero_empenho') or '').strip()
        existe = EmpenhoOrcamentario.objects.filter(
            indicacao_dotacao__indicacao__dfd_id=contrato.dfd_id,
            indicacao_dotacao__indicacao__status='Aprovada',
            cancelada=False, numero_doc=numero,
        ).exists()
        if not existe:
            raise ValidationError({'numero_empenho': 'Nota de empenho não encontrada (ou cancelada) na execução orçamentária da DOD deste contrato — registre o empenho na Indicação Orçamentária antes de pagar.'})
    if not campo('data_pagamento'):
        extras['data_pagamento'] = date.today()
    return extras


class ContratoViewSet(viewsets.ModelViewSet):
    serializer_class   = ContratoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['status', 'exercicio', 'tipo_origem', 'tipo_instrumento']
    search_fields      = ['numero', 'objeto', 'numero_afm']
    ordering_fields    = ['exercicio', 'numero', 'created_at']
    ordering           = ['-exercicio', 'numero']

    def get_queryset(self):
        from modulo_licitacao.models import ResultadoLote
        from modulo_tr.models import LoteTR

        return Contrato.objects.filter(
            org_id=self.request.org_id
        ).select_related(
            'orgao_executor', 'dfd', 'fiscal_contrato', 'gestor_contrato', 'ordenador', 'org_id', 'created_by'
        ).prefetch_related(
            'apostilas', 'aditivos', 'cronograma', 'medicoes__pagamentos', 'pagamentos',
            Prefetch('notificacoes', queryset=Notificacao.objects.select_related('fornecedor')),
            # cadeia_origem (ContratoSerializer) lê estes dois prefetches via cache —
            # nunca .first()/.filter() no related manager, que ignora o prefetch e
            # gera N+1 (ver feedback_webber_drf_prefetch_nested_actions).
            Prefetch('resultado_licitacao', queryset=ResultadoLote.objects.select_related(
                'procedimento', 'procedimento__tr', 'procedimento__tr__etp', 'procedimento__dfd')),
            Prefetch('lotes', queryset=LoteTR.objects.select_related('tr', 'tr__etp')),
        )

    def perform_update(self, serializer):
        self._bloquear_se_encerrado(serializer.instance)
        serializer.save(updated_by=self.request.user)

    def _reload(self, contrato):
        # get_object() prefetches related sets; após criar/alterar um filho, o cache
        # fica desatualizado. Recarrega para a resposta refletir o estado atual.
        return self.get_queryset().get(pk=contrato.pk)

    # ── Apostilas ──────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='apostilas')
    def add_apostila(self, request, pk=None):
        contrato = self.get_object()
        serializer = ApostilaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'apostilas/(?P<apostila_pk>[^/.]+)')
    def del_apostila(self, request, pk=None, apostila_pk=None):
        contrato = self.get_object()
        apostila = get_object_or_404(Apostila, pk=apostila_pk, contrato=contrato)
        apostila.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # ── Aditivos ───────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='aditivos')
    def add_aditivo(self, request, pk=None):
        contrato = self.get_object()
        serializer = AditivoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        aditivo = serializer.save(contrato=contrato)
        # Atualiza data de vigência se for aditivo de prazo
        if aditivo.tipo == 'prazo' and aditivo.nova_vigencia:
            contrato.data_vigencia_fim = aditivo.nova_vigencia
            contrato.save(update_fields=['data_vigencia_fim'])
        # Atualiza valor se for aditivo de valor
        if aditivo.tipo == 'valor' and aditivo.valor_acrescimo:
            contrato.valor_contrato += aditivo.valor_acrescimo
            contrato.save(update_fields=['valor_contrato'])
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'aditivos/(?P<aditivo_pk>[^/.]+)')
    def del_aditivo(self, request, pk=None, aditivo_pk=None):
        contrato = self.get_object()
        aditivo = get_object_or_404(Aditivo, pk=aditivo_pk, contrato=contrato)
        aditivo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _bloquear_se_encerrado(self, contrato):
        if contrato.status in ('Encerrado', 'Rescindido'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Contratos encerrados ou rescindidos não podem ser editados.')

    # ── Cronograma de Entrega ─────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='cronograma')
    def add_cronograma(self, request, pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        serializer = CronogramaEntregaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'cronograma/(?P<item_pk>[^/.]+)')
    def cronograma_item(self, request, pk=None, item_pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        item = get_object_or_404(CronogramaEntrega, pk=item_pk, contrato=contrato)
        if request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = CronogramaEntregaSerializer(item, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data)

    # ── Medições ───────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='medicoes')
    def add_medicao(self, request, pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        self._validar_aditivo_referencia(contrato, request.data)
        extras = _validar_ateste(request, contrato, request.data)
        serializer = MedicaoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato, **extras)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    def _validar_aditivo_referencia(self, contrato, dados, medicao_atual=None):
        houve_alteracao = dados.get('houve_alteracao_planilha')
        if houve_alteracao is None and medicao_atual is not None:
            houve_alteracao = medicao_atual.houve_alteracao_planilha
        if not houve_alteracao:
            return
        aditivo_id = dados.get('aditivo_referencia')
        if aditivo_id is None and medicao_atual is not None:
            aditivo_id = medicao_atual.aditivo_referencia_id
        if not aditivo_id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'aditivo_referencia': 'Informe o Aditivo que autoriza a alteração de item da planilha — pagar por item substituído sem aditivo formal é "química contratual" (irregularidade grave apontada pelo TCU/TCE, mesmo sem dano ao erário).'})
        if not contrato.aditivos.filter(pk=aditivo_id).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'aditivo_referencia': 'O aditivo informado não pertence a este contrato.'})

    @action(detail=True, methods=['patch', 'delete'], url_path=r'medicoes/(?P<medicao_pk>[^/.]+)')
    def medicao_item(self, request, pk=None, medicao_pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        medicao = get_object_or_404(Medicao, pk=medicao_pk, contrato=contrato)
        if request.method == 'DELETE':
            medicao.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if (medicao.status == 'aprovada' and request.data.get('status', 'aprovada') != 'aprovada'
                and medicao.pagamentos.exclude(status='cancelado').exists()):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'status': 'Medição com pagamento registrado não pode perder o ateste — cancele o pagamento antes.'})
        extras = _validar_ateste(request, contrato, request.data, medicao_atual=medicao)
        self._validar_aditivo_referencia(contrato, request.data, medicao_atual=medicao)
        serializer = MedicaoSerializer(medicao, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(**extras)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data)

    # ── Pagamentos ─────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='pagamentos')
    def add_pagamento(self, request, pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        medicao_id = request.data.get('medicao')
        if medicao_id and not contrato.medicoes.filter(pk=medicao_id).exists():
            return Response({'medicao': 'Medição não pertence a este contrato.'}, status=status.HTTP_400_BAD_REQUEST)
        extras = _validar_pagamento(contrato, request.data)
        serializer = PagamentoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato, **extras)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'pagamentos/(?P<pagamento_pk>[^/.]+)')
    def pagamento_item(self, request, pk=None, pagamento_pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        pagamento = get_object_or_404(Pagamento, pk=pagamento_pk, contrato=contrato)
        if request.method == 'DELETE':
            pagamento.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        medicao_id = request.data.get('medicao')
        if medicao_id and not contrato.medicoes.filter(pk=medicao_id).exists():
            return Response({'medicao': 'Medição não pertence a este contrato.'}, status=status.HTTP_400_BAD_REQUEST)
        extras = _validar_pagamento(contrato, request.data, pagamento_atual=pagamento)
        serializer = PagamentoSerializer(pagamento, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(**extras)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data)

    # ── Notificações ───────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='notificacoes')
    def add_notificacao(self, request, pk=None):
        contrato = self.get_object()
        serializer = NotificacaoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'notificacoes/(?P<notificacao_pk>[^/.]+)')
    def notificacao_item(self, request, pk=None, notificacao_pk=None):
        contrato = self.get_object()
        notificacao = get_object_or_404(Notificacao, pk=notificacao_pk, contrato=contrato)
        if request.method == 'DELETE':
            notificacao.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = NotificacaoSerializer(notificacao, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data)

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        from exportacao.pdf_utils import gerar_pdf_contrato, resposta_pdf
        contrato = self.get_object()
        pdf = gerar_pdf_contrato(contrato)
        return resposta_pdf(pdf, f'Contrato_{contrato.numero}.pdf')


class NotificacaoViewSet(viewsets.ModelViewSet):
    """
    Lista cruzada de Notificações de vários contratos ao mesmo tempo —
    contraparte direta da planilha de controle usada hoje. Criar/editar uma
    notificação de um contrato específico também é possível pelas actions
    aninhadas em ContratoViewSet (notificacoes/notificacoes/<id>).
    """
    serializer_class   = NotificacaoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['status', 'categoria_objeto', 'tipo_acao', 'exercicio', 'contrato']
    search_fields      = [
        'numero', 'resumo_fato', 'numero_processo_sei',
        'numero_sei_comunicacao', 'numero_sei_notificacao',
        'contrato__numero', 'contrato__fornecedor__nome_razao_social',
        'fornecedor__nome_razao_social', 'fornecedor__documento',
    ]
    ordering_fields    = ['exercicio', 'numero', 'data_notificacao', 'created_at']
    ordering           = ['-exercicio', '-created_at']

    def get_queryset(self):
        return Notificacao.objects.filter(
            contrato__org_id=self.request.org_id
        ).select_related('contrato', 'contrato__fornecedor', 'contrato__orgao_executor', 'fornecedor')

    def perform_create(self, serializer):
        contrato = serializer.validated_data.get('contrato')
        if not contrato:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'contrato': 'Campo obrigatório.'})
        if contrato.org_id_id != self.request.org_id:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Contrato não pertence a este órgão.')
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class PainelContratosView(APIView):
    """
    Painel gerencial da área de Contratos: visão rápida de controle —
    quantos contratos existem por status, quanto já foi medido/pago, quais
    vencem em breve, e como as Notificações Contratuais se distribuem entre
    eles (contagem por contrato + apanhado cronológico). Não substitui as
    listas detalhadas (ContratoViewSet/NotificacaoViewSet), é a visão de topo.

    GET /api/contratos/painel/
    Parâmetros opcionais: ?exercicio=... ?status=... (filtram os CONTRATOS
    considerados; a agregação de notificações segue os mesmos contratos)
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]
    LIMITE_DIAS_VENCIMENTO = 60

    def get(self, request):
        from decimal import Decimal

        contratos_qs = Contrato.objects.filter(org_id=request.org_id).select_related('fornecedor').prefetch_related(
            'medicoes', 'pagamentos', 'notificacoes',
        )
        params = request.query_params
        if params.get('exercicio'):
            contratos_qs = contratos_qs.filter(exercicio=params['exercicio'])
        if params.get('status'):
            contratos_qs = contratos_qs.filter(status=params['status'])

        contratos = list(contratos_qs)
        hoje = timezone.localdate()

        totais_status = {codigo: 0 for codigo, _ in Contrato.STATUS_CHOICES}
        valor_total_contratado = Decimal('0')
        valor_medido_total = Decimal('0')
        valor_pago_total = Decimal('0')
        vencendo_em_breve = []
        por_contrato = []
        todas_notificacoes = []

        for c in contratos:
            totais_status[c.status] = totais_status.get(c.status, 0) + 1
            valor_total_contratado += c.valor_contrato
            medido = sum((m.valor_medido for m in c.medicoes.all() if m.status == 'aprovada'), Decimal('0'))
            pago = sum((p.valor_pago for p in c.pagamentos.all() if p.status == 'pago'), Decimal('0'))
            valor_medido_total += medido
            valor_pago_total += pago

            notifs = list(c.notificacoes.all())
            todas_notificacoes.extend(notifs)

            if c.status == 'Vigente' and c.data_vigencia_fim:
                dias_restantes = (c.data_vigencia_fim - hoje).days
                if 0 <= dias_restantes <= self.LIMITE_DIAS_VENCIMENTO:
                    vencendo_em_breve.append({
                        'contrato_id': c.id, 'numero': c.numero,
                        'fornecedor_nome': c.fornecedor.nome_razao_social if c.fornecedor_id else None,
                        'data_vigencia_fim': c.data_vigencia_fim, 'dias_restantes': dias_restantes,
                    })

            por_contrato.append({
                'contrato_id': c.id,
                'numero': c.numero,
                'objeto': c.objeto,
                'status': c.status,
                'fornecedor_nome': c.fornecedor.nome_razao_social if c.fornecedor_id else None,
                'valor_contrato': c.valor_contrato,
                'saldo_a_pagar': medido - pago,
                'data_vigencia_fim': c.data_vigencia_fim,
                'notificacoes_total': len(notifs),
                'notificacoes_andamento': sum(1 for n in notifs if n.status == 'andamento'),
                'notificacoes_cpa': sum(1 for n in notifs if n.status == 'cpa'),
                'notificacoes_concluido': sum(1 for n in notifs if n.status == 'concluido'),
                'rescisoes_total': sum(1 for n in notifs if n.tipo_acao == 'rescisao'),
            })

        vencendo_em_breve.sort(key=lambda v: v['dias_restantes'])
        # Contratos com notificações (principalmente as em CPA) primeiro — é o que pede atenção.
        por_contrato.sort(key=lambda g: (-g['notificacoes_cpa'], -g['notificacoes_total'], g['numero']))

        totais_notificacoes = {
            'total': len(todas_notificacoes),
            'andamento': sum(1 for n in todas_notificacoes if n.status == 'andamento'),
            'cpa': sum(1 for n in todas_notificacoes if n.status == 'cpa'),
            'concluido': sum(1 for n in todas_notificacoes if n.status == 'concluido'),
            'notificacoes': sum(1 for n in todas_notificacoes if n.tipo_acao == 'notificacao'),
            'rescisoes': sum(1 for n in todas_notificacoes if n.tipo_acao == 'rescisao'),
            'contratos_afetados': len({n.contrato_id for n in todas_notificacoes}),
        }

        contrato_por_id = {c.id: c for c in contratos}
        timeline_ordenada = sorted(
            todas_notificacoes,
            key=lambda n: n.data_notificacao or n.created_at.date(),
            reverse=True,
        )[:15]
        timeline_notificacoes = [{
            'id': n.id,
            'numero': n.numero,
            'tipo_acao': n.tipo_acao,
            'tipo_acao_display': n.get_tipo_acao_display(),
            'status': n.status,
            'status_display': n.get_status_display(),
            'contrato_id': n.contrato_id,
            'contrato_numero': contrato_por_id[n.contrato_id].numero,
            'fornecedor_nome': n.fornecedor.nome_razao_social if n.fornecedor_id else (
                contrato_por_id[n.contrato_id].fornecedor.nome_razao_social
                if contrato_por_id[n.contrato_id].fornecedor_id else None),
            'resumo_fato': n.resumo_fato,
            'data': n.data_notificacao or n.created_at.date(),
        } for n in timeline_ordenada]

        return Response({
            'totais_contratos': {
                'total': len(contratos),
                **totais_status,
                'valor_total_contratado': valor_total_contratado,
                'valor_medido_total': valor_medido_total,
                'valor_pago_total': valor_pago_total,
                'saldo_a_pagar_total': valor_medido_total - valor_pago_total,
            },
            'vencendo_em_breve': vencendo_em_breve,
            'totais_notificacoes': totais_notificacoes,
            'por_contrato': por_contrato,
            'timeline_notificacoes': timeline_notificacoes,
        })
