from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import TR, HistoricoTR, LoteTR, ItemLoteTR
from .serializers import TRSerializer, LoteTRSerializer, ItemLoteTRSerializer
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA
from exportacao.pdf_utils import gerar_pdf_tr, gerar_html, resposta_pdf, resposta_html

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
        return TR.objects.filter(org_id=oid).prefetch_related(
            'historico',
            'lotes__itens__item_dfd__item_catalogo',
        )

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

    # ------------------------------------------------------------------ #
    # export actions                                                       #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        tr = self.get_object()
        pdf = gerar_pdf_tr(tr)
        return resposta_pdf(pdf, f'TR_{tr.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/html')
    def export_html(self, request, pk=None):
        tr = self.get_object()
        html = gerar_html('tr', {'tr': tr})
        return resposta_html(html, f'TR_{tr.numero_sei}.html')

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

    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        """Derruba a aprovação e retorna o TR para Devolvido (somente admin)."""
        if getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas administradores podem reabrir TRs aprovados.'},
                            status=status.HTTP_403_FORBIDDEN)
        tr = self.get_object()
        if tr.status not in ('Aprovado', 'Cancelado'):
            return Response({'detail': 'Apenas TRs com status Aprovado ou Cancelado podem ser reabertos.'},
                            status=status.HTTP_400_BAD_REQUEST)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da reabertura é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        HistoricoTR.objects.create(
            tr=tr, status_anterior=tr.status, status_novo='Devolvido',
            usuario=request.user, motivo=f'[REABERTURA] {motivo}',
        )
        tr.status = 'Devolvido'
        tr.motivo_devolucao = f'Reabertura pelo admin: {motivo}'
        tr.save(update_fields=['status', 'motivo_devolucao'])
        return Response(TRSerializer(tr, context={'request': request}).data)

    def perform_update(self, serializer):
        if serializer.instance.status in ('Aprovado', 'Cancelado'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('TRs aprovados ou cancelados não podem ser editados. Use "Reabrir" para devolvê-los.')
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status not in ('Rascunho', 'Devolvido'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas TRs em Rascunho ou Devolvido podem ser excluídos.')
        instance.delete()

    # ── Lotes ──────────────────────────────────────────────────────────── #

    def _check_editavel(self, tr):
        if tr.status not in ('Rascunho', 'Devolvido'):
            return Response({'detail': 'Lotes só podem ser editados em TRs em Rascunho ou Devolvido.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return None

    @action(detail=True, methods=['post'], url_path='lotes')
    def criar_lote(self, request, pk=None):
        tr = self.get_object()
        err = self._check_editavel(tr)
        if err: return err
        serializer = LoteTRSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(tr=tr)
        return Response(TRSerializer(tr, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'lotes/(?P<lote_pk>[^/.]+)')
    def excluir_lote(self, request, pk=None, lote_pk=None):
        tr   = self.get_object()
        err  = self._check_editavel(tr)
        if err: return err
        lote = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        lote.delete()
        return Response(TRSerializer(tr, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/itens')
    def adicionar_item(self, request, pk=None, lote_pk=None):
        tr   = self.get_object()
        err  = self._check_editavel(tr)
        if err: return err
        lote = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        serializer = ItemLoteTRSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(lote=lote)
        return Response(TRSerializer(tr, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/itens/(?P<item_pk>[^/.]+)')
    def remover_item(self, request, pk=None, lote_pk=None, item_pk=None):
        tr      = self.get_object()
        err     = self._check_editavel(tr)
        if err: return err
        lote    = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        item    = get_object_or_404(ItemLoteTR, pk=item_pk, lote=lote)
        item.delete()
        return Response(TRSerializer(tr, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/gerar_cota')
    def gerar_cota(self, request, pk=None, lote_pk=None):
        """Gera um lote de Reserva de Cota ME/EPP (25%) a partir de um lote de ampla concorrência."""
        tr   = self.get_object()
        err  = self._check_editavel(tr)
        if err: return err
        lote_origem = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        if lote_origem.modalidade != 'ampla':
            return Response({'detail': 'O lote de origem deve ser de Ampla Concorrência.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not lote_origem.itens.exists():
            return Response({'detail': 'O lote de origem não possui itens.'},
                            status=status.HTTP_400_BAD_REQUEST)

        percentual = request.data.get('percentual', 25)
        try:
            percentual = int(percentual)
            assert 1 <= percentual <= 49
        except (ValueError, AssertionError):
            return Response({'detail': 'Percentual deve ser entre 1 e 49.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from decimal import Decimal, ROUND_HALF_UP
        lote_cota = LoteTR.objects.create(
            tr=tr,
            descricao=f'Cota ME/EPP — {percentual}% de {lote_origem.numero}',
            modalidade='cota_me_epp',
            percentual_cota=percentual,
            lote_origem=lote_origem,
            org_id=tr.org_id,
            created_by=request.user,
            updated_by=request.user,
        )
        for item_orig in lote_origem.itens.select_related('item_dfd'):
            qty_cota = (item_orig.quantidade * Decimal(percentual) / 100).quantize(
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
            ItemLoteTR.objects.create(lote=lote_cota, item_dfd=item_orig.item_dfd,
                                      quantidade=qty_cota)

        return Response(TRSerializer(tr, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='gerar_por_item')
    def gerar_por_item(self, request, pk=None):
        """Cria um lote por item do DFD (tipo_parcelamento = por_item no ETP)."""
        tr = self.get_object()
        err = self._check_editavel(tr)
        if err: return err
        if tr.etp.tipo_parcelamento != 'por_item':
            return Response({'detail': 'O ETP deve ter tipo de parcelamento "por_item".'},
                            status=status.HTTP_400_BAD_REQUEST)
        itens_dfd = tr.etp.dfd.itens.all()
        if not itens_dfd.exists():
            return Response({'detail': 'O DFD de origem não possui itens.'},
                            status=status.HTTP_400_BAD_REQUEST)

        LoteTR.objects.filter(tr=tr).delete()
        for item in itens_dfd:
            lote = LoteTR.objects.create(
                tr=tr,
                descricao=item.objeto[:100],
                modalidade='ampla',
                org_id=tr.org_id,
                created_by=request.user,
                updated_by=request.user,
            )
            ItemLoteTR.objects.create(lote=lote, item_dfd=item, quantidade=item.quantidade)

        return Response(TRSerializer(tr, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)
