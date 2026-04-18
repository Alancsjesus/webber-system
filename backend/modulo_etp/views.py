from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA
from .models import ETP, HistoricoETP
from .serializers import ETPSerializer

PAPEIS_SOLICITANTE = ('solicitante', 'demandante', 'responsavel_tecnico', 'admin')


class ETPViewSet(viewsets.ModelViewSet):
    serializer_class   = ETPSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields    = ['created_at', 'numero_sei', 'status']
    ordering           = ['-created_at']
    search_fields      = ['numero_sei', 'necessidade_contratacao']

    def get_queryset(self):
        oid = self.request.org_id
        return ETP.objects.filter(
            Q(org_id=oid) |
            Q(dfd__org_gestor=oid) |
            Q(dfd__unidade_licitante__orgao_id=oid)
        ).distinct().select_related('dfd', 'org_id').prefetch_related(
            'historico', 'historico_numero_sei', 'tr'
        )

    # ------------------------------------------------------------------ #
    # helpers                                                              #
    # ------------------------------------------------------------------ #

    def _transicao(self, request, status_novo, campos_extra=None):
        etp = self.get_object()
        permitidos = ETP.TRANSICOES_PERMITIDAS.get(etp.status, [])
        if status_novo not in permitidos:
            return Response(
                {'detail': f'Transição de "{etp.status}" para "{status_novo}" não é permitida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        status_anterior = etp.status
        motivo = (campos_extra or {}).get('motivo')

        etp.status = status_novo
        if campos_extra:
            for campo, valor in campos_extra.items():
                if campo != 'motivo':
                    setattr(etp, campo, valor)
        if status_novo == 'Submetido':
            etp.motivo_devolucao = None
        etp.updated_by = request.user
        etp.save()

        HistoricoETP.objects.create(
            etp=etp,
            status_anterior=status_anterior,
            status_novo=status_novo,
            usuario=request.user,
            motivo=motivo,
        )

        return Response(self.get_serializer(etp).data)

    # ------------------------------------------------------------------ #
    # workflow actions                                                     #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_SOLICITANTE:
            return Response({'detail': 'Apenas solicitantes podem submeter o ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Submetido')

    @action(detail=True, methods=['post'])
    def iniciar_analise(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem iniciar análise do ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Em Análise')

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Sem permissão para aprovar ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Aprovado',
                               campos_extra={'motivo': request.data.get('motivo')})

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Sem permissão para devolver ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return self._transicao(request, 'Devolvido',
                               campos_extra={'motivo_devolucao': motivo, 'motivo': motivo})
