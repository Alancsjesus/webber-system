import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import Orgao
from core.permissions import IsMultiTenant
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_planejamento.serializers import NecessidadeSerializer

logger = logging.getLogger(__name__)

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

    def _get_necessidade_autorizada(self, necessidade_id, org_id):
        """Retorna a necessidade se pertencer ao próprio órgão ou a um filho."""
        child_ids = Orgao.objects.filter(parent_id=org_id).values_list('id', flat=True)
        return get_object_or_404(
            NecessidadePlanejamento,
            id=necessidade_id,
            org_id__in=[org_id, *child_ids],
        )

    @action(detail=True, methods=['post'], url_path='vincular-necessidade')
    def vincular_necessidade(self, request, pk=None):
        dotacao = self.get_object()
        serializer = VincularNecessidadeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        necessidade_id = serializer.validated_data['necessidade_id']
        necessidade = self._get_necessidade_autorizada(necessidade_id, request.org_id)
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
        necessidade = self._get_necessidade_autorizada(necessidade_id, request.org_id)
        dotacao.necessidades.remove(necessidade)
        return Response(
            {'detail': f'Necessidade "{necessidade.titulo}" desvinculada com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='necessidades-disponiveis')
    def necessidades_disponiveis(self, request, pk=None):
        dotacao = self.get_object()
        org_id  = request.org_id
        exercicio = dotacao.exercicio_fiscal
        vinculadas_ids = list(dotacao.necessidades.values_list('id', flat=True))

        # Órgãos filhos cujas necessidades externas o órgão pai pode incluir no plano
        child_ids = Orgao.objects.filter(parent_id=org_id).values_list('id', flat=True)

        # Base: necessidades próprias + necessidades externas de filhos
        base_qs = NecessidadePlanejamento.objects.filter(
            Q(org_id=org_id) |
            Q(org_id__in=child_ids, tipo_execucao='externa')
        ).distinct()

        # ── contagens por etapa para diagnóstico ──────────────────────────
        todas       = base_qs
        mesmo_exerc = todas.filter(exercicio_fiscal=exercicio)
        status_ok   = mesmo_exerc.filter(status__in=('Aprovada', 'DFD Criado'))
        disponiveis = status_ok.exclude(id__in=vinculadas_ids)

        total_org    = todas.count()
        total_exerc  = mesmo_exerc.count()
        total_status = status_ok.count()
        total_disp   = disponiveis.count()

        logger.info(
            "[necessidades-disponiveis] dotacao=%s org=%s filhos=%s exercicio=%s | "
            "visíveis=%d exercicio=%d status_ok=%d disponiveis=%d vinculadas=%d",
            dotacao.pk, org_id, list(child_ids), exercicio,
            total_org, total_exerc, total_status, total_disp, len(vinculadas_ids),
        )

        # ── resposta vazia com diagnóstico em linguagem natural ───────────
        if total_disp == 0:
            tem_filhos = len(list(child_ids)) > 0
            escopo = "neste órgão ou em órgãos subordinados" if tem_filhos else "neste órgão"

            if total_org == 0:
                motivo = (
                    f"Nenhuma necessidade de planejamento encontrada {escopo}. "
                    "Cadastre e aprove necessidades antes de vinculá-las à dotação."
                )
            elif total_exerc == 0:
                outros = list(todas.values_list('exercicio_fiscal', flat=True).distinct())
                motivo = (
                    f"Existem {total_org} necessidade(s) visível(is), mas nenhuma está "
                    f"cadastrada para o exercício fiscal {exercicio} desta dotação. "
                    f"Exercícios encontrados: {outros or 'nenhum'}."
                )
            elif total_status == 0:
                status_encontrados = list(mesmo_exerc.values_list('status', flat=True).distinct())
                motivo = (
                    f"Existem {total_exerc} necessidade(s) para o exercício {exercicio}, "
                    f"mas nenhuma está com status 'Aprovada' ou 'DFD Criado'. "
                    f"Status atuais: {status_encontrados}. "
                    "Aprove as necessidades no módulo de planejamento antes de vinculá-las."
                )
            else:
                motivo = (
                    f"As {total_status} necessidade(s) elegíveis já estão vinculadas a esta dotação."
                )

            logger.warning("[necessidades-disponiveis] lista vazia — %s", motivo)
            return Response({'results': [], 'diagnostico': motivo})

        serializer = NecessidadeSerializer(disponiveis, many=True, context={'request': request})
        return Response(serializer.data)
