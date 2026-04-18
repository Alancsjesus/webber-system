from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import TR, HistoricoTR
from .serializers import TRSerializer
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA

PAPEIS_SOLICITANTE = ('solicitante', 'demandante', 'responsavel_tecnico', 'admin')


class TRViewSet(viewsets.ModelViewSet):
    serializer_class   = TRSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['status']
    search_fields      = ['numero_sei', 'objeto_contratacao']
    ordering_fields    = ['created_at', 'numero_sei']
    ordering           = ['-created_at']

    def get_queryset(self):
        oid = self.request.org_id
        return TR.objects.filter(org_id=oid).prefetch_related('historico')

    def _transicao(self, request, status_novo, campos_extra=None):
        tr = self.get_object()
        permitidos = TR.TRANSICOES_PERMITIDAS.get(tr.status, [])
        if status_novo not in permitidos:
            return Response(
                {'detail': f'Transição "{tr.status}" → "{status_novo}" não permitida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        HistoricoTR.objects.create(
            tr=tr,
            status_anterior=tr.status,
            status_novo=status_novo,
            usuario=request.user,
            motivo=campos_extra.get('motivo_devolucao') if campos_extra else None,
        )
        tr.status = status_novo
        if campos_extra:
            for k, v in campos_extra.items():
                setattr(tr, k, v)
        tr.updated_by = request.user
        tr.save()
        return Response(TRSerializer(tr, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_SOLICITANTE:
            return Response({'detail': 'Apenas o demandante pode submeter o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Submetido',
                               campos_extra={'motivo_devolucao': None})

    @action(detail=True, methods=['post'])
    def iniciar_analise(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem iniciar análise do TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Em Análise')

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem aprovar o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Aprovado')

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem devolver o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._transicao(request, 'Devolvido',
                               campos_extra={'motivo_devolucao': motivo})
