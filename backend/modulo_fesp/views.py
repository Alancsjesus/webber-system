from decimal import Decimal

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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

    @action(detail=True, methods=['post'], url_path='gerar_necessidades')
    def gerar_necessidades(self, request, pk=None):
        _check_planejamento(request)
        grupo = self.get_object()
        if grupo.status == 'processado':
            return Response(
                {'detail': 'Este grupo já gerou necessidades.'}, status=status.HTTP_400_BAD_REQUEST,
            )
        from .services import gerar_necessidades_de_grupo
        necessidades = gerar_necessidades_de_grupo(grupo, request)
        return Response({
            'detail': f'{len(necessidades)} necessidade(s) gerada(s).',
            'necessidades_ids': [n.id for n in necessidades],
            'grupo': self.get_serializer(grupo).data,
        })

    @action(detail=True, methods=['post'])
    def desfazer(self, request, pk=None):
        _check_planejamento(request)
        grupo = self.get_object()
        if grupo.status == 'processado':
            return Response(
                {'detail': 'Grupo já processado — necessidades já foram geradas, não é possível desfazer.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        grupo.itens.update(grupo_consolidacao=None, status='pendente')
        grupo.delete()
        return Response({'detail': 'Consolidação desfeita.'})


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

    @action(detail=True, methods=['post'], url_path='gerar_necessidade_individual')
    def gerar_necessidade_individual(self, request, pk=None):
        _check_planejamento(request)
        item = self.get_object()
        if item.status != 'pendente':
            return Response(
                {'detail': 'Este item já está consolidado ou já gerou necessidade.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .services import gerar_necessidade_individual
        nec = gerar_necessidade_individual(item, request)
        return Response({
            'detail': 'Necessidade gerada.' if nec else 'Nenhuma necessidade gerada.',
            'necessidade_id': nec.id if nec else None,
            'item': self.get_serializer(item).data,
        })


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
        natureza = self.request.query_params.get('natureza')
        if exercicio:
            qs = qs.filter(exercicio_fiscal=exercicio)
        if stat:
            qs = qs.filter(status=stat)
        if natureza:
            qs = qs.filter(natureza=natureza)
        return qs

    def perform_create(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_planejamento(self.request)
        serializer.save()

    def _transicao(self, plano, novo_status, usuario, motivo=''):
        permitidos = plano.transicoes_permitidas.get(plano.status, [])
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
        if not plano.usa_rito_conselho:
            return Response(
                {'detail': 'Este plano não segue o rito do Conselho Gestor — use a ação "aprovar".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        if not plano.usa_rito_conselho:
            return Response(
                {'detail': 'Este plano não segue o rito do Conselho Gestor.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
        if not plano.usa_rito_conselho:
            return Response(
                {'detail': 'Este plano não segue o rito do Conselho Gestor.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Motivo da devolução é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
        plano.motivo_devolucao_conselho = motivo
        plano.save(update_fields=['motivo_devolucao_conselho'])
        self._transicao(plano, 'devolvido', request.user, motivo)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        """Reabre um plano devolvido pelo Conselho para nova edição/ajustes."""
        _check_planejamento(request)
        plano = self.get_object()
        self._transicao(plano, 'elaboracao', request.user)
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """Aprovação direta (sem Conselho Gestor/homologação) para naturezas != FESP."""
        plano = self.get_object()
        if plano.usa_rito_conselho:
            return Response(
                {'detail': 'Planos FESP seguem o rito do Conselho Gestor — use "submeter_conselho"/"aprovar_conselho".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        papel = getattr(request, 'papel', None)
        if papel not in ('admin', 'gestor_planejamento', 'ordenador'):
            return Response(
                {'detail': 'Apenas Planejamento, Ordenador ou Admin podem aprovar este plano.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        from core.checklist_engine import ChecklistEngine
        resultado = ChecklistEngine.avaliar_plano_aplicacao(plano)
        if not resultado.pode_submeter:
            return Response(
                {
                    'detail': 'Plano não pode ser aprovado — há pendências obrigatórias.',
                    'bloqueadores': [b.detalhe for b in resultado.bloqueadores],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._transicao(plano, 'aprovado', request.user, request.data.get('motivo', ''))
        return Response(self.get_serializer(plano).data)

    @action(detail=True, methods=['post'])
    def homologar(self, request, pk=None):
        plano = self.get_object()
        if not plano.usa_rito_conselho:
            return Response(
                {'detail': 'Este plano não exige homologação por ato do Chefe do Executivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        papel = getattr(request, 'papel', None)
        if papel not in ('admin', 'ordenador'):
            return Response(
                {'detail': 'Apenas o Ordenador de Despesa pode registrar a homologação.'},
                status=status.HTTP_403_FORBIDDEN,
            )
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

    # ── Consolidação de itens (Fase 3) ──────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='sugestoes_consolidacao')
    def sugestoes_consolidacao(self, request, pk=None):
        """
        Agrupa os itens pendentes do plano (de todas as Metas Específicas) por
        chave de agrupamento (família SIMPAS ou prefixo do Cód. SENASP),
        destacando quando a mesma chave aparece em mais de um órgão
        beneficiário — candidato a consolidação.
        """
        from .services import chave_agrupamento
        plano = self.get_object()
        qs = (
            ItemPlanoAplicacao.objects
            .filter(meta_especifica__plano=plano, status='pendente')
            .select_related('org_beneficiaria', 'item_catalogo')
        )
        grupos = {}
        for item in qs:
            chave = chave_agrupamento(item)
            if not chave:
                continue
            g = grupos.setdefault(chave, {'chave': chave, 'itens': [], 'orgaos': {}})
            g['itens'].append(item)
            org = item.org_beneficiaria
            info = g['orgaos'].setdefault(org.id, {'org_id': org.id, 'sigla': org.sigla, 'nome': org.nome, 'qtd_itens': 0, 'valor': Decimal('0')})
            info['qtd_itens'] += 1
            info['valor'] += item.valor_total_estimado

        resultado = []
        for chave, g in grupos.items():
            n_orgaos = len(g['orgaos'])
            resultado.append({
                'chave_agrupamento': chave,
                'total_itens': len(g['itens']),
                'total_orgaos': n_orgaos,
                'multi_orgao': n_orgaos > 1,
                'valor_total': sum((i.valor_total_estimado for i in g['itens']), Decimal('0')),
                'orgaos': list(g['orgaos'].values()),
                'itens': ItemPlanoAplicacaoSerializer(g['itens'], many=True).data,
            })
        resultado.sort(key=lambda g: (not g['multi_orgao'], -g['total_itens']))
        return Response({'grupos_sugeridos': resultado})

    @action(detail=True, methods=['post'], url_path='confirmar_consolidacao')
    def confirmar_consolidacao(self, request, pk=None):
        _check_planejamento(request)
        plano = self.get_object()
        item_ids = request.data.get('item_ids') or []
        titulo = (request.data.get('titulo') or '').strip()
        if not item_ids or not titulo:
            return Response(
                {'detail': 'Informe "titulo" e ao menos um item em "item_ids".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        itens = ItemPlanoAplicacao.objects.filter(
            id__in=item_ids, meta_especifica__plano=plano, status='pendente',
        )
        if not itens.exists():
            return Response(
                {'detail': 'Nenhum dos itens informados está disponível para consolidação.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from .services import chave_agrupamento
        primeiro = itens.first()
        grupo = GrupoConsolidacaoItem.objects.create(
            org_id_id=request.org_id, created_by=request.user, updated_by=request.user,
            plano=plano, chave_agrupamento=request.data.get('chave_agrupamento') or chave_agrupamento(primeiro),
            titulo=titulo, descricao=request.data.get('descricao', ''),
        )
        itens.update(grupo_consolidacao=grupo, status='consolidado')
        return Response({
            'detail': f'{itens.count()} item(ns) consolidado(s) em "{titulo}".',
            'grupo': GrupoConsolidacaoItemSerializer(grupo).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='gerar_necessidades')
    def gerar_necessidades(self, request, pk=None):
        """Gera necessidades em lote para vários grupos de consolidação do plano. Body: {grupo_ids: [...]}."""
        _check_planejamento(request)
        plano = self.get_object()
        grupo_ids = request.data.get('grupo_ids') or []
        if not grupo_ids:
            return Response({'detail': 'Informe ao menos um grupo em "grupo_ids".'}, status=status.HTTP_400_BAD_REQUEST)

        from .services import gerar_necessidades_de_grupo
        total_necessidades = []
        for grupo in GrupoConsolidacaoItem.objects.filter(id__in=grupo_ids, plano=plano).exclude(status='processado'):
            total_necessidades.extend(gerar_necessidades_de_grupo(grupo, request))

        return Response({
            'detail': f'{len(total_necessidades)} necessidade(s) gerada(s) a partir de {len(grupo_ids)} grupo(s).',
            'necessidades_ids': [n.id for n in total_necessidades],
        })

    # ── Rastreabilidade financeira / prestação de contas (Fase 4) ───────────

    @action(detail=True, methods=['get'])
    def execucao(self, request, pk=None):
        """
        Dashboard de prestação de contas: para cada Necessidade originada
        deste plano, a etapa atual da cadeia (Necessidade→DFD→ETP→TR→
        Procedimento→Contrato) e um resumo de valores planejados x já
        levados a DFD x já contratados. Reaproveita _cadeia/_etapa_atual de
        core.views_rastreabilidade em vez de duplicar essa lógica.
        """
        from core.views_rastreabilidade import _cadeia, _etapa_atual, _qs_base
        plano = self.get_object()

        necessidades = _qs_base().filter(origem_plano_aplicacao_fesp=plano).select_related('org_id')

        linhas = []
        valor_planejado = Decimal('0')
        valor_em_dfd = Decimal('0')
        valor_contratado = Decimal('0')

        for nec in necessidades:
            cadeia = _cadeia(nec)
            etapa_nome, etapa_idx = _etapa_atual(cadeia)
            valor_planejado += nec.valor_estimado or Decimal('0')

            dfd = nec.dfd
            if dfd:
                valor_em_dfd += dfd.valor_estimado or Decimal('0')
                for contrato in dfd.contratos.all():
                    valor_contratado += contrato.valor_contrato or Decimal('0')

            linhas.append({
                'necessidade_id': nec.id,
                'titulo': nec.titulo,
                'org_id': nec.org_id_id,
                'org_sigla': nec.org_id.sigla if nec.org_id else None,
                'valor_estimado': str(nec.valor_estimado),
                'etapa_atual': etapa_nome,
                'etapa_idx': etapa_idx,
                'total_etapas': len(cadeia),
            })

        return Response({
            'plano_id': plano.id,
            'plano_numero': plano.numero,
            'resumo': {
                'total_necessidades': len(linhas),
                'valor_planejado': str(valor_planejado),
                'valor_em_dfd': str(valor_em_dfd),
                'valor_contratado': str(valor_contratado),
                'valor_sem_uso': str(valor_planejado - valor_em_dfd),
            },
            'necessidades': linhas,
        })

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        plano = self.get_object()
        from exportacao.pdf_utils import gerar_pdf_plano_aplicacao, resposta_pdf
        pdf = gerar_pdf_plano_aplicacao(plano)
        return resposta_pdf(pdf, f'PlanoAplicacao-{plano.numero}.pdf')


class IndicadoresExecucaoFespView(APIView):
    """
    Painel de evolução de execução dos Planos de Aplicação FESP: itens
    pendentes vs. executados (já contratados), agrupados por Órgão
    Beneficiário × Exercício Fiscal × Eixo (campo `ementa` do plano).

    GET /api/fesp/indicadores/execucao/
    Parâmetros opcionais:
      ?exercicio=2026        — filtra por exercício do plano
      ?org_beneficiaria=<id> — filtra por órgão beneficiário do item
      ?eixo=<texto>          — busca parcial (icontains) no eixo/ementa do plano
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from .indicadores import itens_plano_aplicacao_queryset

        qs = itens_plano_aplicacao_queryset(request.org_id).exclude(status='cancelado')

        exercicio = request.query_params.get('exercicio')
        org_beneficiaria = request.query_params.get('org_beneficiaria')
        eixo = request.query_params.get('eixo')
        if exercicio:
            qs = qs.filter(meta_especifica__plano__exercicio_fiscal=exercicio)
        if org_beneficiaria:
            qs = qs.filter(org_beneficiaria_id=org_beneficiaria)
        if eixo:
            qs = qs.filter(meta_especifica__plano__ementa__icontains=eixo)

        grupos: dict = {}
        totais = {'pendentes': 0, 'executados': 0, 'valor_pendente': Decimal('0'), 'valor_executado': Decimal('0')}

        for item in qs:
            plano = item.meta_especifica.plano
            chave = (item.org_beneficiaria_id, plano.exercicio_fiscal, plano.ementa)
            if chave not in grupos:
                grupos[chave] = {
                    'org_beneficiaria_id': item.org_beneficiaria_id,
                    'org_sigla': item.org_beneficiaria.sigla,
                    'org_nome': item.org_beneficiaria.nome,
                    'exercicio': plano.exercicio_fiscal,
                    'eixo': plano.ementa,
                    'pendentes': 0,
                    'executados': 0,
                    'valor_pendente': Decimal('0'),
                    'valor_executado': Decimal('0'),
                }
            g = grupos[chave]
            valor = item.valor_total_estimado or Decimal('0')
            if item.executado:
                g['executados'] += 1
                g['valor_executado'] += valor
                totais['executados'] += 1
                totais['valor_executado'] += valor
            else:
                g['pendentes'] += 1
                g['valor_pendente'] += valor
                totais['pendentes'] += 1
                totais['valor_pendente'] += valor

        lista_grupos = sorted(grupos.values(), key=lambda g: (g['org_sigla'] or '', g['exercicio'] or 0, g['eixo'] or ''))
        for g in lista_grupos:
            g['valor_pendente'] = str(g['valor_pendente'])
            g['valor_executado'] = str(g['valor_executado'])
        totais['valor_pendente'] = str(totais['valor_pendente'])
        totais['valor_executado'] = str(totais['valor_executado'])

        return Response({'totais': totais, 'grupos': lista_grupos})


class RelatorioItensPlanoAplicacaoView(APIView):
    """
    Relatório tabular de itens dos Planos de Aplicação FESP, com filtros e
    exportação em PDF/XLSX.

    GET /api/fesp/relatorio-itens/
    Parâmetros opcionais:
      ?exercicio=2026         — filtra por exercício do plano
      ?org_beneficiaria=<id>  — filtra por órgão beneficiário do item
      ?natureza=custeio|investimento
      ?status=pendente|consolidado|necessidade_gerada|cancelado
      ?executado=true|false   — usa a anotação de execução (Contrato vinculado)
      ?eixo=<texto>           — busca parcial no eixo/ementa do plano
      ?export=pdf|xlsx        — exporta em vez de retornar JSON (não usar "format":
                                 é reservado pela negociação de conteúdo do DRF)
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from .indicadores import itens_plano_aplicacao_queryset

        qs = itens_plano_aplicacao_queryset(request.org_id)

        exercicio = request.query_params.get('exercicio')
        org_beneficiaria = request.query_params.get('org_beneficiaria')
        natureza = request.query_params.get('natureza')
        status_param = request.query_params.get('status')
        executado_param = request.query_params.get('executado')
        eixo = request.query_params.get('eixo')

        if exercicio:
            qs = qs.filter(meta_especifica__plano__exercicio_fiscal=exercicio)
        if org_beneficiaria:
            qs = qs.filter(org_beneficiaria_id=org_beneficiaria)
        if natureza:
            qs = qs.filter(natureza=natureza)
        if status_param:
            qs = qs.filter(status=status_param)
        if executado_param in ('true', 'false'):
            qs = qs.filter(executado=(executado_param == 'true'))
        if eixo:
            qs = qs.filter(meta_especifica__plano__ementa__icontains=eixo)

        qs = qs.order_by('meta_especifica__plano__exercicio_fiscal', 'meta_especifica__plano__numero', 'meta_especifica__numero')

        # Nome do param é "export", não "format" — "format" é reservado pelo DRF
        # (URL_FORMAT_OVERRIDE / negociação de conteúdo) e um valor não reconhecido
        # como renderer (ex: "pdf") faz o DRF responder 404 antes de chegar aqui.
        fmt = request.query_params.get('export')
        if fmt == 'pdf':
            from core.models import Orgao
            from exportacao.pdf_utils import gerar_pdf_relatorio_itens_plano_aplicacao, resposta_pdf
            orgao = Orgao.objects.filter(pk=request.org_id).first()
            org_nome = orgao.nome if orgao else 'WEBBER'
            org_sigla = orgao.sigla if orgao else None
            pdf = gerar_pdf_relatorio_itens_plano_aplicacao(list(qs), org_nome, org_sigla)
            nome = f'RelatorioItensFESP{"-" + str(exercicio) if exercicio else ""}.pdf'
            return resposta_pdf(pdf, nome)
        if fmt == 'xlsx':
            from exportacao.xlsx_utils import gerar_xlsx_relatorio_itens_plano_aplicacao
            nome = f'RelatorioItensFESP{"-" + str(exercicio) if exercicio else ""}.xlsx'
            return gerar_xlsx_relatorio_itens_plano_aplicacao(list(qs), nome)

        linhas = []
        for item in qs:
            plano = item.meta_especifica.plano
            linhas.append({
                'item_id': item.id,
                'plano_numero': plano.numero,
                'exercicio': plano.exercicio_fiscal,
                'eixo': plano.ementa,
                'org_gestor_sigla': plano.org_id.sigla if plano.org_id else None,
                'org_beneficiaria_sigla': item.org_beneficiaria.sigla,
                'meta_titulo': item.meta_especifica.titulo,
                'natureza': item.natureza,
                'natureza_display': item.get_natureza_display(),
                'bem_servico': item.bem_servico,
                'status': item.status,
                'status_display': item.get_status_display(),
                'executado': item.executado,
                'valor_total_estimado': str(item.valor_total_estimado or Decimal('0')),
            })

        return Response({'total': len(linhas), 'itens': linhas})
