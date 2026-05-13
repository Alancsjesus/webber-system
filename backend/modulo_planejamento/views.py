import django_filters
from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import NecessidadePlanejamento, PlanoOrcamentario, ItemPlanoOrcamentario
from .serializers import NecessidadeSerializer, PlanoOrcamentarioSerializer, ItemPlanoSerializer
from core.permissions import IsMultiTenant, IsUnidadePlanejamento, PAPEIS_PLANEJAMENTO
from core.models import Orgao


class NecessidadeFilter(django_filters.FilterSet):
    status           = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    prioridade       = django_filters.CharFilter(field_name='prioridade', lookup_expr='exact')
    exercicio_fiscal = django_filters.NumberFilter(field_name='exercicio_fiscal')
    area             = django_filters.CharFilter(method='filter_area')
    sem_dfd          = django_filters.BooleanFilter(field_name='dfd', lookup_expr='isnull')
    tipo_execucao    = django_filters.CharFilter(field_name='tipo_execucao', lookup_expr='exact')

    def filter_area(self, queryset, name, value):
        return queryset.filter(area_aplicacao__contains=value)

    class Meta:
        model  = NecessidadePlanejamento
        fields = ['status', 'prioridade', 'exercicio_fiscal', 'sem_dfd', 'tipo_execucao']


class NecessidadeViewSet(viewsets.ModelViewSet):
    """
    ViewSet para NecessidadePlanejamento.

    Visibilidade:
    - Necessidades criadas por este órgão (org_id)
    - Necessidades direcionadas a este órgão como executor (orgao_executor)
    - Necessidades já sob controle deste órgão (org_gestor)
    """
    serializer_class   = NecessidadeSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class    = NecessidadeFilter
    ordering_fields    = ['created_at', 'titulo', 'valor_estimado', 'prioridade', 'exercicio_fiscal']
    ordering           = ['-created_at']
    search_fields      = ['titulo', 'descricao', 'departamento_solicitante']

    def get_queryset(self):
        oid = self.request.org_id
        # Child orgs that have this org as parent (for inherited external necessidades)
        child_ids = Orgao.objects.filter(parent_id=oid).values_list('id', flat=True)
        return NecessidadePlanejamento.objects.filter(
            Q(org_id=oid) |
            Q(orgao_executor=oid) |
            Q(org_gestor=oid) |
            Q(org_id__in=child_ids, tipo_execucao='externa')
        ).distinct()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _check_planejamento(self, request):
        """Retorna True se o usuário tem permissão de unidade de planejamento."""
        return (
            getattr(request, 'tipo_unidade', None) == 'planejamento'
            or getattr(request, 'papel', None) in PAPEIS_PLANEJAMENTO
        )

    def _transicao(self, request, pk, status_novo, campos_extra=None):
        nec = self.get_object()
        nec.status = status_novo
        if campos_extra:
            for campo, valor in campos_extra.items():
                setattr(nec, campo, valor)
        nec.updated_by = request.user
        nec.save()
        serializer = self.get_serializer(nec)
        return Response(serializer.data)

    # ── Ações de workflow ──────────────────────────────────────────────────

    @action(detail=True, methods=['post'])
    def iniciar_analise(self, request, pk=None):
        """Unidade de planejamento do órgão executor inicia análise da necessidade."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode iniciar análise de necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        nec = self.get_object()
        if nec.status != 'Identificada':
            return Response({'detail': f'Transição inválida a partir de "{nec.status}".'},
                            status=status.HTTP_400_BAD_REQUEST)

        orgao_gestor_id = nec.orgao_executor_id or nec.org_id_id
        return self._transicao(request, pk, 'Em Análise',
                               campos_extra={'org_gestor_id': orgao_gestor_id})

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """Unidade de planejamento aprova a necessidade."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode aprovar necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        nec = self.get_object()
        if nec.status not in ('Identificada', 'Em Análise'):
            return Response({'detail': f'Transição inválida a partir de "{nec.status}".'},
                            status=status.HTTP_400_BAD_REQUEST)

        orgao_gestor_id = nec.orgao_executor_id or nec.org_id_id
        return self._transicao(request, pk, 'Aprovada',
                               campos_extra={'org_gestor_id': orgao_gestor_id})

    @action(detail=True, methods=['post'])
    def rejeitar(self, request, pk=None):
        """Unidade de planejamento rejeita a necessidade."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode rejeitar necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da rejeição é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        nec = self.get_object()
        if nec.status not in ('Identificada', 'Em Análise'):
            return Response({'detail': f'Transição inválida a partir de "{nec.status}".'},
                            status=status.HTTP_400_BAD_REQUEST)

        return self._transicao(request, pk, 'Cancelada',
                               campos_extra={'observacoes': f'[Rejeitada] {motivo}',
                                             'org_gestor_id': None})

    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        """Órgão pai aceita necessidade externa de órgão filho."""
        if not self._check_planejamento(request):
            return Response({'detail': 'Apenas a unidade de planejamento pode aceitar necessidades.'},
                            status=status.HTTP_403_FORBIDDEN)
        nec = self.get_object()
        if nec.tipo_execucao != 'externa':
            return Response({'detail': 'Apenas necessidades com execução externa podem ser aceitas.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if nec.aceite_pai == 'aceita':
            return Response({'detail': 'Necessidade já foi aceita.'}, status=status.HTTP_400_BAD_REQUEST)
        return self._transicao(request, pk, nec.status, campos_extra={'aceite_pai': 'aceita'})

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        """Órgão pai recusa necessidade externa de órgão filho."""
        if not self._check_planejamento(request):
            return Response({'detail': 'Apenas a unidade de planejamento pode recusar necessidades.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da recusa é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        nec = self.get_object()
        if nec.tipo_execucao != 'externa':
            return Response({'detail': 'Apenas necessidades com execução externa podem ser recusadas.'},
                            status=status.HTTP_400_BAD_REQUEST)
        obs = f'[Recusada pelo órgão pai] {motivo}'
        if nec.observacoes:
            obs = f'{obs}\n\n{nec.observacoes}'
        return self._transicao(request, pk, nec.status,
                               campos_extra={'aceite_pai': 'recusada', 'observacoes': obs})

    @action(detail=False, methods=['post'])
    def aceitar_lote(self, request):
        """Aceita em lote necessidades externas pendentes. Body: {ids: [1,2,3]}"""
        if not self._check_planejamento(request):
            return Response({'detail': 'Apenas a unidade de planejamento pode aceitar necessidades.'},
                            status=status.HTTP_403_FORBIDDEN)
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'Lista de ids é obrigatória.'},
                            status=status.HTTP_400_BAD_REQUEST)
        oid = request.org_id
        child_ids = Orgao.objects.filter(parent_id=oid).values_list('id', flat=True)
        updated = NecessidadePlanejamento.objects.filter(
            pk__in=ids,
            org_id__in=child_ids,
            tipo_execucao='externa',
            aceite_pai='pendente',
        ).update(aceite_pai='aceita', updated_by=request.user)
        return Response({'aceitas': updated})

    @action(detail=False, methods=['post'])
    def recusar_lote(self, request):
        """Recusa em lote necessidades externas. Body: {ids: [1,2,3], motivo: '...'}"""
        if not self._check_planejamento(request):
            return Response({'detail': 'Apenas a unidade de planejamento pode recusar necessidades.'},
                            status=status.HTTP_403_FORBIDDEN)
        ids = request.data.get('ids', [])
        motivo = request.data.get('motivo', '').strip()
        if not ids:
            return Response({'detail': 'Lista de ids é obrigatória.'}, status=status.HTTP_400_BAD_REQUEST)
        if not motivo:
            return Response({'detail': 'Motivo é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        oid = request.org_id
        child_ids = Orgao.objects.filter(parent_id=oid).values_list('id', flat=True)
        updated = NecessidadePlanejamento.objects.filter(
            pk__in=ids,
            org_id__in=child_ids,
            tipo_execucao='externa',
        ).update(aceite_pai='recusada', updated_by=request.user)
        return Response({'recusadas': updated})

    @action(detail=True, methods=['post'])
    def iniciar_dfd(self, request, pk=None):
        """
        Cria um DFD a partir de uma NecessidadePlanejamento aprovada.
        Usado pela tela 'Preparar Aquisição'.
        Body: { numero_sei, prazo_necessidade, area_aplicacao, modalidade_aquisicao,
                observacoes, itens: [{item_catalogo_id?, objeto, unidade_medida,
                                      quantidade, valor_unitario_estimado}] }
        """
        from modulo_demanda.models import DFD, ItemDFD
        from modulo_demanda.serializers import DFDSerializer

        nec = self.get_object()

        if nec.status != 'Aprovada':
            return Response(
                {'detail': f'A necessidade deve estar "Aprovada" para iniciar DFD (status atual: {nec.status}).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if nec.dfd_id:
            return Response(
                {'detail': 'Esta necessidade já possui um DFD vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        numero_sei        = (request.data.get('numero_sei') or '').strip()
        prazo_necessidade = request.data.get('prazo_necessidade')
        area_aplicacao    = request.data.get('area_aplicacao', [])
        itens_data        = request.data.get('itens', [])

        erros = {}
        if not numero_sei:
            erros['numero_sei'] = 'Número SEI é obrigatório.'
        if not prazo_necessidade:
            erros['prazo_necessidade'] = 'Prazo da necessidade é obrigatório.'
        if not area_aplicacao:
            erros['area_aplicacao'] = 'Selecione ao menos uma área de aplicação.'
        if not itens_data:
            erros['itens'] = 'Adicione pelo menos 1 item ao DFD.'
        if erros:
            return Response(erros, status=status.HTTP_400_BAD_REQUEST)

        from decimal import Decimal
        valor_estimado_total = sum(
            Decimal(str(it.get('quantidade', 0))) * Decimal(str(it.get('valor_unitario_estimado', 0)))
            for it in itens_data
        )

        dfd = DFD.objects.create(
            numero_sei=numero_sei,
            descricao=nec.descricao,
            prazo_necessidade=prazo_necessidade,
            area_aplicacao=area_aplicacao if isinstance(area_aplicacao, list) else [area_aplicacao],
            modalidade_aquisicao=request.data.get('modalidade_aquisicao', 'licitacao'),
            observacoes=request.data.get('observacoes', ''),
            valor_estimado=valor_estimado_total,
            necessidade_origem=nec,
            org_id=nec.org_id,
            unidade_demandante=nec.unidade_demandante,
            created_by=request.user,
            updated_by=request.user,
        )

        for item in itens_data:
            ItemDFD.objects.create(
                dfd=dfd,
                item_catalogo_id=item.get('item_catalogo_id') or None,
                objeto=item.get('objeto', ''),
                unidade_medida=item.get('unidade_medida', 'un'),
                quantidade=item.get('quantidade', 1),
                valor_unitario_estimado=item.get('valor_unitario_estimado', 0),
                observacao=item.get('observacao', ''),
                org_id=nec.org_id,
                created_by=request.user,
                updated_by=request.user,
            )

        nec.status = 'DFD Criado'
        nec.dfd = dfd
        nec.updated_by = request.user
        nec.save(update_fields=['status', 'dfd', 'updated_by'])

        return Response(
            DFDSerializer(dfd, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def bloquear(self, request, pk=None):
        """Unidade de planejamento bloqueia necessidade não planejada ou sem orçamento."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode bloquear necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do bloqueio é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        nec = self.get_object()
        if nec.status not in ('Identificada', 'Em Análise'):
            return Response(
                {'detail': f'Necessidade com status "{nec.status}" não pode ser bloqueada.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obs = f'[Bloqueada] {motivo}'
        if nec.observacoes:
            obs = f'{obs}\n\n{nec.observacoes}'
        return self._transicao(request, pk, 'Cancelada',
                               campos_extra={'observacoes': obs, 'org_gestor_id': None})


class PlanoOrcamentarioViewSet(viewsets.ModelViewSet):
    """CRUD de Planos Orçamentários e gerenciamento de necessidades vinculadas."""
    serializer_class   = PlanoOrcamentarioSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields    = ['exercicio_fiscal', 'criado_em']
    ordering           = ['-exercicio_fiscal']
    search_fields      = ['descricao', 'orgao__sigla']

    def get_queryset(self):
        oid = self.request.org_id
        return PlanoOrcamentario.objects.filter(orgao_id=oid).prefetch_related(
            'itens__necessidade__org_id',
        )

    def _check_planejamento(self, request):
        return (
            getattr(request, 'tipo_unidade', None) == 'planejamento'
            or getattr(request, 'papel', None) in PAPEIS_PLANEJAMENTO
        )

    def perform_create(self, serializer):
        serializer.save(orgao_id=self.request.org_id)

    def create(self, request, *args, **kwargs):
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode cadastrar planos orçamentários.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode editar planos orçamentários.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode excluir planos orçamentários.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def vincular_necessidade(self, request, pk=None):
        """Vincula uma necessidade ao plano com classificação de origem."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode vincular necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        plano = self.get_object()
        necessidade_id = request.data.get('necessidade_id')
        origem = request.data.get('origem', 'propria')

        if not necessidade_id:
            return Response({'detail': 'necessidade_id é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if origem not in ('propria', 'orgao_filho'):
            return Response({'detail': 'origem deve ser "propria" ou "orgao_filho".'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            necessidade = NecessidadePlanejamento.objects.get(pk=necessidade_id)
        except NecessidadePlanejamento.DoesNotExist:
            return Response({'detail': 'Necessidade não encontrada.'},
                            status=status.HTTP_404_NOT_FOUND)

        item, created = ItemPlanoOrcamentario.objects.get_or_create(
            plano=plano, necessidade=necessidade, defaults={'origem': origem}
        )
        if not created:
            item.origem = origem
            item.save()

        serializer = ItemPlanoSerializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def desvincular_necessidade(self, request, pk=None):
        """Remove uma necessidade do plano."""
        if not self._check_planejamento(request):
            return Response(
                {'detail': 'Apenas a unidade de planejamento pode desvincular necessidades.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        plano = self.get_object()
        necessidade_id = request.data.get('necessidade_id')
        if not necessidade_id:
            return Response({'detail': 'necessidade_id é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = ItemPlanoOrcamentario.objects.filter(
            plano=plano, necessidade_id=necessidade_id
        ).delete()

        if not deleted:
            return Response({'detail': 'Necessidade não está vinculada a este plano.'},
                            status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
