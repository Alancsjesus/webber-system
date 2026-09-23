from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant

from .models import ProcessoTramitacao, HistoricoTramitacaoProcesso
from .serializers import ProcessoTramitacaoSerializer

PAPEIS_PAINEL_TRAMITACAO = ('admin', 'gestor_planejamento', 'ordenador')


def _check_permissao(request):
    if getattr(request, 'papel', None) not in PAPEIS_PAINEL_TRAMITACAO:
        raise PermissionDenied('Apenas Gestor de Planejamento, Ordenador ou Admin podem gerenciar o painel de tramitação.')


class ProcessoTramitacaoViewSet(viewsets.ModelViewSet):
    serializer_class = ProcessoTramitacaoSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_sei', 'objeto']
    ordering_fields = ['data_entrada_fase', 'setor_atual', 'created_at']
    ordering = ['setor_atual', '-data_entrada_fase']

    def get_queryset(self):
        qs = ProcessoTramitacao.objects.filter(org_id=self.request.org_id).select_related(
            'org_id', 'created_by', 'dfd',
        ).prefetch_related('fontes_recurso', 'historico')
        setor = self.request.query_params.get('setor_atual')
        ativo = self.request.query_params.get('ativo')
        if setor:
            qs = qs.filter(setor_atual=setor)
        if ativo in ('true', 'false'):
            qs = qs.filter(ativo=(ativo == 'true'))
        return qs

    def perform_create(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _check_permissao(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _check_permissao(self.request)
        instance.delete()

    @action(detail=True, methods=['post'], url_path='mudar-fase')
    def mudar_fase(self, request, pk=None):
        _check_permissao(request)
        processo = self.get_object()
        setor_novo = request.data.get('setor_atual')
        if setor_novo not in dict(ProcessoTramitacao.SETOR_CHOICES):
            return Response({'detail': 'Setor inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        fase_nova = (request.data.get('fase_atual') or '').strip()
        data_entrada = request.data.get('data_entrada_fase') or processo.data_entrada_fase
        motivo = (request.data.get('motivo') or '').strip()

        HistoricoTramitacaoProcesso.objects.create(
            processo=processo,
            setor_anterior=processo.setor_atual,
            fase_anterior=processo.fase_atual,
            setor_novo=setor_novo,
            fase_nova=fase_nova,
            usuario=request.user,
            motivo=motivo,
        )
        processo.setor_atual = setor_novo
        processo.fase_atual = fase_nova
        processo.data_entrada_fase = data_entrada
        processo.updated_by = request.user
        processo.save()
        if hasattr(processo, '_prefetched_objects_cache'):
            processo._prefetched_objects_cache.pop('historico', None)
        return Response(self.get_serializer(processo).data)


class PainelTramitacaoView(APIView):
    """
    GET /api/tramitacao/painel/
    Agrega, por setor, dois grupos de origem:
    1. Automática — todo DFD "aberto" da organização (status != Rejeitada, ainda não
       chegou a Procedimento contratado), com o setor resolvido em
       `estagio.resolver_item_painel()` (TramitacaoExterna aberta > mesa_atual manual
       > FK fixa de responsabilidade da etapa > fallback etapa+status). Zero digitação
       na maioria dos casos — só quando nem a FK fixa está preenchida.
    2. Manual — `ProcessoTramitacao` com `dfd` nulo: fase anterior a existir DFD no
       sistema ("demandante puro"). Ao vincular um DFD a um registro existente, ele
       passa a ser coberto pela agregação automática e some daqui.

    Setor deixa de ser um código fixo — é o rótulo da unidade/órgão/etapa resolvida,
    então os grupos vêm ordenados alfabeticamente (não há mais uma ordem fixa possível).

    Filtro opcional: ?busca=<texto> (nº SEI ou objeto). Exportação: ?export=pdf|xlsx
    (nunca ?format=, reservado pela negociação de conteúdo do DRF).
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def _itens(self, request):
        from .estagio import listar_itens_painel
        return listar_itens_painel(request)

    def get(self, request):
        itens = self._itens(request)

        fmt = request.query_params.get('export')
        if fmt == 'pdf':
            from core.models import Orgao
            from exportacao.pdf_utils import gerar_pdf_painel_tramitacao, resposta_pdf
            orgao = Orgao.objects.filter(pk=request.org_id).first()
            pdf = gerar_pdf_painel_tramitacao(itens, orgao)
            return resposta_pdf(pdf, 'PainelTramitacao.pdf')
        if fmt == 'xlsx':
            from exportacao.xlsx_utils import gerar_xlsx_painel_tramitacao
            return gerar_xlsx_painel_tramitacao(itens, 'PainelTramitacao.xlsx')

        por_setor = {}
        for item in itens:
            por_setor.setdefault(item['setor'], []).append(item)

        grupos = []
        for setor in sorted(por_setor.keys()):
            grupo_itens = sorted(por_setor[setor], key=lambda i: i['numero_sei'] or '')
            grupos.append({
                'setor': setor,
                'setor_display': setor,
                'total': len(grupo_itens),
                'itens': grupo_itens,
            })

        return Response({'total_geral': len(itens), 'grupos': grupos})


class IndicadoresTramitacaoView(APIView):
    """
    GET /api/tramitacao/indicadores/
    Indicadores de tempo sobre o Painel de Tramitação (D1): tempo médio de
    permanência na etapa/fase atual (geral, por setor e por etapa), contagem
    de processos críticos/em atenção (limiares configuráveis via
    ParametroSistema: tramitacao_dias_atencao, tramitacao_dias_critico —
    default 15/30 dias) e lista dos processos mais parados.

    Também traz `duracao_por_modalidade`: diferente do resto do endpoint (que
    mede tempo NA ETAPA ATUAL de processos em andamento), isto mede o ciclo
    completo — dias do início do Procedimento até a assinatura do Contrato —
    de processos já CONCLUÍDOS, por modalidade (Pregão, Dispensa, etc.). Ver
    core.cronograma_contratacoes.estatisticas_duracao_por_modalidade.

    Filtros opcionais: ?busca=<texto> (nº SEI ou objeto, mesmo do painel),
    ?setor=<setor exato>, ?etapa=<DFD|ETP|TR|Procedimento|manual>,
    ?data_inicio=/?data_fim=<YYYY-MM-DD> (sobre data_entrada_fase).
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from .indicadores import calcular_indicadores
        return Response(calcular_indicadores(request))
