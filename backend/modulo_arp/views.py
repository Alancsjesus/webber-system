from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsMultiTenant

from .models import Ata, ItemAta, HistoricoAta
from .serializers import AtaSerializer, ItemAtaSerializer

PAPEIS_GERENCIAM_ARP = ('admin', 'analista', 'gestor_contrato', 'ordenador')


def _check_permissao(request):
    if getattr(request, 'papel', None) not in PAPEIS_GERENCIAM_ARP:
        raise PermissionDenied('Apenas Analista, Gestor de Contrato, Ordenador ou Admin podem gerenciar atas.')


class AtaViewSet(viewsets.ModelViewSet):
    serializer_class = AtaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_ata', 'objeto', 'orgao_gerenciador_nome']
    ordering_fields = ['data_assinatura', 'data_vigencia_fim', 'status', 'created_at']
    ordering = ['-data_assinatura']

    def get_queryset(self):
        qs = Ata.objects.filter(org_id=self.request.org_id).select_related(
            'org_id', 'created_by', 'procedimento',
        ).prefetch_related('itens', 'historico')
        tipo = self.request.query_params.get('tipo_origem')
        stat = self.request.query_params.get('status')
        if tipo:
            qs = qs.filter(tipo_origem=tipo)
        if stat:
            qs = qs.filter(status=stat)
        return qs

    def perform_create(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao(self.request)
        if instance.status != 'rascunho':
            raise ValidationError('Só é possível excluir atas em Rascunho — use Cancelar para atas vigentes/encerradas.')
        instance.delete()

    def _transicao(self, ata, novo_status, usuario, motivo=''):
        permitidos = Ata.TRANSICOES_PERMITIDAS.get(ata.status, [])
        if novo_status not in permitidos:
            raise ValidationError(f'Transição "{ata.status}" → "{novo_status}" não permitida.')
        anterior = ata.status
        ata.status = novo_status
        ata.updated_by = usuario
        ata.save()
        HistoricoAta.objects.create(
            ata=ata, status_anterior=anterior, status_novo=novo_status,
            usuario=usuario, motivo=motivo,
        )
        # get_queryset() prefetch_related('historico') deixa um cache obsoleto
        # no objeto já carregado — invalida para o novo registro aparecer na resposta.
        if hasattr(ata, '_prefetched_objects_cache'):
            ata._prefetched_objects_cache.pop('historico', None)

    @action(detail=True, methods=['post'])
    def ativar(self, request, pk=None):
        _check_permissao(request)
        ata = self.get_object()
        self._transicao(ata, 'vigente', request.user)
        return Response(self.get_serializer(ata).data)

    @action(detail=True, methods=['post'])
    def encerrar(self, request, pk=None):
        _check_permissao(request)
        ata = self.get_object()
        self._transicao(ata, 'encerrada', request.user, request.data.get('motivo', ''))
        return Response(self.get_serializer(ata).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        _check_permissao(request)
        ata = self.get_object()
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Motivo do cancelamento é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        self._transicao(ata, 'cancelada', request.user, motivo)
        return Response(self.get_serializer(ata).data)

    @action(detail=True, methods=['get', 'post'], url_path='itens')
    def itens(self, request, pk=None):
        ata = self.get_object()
        if request.method == 'GET':
            serializer = ItemAtaSerializer(ata.itens.all(), many=True, context={'request': request})
            return Response(serializer.data)

        _check_permissao(request)
        serializer = ItemAtaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(ata=ata)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'itens/(?P<item_pk>[^/.]+)')
    def item_detail(self, request, pk=None, item_pk=None):
        ata = self.get_object()
        _check_permissao(request)
        try:
            item = ata.itens.get(pk=item_pk)
        except ItemAta.DoesNotExist:
            return Response({'detail': 'Item não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        partial = request.method == 'PATCH'
        serializer = ItemAtaSerializer(item, data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def confronto(self, request):
        """
        Cruza itens de DFD pendentes de contratação (item_catalogo preenchido,
        DFD sem nenhum Contrato vinculado e não Cancelada/Rejeitada) contra
        itens de Atas vigentes do mesmo órgão com o mesmo item_catalogo e
        saldo disponível.

        Limitação conhecida: não existe rastreamento de contratação por item
        (só por DFD inteiro — Contrato.dfd é FK ao DFD todo), então a
        heurística de "pendente" é por DFD sem nenhum contrato, não por item
        individual já contratado.
        """
        from modulo_demanda.models import ItemDFD

        org_id = request.org_id
        itens_pendentes = (
            ItemDFD.objects
            .filter(dfd__org_id=org_id, item_catalogo__isnull=False)
            .exclude(dfd__status__in=['Rejeitada', 'Cancelada'])
            .exclude(dfd__contratos__isnull=False)
            .select_related('dfd', 'item_catalogo')
        )

        itens_ata_vigentes = (
            ItemAta.objects
            .filter(ata__org_id=org_id, ata__status='vigente', item_catalogo__isnull=False)
            .select_related('ata', 'item_catalogo', 'fornecedor')
        )
        por_catalogo = {}
        for item_ata in itens_ata_vigentes:
            if item_ata.saldo_disponivel <= 0:
                continue
            por_catalogo.setdefault(item_ata.item_catalogo_id, []).append(item_ata)

        resultado = []
        for item_dfd in itens_pendentes:
            sugestoes = por_catalogo.get(item_dfd.item_catalogo_id)
            if not sugestoes:
                continue
            resultado.append({
                'item_dfd': {
                    'id': item_dfd.id,
                    'dfd_id': item_dfd.dfd_id,
                    'dfd_numero_sei': item_dfd.dfd.numero_sei,
                    'objeto': item_dfd.objeto,
                    'quantidade': item_dfd.quantidade,
                    'catalogo_nome': item_dfd.item_catalogo.nome,
                },
                'sugestoes': [
                    {
                        'ata_id': ia.ata_id,
                        'ata_numero': ia.ata.numero_ata,
                        'item_ata_id': ia.id,
                        'fornecedor_nome': ia.fornecedor.nome_razao_social if ia.fornecedor_id else None,
                        'valor_unitario_registrado': ia.valor_unitario_registrado,
                        'saldo_disponivel': ia.saldo_disponivel,
                    }
                    for ia in sugestoes
                ],
            })

        return Response(resultado)
