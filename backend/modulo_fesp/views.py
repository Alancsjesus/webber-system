from datetime import date

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsMultiTenant

from .models import (
    InstrumentoFinanceiro, HistoricoInstrumentoFinanceiro,
    ComposicaoConselhoGestor, ReuniaoConselhoGestor,
    PlanoAplicacao, HistoricoPlanoAplicacao, MetaEspecifica,
    GrupoConsolidacaoItem, ItemPlanoAplicacao,
)
from .permissions import IsMembroConselhoFesp
from .serializers import (
    InstrumentoFinanceiroSerializer,
    ComposicaoConselhoGestorSerializer,
    ReuniaoConselhoGestorSerializer,
    PlanoAplicacaoSerializer,
    MetaEspecificaSerializer,
    GrupoConsolidacaoItemSerializer,
    ItemPlanoAplicacaoSerializer,
)


def _check_planejamento(request):
    papel = getattr(request, 'papel', None)
    tipo_unidade = getattr(request, 'tipo_unidade', None)
    if papel not in ('admin', 'gestor_planejamento') and tipo_unidade != 'planejamento':
        raise PermissionDenied('Apenas Planejamento ou Admin podem gerenciar este recurso.')


class InstrumentoFinanceiroViewSet(viewsets.ModelViewSet):
    """Instrumentos jurídicos de origem dos recursos (FESP, emendas, convênios, repasses, financiamentos)."""
    serializer_class = InstrumentoFinanceiroSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_instrumento', 'objeto', 'orgao_concedente_nome']
    ordering_fields = ['data_assinatura', 'valor_total_pactuado', 'status', 'created_at']
    ordering = ['-data_assinatura']

    def get_queryset(self):
        qs = InstrumentoFinanceiro.objects.filter(org_id=self.request.org_id).select_related(
            'fonte_recurso', 'org_id', 'created_by',
        )
        tipo = self.request.query_params.get('tipo_instrumento')
        stat = self.request.query_params.get('status')
        if tipo:
            qs = qs.filter(tipo_instrumento=tipo)
        if stat:
            qs = qs.filter(status=stat)
        return qs

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def _transicao(self, instrumento, novo_status, usuario, motivo=''):
        permitidos = InstrumentoFinanceiro.TRANSICOES_PERMITIDAS.get(instrumento.status, [])
        if novo_status not in permitidos:
            raise ValidationError(f'Transição "{instrumento.status}" → "{novo_status}" não permitida.')
        anterior = instrumento.status
        instrumento.status = novo_status
        instrumento.updated_by = usuario
        instrumento.save()
        HistoricoInstrumentoFinanceiro.objects.create(
            instrumento=instrumento, status_anterior=anterior,
            status_novo=novo_status, usuario=usuario, motivo=motivo,
        )

    @action(detail=True, methods=['post'])
    def ativar(self, request, pk=None):
        _check_planejamento(request)
        instrumento = self.get_object()
        self._transicao(instrumento, 'vigente', request.user)
        return Response(self.get_serializer(instrumento).data)

    @action(detail=True, methods=['post'])
    def encerrar(self, request, pk=None):
        _check_planejamento(request)
        instrumento = self.get_object()
        self._transicao(instrumento, 'encerrado', request.user, request.data.get('motivo', ''))
        return Response(self.get_serializer(instrumento).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        _check_planejamento(request)
        instrumento = self.get_object()
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Motivo do cancelamento é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        self._transicao(instrumento, 'cancelado', request.user, motivo)
        return Response(self.get_serializer(instrumento).data)


class ComposicaoConselhoGestorViewSet(viewsets.ModelViewSet):
    """Composição do Conselho Gestor do FESP (Configurações → Conselho Gestor FESP)."""
    serializer_class = ComposicaoConselhoGestorSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['usuario__username', 'usuario__first_name', 'usuario__last_name', 'nome_orgao_externo']
    ordering = ['cargo']

    def get_queryset(self):
        qs = ComposicaoConselhoGestor.objects.filter(org_id=self.request.org_id).select_related(
            'usuario', 'orgao_representado',
        )
        if self.request.query_params.get('ativos') == 'true':
            qs = qs.filter(ativo=True)
        return qs

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_planejamento(self.request)
        instance.ativo = False
        instance.save(update_fields=['ativo'])


class ReuniaoConselhoGestorViewSet(viewsets.ReadOnlyModelViewSet):
    """Atas de reunião do Conselho Gestor — criadas via PlanoAplicacaoViewSet.aprovar_conselho/devolver."""
    serializer_class = ReuniaoConselhoGestorSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    ordering = ['-data_reuniao']

    def get_queryset(self):
        return ReuniaoConselhoGestor.objects.filter(org_id=self.request.org_id).prefetch_related('presentes')


class MetaEspecificaViewSet(viewsets.ModelViewSet):
    """Metas Específicas de um Plano de Aplicação — editáveis só enquanto o plano está em elaboração."""
    serializer_class = MetaEspecificaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'descricao_meta']
    ordering = ['numero']

    def get_queryset(self):
        qs = MetaEspecifica.objects.filter(org_id=self.request.org_id).select_related('plano')
        plano_id = self.request.query_params.get('plano')
        if plano_id:
            qs = qs.filter(plano_id=plano_id)
        return qs

    def _check_plano_editavel(self, plano):
        if plano.status != 'elaboracao':
            raise ValidationError('Metas Específicas só podem ser alteradas enquanto o plano está em elaboração.')

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        plano = serializer.validated_data.get('plano')
        if plano and str(plano.org_id_id) != str(self.request.org_id):
            raise PermissionDenied('Plano não pertence à organização.')
        if plano:
            self._check_plano_editavel(plano)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        self._check_plano_editavel(serializer.instance.plano)
        serializer.save()

    def perform_destroy(self, instance):
        _check_planejamento(self.request)
        self._check_plano_editavel(instance.plano)
        instance.delete()


class GrupoConsolidacaoItemViewSet(viewsets.ModelViewSet):
    """Grupos de consolidação de itens (Fase 3) — CRUD básico; a geração automática de sugestões vem depois."""
    serializer_class = GrupoConsolidacaoItemSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    ordering = ['-created_at']

    def get_queryset(self):
        qs = GrupoConsolidacaoItem.objects.filter(org_id=self.request.org_id).select_related('plano')
        plano_id = self.request.query_params.get('plano')
        if plano_id:
            qs = qs.filter(plano_id=plano_id)
        return qs

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_planejamento(self.request)
        instance.delete()


class ItemPlanoAplicacaoViewSet(viewsets.ModelViewSet):
    """Itens de uma Meta Específica — editáveis só enquanto o plano está em elaboração."""
    serializer_class = ItemPlanoAplicacaoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['bem_servico', 'descricao', 'codigo_senasp', 'destinacao']
    ordering = ['created_at']

    def get_queryset(self):
        qs = ItemPlanoAplicacao.objects.filter(org_id=self.request.org_id).select_related(
            'meta_especifica__plano', 'instrumento', 'org_beneficiaria', 'unidade_beneficiaria', 'item_catalogo',
        )
        meta_id = self.request.query_params.get('meta_especifica')
        plano_id = self.request.query_params.get('plano')
        if meta_id:
            qs = qs.filter(meta_especifica_id=meta_id)
        if plano_id:
            qs = qs.filter(meta_especifica__plano_id=plano_id)
        return qs

    def _check_plano_editavel(self, meta_especifica):
        if meta_especifica.plano.status != 'elaboracao':
            raise ValidationError('Itens só podem ser alterados enquanto o plano está em elaboração.')

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        meta = serializer.validated_data.get('meta_especifica')
        if meta and str(meta.org_id_id) != str(self.request.org_id):
            raise PermissionDenied('Meta Específica não pertence à organização.')
        if meta:
            self._check_plano_editavel(meta)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        self._check_plano_editavel(serializer.instance.meta_especifica)
        serializer.save()

    def perform_destroy(self, instance):
        _check_planejamento(self.request)
        self._check_plano_editavel(instance.meta_especifica)
        instance.delete()


class PlanoAplicacaoViewSet(viewsets.ModelViewSet):
    """Plano de Aplicação anual (FESP, Emendas e Financiamentos)."""
    serializer_class = PlanoAplicacaoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'ementa', 'descricao']
    ordering_fields = ['exercicio_fiscal', 'status', 'created_at']
    ordering = ['-exercicio_fiscal']

    def get_queryset(self):
        qs = PlanoAplicacao.objects.filter(org_id=self.request.org_id).select_related(
            'org_id', 'created_by', 'reuniao_aprovacao',
        )
        exercicio = self.request.query_params.get('exercicio_fiscal')
        stat = self.request.query_params.get('status')
        if exercicio:
            qs = qs.filter(exercicio_fiscal=exercicio)
        if stat:
            qs = qs.filter(status=stat)
        return qs

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def _transicao(self, plano, novo_status, usuario, motivo=''):
        permitidos = PlanoAplicacao.TRANSICOES_PERMITIDAS.get(plano.status, [])
        if novo_status not in permitidos:
            raise ValidationError(f'Transição "{plano.status}" → "{novo_status}" não permitida.')
        anterior = plano.status
        plano.status = novo_status
        plano.updated_by = usuario
        plano.save()
        HistoricoPlanoAplicacao.objects.create(
            plano=plano, status_anterior=anterior,
            status_novo=novo_status, usuario=usuario, motivo=motivo,
        )

    @action(detail=True, methods=['post'], url_path='submeter_conselho')
    def submeter_conselho(self, request, pk=None):
        _check_planejamento(request)
        plano = self.get_object()
        from core.checklist_engine import ChecklistEngine
        resultado = ChecklistEngine.avaliar_plano_aplicacao(plano)
        if not resultado.pode_submeter:
            return Response(
                {
                    'detail': 'Plano não pode ser submetido — há pendências obrigatórias.',
                    'bloqueadores': [b.detalhe for b in resultado.bloqueadores],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._transicao(plano, 'submetido_conselho', request.user)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'], url_path='aprovar_conselho', permission_classes=[IsAuthenticated, IsMultiTenant, IsMembroConselhoFesp])
    def aprovar_conselho(self, request, pk=None):
        plano = self.get_object()
        numero_ata = (request.data.get('numero_ata') or '').strip()
        data_reuniao = request.data.get('data_reuniao')
        if not numero_ata or not data_reuniao:
            return Response(
                {'detail': 'Número da ata e data da reunião são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reuniao = ReuniaoConselhoGestor.objects.create(
            org_id_id=request.org_id,
            created_by=request.user, updated_by=request.user,
            plano=plano, numero_ata=numero_ata,
            tipo=request.data.get('tipo', 'ordinaria'),
            data_reuniao=data_reuniao,
            quorum_atingido=request.data.get('quorum_atingido', True),
            deliberacao=request.data.get('deliberacao', ''),
        )
        presentes_ids = request.data.get('presentes', [])
        if presentes_ids:
            reuniao.presentes.set(
                ComposicaoConselhoGestor.objects.filter(id__in=presentes_ids, org_id=request.org_id)
            )
        plano.reuniao_aprovacao = reuniao
        plano.save(update_fields=['reuniao_aprovacao'])
        self._transicao(plano, 'aprovado_conselho', request.user)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsMultiTenant, IsMembroConselhoFesp])
    def devolver(self, request, pk=None):
        plano = self.get_object()
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Motivo da devolução é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        plano.motivo_devolucao_conselho = motivo
        plano.save(update_fields=['motivo_devolucao_conselho'])
        self._transicao(plano, 'devolvido', request.user, motivo)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def homologar(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in ('admin', 'ordenador'):
            return Response(
                {'detail': 'Apenas o Ordenador de Despesa pode registrar a homologação.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        plano = self.get_object()
        numero_ato = (request.data.get('numero_ato') or '').strip()
        data_ato = request.data.get('data_ato')
        if not numero_ato or not data_ato:
            return Response(
                {'detail': 'Número e data do ato de homologação são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        plano.numero_ato = numero_ato
        plano.data_ato = data_ato
        plano.numero_processo_sei_ato = request.data.get('numero_processo_sei_ato', '')
        plano.save(update_fields=['numero_ato', 'data_ato', 'numero_processo_sei_ato'])
        self._transicao(plano, 'homologado', request.user)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def publicar(self, request, pk=None):
        _check_planejamento(request)
        plano = self.get_object()
        self._transicao(plano, 'publicado', request.user)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def encerrar(self, request, pk=None):
        _check_planejamento(request)
        plano = self.get_object()
        self._transicao(plano, 'encerrado', request.user, request.data.get('motivo', ''))
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        _check_planejamento(request)
        plano = self.get_object()
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Motivo do cancelamento é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        self._transicao(plano, 'cancelado', request.user, motivo)
        return Response(self.get_serializer(plano).data)
