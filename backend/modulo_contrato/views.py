from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsMultiTenant
from .models import Contrato, Apostila, Aditivo, CronogramaEntrega, Medicao, Pagamento, Notificacao
from .serializers import (
    ContratoSerializer, ApostilaSerializer, AditivoSerializer,
    CronogramaEntregaSerializer, MedicaoSerializer, PagamentoSerializer,
    NotificacaoSerializer,
)

PAPEIS_GESTORES = ['admin', 'gestor_contrato', 'analista', 'ordenador']


class ContratoViewSet(viewsets.ModelViewSet):
    serializer_class   = ContratoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['status', 'exercicio', 'tipo_origem']
    search_fields      = ['numero', 'objeto']
    ordering_fields    = ['exercicio', 'numero', 'created_at']
    ordering           = ['-exercicio', 'numero']

    def get_queryset(self):
        return Contrato.objects.filter(
            org_id=self.request.org_id
        ).select_related(
            'orgao_executor', 'dfd', 'fiscal_contrato', 'gestor_contrato', 'ordenador', 'org_id', 'created_by'
        ).prefetch_related(
            'apostilas', 'aditivos', 'cronograma', 'medicoes__pagamentos', 'pagamentos',
            Prefetch('notificacoes', queryset=Notificacao.objects.select_related('fornecedor')),
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
        serializer = MedicaoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch', 'delete'], url_path=r'medicoes/(?P<medicao_pk>[^/.]+)')
    def medicao_item(self, request, pk=None, medicao_pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        medicao = get_object_or_404(Medicao, pk=medicao_pk, contrato=contrato)
        if request.method == 'DELETE':
            medicao.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = MedicaoSerializer(medicao, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ContratoSerializer(self._reload(contrato), context={'request': request}).data)

    # ── Pagamentos ─────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='pagamentos')
    def add_pagamento(self, request, pk=None):
        contrato = self.get_object()
        self._bloquear_se_encerrado(contrato)
        medicao_id = request.data.get('medicao')
        if medicao_id and not contrato.medicoes.filter(pk=medicao_id).exists():
            return Response({'medicao': 'Medição não pertence a este contrato.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = PagamentoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
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
        serializer = PagamentoSerializer(pagamento, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
