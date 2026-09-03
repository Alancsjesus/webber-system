from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsMultiTenant

from .models import ProcessoTramitacao, HistoricoTramitacaoProcesso
from .serializers import ProcessoTramitacaoSerializer, ProcessoTramitacaoResumoSerializer

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
    Agrega processos ativos por setor, na ordem de ProcessoTramitacao.SETOR_CHOICES
    (não alfabética — bate com o relatório gerencial de referência).

    Filtros opcionais: ?setor_atual=<código> / ?fonte_recurso=<id> / ?busca=<texto>
    Exportação: ?export=pdf|xlsx (nunca ?format=, reservado pela negociação de
    conteúdo do DRF — já causou 404 silencioso em outros endpoints do projeto).
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def _queryset(self, request):
        qs = ProcessoTramitacao.objects.filter(org_id=request.org_id, ativo=True).prefetch_related('fontes_recurso')
        setor = request.query_params.get('setor_atual')
        fonte = request.query_params.get('fonte_recurso')
        busca = request.query_params.get('busca')
        if setor:
            qs = qs.filter(setor_atual=setor)
        if fonte:
            qs = qs.filter(fontes_recurso__id=fonte)
        if busca:
            qs = qs.filter(Q(numero_sei__icontains=busca) | Q(objeto__icontains=busca))
        return qs.order_by('-data_entrada_fase')

    def get(self, request):
        qs = self._queryset(request)

        fmt = request.query_params.get('export')
        if fmt == 'pdf':
            from core.models import Orgao
            from exportacao.pdf_utils import gerar_pdf_painel_tramitacao, resposta_pdf
            orgao = Orgao.objects.filter(pk=request.org_id).first()
            pdf = gerar_pdf_painel_tramitacao(list(qs), orgao)
            return resposta_pdf(pdf, 'PainelTramitacao.pdf')
        if fmt == 'xlsx':
            from exportacao.xlsx_utils import gerar_xlsx_painel_tramitacao
            return gerar_xlsx_painel_tramitacao(list(qs), 'PainelTramitacao.xlsx')

        ordem = [codigo for codigo, _ in ProcessoTramitacao.SETOR_CHOICES]
        por_setor = {codigo: [] for codigo in ordem}
        for processo in qs:
            por_setor[processo.setor_atual].append(processo)

        grupos = []
        for codigo, label in ProcessoTramitacao.SETOR_CHOICES:
            itens = por_setor[codigo]
            if not itens:
                continue
            grupos.append({
                'setor': codigo,
                'setor_display': label,
                'total': len(itens),
                'itens': ProcessoTramitacaoResumoSerializer(itens, many=True).data,
            })

        return Response({'total_geral': qs.count(), 'grupos': grupos})
