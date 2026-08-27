import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from core.models import Orgao
from core.permissions import IsMultiTenant
from modulo_planejamento.models import NecessidadePlanejamento
from modulo_planejamento.serializers import NecessidadeSerializer
from modulo_demanda.models import ItemDFD

logger = logging.getLogger(__name__)

from .filters import AcaoOrcamentariaFilter, FonteRecursoFilter, SubFonteRecursoFilter, DotacaoOrcamentariaFilter
from .models import (
    AcaoOrcamentaria, ElementoDespesa, NaturezaDespesa, FonteRecurso, SubFonteRecurso,
    DotacaoOrcamentaria, IndicacaoOrcamentaria, IndicacaoDotacao, HistoricoIndicacao,
    TipoAcaoOrcamentaria, TipoFonteRecurso,
)
from .serializers import (
    AcaoOrcamentariaSerializer,
    ElementoDespesaSerializer,
    NaturezaDespesaSerializer,
    FonteRecursoSerializer,
    SubFonteRecursoSerializer,
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


class SubFonteRecursoViewSet(viewsets.ModelViewSet):
    serializer_class = SubFonteRecursoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubFonteRecursoFilter
    search_fields = ['nome', 'codigo']
    ordering_fields = ['codigo', 'nome']
    ordering = ['fonte_recurso__codigo', 'codigo']

    def get_queryset(self):
        qs = SubFonteRecurso.objects.filter(
            org_id=self.request.org_id
        ).select_related('fonte_recurso')
        if self.request.query_params.get('inativas') != 'true':
            qs = qs.filter(ativa=True)
        return qs

    def perform_create(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao_planejamento(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao_planejamento(self.request)
        instance.ativa = False
        instance.save()


class DotacaoOrcamentariaViewSet(viewsets.ModelViewSet):
    serializer_class = DotacaoOrcamentariaSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DotacaoOrcamentariaFilter
    search_fields = [
        'eixo', 'objetivo_estrategico', 'observacoes', 'acao__nome', 'acao__codigo',
        'elemento_despesa__descricao', 'fonte_recurso__nome', 'fonte_recurso__codigo',
    ]
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
        em_diligencia  = serializer.validated_data.get('em_diligencia', False)

        dotacao = get_object_or_404(
            DotacaoOrcamentaria, id=dotacao_id, org_id=request.org_id
        )
        item, created = IndicacaoDotacao.objects.update_or_create(
            indicacao=indicacao, dotacao=dotacao,
            defaults={'valor_indicado': valor_indicado, 'em_diligencia': em_diligencia},
        )
        # Recalcular valor total
        total = sum(i.valor_indicado for i in indicacao.itens.all())
        indicacao.valor_total = total
        indicacao.save(update_fields=['valor_total'])

        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': f'Dotação vinculada com R$ {valor_indicado:,.2f}.', **serializer})

    @action(detail=True, methods=['post'], url_path='detalhar-itens')
    def detalhar_itens(self, request, pk=None):
        """
        Substitui o rateio por item de uma linha indicação+dotação. Payload:
        { "indicacao_dotacao_id": 12, "itens": [{"item_dfd_id": 5, "valor": 3000}, ...] }
        Itens com valor 0/em branco são ignorados. Não acumula: a lista enviada
        substitui integralmente o rateio anterior daquela linha.
        """
        from django.db import transaction
        from .models import ItemIndicacaoDotacao
        from .serializers import DetalharItensSerializer

        indicacao = self.get_object()
        if indicacao.status not in ('Rascunho',):
            return Response(
                {'detail': 'Só é possível detalhar itens em Rascunho.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = DetalharItensSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        linha = get_object_or_404(
            IndicacaoDotacao, id=serializer.validated_data['indicacao_dotacao_id'], indicacao=indicacao,
        )
        itens_validos = [i for i in serializer.validated_data['itens'] if i['valor']]

        soma = sum(i['valor'] for i in itens_validos)
        if soma > linha.valor_indicado:
            return Response(
                {'detail': f'Soma do rateio (R$ {soma:,.2f}) não pode superar o valor indicado da linha (R$ {linha.valor_indicado:,.2f}).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for i in itens_validos:
            item_dfd = get_object_or_404(ItemDFD, id=i['item_dfd_id'], dfd_id=indicacao.dfd_id)
            i['item_dfd'] = item_dfd

        with transaction.atomic():
            linha.itens_detalhados.all().delete()
            ItemIndicacaoDotacao.objects.bulk_create([
                ItemIndicacaoDotacao(indicacao_dotacao=linha, item_dfd=i['item_dfd'], valor=i['valor'])
                for i in itens_validos
            ])

        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Rateio por item atualizado.', **serializer})

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

    # ── Empenho ─────────────────────────────────────────────────────────────── #

    @action(detail=True, methods=['post'], url_path='registrar-empenhos')
    def registrar_empenhos(self, request, pk=None):
        """
        Registra empenhos em bloco. Payload: { "empenhos": [{"indicacao_dotacao_id": X,
        "numero_doc": "...", "data_emissao": "...", "valor": ..., "observacoes": ""}, ...] }
        Valida: valor_empenhado + novo_valor <= valor_indicado da própria linha.
        """
        from .models import EmpenhoOrcamentario, IndicacaoDotacao
        from decimal import Decimal

        indicacao = self.get_object()
        if indicacao.status != 'Aprovada':
            return Response({'detail': 'Empenhos só podem ser registrados em indicações aprovadas.'},
                            status=status.HTTP_400_BAD_REQUEST)

        dados = request.data.get('empenhos', [])
        criados = []
        erros = []
        for item in dados:
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
            if dotacao.valor_empenhado + novo_valor > ind_dot.valor_indicado:
                erros.append(f'Dotação {dotacao.id}: valor empenhado superaria o indicado.')
                continue
            EmpenhoOrcamentario.objects.create(
                indicacao_dotacao=ind_dot,
                numero_doc=numero_doc,
                data_emissao=data_emis,
                valor=novo_valor,
                observacoes=obs,
                registrada_por=request.user,
            )
            dotacao.valor_empenhado = dotacao.valor_empenhado + novo_valor
            dotacao.save(update_fields=['valor_empenhado'])
            criados.append(ind_dot_id)

        serializer = self._indicacao_serializer(indicacao)
        msg = f'{len(criados)} empenho(s) registrado(s).'
        if erros:
            msg += ' Erros: ' + ' | '.join(erros)
        return Response({'detail': msg, **serializer}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'cancelar-empenho/(?P<emp_pk>[^/.]+)')
    def cancelar_empenho(self, request, pk=None, emp_pk=None):
        from .models import EmpenhoOrcamentario
        from django.shortcuts import get_object_or_404 as goo
        indicacao = self.get_object()
        emp = goo(EmpenhoOrcamentario, pk=emp_pk,
                  indicacao_dotacao__indicacao=indicacao, cancelada=False)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do cancelamento é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        dotacao = emp.indicacao_dotacao.dotacao
        liquidado = dotacao.valor_liquidado
        novo_emp = dotacao.valor_empenhado - emp.valor
        if novo_emp < liquidado:
            return Response({
                'detail': f'Não é possível cancelar: R$ {float(liquidado):,.2f} já foram liquidados contra este empenho.'
            }, status=status.HTTP_400_BAD_REQUEST)

        from datetime import date
        emp.cancelada = True
        emp.data_cancelamento = date.today()
        emp.motivo_cancelamento = motivo
        emp.save()
        dotacao.valor_empenhado = novo_emp
        dotacao.save(update_fields=['valor_empenhado'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Empenho cancelado.', **serializer})

    # ── Liquidação ──────────────────────────────────────────────────────────── #

    @action(detail=True, methods=['post'], url_path='registrar-liquidacoes')
    def registrar_liquidacoes(self, request, pk=None):
        """
        Registra liquidações em bloco.
        Valida: valor_liquidado + novo_valor <= valor_empenhado.
        """
        from .models import LiquidacaoOrcamentaria, IndicacaoDotacao
        from decimal import Decimal

        indicacao = self.get_object()
        if indicacao.status != 'Aprovada':
            return Response({'detail': 'Liquidações só podem ser registradas em indicações aprovadas.'},
                            status=status.HTTP_400_BAD_REQUEST)

        dados = request.data.get('liquidacoes', [])
        criados = []
        erros = []
        for item in dados:
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
            if dotacao.valor_liquidado + novo_valor > dotacao.valor_empenhado:
                erros.append(f'Dotação {dotacao.id}: valor liquidado superaria o empenhado.')
                continue
            LiquidacaoOrcamentaria.objects.create(
                indicacao_dotacao=ind_dot,
                numero_doc=numero_doc,
                data_emissao=data_emis,
                valor=novo_valor,
                observacoes=obs,
                registrada_por=request.user,
            )
            dotacao.valor_liquidado = dotacao.valor_liquidado + novo_valor
            dotacao.save(update_fields=['valor_liquidado'])
            criados.append(ind_dot_id)

        serializer = self._indicacao_serializer(indicacao)
        msg = f'{len(criados)} liquidação(ões) registrada(s).'
        if erros:
            msg += ' Erros: ' + ' | '.join(erros)
        return Response({'detail': msg, **serializer}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'cancelar-liquidacao/(?P<liq_pk>[^/.]+)')
    def cancelar_liquidacao(self, request, pk=None, liq_pk=None):
        from .models import LiquidacaoOrcamentaria
        from django.shortcuts import get_object_or_404 as goo
        indicacao = self.get_object()
        liq = goo(LiquidacaoOrcamentaria, pk=liq_pk,
                  indicacao_dotacao__indicacao=indicacao, cancelada=False)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do cancelamento é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        dotacao = liq.indicacao_dotacao.dotacao
        pago = dotacao.valor_pago
        novo_liq = dotacao.valor_liquidado - liq.valor
        if novo_liq < pago:
            return Response({
                'detail': f'Não é possível cancelar: R$ {float(pago):,.2f} já foram pagos contra esta liquidação.'
            }, status=status.HTTP_400_BAD_REQUEST)

        from datetime import date
        liq.cancelada = True
        liq.data_cancelamento = date.today()
        liq.motivo_cancelamento = motivo
        liq.save()
        dotacao.valor_liquidado = novo_liq
        dotacao.save(update_fields=['valor_liquidado'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Liquidação cancelada.', **serializer})

    # ── Pagamento ───────────────────────────────────────────────────────────── #

    @action(detail=True, methods=['post'], url_path='registrar-pagamentos')
    def registrar_pagamentos(self, request, pk=None):
        """
        Registra pagamentos em bloco.
        Valida: valor_pago + novo_valor <= valor_liquidado.
        """
        from .models import PagamentoOrcamentario, IndicacaoDotacao
        from decimal import Decimal

        indicacao = self.get_object()
        if indicacao.status != 'Aprovada':
            return Response({'detail': 'Pagamentos só podem ser registrados em indicações aprovadas.'},
                            status=status.HTTP_400_BAD_REQUEST)

        dados = request.data.get('pagamentos', [])
        criados = []
        erros = []
        for item in dados:
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
            if dotacao.valor_pago + novo_valor > dotacao.valor_liquidado:
                erros.append(f'Dotação {dotacao.id}: valor pago superaria o liquidado.')
                continue
            PagamentoOrcamentario.objects.create(
                indicacao_dotacao=ind_dot,
                numero_doc=numero_doc,
                data_emissao=data_emis,
                valor=novo_valor,
                observacoes=obs,
                registrada_por=request.user,
            )
            dotacao.valor_pago = dotacao.valor_pago + novo_valor
            dotacao.save(update_fields=['valor_pago'])
            criados.append(ind_dot_id)

        serializer = self._indicacao_serializer(indicacao)
        msg = f'{len(criados)} pagamento(s) registrado(s).'
        if erros:
            msg += ' Erros: ' + ' | '.join(erros)
        return Response({'detail': msg, **serializer}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path=r'cancelar-pagamento/(?P<pag_pk>[^/.]+)')
    def cancelar_pagamento(self, request, pk=None, pag_pk=None):
        from .models import PagamentoOrcamentario
        from django.shortcuts import get_object_or_404 as goo
        indicacao = self.get_object()
        pag = goo(PagamentoOrcamentario, pk=pag_pk,
                  indicacao_dotacao__indicacao=indicacao, cancelada=False)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo do cancelamento é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        from datetime import date
        pag.cancelada = True
        pag.data_cancelamento = date.today()
        pag.motivo_cancelamento = motivo
        pag.save()
        dotacao = pag.indicacao_dotacao.dotacao
        dotacao.valor_pago = dotacao.valor_pago - pag.valor
        dotacao.save(update_fields=['valor_pago'])
        serializer = self._indicacao_serializer(indicacao)
        return Response({'detail': 'Pagamento cancelado.', **serializer})

    def _indicacao_serializer(self, indicacao):
        """Re-busca a indicação com prefetch completo e retorna os dados serializados."""
        from .serializers import IndicacaoOrcamentariaSerializer
        ind = IndicacaoOrcamentaria.objects.prefetch_related(
            'itens__descentralizacoes', 'itens__concessoes',
            'itens__empenhos', 'itens__liquidacoes', 'itens__pagamentos',
            'historico', 'itens__dotacao', 'itens__itens_detalhados__item_dfd',
        ).get(pk=indicacao.pk)
        return IndicacaoOrcamentariaSerializer(ind, context={'request': self.request}).data


def _itens_indicacao_queryset(org_id):
    """
    Queryset base de IndicacaoDotacao cruzando TODAS as Indicações
    Orçamentárias do órgão (não uma única) — reaproveitado pelo relatório
    plano (RelatorioIndicacoesView) e pelo painel agregado (PainelOrcamentoView).
    """
    return IndicacaoDotacao.objects.filter(
        indicacao__org_id=org_id
    ).exclude(
        indicacao__status='Cancelada'
    ).select_related(
        'indicacao', 'indicacao__dfd', 'indicacao__dfd__necessidade_origem',
        'indicacao__dfd__necessidade_origem__orgao_executor',
        'indicacao__necessidade', 'indicacao__necessidade__orgao_executor',
        'dotacao__acao', 'dotacao__elemento_despesa', 'dotacao__natureza_despesa', 'dotacao__fonte_recurso',
        'dotacao__subfonte_recurso',
    ).prefetch_related(
        'descentralizacoes', 'concessoes', 'empenhos', 'liquidacoes', 'pagamentos',
        'itens_detalhados__item_dfd',
        'indicacao__dfd__itens__item_catalogo',
        'indicacao__dfd__necessidade_origem__itens_plano_aplicacao_fesp__instrumento',
        'indicacao__necessidade__itens_plano_aplicacao_fesp__instrumento',
    ).order_by('-indicacao__exercicio_fiscal', 'dotacao__fonte_recurso__codigo', 'indicacao__numero')


class RelatorioIndicacoesView(APIView):
    """
    Relatório de itens de indicação cruzando VÁRIAS Indicações Orçamentárias
    do mesmo órgão — uma linha por dotação/item indicado, com toda a cadeia de
    execução (Indicado/Empenhado/Liquidado/Pago/Saldo), independente de a qual
    Indicação cada linha pertence. Útil para ver, por Fonte de Recurso, todos os
    itens financiados por ela ao longo de várias indicações diferentes.

    GET /api/orcamento/relatorio-indicacoes/
    Parâmetros opcionais (filtram diretamente no banco):
      ?fonte_recurso=<id>     — fonte de recurso da dotação
      ?subfonte_recurso=<id>  — subfonte de recurso da dotação
      ?acao=<id>              — ação orçamentária da dotação
      ?elemento_despesa=<id>  — elemento de despesa da dotação
      ?natureza_despesa=<id>  — natureza de despesa da dotação
      ?exercicio_fiscal=...   — exercício da indicação
      ?numero_sei=...         — busca parcial no processo SEI da indicação
    Parâmetros opcionais (filtram após resolver a Necessidade de origem, que
    pode vir por dois caminhos de FK diferentes — DFD ou Necessidade solta):
      ?status_execucao=...    — Pago|Liquidado|Empenhado|Em Diligência|Indicado|Sem Execução
      ?area_aplicacao=...     — presente na lista de áreas da Necessidade de origem
      ?orgao_executor=<id>    — órgão executor da Necessidade de origem
      ?beneficiada=Sim|Não    — execução externa (Sim) ou interna (Não)
      ?instrumento_financeiro=<id> — instrumento financeiro FESP vinculado à Necessidade
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from .serializers import IndicacaoDotacaoSerializer

        qs = _itens_indicacao_queryset(request.org_id)
        params = request.query_params

        filtros_diretos = {
            'fonte_recurso':    'dotacao__fonte_recurso_id',
            'subfonte_recurso': 'dotacao__subfonte_recurso_id',
            'acao':             'dotacao__acao_id',
            'elemento_despesa': 'dotacao__elemento_despesa_id',
            'natureza_despesa': 'dotacao__natureza_despesa_id',
            'exercicio_fiscal': 'indicacao__exercicio_fiscal',
        }
        for param, campo in filtros_diretos.items():
            valor = params.get(param)
            if valor:
                qs = qs.filter(**{campo: valor})

        numero_sei = params.get('numero_sei')
        if numero_sei:
            qs = qs.filter(indicacao__numero_sei__icontains=numero_sei)

        itens = _flatten_por_item(IndicacaoDotacaoSerializer(qs, many=True).data)

        filtros_pos_flatten = {
            'status_execucao': lambda i, v: i['status_execucao'] == v,
            'area_aplicacao':  lambda i, v: v in (i.get('area_aplicacao') or []),
            'orgao_executor':  lambda i, v: str(i.get('orgao_executor_id')) == str(v),
            'beneficiada':     lambda i, v: i.get('beneficiada') == v,
            'instrumento_financeiro': lambda i, v: str(i.get('instrumento_financeiro_id')) == str(v),
        }
        for param, predicado in filtros_pos_flatten.items():
            valor = params.get(param)
            if valor:
                itens = [i for i in itens if predicado(i, valor)]

        return Response({'total': len(itens), 'itens': itens})


def _flatten_por_item(itens):
    """
    Achata as linhas indicação+dotação para nível de item quando há rateio
    (`itens_detalhados`) registrado. Uma linha sem rateio continua aparecendo
    como 1 linha (item "—") — cobre indicações vinculadas a Necessidade solta,
    sem DFD, onde não existe item para ratear.

    Empenhado/Liquidado/Pago/Saldo em linhas rateadas são PRORATEADOS
    proporcionalmente à fatia do item na linha — a execução orçamentária real
    (empenho/liquidação/pagamento) é sempre registrada por dotação, nunca por
    item, então esses valores por item são uma estimativa (`rateio: True`),
    não um lançamento auditado individualmente.
    """
    linhas = []
    for linha in itens:
        detalhes = linha.get('itens_detalhados') or []
        if not detalhes:
            linhas.append({**linha, 'item_dfd_objeto': None, 'valor_indicado_item': linha['valor_indicado'], 'rateio': False})
            continue
        base = float(linha['valor_indicado']) or 1
        for d in detalhes:
            fatia = float(d['valor']) / base
            linhas.append({
                **linha,
                'item_dfd_objeto': d['item_dfd_objeto'],
                'valor_indicado_item': d['valor'],
                'valor_empenhado': round(float(linha['valor_empenhado']) * fatia, 2),
                'valor_liquidado': round(float(linha['valor_liquidado']) * fatia, 2),
                'valor_pago':      round(float(linha['valor_pago']) * fatia, 2),
                'saldo':           round(float(d['valor']) - float(linha['valor_pago']) * fatia, 2),
                'rateio': True,
            })
    return linhas


class PainelOrcamentoView(APIView):
    """
    Painel de gerenciamento orçamentário: duas visões complementares.
      - "aplicacao": o que já foi indicado, agregado por Fonte de Recurso, com o
        estágio de execução (Indicado/Empenhado/Liquidado/Pago/Saldo).
      - "pendentes": Necessidades de Planejamento já aprovadas cujo valor
        estimado ainda não está totalmente coberto por indicações ativas —
        agrupadas por Área de Aplicação, com detalhe por necessidade/órgão executor.

    GET /api/orcamento/painel/
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        return Response({
            'aplicacao': self._aplicacao(request.org_id),
            'pendentes': self._pendentes(request.org_id),
        })

    def _aplicacao(self, org_id):
        from decimal import Decimal
        from .serializers import IndicacaoDotacaoSerializer

        itens = IndicacaoDotacaoSerializer(_itens_indicacao_queryset(org_id), many=True).data

        totais = {'indicado': Decimal('0'), 'empenhado': Decimal('0'), 'liquidado': Decimal('0'), 'pago': Decimal('0'), 'saldo': Decimal('0')}
        grupos = {}
        for it in itens:
            chave = (it['fonte_codigo'], it['fonte_nome'])
            if chave not in grupos:
                grupos[chave] = {
                    'fonte_codigo': it['fonte_codigo'], 'fonte_nome': it['fonte_nome'],
                    'qtd_itens': 0, 'indicado': Decimal('0'), 'empenhado': Decimal('0'),
                    'liquidado': Decimal('0'), 'pago': Decimal('0'), 'saldo': Decimal('0'),
                }
            g = grupos[chave]
            g['qtd_itens'] += 1
            g['indicado'] += Decimal(str(it['valor_indicado']))
            g['empenhado'] += Decimal(str(it['valor_empenhado']))
            g['liquidado'] += Decimal(str(it['valor_liquidado']))
            g['pago'] += Decimal(str(it['valor_pago']))
            g['saldo'] += Decimal(str(it['saldo']))

        # soma dos totais gerais a partir dos grupos já computados (evita duplicar a leitura de `itens`)
        for g in grupos.values():
            for k in ('indicado', 'empenhado', 'liquidado', 'pago', 'saldo'):
                totais[k] += g[k]

        por_fonte = sorted(grupos.values(), key=lambda g: (g['fonte_codigo'] or 0))
        for g in por_fonte:
            for k in ('indicado', 'empenhado', 'liquidado', 'pago', 'saldo'):
                g[k] = str(g[k])
        for k in totais:
            totais[k] = str(totais[k])

        return {'totais': totais, 'por_fonte': por_fonte}

    def _pendentes(self, org_id):
        from decimal import Decimal
        from modulo_planejamento.models import NecessidadePlanejamento

        AREA_LABELS = dict(NecessidadePlanejamento.AREA_CHOICES)

        necessidades = NecessidadePlanejamento.objects.filter(
            org_id=org_id, status__in=['Aprovada', 'DFD Criado'],
        ).select_related('orgao_executor', 'dfd').prefetch_related('indicacoes', 'dfd__indicacoes')

        totais = {'qtd': 0, 'valor_estimado': Decimal('0'), 'valor_indicado': Decimal('0'), 'valor_pendente': Decimal('0')}
        grupos = {}

        for nec in necessidades:
            ativas = list(nec.indicacoes.exclude(status='Cancelada'))
            if nec.dfd_id:
                ativas += list(nec.dfd.indicacoes.exclude(status='Cancelada'))
            valor_indicado = sum((i.valor_total for i in ativas), Decimal('0'))
            pendente = nec.valor_estimado - valor_indicado
            if pendente <= 0:
                continue

            area = (nec.area_aplicacao or ['Sem área'])[0] if nec.area_aplicacao else 'Sem área'
            if area not in grupos:
                grupos[area] = {
                    'area': area, 'area_label': AREA_LABELS.get(area, area),
                    'qtd': 0, 'valor_estimado': Decimal('0'), 'valor_indicado': Decimal('0'),
                    'valor_pendente': Decimal('0'), 'necessidades': [],
                }
            g = grupos[area]
            g['qtd'] += 1
            g['valor_estimado'] += nec.valor_estimado
            g['valor_indicado'] += valor_indicado
            g['valor_pendente'] += pendente
            g['necessidades'].append({
                'id': nec.id, 'titulo': nec.titulo,
                'orgao_executor_sigla': nec.orgao_executor.sigla if nec.orgao_executor_id else None,
                'valor_estimado': str(nec.valor_estimado), 'valor_indicado': str(valor_indicado),
                'valor_pendente': str(pendente),
                'dfd_numero_sei': nec.dfd.numero_sei if nec.dfd_id else None,
            })

            totais['qtd'] += 1
            totais['valor_estimado'] += nec.valor_estimado
            totais['valor_indicado'] += valor_indicado
            totais['valor_pendente'] += pendente

        por_area = sorted(grupos.values(), key=lambda g: -g['valor_pendente'])
        for g in por_area:
            for k in ('valor_estimado', 'valor_indicado', 'valor_pendente'):
                g[k] = str(g[k])
        for k in ('valor_estimado', 'valor_indicado', 'valor_pendente'):
            totais[k] = str(totais[k])

        return {'totais': totais, 'por_area': por_area}
