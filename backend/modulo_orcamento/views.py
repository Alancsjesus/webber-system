from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from core.permissions import IsMultiTenant
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_planejamento.serializers import NecessidadeSerializer

from .filters import AcaoOrcamentariaFilter, FonteRecursoFilter, DotacaoOrcamentariaFilter
from .models import AcaoOrcamentaria, ElementoDespesa, FonteRecurso, DotacaoOrcamentaria
from .serializers import (
    AcaoOrcamentariaSerializer,
    ElementoDespesaSerializer,
    FonteRecursoSerializer,
    DotacaoOrcamentariaSerializer,
    VincularNecessidadeSerializer,
)


class AcaoOrcamentariaViewSet(viewsets.ModelViewSet):
    serializer_class = AcaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AcaoOrcamentariaFilter
    search_fields = ['codigo', 'nome', 'descricao']
    ordering_fields = ['codigo', 'nome', 'tipo', 'created_at']
    ordering = ['codigo']

    def get_queryset(self):
        return AcaoOrcamentaria.objects.filter(org_id=self.request.org_id)


class ElementoDespesaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Global expense elements — standardized by law, read-only via API.
    Populated via management command.
    """
    serializer_class = ElementoDespesaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['codigo']
    ordering = ['codigo']

    def get_queryset(self):
        return ElementoDespesa.objects.filter(ativo=True)


class FonteRecursoViewSet(viewsets.ModelViewSet):
    serializer_class = FonteRecursoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FonteRecursoFilter
    search_fields = ['nome', 'codigo']
    ordering_fields = ['codigo', 'nome', 'tipo']
    ordering = ['codigo']

    def get_queryset(self):
        return FonteRecurso.objects.filter(org_id=self.request.org_id)


class DotacaoOrcamentariaViewSet(viewsets.ModelViewSet):
    serializer_class = DotacaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DotacaoOrcamentariaFilter
    search_fields = ['eixo', 'objetivo_estrategico', 'observacoes', 'acao__nome', 'acao__codigo']
    ordering_fields = ['exercicio_fiscal', 'valor_dotado', 'status', 'created_at']
    ordering = ['-exercicio_fiscal', 'acao__codigo']

    def get_queryset(self):
        return DotacaoOrcamentaria.objects.filter(
            org_id=self.request.org_id
        ).select_related('acao', 'elemento_despesa', 'fonte_recurso')

    @action(detail=True, methods=['post'], url_path='vincular-necessidade')
    def vincular_necessidade(self, request, pk=None):
        dotacao = self.get_object()
        serializer = VincularNecessidadeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        necessidade_id = serializer.validated_data['necessidade_id']
        necessidade = get_object_or_404(
            NecessidadePlanejamento,
            id=necessidade_id,
            org_id=request.org_id,
        )
        dotacao.necessidades.add(necessidade)
        return Response(
            {'detail': f'Necessidade "{necessidade.titulo}" vinculada com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='desvincular-necessidade')
    def desvincular_necessidade(self, request, pk=None):
        dotacao = self.get_object()
        serializer = VincularNecessidadeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        necessidade_id = serializer.validated_data['necessidade_id']
        necessidade = get_object_or_404(
            NecessidadePlanejamento,
            id=necessidade_id,
            org_id=request.org_id,
        )
        dotacao.necessidades.remove(necessidade)
        return Response(
            {'detail': f'Necessidade "{necessidade.titulo}" desvinculada com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='necessidades-disponiveis')
    def necessidades_disponiveis(self, request, pk=None):
        dotacao = self.get_object()
        vinculadas_ids = dotacao.necessidades.values_list('id', flat=True)
        disponiveis = NecessidadePlanejamento.objects.filter(
            org_id=request.org_id,
            exercicio_fiscal=dotacao.exercicio_fiscal,
            status='Aprovada',
        ).exclude(id__in=vinculadas_ids)
        serializer = NecessidadeSerializer(disponiveis, many=True, context={'request': request})
        return Response(serializer.data)
