from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Fornecedor, FornecedorFamilia
from .serializers import FornecedorSerializer, FornecedorFamiliaSerializer

PAPEIS_GERENCIAM_FORNECEDOR = ('admin', 'analista', 'gestor_contrato', 'ordenador')


def _check_permissao(request):
    if getattr(request, 'papel', None) not in PAPEIS_GERENCIAM_FORNECEDOR:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Apenas Analista, Gestor de Contrato, Ordenador ou Admin podem gerenciar fornecedores.')


class FornecedorViewSet(viewsets.ModelViewSet):
    serializer_class = FornecedorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['documento', 'nome_razao_social', 'nome_fantasia']
    ordering_fields = ['nome_razao_social', 'documento', 'created_at']
    ordering = ['nome_razao_social']

    def get_queryset(self):
        qs = Fornecedor.objects.all()
        ativos = self.request.query_params.get('ativos')
        if ativos == 'true':
            qs = qs.filter(ativo=True)
        familia = self.request.query_params.get('familia')
        if familia:
            qs = qs.filter(familias__familia_simpas=familia)
        return qs.distinct()

    def perform_create(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao(self.request)
        instance.ativo = False
        instance.save()

    # ── Famílias SIMPAS vinculadas ──────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='familias')
    def familias(self, request, pk=None):
        fornecedor = self.get_object()
        if request.method == 'POST':
            _check_permissao(request)
            serializer = FornecedorFamiliaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(fornecedor=fornecedor)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        qs = fornecedor.familias.all()
        return Response(FornecedorFamiliaSerializer(qs, many=True).data)

    @action(detail=True, methods=['delete'], url_path='familias/(?P<familia_pk>[^/.]+)')
    def familia_detail(self, request, pk=None, familia_pk=None):
        _check_permissao(request)
        fornecedor = self.get_object()
        fam = get_object_or_404(FornecedorFamilia, pk=familia_pk, fornecedor=fornecedor)
        fam.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):
        """
        Agrega todo o histórico de relação do fornecedor com a administração:
        cotações, resultados de licitação e contratos.
        """
        fornecedor = self.get_object()

        cotacoes = [
            {
                'id': r.id,
                'mapa_id': r.solicitacao.mapa_id,
                'familia_simpas': r.solicitacao.familia_simpas,
                'data_resposta': r.data_resposta,
                'recusou': r.recusou,
                'valor_respondido': r.valor_respondido,
            }
            for r in fornecedor.respostas_cotacao.select_related('solicitacao').order_by('-data_resposta')
        ]

        resultados_licitacao = [
            {
                'id': r.id,
                'procedimento_id': r.procedimento_id,
                'procedimento_numero': r.procedimento.numero,
                'resultado': r.resultado,
                'valor_final': r.valor_final,
            }
            for r in fornecedor.resultados_licitacao.select_related('procedimento').order_by('-id')
        ]

        contratos = [
            {
                'id': ct.id,
                'numero': ct.numero,
                'objeto': ct.objeto,
                'status': ct.status,
                'valor_contrato': ct.valor_contrato,
                'data_vigencia_inicio': ct.data_vigencia_inicio,
                'data_vigencia_fim': ct.data_vigencia_fim,
            }
            for ct in fornecedor.contratos.order_by('-data_assinatura')
        ]

        return Response({
            'fornecedor_id': fornecedor.id,
            'ja_teve_relacao': bool(cotacoes or resultados_licitacao or contratos),
            'cotacoes': cotacoes,
            'resultados_licitacao': resultados_licitacao,
            'contratos': contratos,
        })
