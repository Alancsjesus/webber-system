import django_filters
from decimal import Decimal
from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import DFD, HistoricoTramitacao, ItemDFD, NumeroProcesso
from .serializers import DFDSerializer, ItemDFDSerializer, NumeroProcessoSerializer
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA, PAPEIS_SOLICITANTE
from exportacao.pdf_utils import gerar_pdf_dfd, gerar_html, resposta_pdf, resposta_html


class DFDFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name='status', lookup_expr='exact')
    area   = django_filters.CharFilter(method='filter_area')

    def filter_area(self, queryset, name, value):
        return queryset.filter(area_aplicacao__contains=value)

    class Meta:
        model = DFD
        fields = ['status']


class DFDViewSet(viewsets.ModelViewSet):
    serializer_class   = DFDSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class    = DFDFilter
    ordering_fields    = ['created_at', 'numero_sei']
    ordering           = ['-created_at']
    search_fields      = ['numero_sei', 'descricao']

    def get_queryset(self):
        oid = self.request.org_id
        return (
            DFD.objects
            .filter(
                Q(org_id=oid) |
                Q(unidade_licitante__orgao_id=oid) |
                Q(unidade_contratante__orgao_id=oid)
            )
            .distinct()
            .prefetch_related('historico', 'itens', 'processos')
        )

    # ------------------------------------------------------------------ #
    # helpers                                                              #
    # ------------------------------------------------------------------ #

    def _transicao(self, request, status_novo, campos_extra=None):
        """Executa uma transição de status, registra no histórico e retorna Response."""
        dfd = self.get_object()
        permitidos = DFD.TRANSICOES_PERMITIDAS.get(dfd.status, [])

        if status_novo not in permitidos:
            return Response(
                {'detail': f'Transição de "{dfd.status}" para "{status_novo}" não é permitida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_anterior = dfd.status
        motivo = (campos_extra or {}).get('motivo')

        dfd.status = status_novo
        if campos_extra:
            for campo, valor in campos_extra.items():
                if campo != 'motivo':
                    setattr(dfd, campo, valor)
        if status_novo == 'Submetida':
            dfd.motivo_devolucao = None
        dfd.updated_by = request.user
        dfd.save()

        categoria = (campos_extra or {}).get('categoria_motivo', '')
        HistoricoTramitacao.objects.create(
            dfd=dfd,
            status_anterior=status_anterior,
            status_novo=status_novo,
            usuario=request.user,
            motivo=motivo,
            categoria_motivo=categoria,
        )

        serializer = self.get_serializer(dfd)
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # actions de workflow                                                   #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def submeter(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_SOLICITANTE:
            return Response({'detail': 'Apenas solicitantes podem submeter DFDs.'},
                            status=status.HTTP_403_FORBIDDEN)

        dfd = self.get_object()
        necessidade = getattr(dfd, 'necessidade_origem', None)
        just = (dfd.justificativa_sem_planejamento or '').strip()

        if necessidade is None:
            # DFD sem planejamento — justificativa obrigatória
            if not just:
                return Response(
                    {'detail': 'Este DFD não está vinculado a uma necessidade de planejamento. '
                               'Preencha a justificativa antes de submeter.',
                     'codigo': 'sem_planejamento'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            # Necessidade deve estar aprovada
            if necessidade.status not in ('Aprovada', 'DFD Criado'):
                return Response(
                    {'detail': 'A necessidade vinculada ainda não foi aprovada pela unidade de planejamento.',
                     'codigo': 'necessidade_nao_aprovada'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Necessidade deve ter vínculo orçamentário (plano OU dotação)
            tem_vinculo_orcamentario = (
                necessidade.itens_plano.exists() or
                necessidade.dotacoes.exists()
            )
            if not tem_vinculo_orcamentario and not just:
                return Response(
                    {'detail': 'A necessidade não possui vínculo orçamentário. '
                               'Vincule-a a um plano orçamentário ou a uma dotação antes de submeter, '
                               'ou preencha a justificativa.',
                     'codigo': 'sem_plano_orcamentario'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # verificar extrapolação de valor e área
            # Verificar extrapolação de valor (>10% acima do planejado)
            valor_planejado = necessidade.valor_estimado
            valor_dfd = dfd.valor_estimado
            extrapola_valor = valor_planejado and valor_dfd > valor_planejado * Decimal('1.10')

            # Verificar áreas além do planejado
            areas_planejadas = set(necessidade.area_aplicacao or [])
            areas_dfd = set(dfd.area_aplicacao or [])
            extrapola_area = not areas_dfd.issubset(areas_planejadas)

            if (extrapola_valor or extrapola_area) and not just:
                motivos = []
                if extrapola_valor:
                    motivos.append(
                        f'valor estimado ({valor_dfd}) supera em mais de 10% o planejado ({valor_planejado})'
                    )
                if extrapola_area:
                    extras = areas_dfd - areas_planejadas
                    motivos.append(f'áreas não previstas no planejamento: {", ".join(extras)}')
                return Response(
                    {'detail': f'O DFD extrapola a necessidade planejada ({"; ".join(motivos)}). '
                               'Preencha a justificativa antes de submeter.',
                     'codigo': 'extrapolacao'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return self._transicao(request, 'Submetida')

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def iniciar_analise(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem iniciar análise.'},
                            status=status.HTTP_403_FORBIDDEN)

        dfd = self.get_object()
        # O órgão da unidade licitante assume o controle a partir daqui
        org_gestor_id = None
        if dfd.unidade_licitante_id:
            org_gestor_id = dfd.unidade_licitante.orgao_id
        else:
            org_gestor_id = request.org_id

        return self._transicao(request, 'Em Análise',
                               campos_extra={
                                   'org_gestor_id':    org_gestor_id,
                                   'orgao_compras_id': org_gestor_id,
                               })

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def aprovar(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem aprovar DFDs.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Aprovada',
                               campos_extra={'motivo': request.data.get('motivo')})

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def devolver(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem devolver DFDs.'},
                            status=status.HTTP_403_FORBIDDEN)

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        categoria = request.data.get('categoria_motivo', '')
        return self._transicao(request, 'Devolvida',
                               campos_extra={'motivo_devolucao': motivo, 'motivo': motivo,
                                             'categoria_motivo': categoria})

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def reabrir(self, request, pk=None):
        """Derruba a aprovação do DFD e retorna para Devolvida (somente admin)."""
        if getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas administradores podem reabrir DFDs aprovados.'},
                            status=status.HTTP_403_FORBIDDEN)
        dfd = self.get_object()
        if dfd.status not in ('Aprovada', 'Rejeitada'):
            return Response({'detail': 'Apenas DFDs Aprovados ou Rejeitados podem ser reabertos.'},
                            status=status.HTTP_400_BAD_REQUEST)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da reabertura é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        from .models import HistoricoTramitacao
        HistoricoTramitacao.objects.create(
            dfd=dfd, status_anterior=dfd.status, status_novo='Devolvida',
            usuario=request.user, motivo=f'[REABERTURA] {motivo}',
        )
        dfd.status = 'Devolvida'
        dfd.motivo_devolucao = f'Reabertura pelo admin: {motivo}'
        dfd.save(update_fields=['status', 'motivo_devolucao'])
        return Response(DFDSerializer(dfd, context={'request': request}).data)

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated, IsMultiTenant])
    def dispensar_etp(self, request, pk=None):
        """
        Dispensa a criação do ETP e cria automaticamente um ETP com status='Dispensado',
        permitindo que o TR seja criado diretamente a partir do DFD aprovado.

        Condições permitidas (qualquer uma basta):
        - modalidade_aquisicao in ('dispensa_valor', 'dispensa_emergencia', 'arp_saque')
        - valor_estimado < limite configurado em ParametroSistema.valor_limite_dispensa
        - papel in PAPEIS_ANALISTA e unidade licitante (autorização manual)
        """
        from modulo_etp.models import ETP
        from core.models import ParametroSistema

        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas/licitante podem dispensar o ETP.'},
                            status=status.HTTP_403_FORBIDDEN)

        dfd = self.get_object()
        if dfd.status != 'Aprovada':
            return Response({'detail': 'Apenas DFDs aprovados podem ter ETP dispensado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if hasattr(dfd, 'etp'):
            return Response({'detail': 'Este DFD já possui um ETP associado.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Verificar elegibilidade para dispensa
        modalidades_dispensa = ('dispensa_valor', 'dispensa_emergencia', 'arp_saque')
        limite_str = ParametroSistema.get('valor_limite_dispensa', '62000.00')
        try:
            limite = Decimal(limite_str)
        except Exception:
            limite = Decimal('62000.00')

        elegivel_modalidade = dfd.modalidade_aquisicao in modalidades_dispensa
        elegivel_valor      = dfd.valor_estimado < limite
        autorizado_licitante = (
            getattr(request, 'tipo_unidade', None) == 'licitante'
            and papel in PAPEIS_ANALISTA
        )

        if not (elegivel_modalidade or elegivel_valor or autorizado_licitante):
            return Response({
                'detail': (
                    'O DFD não atende as condições para dispensa de ETP. '
                    'Condições: modalidade dispensa/ARP, valor abaixo do limite configurado, '
                    'ou autorização manual da unidade licitante.'
                ),
                'codigo': 'etp_obrigatorio',
                'valor_limite': str(limite),
            }, status=status.HTTP_400_BAD_REQUEST)

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da dispensa é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        etp = ETP.objects.create(
            dfd=dfd,
            numero_sei=dfd.numero_sei,
            necessidade_contratacao=dfd.descricao,
            status='Dispensado',
            dispensa_motivo=motivo,
            org_id=dfd.org_id,
            created_by=request.user,
            updated_by=request.user,
        )

        from modulo_etp.serializers import ETPSerializer
        serializer = ETPSerializer(etp, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------ #
    # actions de itens                                                     #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # status da família SIMPAS no plano de compras                        #
    # ------------------------------------------------------------------ #

    @action(detail=False, methods=['get'], url_path='status-familia')
    def status_familia(self, request):
        """
        Retorna DFDs existentes para uma família SIMPAS com o status de cada
        aquisição em andamento (ETP, TR, Procedimento).
        Query params: familia, exercicio (opcional)
        """
        from core.models import ItemCatalogo

        familia   = (request.query_params.get('familia') or '').strip()
        exercicio = request.query_params.get('exercicio')

        if not familia:
            return Response({'detail': 'Parâmetro "familia" é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # DFDs do org com itens nessa família SIMPAS
        qs = DFD.objects.filter(
            Q(org_id=request.org_id) |
            Q(unidade_licitante__orgao_id=request.org_id) |
            Q(unidade_contratante__orgao_id=request.org_id),
            itens__item_catalogo__familia=familia,
        ).exclude(
            status__in=['Rejeitada', 'Cancelada'],
        ).distinct().prefetch_related('itens__item_catalogo')

        if exercicio:
            try:
                ano = int(exercicio)
                qs = qs.filter(prazo_necessidade__year=ano)
            except (ValueError, TypeError):
                pass

        dfds_info = []
        for dfd in qs:
            etp = getattr(dfd, 'etp', None)
            tr  = getattr(etp, 'tr', None) if etp else None
            procedimentos = list(
                dfd.procedimentos.exclude(status__in=['Anulado', 'Revogado'])
                .values('id', 'numero', 'modalidade', 'status')
            )
            itens_familia = [
                {
                    'id':                       it.id,
                    'item_catalogo_id':         it.item_catalogo_id,
                    'objeto':                   it.objeto,
                    'catalogo_codigo':          it.item_catalogo.codigo_interno if it.item_catalogo else '',
                    'catalogo_simpas':          it.item_catalogo.codigo_simpas  if it.item_catalogo else '',
                    'unidade_medida':           it.unidade_medida,
                    'quantidade':               float(it.quantidade),
                    'valor_unitario_estimado':  float(it.valor_unitario_estimado),
                }
                for it in dfd.itens.all()
                if it.item_catalogo and it.item_catalogo.familia == familia
            ]
            dfds_info.append({
                'id':              dfd.id,
                'numero_sei':      dfd.numero_sei,
                'descricao':       dfd.descricao,
                'status':          dfd.status,
                'valor_estimado':  float(dfd.valor_estimado or 0),
                'tem_etp':         etp is not None,
                'etp_id':          etp.pk       if etp else None,
                'etp_status':      etp.status   if etp else None,
                'tem_tr':          tr is not None,
                'tr_id':           tr.pk        if tr else None,
                'tr_status':       tr.status    if tr else None,
                'tem_procedimento': len(procedimentos) > 0,
                'procedimentos':   procedimentos,
                'itens_familia':   itens_familia,
            })

        aprovados_sem_etp = [d for d in dfds_info if d['status'] == 'Aprovada' and not d['tem_etp']]
        em_andamento = [d for d in dfds_info if d['tem_etp'] or d['tem_procedimento']]

        return Response({
            'familia': familia,
            'dfds':    dfds_info,
            'resumo':  {
                'total':              len(dfds_info),
                'aprovados_sem_etp':  len(aprovados_sem_etp),
                'em_andamento':       len(em_andamento),
            },
        })

    # ------------------------------------------------------------------ #
    # iniciar de família SIMPAS                                            #
    # ------------------------------------------------------------------ #

    @action(detail=False, methods=['post'], url_path='iniciar-de-familia')
    def iniciar_de_familia(self, request):
        """
        Cria um DFD agrupado a partir de itens consolidados de uma família SIMPAS.
        Usado pela tela 'Preparar Aquisição' quando a origem é o Plano de Compras.
        Body: { familia, exercicio, numero_sei, prazo_necessidade, area_aplicacao,
                modalidade_aquisicao, observacoes,
                itens: [{item_catalogo_id?, objeto, unidade_medida,
                          quantidade, valor_unitario_estimado}] }
        """
        numero_sei        = (request.data.get('numero_sei') or '').strip()
        prazo_necessidade = request.data.get('prazo_necessidade')
        area_aplicacao    = request.data.get('area_aplicacao', [])
        itens_data        = request.data.get('itens', [])
        familia           = (request.data.get('familia') or '').strip()

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

        descricao = request.data.get('descricao') or (
            f'DFD agrupado — Família SIMPAS {familia}' if familia else 'DFD agrupado a partir do Plano de Compras'
        )

        from decimal import Decimal
        valor_estimado_total = sum(
            Decimal(str(it.get('quantidade', 0))) * Decimal(str(it.get('valor_unitario_estimado', 0)))
            for it in itens_data
        )

        dfd = DFD.objects.create(
            numero_sei=numero_sei,
            descricao=descricao,
            prazo_necessidade=prazo_necessidade,
            area_aplicacao=area_aplicacao if isinstance(area_aplicacao, list) else [area_aplicacao],
            modalidade_aquisicao=request.data.get('modalidade_aquisicao', 'licitacao'),
            observacoes=request.data.get('observacoes', ''),
            valor_estimado=valor_estimado_total,
            org_id_id=request.org_id,
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
                org_id_id=request.org_id,
                created_by=request.user,
                updated_by=request.user,
            )

        serializer = self.get_serializer(dfd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ------------------------------------------------------------------ #
    # export actions                                                       #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        dfd = self.get_object()
        pdf = gerar_pdf_dfd(dfd)
        return resposta_pdf(pdf, f'DFD_{dfd.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/html')
    def export_html(self, request, pk=None):
        dfd = self.get_object()
        html = gerar_html('dfd', {'dfd': dfd})
        return resposta_html(html, f'DFD_{dfd.numero_sei}.html')

    @action(detail=True, methods=['get'], url_path='export/historico')
    def export_historico(self, request, pk=None):
        from exportacao.pdf_utils import gerar_pdf_historico
        dfd = self.get_object()
        pdf = gerar_pdf_historico(
            titulo='DFD',
            numero_ref=dfd.numero_sei,
            historico_entries=dfd.historico.select_related('usuario').order_by('-criado_em'),
            org_nome=dfd.org_id.nome if dfd.org_id else '',
            org_sigla=dfd.org_id.sigla if dfd.org_id else None,
            criado_por=dfd.created_by,
            created_at=dfd.created_at,
        )
        return resposta_pdf(pdf, f'Historico_DFD_{dfd.numero_sei}.pdf')

    @action(detail=True, methods=['get', 'post'], url_path='itens')
    def itens(self, request, pk=None):
        dfd = self.get_object()
        if request.method == 'GET':
            serializer = ItemDFDSerializer(
                dfd.itens.all(), many=True, context={'request': request}
            )
            return Response(serializer.data)

        serializer = ItemDFDSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(dfd=dfd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'itens/(?P<item_pk>[^/.]+)')
    def item_detail(self, request, pk=None, item_pk=None):
        dfd = self.get_object()
        try:
            item = dfd.itens.get(pk=item_pk)
        except ItemDFD.DoesNotExist:
            return Response({'detail': 'Item não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        partial = request.method == 'PATCH'
        serializer = ItemDFDSerializer(
            item, data=request.data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ------------------------------------------------------------------ #
    # actions de processos SEI                                             #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get', 'post'], url_path='processos')
    def processos(self, request, pk=None):
        dfd = self.get_object()
        if request.method == 'GET':
            serializer = NumeroProcessoSerializer(
                dfd.processos.all(), many=True, context={'request': request}
            )
            return Response(serializer.data)

        serializer = NumeroProcessoSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(dfd=dfd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'patch', 'delete'],
            url_path=r'processos/(?P<proc_pk>[^/.]+)')
    def processo_detail(self, request, pk=None, proc_pk=None):
        dfd = self.get_object()
        try:
            proc = dfd.processos.get(pk=proc_pk)
        except NumeroProcesso.DoesNotExist:
            return Response({'detail': 'Processo não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            proc.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        partial = request.method == 'PATCH'
        serializer = NumeroProcessoSerializer(
            proc, data=request.data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
