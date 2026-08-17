from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import IsMultiTenant, PAPEIS_ANALISTA, check_licitante
from core.checklist_engine import ChecklistEngine
from .models import ETP, HistoricoETP
from .serializers import ETPSerializer
from exportacao.pdf_utils import gerar_pdf_etp, gerar_html, resposta_pdf, resposta_html

PAPEIS_SOLICITANTE = ('solicitante', 'demandante', 'responsavel_tecnico', 'admin')

# Códigos de SecaoArtefato já exibidos estaticamente em templates/exportacao/etp.html —
# usado para não duplicar conteúdo ao acrescentar seções custom (ver core/document_engine.py)
CODIGOS_ESTATICOS_ETP = [
    'numero_sei', 'necessidade', 'requisitos', 'levantamento_mercado', 'solucao',
    'justificativa', 'estimativa_valor', 'riscos', 'sustentabilidade', 'parcelamento',
    'cota_me_epp', 'posicionamento_conclusivo', 'classificacao_sensivel',
    'alinhamento_planesp', 'contratacoes_correlatas', 'impacto_ambiental',
    'providencias_pre_contrato', 'compra_vs_locacao', 'observacoes',
]


class ETPViewSet(viewsets.ModelViewSet):
    serializer_class   = ETPSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields    = ['created_at', 'numero_sei', 'status']
    ordering           = ['-created_at']
    search_fields      = ['numero_sei', 'necessidade_contratacao']

    def get_queryset(self):
        oid = self.request.org_id
        return ETP.objects.filter(
            Q(org_id=oid) |
            Q(dfd__org_gestor=oid) |
            Q(dfd__unidade_licitante__orgao_id=oid)
        ).distinct().select_related('dfd', 'org_id').prefetch_related(
            'historico', 'historico_numero_sei', 'tr'
        )

    # ------------------------------------------------------------------ #
    # helpers                                                              #
    # ------------------------------------------------------------------ #

    def _transicao(self, request, status_novo, campos_extra=None):
        etp = self.get_object()
        permitidos = ETP.TRANSICOES_PERMITIDAS.get(etp.status, [])
        if status_novo not in permitidos:
            return Response(
                {'detail': f'Transição de "{etp.status}" para "{status_novo}" não é permitida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        status_anterior = etp.status
        motivo = (campos_extra or {}).get('motivo')

        etp.status = status_novo
        if campos_extra:
            for campo, valor in campos_extra.items():
                if campo != 'motivo':
                    setattr(etp, campo, valor)
        if status_novo == 'Submetido':
            etp.motivo_devolucao = None
        etp.updated_by = request.user
        etp.save()

        categoria = (campos_extra or {}).get('categoria_motivo', '')
        HistoricoETP.objects.create(
            etp=etp,
            status_anterior=status_anterior,
            status_novo=status_novo,
            usuario=request.user,
            motivo=motivo,
            categoria_motivo=categoria,
        )

        return Response(self.get_serializer(etp).data)

    # ------------------------------------------------------------------ #
    # checklist                                                            #
    # ------------------------------------------------------------------ #

    @action(detail=True, methods=['get'])
    def checklist(self, request, pk=None):
        etp = self.get_object()
        resultado = ChecklistEngine.avaliar_etp(etp)
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
        etp = self.get_object()
        pdf = gerar_pdf_etp(etp)
        return resposta_pdf(pdf, f'ETP_{etp.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/historico')
    def export_historico(self, request, pk=None):
        from exportacao.pdf_utils import gerar_pdf_historico
        etp = self.get_object()
        pdf = gerar_pdf_historico(
            titulo='ETP',
            numero_ref=etp.numero_sei,
            historico_entries=etp.historico.select_related('usuario').order_by('-criado_em'),
            org_nome=etp.org_id.nome if etp.org_id else '',
            org_sigla=etp.org_id.sigla if etp.org_id else None,
            criado_por=etp.created_by,
            created_at=etp.created_at,
        )
        return resposta_pdf(pdf, f'Historico_ETP_{etp.numero_sei}.pdf')

    @action(detail=True, methods=['get'], url_path='export/html')
    def export_html(self, request, pk=None):
        from core.document_engine import DocumentEngine
        etp = self.get_object()
        html = gerar_html('etp', {
            'etp': etp,
            'secoes_geradas': DocumentEngine.gerar('ETP', etp),
            'codigos_estaticos': CODIGOS_ESTATICOS_ETP,
        })
        return resposta_html(html, f'ETP_{etp.numero_sei}.html')

    @action(detail=True, methods=['get'], url_path='gerar-texto')
    def gerar_texto(self, request, pk=None):
        from core.document_engine import DocumentEngine
        etp = self.get_object()
        return Response(DocumentEngine.gerar('ETP', etp))

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_SOLICITANTE:
            return Response({'detail': 'Apenas solicitantes podem submeter o ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Submetido')

    @action(detail=True, methods=['post'])
    def iniciar_analise(self, request, pk=None):
        papel = getattr(request, 'papel', None)
        if papel not in PAPEIS_ANALISTA:
            return Response({'detail': 'Apenas analistas podem iniciar análise do ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Em Análise')

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem aprovar o ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        return self._transicao(request, 'Aprovado',
                               campos_extra={'motivo': request.data.get('motivo')})

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        if not check_licitante(request):
            return Response({'detail': 'Apenas analistas da unidade licitante podem devolver o ETP.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        categoria = request.data.get('categoria_motivo', '')
        return self._transicao(request, 'Devolvido',
                               campos_extra={'motivo_devolucao': motivo, 'motivo': motivo,
                                             'categoria_motivo': categoria})

    @action(detail=True, methods=['post'])
    def reabrir(self, request, pk=None):
        """Derruba a aprovação do ETP e retorna para Devolvido (somente admin).
        Se existir TR Aprovado vinculado, também o devolve automaticamente."""
        if getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas administradores podem reabrir ETPs aprovados.'},
                            status=status.HTTP_403_FORBIDDEN)
        etp = self.get_object()
        if etp.status not in ('Aprovado', 'Cancelado'):
            return Response({'detail': 'Apenas ETPs Aprovados ou Cancelados podem ser reabertos.'},
                            status=status.HTTP_400_BAD_REQUEST)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'O motivo da reabertura é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)

        HistoricoETP.objects.create(
            etp=etp, status_anterior=etp.status, status_novo='Devolvido',
            usuario=request.user, motivo=f'[REABERTURA] {motivo}',
        )
        etp.status = 'Devolvido'
        etp.motivo_devolucao = f'Reabertura pelo admin: {motivo}'
        etp.save(update_fields=['status', 'motivo_devolucao'])

        # Cascata: se TR vinculado está Aprovado, devolver também
        tr_cascata = None
        try:
            tr = etp.tr
            if tr and tr.status == 'Aprovado':
                from modulo_tr.models import HistoricoTR
                motivo_tr = f'[CASCATA ETP] ETP reaaberto pelo admin: {motivo}'
                HistoricoTR.objects.create(
                    tr=tr, status_anterior=tr.status, status_novo='Devolvido',
                    usuario=request.user, motivo=motivo_tr,
                )
                tr.status = 'Devolvido'
                tr.motivo_devolucao = motivo_tr
                tr.save(update_fields=['status', 'motivo_devolucao'])
                tr_cascata = tr.numero_sei
        except Exception:
            pass

        data = ETPSerializer(etp, context={'request': request}).data
        if tr_cascata:
            data['aviso'] = f'TR {tr_cascata} também foi devolvido automaticamente pois estava Aprovado.'
        return Response(data)

    def perform_update(self, serializer):
        if serializer.instance.status in ('Aprovado', 'Cancelado', 'Dispensado'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('ETPs aprovados, dispensados ou cancelados não podem ser editados.')
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status not in ('Rascunho', 'Devolvido'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Apenas ETPs em Rascunho ou Devolvido podem ser excluídos.')
        instance.delete()
