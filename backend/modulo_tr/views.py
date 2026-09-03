from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import TR, HistoricoTR, LoteTR, ItemLoteTR
from .serializers import TRSerializer, LoteTRSerializer, ItemLoteTRSerializer
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA, check_licitante
from core.checklist_engine import ChecklistEngine
from exportacao.pdf_utils import gerar_pdf_tr, gerar_html, resposta_pdf, resposta_html

PAPEIS_SOLICITANTE = ('solicitante', 'demandante', 'responsavel_tecnico', 'admin')

# Códigos de SecaoArtefato já exibidos estaticamente em templates/exportacao/tr.html —
# usado para não duplicar conteúdo ao acrescentar seções custom (ver core/document_engine.py)
CODIGOS_ESTATICOS_TR = [
    'numero_sei', 'objeto', 'justificativa', 'requisitos', 'obrigacoes_contratada',
    'obrigacoes_contratante', 'criterios_selecao', 'criterios_medicao', 'prazo_vigencia',
    'local_entrega', 'garantia', 'lotes', 'adequacao_orcamentaria', 'permite_consorcio',
    'qualificacao_juridica', 'qualificacao_economica', 'prazos_execucao', 'degrau_lances',
    'estimativa_valor', 'observacoes',
    # hab_juridica/hab_economica são o mesmo conteúdo de qualificacao_juridica/
    # qualificacao_economica sob os códigos oficiais do checklist (14.1/14.3) —
    # o bloco fixo acima já cobre supressão/dispensa com justificativa; excluir
    # do loop genérico para não duplicar a seção com título diferente.
    'hab_juridica', 'hab_economica',
]


def _buscar_preco_referencia(item_dfd):
    """
    Retorna (valor_unitario, origem) para um ItemDFD.
    Prioriza o Mapa de Preços aprovado vinculado ao DFD:
    1. Match por código SIMPAS (mais preciso)
    2. Match por descrição (icontains)
    3. Match posicional — se DFD e Mapa têm o mesmo número de itens,
       correlaciona ItemDFD[i] com ItemMapa[i] por ordem de criação
    Fallback: estimativa do próprio ItemDFD.
    """
    if not item_dfd:
        return None, 'dfd'
    try:
        from modulo_mapa_precos.models import MapaComparativoPrecos, ItemMapa
        mapa = (
            MapaComparativoPrecos.objects
            .filter(dfd=item_dfd.dfd, status='Aprovado')
            .order_by('-created_at')
            .first()
        )
        if mapa:
            item_mapa = None

            # 1. Match por código SIMPAS do catálogo
            if item_dfd.item_catalogo and item_dfd.item_catalogo.codigo_simpas:
                item_mapa = ItemMapa.objects.filter(
                    mapa=mapa,
                    codigo_simpas=item_dfd.item_catalogo.codigo_simpas,
                ).first()

            # 2. Match por descrição (primeiros 20 chars, case-insensitive)
            if not item_mapa and item_dfd.objeto:
                item_mapa = ItemMapa.objects.filter(
                    mapa=mapa,
                    descricao__icontains=item_dfd.objeto[:20],
                ).first()

            # 3. Match posicional — correlaciona por índice quando contagens batem
            if not item_mapa:
                dfd_itens  = list(item_dfd.dfd.itens.order_by('id'))
                mapa_itens = list(ItemMapa.objects.filter(mapa=mapa).order_by('ordem', 'id'))
                if dfd_itens and mapa_itens and len(dfd_itens) == len(mapa_itens):
                    try:
                        idx = dfd_itens.index(item_dfd)
                        item_mapa = mapa_itens[idx]
                    except (ValueError, IndexError):
                        pass

            if item_mapa and item_mapa.valor_unitario_calculado:
                return item_mapa.valor_unitario_calculado, 'mapa'
    except Exception:
        pass
    return item_dfd.valor_unitario_estimado, 'dfd'


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
        categoria = (campos_extra or {}).get('categoria_motivo', '')
        HistoricoTR.objects.create(
            tr=tr,
            status_anterior=tr.status,
            status_novo=status_novo,
            usuario=request.user,
            motivo=campos_extra.get('motivo_devolucao') if campos_extra else None,
            categoria_motivo=categoria,
        )
        tr.status = status_novo
        if campos_extra:
            for k, v in campos_extra.items():
                setattr(tr, k, v)
        tr.updated_by = request.user
        tr.save()
        return Response(TRSerializer(tr, context={'request': request}).data)

    # ------------------------------------------------------------------ #
    # checklist                                                            #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        tr = self.get_object()
        resultado = ChecklistEngine.avaliar_tr(tr)
        return Response({
            'score': resultado.score,
            'total': resultado.total,
            'percentual': resultado.percentual,
            'pode_submeter': resultado.pode_submeter,
            'bloqueadores': [
                {
                    'campo': r.campo, 'descricao': r.descricao,
                    'base_legal': r.base_legal, 'detalhe': r.detalhe,
                }
                for r in resultado.bloqueadores
            ],
            'avisos': [
                {
                    'campo': r.campo, 'descricao': r.descricao,
                    'base_legal': r.base_legal, 'detalhe': r.detalhe,
                }
                for r in resultado.avisos
            ],
        })

    # ------------------------------------------------------------------ #
    # export actions                                                       #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        tr = self.get_object()
        pdf = gerar_pdf_tr(tr)
        return resposta_pdf(pdf, f'TR_{tr.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/historico')
    def export_historico(self, request, pk=None):
        from exportacao.pdf_utils import gerar_pdf_historico, resposta_pdf
        tr = self.get_object()
        pdf = gerar_pdf_historico(
            titulo='TR',
            numero_ref=tr.numero_sei,
            historico_entries=tr.historico.select_related('usuario').order_by('-criado_em'),
            org_nome=tr.org_id.nome if tr.org_id else '',
            org_sigla=tr.org_id.sigla if tr.org_id else None,
            criado_por=tr.created_by,
            created_at=tr.created_at,
        )
        return resposta_pdf(pdf, f'Historico_TR_{tr.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/html')
    def export_html(self, request, pk=None):
        from core.document_engine import DocumentEngine
        tr = self.get_object()
        modalidade = getattr(tr, 'modalidade_aquisicao', None)
        html = gerar_html('tr', {
            'tr': tr,
            'secoes_geradas': DocumentEngine.gerar('TR', tr, modalidade=modalidade),
            'codigos_estaticos': CODIGOS_ESTATICOS_TR,
        })
        return resposta_html(html, f'TR_{tr.numero_sei}.html')

    @action(detail=True, methods=['get'], url_path='gerar-texto')
    def gerar_texto(self, request, pk=None):
        from core.document_engine import DocumentEngine
        tr = self.get_object()
        modalidade = getattr(tr, 'modalidade_aquisicao', None)
        return Response(DocumentEngine.gerar('TR', tr, modalidade=modalidade))

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_SOLICITANTE:
            return Response({'detail': 'Apenas o demandante pode submeter o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        tr = self.get_object()
        resultado = ChecklistEngine.avaliar_tr(tr)
        if not resultado.pode_submeter:
            return Response(
                {
                    'detail': 'TR não pode ser submetido — há pendências obrigatórias do checklist.',
                    'bloqueadores': [b.detalhe for b in resultado.bloqueadores],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem aprovar o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Aprovado')

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem devolver o TR.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        categoria = request.data.get('categoria_motivo', '')
        return self._transicao(request, 'Devolvido',
                               campos_extra={'motivo_devolucao': motivo,
                                             'categoria_motivo': categoria})

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

    def _check_licitante_editavel(self, request, tr):
        """Verifica papel de licitante E status editável."""
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem gerenciar lotes.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._check_editavel(tr)

    def _tr_atualizado(self, pk, request):
        """Re-busca o TR com prefetch completo após modificação de lotes."""
        tr = self.get_queryset().get(pk=pk)
        return Response(TRSerializer(tr, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='lotes')
    def criar_lote(self, request, pk=None):
        tr = self.get_object()
        err = self._check_licitante_editavel(request, tr)
        if err: return err
        serializer = LoteTRSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(tr=tr)
        resp = self._tr_atualizado(tr.pk, request)
        resp.status_code = status.HTTP_201_CREATED
        return resp

    @action(detail=True, methods=['patch', 'delete'], url_path=r'lotes/(?P<lote_pk>[^/.]+)')
    def lote_detail(self, request, pk=None, lote_pk=None):
        """
        PATCH edita um lote já criado — descrição, modalidade (Ampla ↔
        Exclusivo ME/EPP) e justificativa de agrupamento. Necessário para
        corrigir a modalidade de lotes gerados em lote (gerar_por_item
        sempre cria como "ampla") e para atender o alerta de reclassificação
        por valor < R$80k. Lotes de Reserva de Cota (modalidade='cota_me_epp')
        não podem trocar de modalidade por aqui — são derivados de um lote
        de origem via gerar_cota, com percentual/lote_origem próprios.

        DELETE exclui o lote.
        """
        tr   = self.get_object()
        err  = self._check_licitante_editavel(request, tr)
        if err: return err
        lote = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)

        if request.method == 'DELETE':
            lote.delete()
            return self._tr_atualizado(tr.pk, request)

        nova_modalidade = request.data.get('modalidade')
        if nova_modalidade is not None:
            if lote.modalidade == 'cota_me_epp' or nova_modalidade == 'cota_me_epp':
                return Response(
                    {'detail': 'Lotes de Reserva de Cota ME/EPP não podem ter a modalidade alterada por aqui — exclua e gere novamente a partir do lote de origem.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if nova_modalidade not in ('ampla', 'exclusiva_me_epp'):
                return Response({'detail': 'Modalidade inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = LoteTRSerializer(
            lote, data=request.data, partial=True, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return self._tr_atualizado(tr.pk, request)

    @action(detail=True, methods=['post'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/itens')
    def adicionar_item(self, request, pk=None, lote_pk=None):
        tr   = self.get_object()
        err  = self._check_licitante_editavel(request, tr)
        if err: return err
        lote = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        serializer = ItemLoteTRSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        item_dfd_instance = serializer.validated_data.get('item_dfd')
        valor_ref, origem = _buscar_preco_referencia(item_dfd_instance)
        serializer.save(lote=lote, valor_unitario_ref=valor_ref, preco_origem=origem)
        resp = self._tr_atualizado(tr.pk, request)
        resp.status_code = status.HTTP_201_CREATED
        return resp

    @action(detail=True, methods=['delete'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/itens/(?P<item_pk>[^/.]+)')
    def remover_item(self, request, pk=None, lote_pk=None, item_pk=None):
        tr      = self.get_object()
        err     = self._check_licitante_editavel(request, tr)
        if err: return err
        lote    = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        item    = get_object_or_404(ItemLoteTR, pk=item_pk, lote=lote)
        item.delete()
        return self._tr_atualizado(tr.pk, request)

    @action(detail=True, methods=['post'], url_path=r'lotes/(?P<lote_pk>[^/.]+)/gerar_cota')
    def gerar_cota(self, request, pk=None, lote_pk=None):
        """Gera um lote de Reserva de Cota ME/EPP (25%) a partir de um lote de ampla concorrência."""
        tr   = self.get_object()
        err  = self._check_licitante_editavel(request, tr)
        if err: return err
        lote_origem = get_object_or_404(LoteTR, pk=lote_pk, tr=tr)
        if lote_origem.modalidade != 'ampla':
            return Response({'detail': 'O lote de origem deve ser de Ampla Concorrência.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not lote_origem.itens.exists():
            return Response({'detail': 'O lote de origem não possui itens.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from decimal import Decimal
        LIMITE_EXCLUSIVO = Decimal('80000.00')
        if lote_origem.valor_total < LIMITE_EXCLUSIVO and lote_origem.valor_total > 0:
            return Response({
                'detail': (
                    f'Lote com valor R$ {float(lote_origem.valor_total):,.2f} é inferior a R$ 80.000,00. '
                    'Não é possível criar cota reservada — este lote deve ser classificado como '
                    '"Exclusivo ME/EPP" (LC 123/2006, Art. 48, I).'
                )
            }, status=status.HTTP_400_BAD_REQUEST)

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
            # Herda o mesmo preço de referência do item de origem
            ItemLoteTR.objects.create(
                lote=lote_cota,
                item_dfd=item_orig.item_dfd,
                quantidade=qty_cota,
                valor_unitario_ref=item_orig.valor_unitario_ref,
                preco_origem=item_orig.preco_origem,
            )

        resp = self._tr_atualizado(tr.pk, request)
        resp.status_code = status.HTTP_201_CREATED
        return resp

    @action(detail=True, methods=['post'], url_path='gerar_por_item')
    def gerar_por_item(self, request, pk=None):
        """Cria um lote por item do DFD (tipo_parcelamento = por_item no ETP)."""
        tr = self.get_object()
        err = self._check_licitante_editavel(request, tr)
        if err: return err
        if tr.etp.tipo_parcelamento != 'por_item':
            return Response({'detail': 'O ETP deve ter tipo de parcelamento "por_item".'},
                            status=status.HTTP_400_BAD_REQUEST)
        itens_dfd = tr.etp.dfd.itens.all()
        if not itens_dfd.exists():
            return Response({'detail': 'O DFD de origem não possui itens.'},
                            status=status.HTTP_400_BAD_REQUEST)

        LoteTR.objects.filter(tr=tr).delete()

        # Recarrega os itens após excluir os lotes anteriores deste TR — a
        # exclusão libera (via sinal) o saldo que este próprio TR comprometia,
        # então a checagem abaixo reflete só o que está comprometido em *outros*
        # TRs/lotes.
        itens_dfd = list(tr.etp.dfd.itens.all())
        saldo_insuficiente = [
            item for item in itens_dfd if item.quantidade > item.quantidade_disponivel
        ]
        if saldo_insuficiente:
            return Response({
                'detail': (
                    'Um ou mais itens do DFD já estão parcial ou totalmente comprometidos '
                    'em outro TR/lote e não podem ser levados a este lote sem exceder o saldo: '
                    + '; '.join(
                        f'{i.objeto} (disponível {i.quantidade_disponivel} de {i.quantidade} {i.unidade_medida})'
                        for i in saldo_insuficiente
                    )
                )
            }, status=status.HTTP_400_BAD_REQUEST)

        for item in itens_dfd:
            lote = LoteTR.objects.create(
                tr=tr,
                descricao=item.objeto[:100],
                modalidade='ampla',
                org_id=tr.org_id,
                created_by=request.user,
                updated_by=request.user,
            )
            valor_ref, origem = _buscar_preco_referencia(item)
            ItemLoteTR.objects.create(
                lote=lote, item_dfd=item, quantidade=item.quantidade,
                valor_unitario_ref=valor_ref, preco_origem=origem,
            )

        resp = self._tr_atualizado(tr.pk, request)
        resp.status_code = status.HTTP_201_CREATED
        return resp
