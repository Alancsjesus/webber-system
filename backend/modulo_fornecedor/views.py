from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Fornecedor
from .serializers import FornecedorSerializer

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
        return qs

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

    @action(detail=True, methods=['get'], url_path='historico')
    def historico(self, request, pk=None):
        """
        Agrega todo o histórico de relação do fornecedor com a administração:
        cotações, resultados de licitação e contratos.
        """
        fornecedor = self.get_object()

        cotacoes = [
            {
                'id': c.id,
                'mapa_id': c.mapa_id,
                'status': c.status,
                'data_envio': c.data_envio,
                'respondeu': c.respondeu,
                'valor_respondido': c.valor_respondido,
            }
            for c in fornecedor.cotacoes.select_related('mapa').order_by('-data_envio')
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
