from datetime import date
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.permissions import IsMultiTenant, check_licitante, PAPEIS_ANALISTA
from .models import (
    Procedimento, HistoricoProcedimento, TramitacaoExterna, ResultadoLote,
    TRANSICOES_PERMITIDAS,
)
from .serializers import (
    ProcedimentoSerializer, ProcedimentoListSerializer,
    TramitacaoExternaSerializer, ResultadoLoteSerializer,
)


class ProcedimentoViewSet(viewsets.ModelViewSet):
    """
    CRUD de Procedimentos licitatórios e contratações diretas.
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['numero', 'objeto', 'dfd__numero_sei', 'empresa_vencedora']
    ordering_fields    = ['exercicio', 'status', 'modalidade', 'created_at']
    ordering           = ['-exercicio', '-created_at']

    def get_queryset(self):
        qs = Procedimento.objects.filter(
            org_id=self.request.org_id
        ).select_related('dfd', 'tr', 'org_id', 'unidade_gestora', 'created_by').prefetch_related(
            'tramitacoes', 'resultados', 'historico'
        )
        modalidade = self.request.query_params.get('modalidade')
        stat       = self.request.query_params.get('status')
        exercicio  = self.request.query_params.get('exercicio')
        if modalidade:
            qs = qs.filter(modalidade=modalidade)
        if stat:
            qs = qs.filter(status=stat)
        if exercicio:
            qs = qs.filter(exercicio=exercicio)
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcedimentoListSerializer
        return ProcedimentoSerializer

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _transicao(self, procedimento, novo_status, usuario, motivo=''):
        permitidos = TRANSICOES_PERMITIDAS.get(procedimento.status, [])
        if novo_status not in permitidos:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f'Transição "{procedimento.status}" → "{novo_status}" não permitida.'
            )
        anterior = procedimento.status
        procedimento.status = novo_status
        procedimento.updated_by = usuario
        procedimento.save()
        HistoricoProcedimento.objects.create(
            procedimento=procedimento,
            status_anterior=anterior,
            status_novo=novo_status,
            usuario=usuario,
            motivo=motivo,
        )

    def _serializar(self, procedimento):
        proc = Procedimento.objects.prefetch_related(
            'tramitacoes', 'resultados', 'historico',
            'dfd__mapas_preco',
        ).select_related('dfd', 'tr', 'org_id', 'unidade_gestora', 'created_by').get(pk=procedimento.pk)
        return ProcedimentoSerializer(proc, context={'request': self.request}).data

    # ── Transições de status ──────────────────────────────────────────────────

    def _check_licitante(self, request):
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem executar esta ação.'},
                            status=status.HTTP_403_FORBIDDEN)
        return None

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        self._transicao(proc, 'Aguardando Aprovação', request.user,
                        request.data.get('motivo', 'Submetido para aprovação interna.'))
        return Response({'detail': 'Submetido para aprovação.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        self._transicao(proc, 'Aprovado', request.user,
                        request.data.get('motivo', 'Aprovado pela Unidade de Licitações.'))
        return Response({'detail': 'Procedimento aprovado.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Motivo de devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        self._transicao(proc, 'Em Instrução', request.user, motivo)
        return Response({'detail': 'Procedimento devolvido para instrução.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def publicar(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        if not proc.data_publicacao:
            proc.data_publicacao = date.today()
        self._transicao(proc, 'Publicado', request.user,
                        f'Edital publicado em {proc.data_publicacao}.')
        proc.save(update_fields=['data_publicacao'])
        return Response({'detail': 'Edital publicado.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def iniciar_sessao(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        self._transicao(proc, 'Em Sessão', request.user, 'Sessão pública iniciada.')
        return Response({'detail': 'Sessão iniciada.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def homologar(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()

        if not proc.resultados.exists():
            return Response(
                {'detail': 'Registre o resultado de ao menos um lote (empresa vencedora e valor final) antes de homologar — a fase de disputa pode ter reduzido o valor estimado, e é esse valor final que serve de base para o contrato.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pendentes = proc.resultados.filter(resultado='homologado', valor_final__isnull=True)
        if pendentes.exists():
            descricoes = ', '.join(r.descricao_lote or (r.lote.descricao if r.lote_id else f'lote #{r.id}') for r in pendentes)
            return Response(
                {'detail': f'Informe o valor final adjudicado antes de homologar — pendente em: {descricoes}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not proc.data_homologacao:
            proc.data_homologacao = date.today()
            proc.save(update_fields=['data_homologacao'])
        self._transicao(proc, 'Homologado', request.user,
                        f'Procedimento homologado em {proc.data_homologacao}.')
        return Response({'detail': 'Homologado.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def declarar_deserto(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        motivo = request.data.get('motivo', 'Nenhuma proposta recebida.')
        self._transicao(proc, 'Deserto', request.user, motivo)
        return Response({'detail': 'Declarado deserto.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def declarar_fracassado(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        motivo = request.data.get('motivo', 'Todas as propostas foram desclassificadas.')
        self._transicao(proc, 'Fracassado', request.user, motivo)
        return Response({'detail': 'Declarado fracassado.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def revogar(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Motivo de revogação é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        proc.motivo_revogacao = motivo
        proc.save(update_fields=['motivo_revogacao'])
        self._transicao(proc, 'Revogado', request.user, motivo)
        return Response({'detail': 'Procedimento revogado.', **self._serializar(proc)})

    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        err = self._check_licitante(request)
        if err: return err
        proc = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Motivo de anulação é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        proc.motivo_revogacao = motivo
        proc.save(update_fields=['motivo_revogacao'])
        self._transicao(proc, 'Anulado', request.user, motivo)
        return Response({'detail': 'Procedimento anulado.', **self._serializar(proc)})

    # ── Tramitações externas ──────────────────────────────────────────────────

    @action(detail=True, methods=['get', 'post'], url_path='tramitacoes')
    def tramitacoes_list(self, request, pk=None):
        proc = self.get_object()
        if request.method == 'POST':
            s = TramitacaoExternaSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            s.save(procedimento=proc, registrado_por=request.user)
            return Response(self._serializar(proc), status=status.HTTP_201_CREATED)
        return Response(TramitacaoExternaSerializer(proc.tramitacoes.all(), many=True).data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'tramitacoes/(?P<tram_pk>[^/.]+)')
    def tramitacao_detail(self, request, pk=None, tram_pk=None):
        proc = self.get_object()
        tram = get_object_or_404(TramitacaoExterna, pk=tram_pk, procedimento=proc)
        if request.method == 'DELETE':
            tram.delete()
            return Response(self._serializar(proc))
        s = TramitacaoExternaSerializer(tram, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(self._serializar(proc))

    # ── Resultados dos lotes ──────────────────────────────────────────────────

    @action(detail=True, methods=['get', 'post'], url_path='resultados')
    def resultados_list(self, request, pk=None):
        proc = self.get_object()
        if request.method == 'POST':
            s = ResultadoLoteSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            s.save(procedimento=proc)
            return Response(self._serializar(proc), status=status.HTTP_201_CREATED)
        return Response(ResultadoLoteSerializer(proc.resultados.all(), many=True).data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path=r'resultados/(?P<res_pk>[^/.]+)')
    def resultado_detail(self, request, pk=None, res_pk=None):
        proc = self.get_object()
        res = get_object_or_404(ResultadoLote, pk=res_pk, procedimento=proc)
        if request.method == 'DELETE':
            res.delete()
            return Response(self._serializar(proc))
        s = ResultadoLoteSerializer(res, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(self._serializar(proc))

    # ── Gerar Contrato a partir de resultado ──────────────────────────────────

    @action(detail=True, methods=['post'], url_path=r'resultados/(?P<res_pk>[^/.]+)/gerar-contrato')
    def gerar_contrato(self, request, pk=None, res_pk=None):
        """
        Cria um Contrato pré-preenchido a partir de um ResultadoLote homologado.
        Vincula automaticamente o lote e o DFD de origem.
        """
        proc = self.get_object()
        res = get_object_or_404(ResultadoLote, pk=res_pk, procedimento=proc)

        if res.resultado != 'homologado':
            return Response(
                {'detail': 'Só é possível gerar contrato para lotes homologados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if res.contrato_gerado:
            from modulo_contrato.serializers import ContratoSerializer
            return Response({
                'detail': 'Contrato já gerado para este lote.',
                'contrato_id': res.contrato_gerado.pk,
                'contrato_numero': res.contrato_gerado.numero,
            })

        from modulo_contrato.models import Contrato
        contrato = Contrato(
            exercicio=proc.exercicio,
            orgao_executor=proc.org_id,
            objeto=f'{proc.objeto} — {res.descricao_lote or (res.lote.descricao if res.lote else "")}',
            tipo_origem='licitacao' if proc.eh_licitacao else 'dispensa',
            dfd=proc.dfd,
            numero_processo_sei=proc.numero_sei or '',
            valor_contrato=res.valor_final or res.valor_estimado or Decimal('0'),
            status='Vigente',
            observacoes=(
                f'Gerado automaticamente via {proc.numero}. '
                f'Empresa: {res.empresa_vencedora} | CNPJ: {res.cnpj_vencedor}'
            ),
            org_id=proc.org_id,
            created_by=request.user,
            updated_by=request.user,
        )
        contrato.save()

        # Vincular o lote ao contrato
        if res.lote:
            contrato.lotes.add(res.lote)

        # Registrar resultado
        res.contrato_gerado = contrato
        res.save(update_fields=['contrato_gerado'])

        # Se todos os lotes tiverem contrato, marcar procedimento como Contratado
        todos_homologados = proc.resultados.filter(resultado='homologado')
        todos_com_contrato = all(r.contrato_gerado_id for r in todos_homologados)
        if todos_com_contrato and proc.status == 'Homologado':
            self._transicao(proc, 'Contratado', request.user,
                            f'Contrato {contrato.numero} gerado.')

        return Response({
            'detail': f'Contrato {contrato.numero} criado com sucesso.',
            'contrato_id': contrato.pk,
            'contrato_numero': contrato.numero,
            **self._serializar(proc),
        }, status=status.HTTP_201_CREATED)

    # ── Relatório completo de tramitação ─────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='export/historico')
    def export_historico(self, request, pk=None):
        from exportacao.pdf_utils import gerar_relatorio_procedimento, resposta_pdf
        proc = self.get_object()
        # Pré-carregar relacionamentos para evitar N+1 queries no PDF
        proc = (
            self.get_queryset()
            .select_related('org_id', 'dfd', 'tr', 'unidade_gestora', 'created_by')
            .prefetch_related(
                'historico__usuario',
                'tramitacoes__registrado_por',
                'resultados__lote',
                'resultados__contrato_gerado',
                'tr__lotes',
            )
            .get(pk=pk)
        )
        pdf = gerar_relatorio_procedimento(proc)
        return resposta_pdf(pdf, f'Relatorio_{proc.numero}.pdf')

    # ── Dashboard ─────────────────────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Retorna estatísticas agregadas para o painel de licitações.
        Query param: exercicio (opcional, padrão = ano corrente)
        """
        from django.db.models import Sum, Count

        exercicio = request.query_params.get('exercicio')
        qs = Procedimento.objects.filter(org_id=request.org_id)
        if exercicio:
            try:
                qs = qs.filter(exercicio=int(exercicio))
            except (ValueError, TypeError):
                pass

        total             = qs.count()
        valor_total       = qs.aggregate(v=Sum('valor_estimado'))['v'] or Decimal('0')
        em_andamento      = qs.exclude(status__in=['Contratado','Homologado','Deserto','Fracassado','Revogado','Anulado']).count()
        concluidos        = qs.filter(status__in=['Contratado','Homologado']).count()
        malsucedidos      = qs.filter(status__in=['Deserto','Fracassado','Revogado','Anulado']).count()

        MODALIDADE_LABEL = {
            'pregao_eletronico':    'Pregão Eletrônico',
            'concorrencia':         'Concorrência',
            'dispensa_eletronica':  'Dispensa Eletrônica',
            'dispensa_tradicional': 'Dispensa Tradicional',
            'inexigibilidade':      'Inexigibilidade',
        }
        por_modalidade = []
        for row in qs.values('modalidade').annotate(count=Count('id'), valor=Sum('valor_estimado')).order_by('-count'):
            por_modalidade.append({
                'modalidade': row['modalidade'],
                'label':      MODALIDADE_LABEL.get(row['modalidade'], row['modalidade']),
                'count':      row['count'],
                'valor':      float(row['valor'] or 0),
            })

        por_status = []
        for row in qs.values('status').annotate(count=Count('id')).order_by('-count'):
            por_status.append({'status': row['status'], 'count': row['count']})

        por_exercicio = []
        for row in qs.values('exercicio').annotate(count=Count('id'), valor=Sum('valor_estimado')).order_by('exercicio'):
            por_exercicio.append({
                'exercicio': row['exercicio'],
                'count':     row['count'],
                'valor':     float(row['valor'] or 0),
            })

        return Response({
            'total':              total,
            'valor_total':        float(valor_total),
            'em_andamento':       em_andamento,
            'concluidos':         concluidos,
            'malsucedidos':       malsucedidos,
            'por_modalidade':     por_modalidade,
            'por_status':         por_status,
            'por_exercicio':      por_exercicio,
        })

    # ── Verificar teto de dispensa ────────────────────────────────────────────

    @action(detail=False, methods=['get'], url_path='teto-dispensa')
    def teto_dispensa(self, request):
        """
        Retorna o acumulado de dispensas por exercício para a org corrente.
        """
        from django.db.models import Sum
        exercicio = int(request.query_params.get('exercicio', date.today().year))

        dispensas = Procedimento.objects.filter(
            org_id=request.org_id,
            exercicio=exercicio,
            modalidade__in=['dispensa_eletronica', 'dispensa_tradicional'],
            status__in=['Aprovado', 'Contratado', 'Homologado'],
        )

        total_geral = dispensas.aggregate(
            total=Sum('valor_estimado')
        )['total'] or Decimal('0')

        return Response({
            'exercicio': exercicio,
            'teto_bens_servicos': float(TETO_DISPENSA_BENS_SERVICOS),
            'teto_obras': float(TETO_DISPENSA_OBRAS),
            'total_dispensas': float(total_geral),
            'percentual_bens': round(float(total_geral / TETO_DISPENSA_BENS_SERVICOS * 100), 1),
            'qtd_procedimentos': dispensas.count(),
        })

    # ── Aprovação de peças instrutórias direto do Procedimento ───────────────────

    @action(detail=True, methods=['post'], url_path=r'pecas/(?P<tipo>[^/.]+)/(?P<peca_pk>[^/.]+)/aprovar')
    def aprovar_peca(self, request, pk=None, tipo=None, peca_pk=None):
        """
        Aprova uma peça instrutória (ETP, TR, Mapa) diretamente do Procedimento.
        tipo: 'etp' | 'tr' | 'mapa'
        """
        err = self._check_licitante(request)
        if err:
            return err

        self.get_object()  # verifica acesso ao procedimento

        try:
            if tipo == 'etp':
                from modulo_etp.models import ETP, HistoricoETP
                obj = get_object_or_404(ETP, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'ETP não está em análise (status: {obj.status}).'}, status=400)
                HistoricoETP.objects.create(etp=obj, status_anterior=obj.status,
                    status_novo='Aprovado', usuario=request.user,
                    motivo='Aprovado via painel do Procedimento.')
                obj.status = 'Aprovado'
                obj.updated_by = request.user
                obj.save()

            elif tipo == 'tr':
                from modulo_tr.models import TR, HistoricoTR
                obj = get_object_or_404(TR, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'TR não está em análise (status: {obj.status}).'}, status=400)
                HistoricoTR.objects.create(tr=obj, status_anterior=obj.status,
                    status_novo='Aprovado', usuario=request.user,
                    motivo='Aprovado via painel do Procedimento.')
                obj.status = 'Aprovado'
                obj.updated_by = request.user
                obj.save()

            elif tipo == 'mapa':
                from modulo_mapa_precos.models import MapaComparativoPrecos, HistoricoMapa
                from datetime import date
                obj = get_object_or_404(MapaComparativoPrecos, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'Mapa não está em análise (status: {obj.status}).'}, status=400)
                HistoricoMapa.objects.create(mapa=obj, status_anterior=obj.status,
                    status_novo='Aprovado', usuario=request.user,
                    motivo='Aprovado via painel do Procedimento.')
                obj.status = 'Aprovado'
                obj.aprovador = request.user
                obj.data_aprovacao = date.today()
                obj.updated_by = request.user
                obj.save()

            else:
                return Response({'detail': f'Tipo de peça desconhecido: {tipo}.'}, status=400)

        except Exception as e:
            return Response({'detail': str(e)}, status=400)

        proc = self.get_object()
        return Response({'detail': f'{tipo.upper()} aprovado com sucesso.', **self._serializar(proc)})

    @action(detail=True, methods=['post'], url_path=r'pecas/(?P<tipo>[^/.]+)/(?P<peca_pk>[^/.]+)/devolver')
    def devolver_peca(self, request, pk=None, tipo=None, peca_pk=None):
        """
        Devolve uma peça instrutória para correção diretamente do Procedimento.
        tipo: 'etp' | 'tr' | 'mapa'
        """
        err = self._check_licitante(request)
        if err:
            return err

        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Motivo da devolução é obrigatório.'}, status=400)

        self.get_object()

        try:
            if tipo == 'etp':
                from modulo_etp.models import ETP, HistoricoETP
                obj = get_object_or_404(ETP, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'ETP não está em análise (status: {obj.status}).'}, status=400)
                HistoricoETP.objects.create(etp=obj, status_anterior=obj.status,
                    status_novo='Devolvido', usuario=request.user, motivo=motivo)
                obj.status = 'Devolvido'
                obj.motivo_devolucao = motivo
                obj.updated_by = request.user
                obj.save()

            elif tipo == 'tr':
                from modulo_tr.models import TR, HistoricoTR
                obj = get_object_or_404(TR, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'TR não está em análise (status: {obj.status}).'}, status=400)
                HistoricoTR.objects.create(tr=obj, status_anterior=obj.status,
                    status_novo='Devolvido', usuario=request.user, motivo=motivo)
                obj.status = 'Devolvido'
                obj.motivo_devolucao = motivo
                obj.updated_by = request.user
                obj.save()

            elif tipo == 'mapa':
                from modulo_mapa_precos.models import MapaComparativoPrecos, HistoricoMapa
                obj = get_object_or_404(MapaComparativoPrecos, pk=peca_pk, org_id=request.org_id)
                if obj.status != 'Em Análise':
                    return Response({'detail': f'Mapa não está em análise (status: {obj.status}).'}, status=400)
                HistoricoMapa.objects.create(mapa=obj, status_anterior=obj.status,
                    status_novo='Devolvido', usuario=request.user, motivo=motivo)
                obj.status = 'Devolvido'
                obj.motivo_devolucao = motivo
                obj.updated_by = request.user
                obj.save()

            else:
                return Response({'detail': f'Tipo de peça desconhecido: {tipo}.'}, status=400)

        except Exception as e:
            return Response({'detail': str(e)}, status=400)

        proc = self.get_object()
        return Response({'detail': f'{tipo.upper()} devolvido. Motivo registrado no histórico.', **self._serializar(proc)})
