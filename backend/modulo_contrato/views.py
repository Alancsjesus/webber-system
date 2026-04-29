from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsMultiTenant
from .models import Contrato, Apostila, Aditivo
from .serializers import ContratoSerializer, ApostilaSerializer, AditivoSerializer

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
        ).prefetch_related('apostilas', 'aditivos')

    def perform_update(self, serializer):
        if serializer.instance.status in ('Encerrado', 'Rescindido'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Contratos encerrados ou rescindidos não podem ser editados.')
        serializer.save(updated_by=self.request.user)

    # ── Apostilas ──────────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='apostilas')
    def add_apostila(self, request, pk=None):
        contrato = self.get_object()
        serializer = ApostilaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(contrato=contrato)
        return Response(ContratoSerializer(contrato, context={'request': request}).data,
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
        return Response(ContratoSerializer(contrato, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'aditivos/(?P<aditivo_pk>[^/.]+)')
    def del_aditivo(self, request, pk=None, aditivo_pk=None):
        contrato = self.get_object()
        aditivo = get_object_or_404(Aditivo, pk=aditivo_pk, contrato=contrato)
        aditivo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
