import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.models import Orgao
from core.permissions import IsMultiTenant
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_planejamento.serializers import NecessidadeSerializer

logger = logging.getLogger(__name__)

from .filters import AcaoOrcamentariaFilter, FonteRecursoFilter, DotacaoOrcamentariaFilter
from .models import (
    AcaoOrcamentaria, ElementoDespesa, NaturezaDespesa, FonteRecurso,
    DotacaoOrcamentaria, IndicacaoOrcamentaria, IndicacaoDotacao, HistoricoIndicacao,
    TipoAcaoOrcamentaria, TipoFonteRecurso,
)
from .serializers import (
    AcaoOrcamentariaSerializer,
    ElementoDespesaSerializer,
    NaturezaDespesaSerializer,
    FonteRecursoSerializer,
    DotacaoOrcamentariaSerializer,
    VincularNecessidadeSerializer,
    IndicacaoOrcamentariaSerializer,
    VincularDotacaoSerializer,
    TipoAcaoOrcamentariaSerializer,
    TipoFonteRecursoSerializer,
)


def _check_permissao_planejamento(request):
    """Restringe escrita nos catálogos globais de Orçamento a Planejamento/Admin."""
    papel = getattr(request, 'papel', None)
    tipo_unidade = getattr(request, 'tipo_unidade', None)
    if papel not in ('admin', 'gestor_planejamento') and tipo_unidade != 'planejamento':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Apenas Planejamento ou Admin podem gerenciar este catálogo.')


class TipoAcaoOrcamentariaViewSet(viewsets.ModelViewSet):
    """Catálogo parametrizável de tipos de Ação Orçamentária (Configurações → Orçamento)."""
    serializer_class = TipoAcaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['descricao']
    ordering = ['descricao']

    def get_queryset(self):
        mostrar_inativos = self.request.query_params.get('inativos') == 'true'
        qs = TipoAcaoOrcamentaria.objects.all()
        if not mostrar_inativos:
            qs = qs.filter(ativo=True)
        return qs

    def perform_create(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao_planejamento(self.request)
        instance.ativo = False
        instance.save()


class TipoFonteRecursoViewSet(viewsets.ModelViewSet):
    """Catálogo parametrizável de tipos de Fonte de Recurso (Configurações → Orçamento)."""
    serializer_class = TipoFonteRecursoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao']
    ordering_fields = ['descricao']
    ordering = ['descricao']

    def get_queryset(self):
        mostrar_inativos = self.request.query_params.get('inativos') == 'true'
        qs = TipoFonteRecurso.objects.all()
        if not mostrar_inativos:
            qs = qs.filter(ativo=True)
        return qs

    def perform_create(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao_planejamento(self.request)
        instance.ativo = False
        instance.save()


class AcaoOrcamentariaViewSet(viewsets.ModelViewSet):
    serializer_class = AcaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AcaoOrcamentariaFilter
    search_fields = ['codigo', 'nome', 'descricao']
    ordering_fields = ['codigo', 'nome', 'tipo', 'created_at']
    ordering = ['codigo']

    def get_queryset(self):
        return AcaoOrcamentaria.objects.filter(org_id=self.request.org_id)


class ElementoDespesaViewSet(viewsets.ModelViewSet):
    """
    Elementos de despesa (código 2 dígitos: 30, 39, 52...).
    Gerenciados pela Unidade de Planejamento ou Admin.
    """
    serializer_class = ElementoDespesaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['descricao', 'codigo']
    ordering_fields = ['codigo']
    ordering = ['codigo']

    def get_queryset(self):
        mostrar_inativos = self.request.query_params.get('inativos') == 'true'
        qs = ElementoDespesa.objects.all()
        if not mostrar_inativos:
            qs = qs.filter(ativo=True)
        return qs

    def _check_permissao(self, request):
        papel = getattr(request, 'papel', None)
        tipo_unidade = getattr(request, 'tipo_unidade', None)
        if papel not in ('admin', 'gestor_planejamento') and tipo_unidade != 'planejamento':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas Planejamento ou Admin podem gerenciar elementos de despesa.')

    def perform_create(self, serializer):
        self._check_permissao(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_permissao(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_permissao(self.request)
        instance.ativo = False
        instance.save()


class NaturezaDespesaViewSet(viewsets.ModelViewSet):
    """
    Naturezas de despesa no formato 3.3.90.30 (ex: 339030, 339039, 449052).
    Gerenciadas pela Unidade de Planejamento ou Admin.
    """
    serializer_class = NaturezaDespesaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['codigo', 'descricao']
    ordering_fields = ['codigo']
    ordering = ['codigo']

    def get_queryset(self):
        qs = NaturezaDespesa.objects.select_related('elemento_despesa')
        elemento = self.request.query_params.get('elemento_despesa')
        if elemento:
            qs = qs.filter(elemento_despesa_id=elemento)
        mostrar_inativas = self.request.query_params.get('inativas') == 'true'
        if not mostrar_inativas:
            qs = qs.filter(ativa=True)
        return qs

    def _check_permissao(self, request):
        papel = getattr(request, 'papel', None)
        tipo_unidade = getattr(request, 'tipo_unidade', None)
        if papel not in ('admin', 'gestor_planejamento') and tipo_unidade != 'planejamento':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas Planejamento ou Admin podem gerenciar naturezas de despesa.')

    def perform_create(self, serializer):
        self._check_permissao(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_permissao(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_permissao(self.request)
        instance.ativa = False
        instance.save()


class FonteRecursoViewSet(viewsets.ModelViewSet):
    serializer_class = FonteRecursoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FonteRecursoFilter
    search_fields = ['nome', 'codigo']
    ordering_fields = ['codigo', 'nome', 'tipo']
    ordering = ['codigo']

    def get_queryset(self):
        return FonteRecurso.objects.filter(org_id=self.request.org_id)


class DotacaoOrcamentariaViewSet(viewsets.ModelViewSet):
    serializer_class = DotacaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DotacaoOrcamentariaFilter
    search_fields = ['eixo', 'objetivo_estrategico', 'observacoes', 'acao__nome', 'acao__codigo']
    ordering_fields = ['exercicio_fiscal', 'valor_dotado', 'status', 'created_at']
    ordering = ['-exercicio_fiscal', 'acao__codigo']

    def get_queryset(self):
        return DotacaoOrcamentaria.objects.filter(
            org_id=self.request.org_id
        ).select_related('acao', 'elemento_despesa', 'fonte_recurso')

    def _get_necessidade_autorizada(self, necessidade_id, org_id):
        """Retorna a necessidade se pertencer ao próprio órgão ou a um filho."""
        child_ids = Orgao.objects.filter(parent_id=org_id).values_list('id', flat=True)
        return get_object_or_404(
            NecessidadePlanejamento,
            id=necessidade_id,
            org_id__in=[org_id, *child_ids],
        )

    @action(detail=True, methods=['post'], url_path='vincular-necessidade')
    def vincular_necessidade(self, request, pk=None):
        dotacao = self.get_object()
        serializer = VincularNecessidadeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        necessidade_id = serializer.validated_data['necessidade_id']
        necessidade = self._get_necessidade_autorizada(necessidade_id, request.org_id)
        dotacao.necessidades.add(necessidade)
        return Response(
            {'detail': f'Necessidade "{necessidade.titulo}" vinculada com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='desvincular-necessidade')
    def desvincular_necessidade(self, request, pk=None):
        dotacao = self.get_object()
        serializer = VincularNecessidadeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        necessidade_id = serializer.validated_data['necessidade_id']
        necessidade = self._get_necessidade_autorizada(necessidade_id, request.org_id)
        dotacao.necessidades.remove(necessidade)
        return Response(
            {'detail': f'Necessidade "{necessidade.titulo}" desvinculada com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['get'], url_path='necessidades-disponiveis')
    def necessidades_disponiveis(self, request, pk=None):
        dotacao = self.get_object()
        org_id  = request.org_id
        exercicio = dotacao.exercicio_fiscal
        vinculadas_ids = list(dotacao.necessidades.values_list('id', flat=True))

        # Órgãos filhos cujas necessidades externas o órgão pai pode incluir no plano
        child_ids = Orgao.objects.filter(parent_id=org_id).values_list('id', flat=True)

        # Base: necessidades próprias + necessidades externas de filhos
        base_qs = NecessidadePlanejamento.objects.filter(
            Q(org_id=org_id) |
            Q(org_id__in=child_ids, tipo_execucao='externa')
        ).distinct()

        # ── contagens por etapa para diagnóstico ──────────────────────────
        todas       = base_qs
        mesmo_exerc = todas.filter(exercicio_fiscal=exercicio)
        status_ok   = mesmo_exerc.filter(status__in=('Aprovada', 'DFD Criado'))
        disponiveis = status_ok.exclude(id__in=vinculadas_ids)

        total_org    = todas.count()
        total_exerc  = mesmo_exerc.count()
        total_status = status_ok.count()
        total_disp   = disponiveis.count()

        logger.info(
            "[necessidades-disponiveis] dotacao=%s org=%s filhos=%s exercicio=%s | "
            "visíveis=%d exercicio=%d status_ok=%d disponiveis=%d vinculadas=%d",
            dotacao.pk, org_id, list(child_ids), exercicio,
            total_org, total_exerc, total_status, total_disp, len(vinculadas_ids),
        )

        # ── resposta vazia com diagnóstico em linguagem natural ───────────
        if total_disp == 0:
            tem_filhos = len(list(child_ids)) > 0
            escopo = "neste órgão ou em órgãos subordinados" if tem_filhos else "neste órgão"

            if total_org == 0:
                motivo = (
                    f"Nenhuma necessidade de planejamento encontrada {escopo}. "
                    "Cadastre e aprove necessidades antes de vinculá-las à dotação."
                )
            elif total_exerc == 0:
                outros = list(todas.values_list('exercicio_fiscal', flat=True).distinct())
                motivo = (
                    f"Existem {total_org} necessidade(s) visível(is), mas nenhuma está "
                    f"cadastrada para o exercício fiscal {exercicio} desta dotação. "
                    f"Exercícios encontrados: {outros or 'nenhum'}."
                )
            elif total_status == 0:
                status_encontrados = list(mesmo_exerc.values_list('status', flat=True).distinct())
                motivo = (
                    f"Existem {total_exerc} necessidade(s) para o exercício {exercicio}, "
                    f"mas nenhuma está com status 'Aprovada' ou 'DFD Criado'. "
                    f"Status atuais: {status_encontrados}. "
                    "Aprove as necessidades no módulo de planejamento antes de vinculá-las."
                )
            else:
                motivo = (
                    f"As {total_status} necessidade(s) elegíveis já estão vinculadas a esta dotação."
                )

            logger.warning("[necessidades-disponiveis] lista vazia — %s", motivo)
            return Response({'results': [], 'diagnostico': motivo})

        serializer = NecessidadeSerializer(disponiveis, many=True, context={'request': request})
        return Response(serializer.data)


class IndicacaoOrcamentariaViewSet(viewsets.ModelViewSet):
    """Indicações Orçamentárias / DOD."""
    serializer_class   = IndicacaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['numero', 'observacoes', 'dfd__numero_sei', 'necessidade__titulo']
    ordering_fields    = ['exercicio_fiscal', 'status', 'created_at']
    ordering           = ['-exercicio_fiscal', '-created_at']

    def get_queryset(self):
        qs = IndicacaoOrcamentaria.objects.filter(
            org_id=self.request.org_id
        ).select_related('dfd', 'necessidade', 'ordenador', 'org_id', 'created_by')
        exercicio = self.request.query_params.get('exercicio_fiscal')
        stat      = self.request.query_params.get('status')
        if exercicio:
            qs = qs.filter(exercicio_fiscal=exercicio)
        if stat:
            qs = qs.filter(status=stat)
        return qs

    def _check_planejamento(self, request):
        papel      = getattr(request, 'papel', None)
        tipo_unid  = getattr(request, 'tipo_unidade', None)
        from rest_framework.exceptions import PermissionDenied
        if papel not in ('admin', 'gestor_planejamento', 'ordenador') and tipo_unid != 'planejamento':
            raise PermissionDenied('Apenas Planejamento, Ordenador ou Admin podem gerenciar indicações.')

    def perform_create(self, serializer):
        self._check_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_planejamento(self.request)
        serializer.save()

    def _transicao(self, indicacao, novo_status, usuario, motivo=None):
        permitidos = IndicacaoOrcamentaria.TRANSICOES_PERMITIDAS.get(indicacao.status, [])
        if novo_status not in permitidos:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f'Transição "{indicacao.status}" → "{novo_status}" não permitida.'
            )
        anterior = indicacao.status
        indicacao.status = novo_status
        indicacao.updated_by = usuario
        indicacao.save()
        HistoricoIndicacao.objects.create(
            indicacao=indicacao, status_anterior=anterior,
            status_novo=novo_status, usuario=usuario, motivo=motivo,
        )

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        indicacao = self.get_object()
        if not indicacao.itens.exists():
            return Response(
                {'detail': 'Vincule ao menos uma dotação antes de submeter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._transicao(indicacao, 'Submetida', request.user)
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Indicação submetida com sucesso.', **serializer})

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in ('admin', 'ordenador'):
            return Response(
                {'detail': 'Apenas o Ordenador de Despesa pode aprovar indicações.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        indicacao = self.get_object()
        self._transicao(indicacao, 'Aprovada', request.user)
        from datetime import date
        indicacao.ordenador       = request.user
        indicacao.data_aprovacao  = date.today()
        indicacao.save()
        # Atualiza valor_indicado nas dotações vinculadas
        for item in indicacao.itens.select_related('dotacao'):
            dot = item.dotacao
            dot.valor_indicado = item.valor_indicado
            dot.save(update_fields=['valor_indicado'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'DOD emitida. Indicação aprovada com sucesso.', **serializer})

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        indicacao = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response(
                {'detail': 'Motivo do cancelamento é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self._transicao(indicacao, 'Cancelada', request.user, motivo)
        indicacao.motivo_cancelamento = motivo
        indicacao.save(update_fields=['motivo_cancelamento'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Indicação cancelada.', **serializer})

    @action(detail=True, methods=['post'], url_path='vincular-dotacao')
    def vincular_dotacao(self, request, pk=None):
        indicacao = self.get_object()
        if indicacao.status not in ('Rascunho',):
            return Response(
                {'detail': 'Só é possível vincular dotações em Rascunho.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = VincularDotacaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dotacao_id     = serializer.validated_data['dotacao_id']
        valor_indicado = serializer.validated_data['valor_indicado']

        dotacao = get_object_or_404(
            DotacaoOrcamentaria, id=dotacao_id, org_id=request.org_id
        )
        item, created = IndicacaoDotacao.objects.update_or_create(
            indicacao=indicacao, dotacao=dotacao,
            defaults={'valor_indicado': valor_indicado},
        )
        # Recalcular valor total
        total = sum(i.valor_indicado for i in indicacao.itens.all())
        indicacao.valor_total = total
        indicacao.save(update_fields=['valor_total'])

        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': f'Dotação vinculada com R$ {valor_indicado:,.2f}.', **serializer})

    @action(detail=True, methods=['post'], url_path='desvincular-dotacao')
    def desvincular_dotacao(self, request, pk=None):
        indicacao = self.get_object()
        if indicacao.status not in ('Rascunho',):
            return Response(
                {'detail': 'Só é possível desvincular dotações em Rascunho.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dotacao_id = request.data.get('dotacao_id')
        IndicacaoDotacao.objects.filter(indicacao=indicacao, dotacao_id=dotacao_id).delete()
        total = sum(i.valor_indicado for i in indicacao.itens.all())
        indicacao.valor_total = total
        indicacao.save(update_fields=['valor_total'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Dotação desvinculada.', **serializer})

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        indicacao = self.get_object()
        from exportacao.pdf_utils import gerar_pdf_indicacao, resposta_pdf
        pdf = gerar_pdf_indicacao(indicacao)
        return resposta_pdf(pdf, f'DOD-{indicacao.numero}.pdf')

    # ── NPO / Descentralização ──────────────────────────────────────────────── #

    @action(detail=True, methods=['post'], url_path='registrar-npos')
    def registrar_npos(self, request, pk=None):
        """
        Registra NPOs em bloco para todas as dotações de uma indicação aprovada.
        Payload: { "npos": [{"indicacao_dotacao_id": X, "numero_npo": "...", "data_emissao": "YYYY-MM-DD", "valor": 1000.00, "observacoes": ""}, ...] }
        Ignora itens sem numero_npo ou valor.
        """
        from .models import DescentralizacaoOrcamentaria, IndicacaoDotacao
        from .serializers import DescentralizacaoSerializer
        from decimal import Decimal

        indicacao = self.get_object()
        if indicacao.status != 'Aprovada':
            return Response({'detail': 'NPOs só podem ser registradas em indicações aprovadas.'},
                            status=status.HTTP_400_BAD_REQUEST)

        npos_data = request.data.get('npos', [])
        criados = []
        for item in npos_data:
            ind_dot_id  = item.get('indicacao_dotacao_id')
            numero_npo  = (item.get('numero_npo') or '').strip()
            valor       = item.get('valor')
            data_emis   = item.get('data_emissao')
            obs         = item.get('observacoes', '')
            if not (ind_dot_id and numero_npo and valor and data_emis):
                continue
            ind_dot = get_object_or_404(IndicacaoDotacao, pk=ind_dot_id, indicacao=indicacao)
            npo = DescentralizacaoOrcamentaria.objects.create(
                indicacao_dotacao=ind_dot,
                numero_npo=numero_npo,
                data_emissao=data_emis,
                valor=Decimal(str(valor)),
                observacoes=obs,
                registrada_por=request.user,
            )
            # Atualizar valor_descentralizado da dotação
            ind_dot.dotacao.valor_descentralizado = (
                ind_dot.dotacao.valor_descentralizado + Decimal(str(valor))
            )
            ind_dot.dotacao.save(update_fields=['valor_descentralizado'])
            criados.append(npo.id)

        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': f'{len(criados)} NPO(s) registrada(s).', **serializer}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'cancelar-npo/(?P<npo_pk>[^/.]+)')
    def cancelar_npo(self, request, pk=None, npo_pk=None):
        from .models import DescentralizacaoOrcamentaria
        from decimal import Decimal
        from django.shortcuts import get_object_or_404 as goo
        indicacao = self.get_object()
        npo = goo(DescentralizacaoOrcamentaria, pk=npo_pk,
                  indicacao_dotacao__indicacao=indicacao, cancelada=False)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do cancelamento é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        dotacao = npo.indicacao_dotacao.dotacao
        concedido = dotacao.valor_concedido
        novo_desc = dotacao.valor_descentralizado - npo.valor
        if novo_desc < concedido:
            return Response({
                'detail': f'Não é possível cancelar: R$ {float(concedido):,.2f} já foram concedidos contra este saldo descentralizado.'
            }, status=status.HTTP_400_BAD_REQUEST)

        from datetime import date
        npo.cancelada = True
        npo.data_cancelamento = date.today()
        npo.motivo_cancelamento = motivo
        npo.save()
        dotacao.valor_descentralizado = novo_desc
        dotacao.save(update_fields=['valor_descentralizado'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'NPO cancelada.', **serializer})

    # ── Concessão ───────────────────────────────────────────────────────────── #

    @action(detail=True, methods=['post'], url_path='registrar-concessoes')
    def registrar_concessoes(self, request, pk=None):
        """
        Registra concessões em bloco.
        Payload: { "concessoes": [{"indicacao_dotacao_id": X, "numero_doc": "...", "data_emissao": "...", "valor": ..., "observacoes": ""}, ...] }
        Valida: valor_concedido + novo_valor <= valor_descentralizado.
        """
        from .models import ConcessaoOrcamentaria, IndicacaoDotacao
        from decimal import Decimal

        indicacao = self.get_object()
        if indicacao.status != 'Aprovada':
            return Response({'detail': 'Concessões só podem ser registradas em indicações aprovadas.'},
                            status=status.HTTP_400_BAD_REQUEST)

        conc_data = request.data.get('concessoes', [])
        criados = []
        erros   = []
        for item in conc_data:
            ind_dot_id = item.get('indicacao_dotacao_id')
            numero_doc = (item.get('numero_doc') or '').strip()
            valor      = item.get('valor')
            data_emis  = item.get('data_emissao')
            obs        = item.get('observacoes', '')
            if not (ind_dot_id and numero_doc and valor and data_emis):
                continue
            ind_dot = get_object_or_404(IndicacaoDotacao, pk=ind_dot_id, indicacao=indicacao)
            dotacao = ind_dot.dotacao
            novo_valor = Decimal(str(valor))
            if dotacao.valor_concedido + novo_valor > dotacao.valor_descentralizado:
                erros.append(f'Dotação {dotacao.id}: valor concedido superaria o descentralizado.')
                continue
            ConcessaoOrcamentaria.objects.create(
                indicacao_dotacao=ind_dot,
                numero_doc=numero_doc,
                data_emissao=data_emis,
                valor=novo_valor,
                observacoes=obs,
                registrada_por=request.user,
            )
            dotacao.valor_concedido = dotacao.valor_concedido + novo_valor
            dotacao.save(update_fields=['valor_concedido'])
            criados.append(ind_dot_id)

        serializer = self._indicacao_serializer(indicacao)
        msg = f'{len(criados)} concessão(ões) registrada(s).'
        if erros:
            msg += ' Erros: ' + ' | '.join(erros)
        return Response({'detail': msg, **serializer}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'cancelar-concessao/(?P<conc_pk>[^/.]+)')
    def cancelar_concessao(self, request, pk=None, conc_pk=None):
        from .models import ConcessaoOrcamentaria
        from decimal import Decimal
        from django.shortcuts import get_object_or_404 as goo
        indicacao = self.get_object()
        conc = goo(ConcessaoOrcamentaria, pk=conc_pk,
                   indicacao_dotacao__indicacao=indicacao, cancelada=False)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do cancelamento é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        from datetime import date
        conc.cancelada = True
        conc.data_cancelamento = date.today()
        conc.motivo_cancelamento = motivo
        conc.save()
        dotacao = conc.indicacao_dotacao.dotacao
        dotacao.valor_concedido = dotacao.valor_concedido - conc.valor
        dotacao.save(update_fields=['valor_concedido'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Concessão cancelada.', **serializer})

    def _indicacao_serializer(self, indicacao):
        """Re-busca a indicação com prefetch completo e retorna os dados serializados."""
        from .serializers import IndicacaoOrcamentariaSerializer
        ind = IndicacaoOrcamentaria.objects.prefetch_related(
            'itens__descentralizacoes', 'itens__concessoes',
            'historico', 'itens__dotacao',
        ).get(pk=indicacao.pk)
        return IndicacaoOrcamentariaSerializer(ind, context={'request': self.request}).data
