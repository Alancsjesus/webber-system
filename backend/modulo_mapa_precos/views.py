from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsMultiTenant
from .models import (
    MapaComparativoPrecos, FonteConsultada, ItemMapa,
    PrecoColetado, TIPO_FONTE_CHOICES, METODO_CALCULO_CHOICES,
)
from .serializers import (
    MapaComparativoPrecosSerializer, FonteConsultadaSerializer,
    ItemMapaSerializer, PrecoColetadoSerializer,
)


class MapaComparativoPrecosViewSet(viewsets.ModelViewSet):
    serializer_class   = MapaComparativoPrecosSerializer
    permission_classes = [IsAuthenticated, IsMultiTenant]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['objeto', 'dfd__numero_sei']
    ordering_fields    = ['exercicio_fiscal', 'status', 'created_at']
    ordering           = ['-exercicio_fiscal', '-created_at']

    def get_queryset(self):
        qs = MapaComparativoPrecos.objects.filter(
            org_id=self.request.org_id
        ).select_related('dfd', 'responsavel', 'org_id', 'created_by')
        stat = self.request.query_params.get('status')
        exercicio = self.request.query_params.get('exercicio_fiscal')
        if stat:
            qs = qs.filter(status=stat)
        if exercicio:
            qs = qs.filter(exercicio_fiscal=exercicio)
        return qs

    # ── Metadados para o frontend ──────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='metadados')
    def metadados(self, request):
        return Response({
            'tipos_fonte':      [{'value': v, 'label': l} for v, l in TIPO_FONTE_CHOICES],
            'metodos_calculo':  [{'value': v, 'label': l} for v, l in METODO_CALCULO_CHOICES],
        })

    # ── Finalizar mapa ────────────────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        mapa = self.get_object()
        if mapa.status != 'Rascunho':
            return Response({'detail': 'Apenas mapas em Rascunho podem ser finalizados.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Recalcula todos os itens antes de finalizar
        for item in mapa.itens.all():
            item.calcular(metodo=mapa.metodo_calculo)
        mapa.recalcular_total()
        mapa.status = 'Finalizado'
        mapa.updated_by = request.user
        mapa.save()
        return Response({'detail': 'Mapa finalizado.', 'valor_total': float(mapa.valor_estimado_total)})

    # ── Recalcular todos os itens ─────────────────────────────────────────────
    @action(detail=True, methods=['post'])
    def recalcular(self, request, pk=None):
        mapa = self.get_object()
        resultados = []
        for item in mapa.itens.all():
            r = item.calcular(metodo=mapa.metodo_calculo)
            resultados.append({'item_id': item.id, 'descricao': item.descricao[:50], **r})
        mapa.recalcular_total()
        return Response({
            'itens':        resultados,
            'valor_total':  float(mapa.valor_estimado_total),
        })

    # ── Consultar histórico WEBBER ─────────────────────────────────────────────
    @action(detail=True, methods=['get'], url_path='historico-webber')
    def historico_webber(self, request, pk=None):
        """
        Busca preços de referência no histórico interno do WEBBER.
        Retorna itens de DFDs aprovados com descrição similar ao objeto do mapa.
        Inclui indicação se a aquisição foi bem-sucedida, deserta ou fracassada.
        """
        from modulo_demanda.models import DFD, ItemDFD
        mapa = self.get_object()

        # Busca DFDs aprovados do mesmo órgão nos últimos 2 anos
        from django.utils import timezone
        from datetime import timedelta
        dois_anos_atras = timezone.now() - timedelta(days=730)

        dfds_aprovados = DFD.objects.filter(
            org_id=request.org_id,
            status='Aprovada',
            created_at__gte=dois_anos_atras,
        ).exclude(pk=mapa.dfd_id)

        resultados = []
        for dfd in dfds_aprovados[:20]:  # limita para performance
            for item in dfd.itens.all():
                resultados.append({
                    'dfd_id':           dfd.pk,
                    'dfd_numero_sei':   dfd.numero_sei,
                    'dfd_status':       dfd.status,
                    'dfd_data':         dfd.created_at.strftime('%d/%m/%Y'),
                    'item_descricao':   item.objeto,
                    'valor_unitario':   float(item.valor_unitario_estimado),
                    'unidade_medida':   item.unidade_medida,
                    'quantidade':       float(item.quantidade),
                    'origem':           'HIST',
                    'origem_label':     f'Histórico WEBBER — DFD {dfd.numero_sei}',
                })

        return Response({
            'total': len(resultados),
            'itens': resultados,
            'nota':  'Preços de DFDs aprovados do seu órgão nos últimos 2 anos. '
                     'Use para validar coerência dos preços coletados externamente.',
        })

    # ── CRUD de Fontes ─────────────────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='fontes')
    def fontes(self, request, pk=None):
        mapa = self.get_object()
        if request.method == 'POST':
            serializer = FonteConsultadaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(mapa=mapa)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer = FonteConsultadaSerializer(mapa.fontes.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='fontes/(?P<fonte_pk>[^/.]+)')
    def fonte_detail(self, request, pk=None, fonte_pk=None):
        mapa  = self.get_object()
        fonte = get_object_or_404(FonteConsultada, pk=fonte_pk, mapa=mapa)
        if request.method == 'DELETE':
            fonte.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = FonteConsultadaSerializer(fonte, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── CRUD de Itens ──────────────────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='itens')
    def itens(self, request, pk=None):
        mapa = self.get_object()
        if request.method == 'POST':
            serializer = ItemMapaSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(mapa=mapa)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer = ItemMapaSerializer(mapa.itens.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='itens/(?P<item_pk>[^/.]+)')
    def item_detail(self, request, pk=None, item_pk=None):
        mapa = self.get_object()
        item = get_object_or_404(ItemMapa, pk=item_pk, mapa=mapa)
        if request.method == 'DELETE':
            item.delete()
            mapa.recalcular_total()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = ItemMapaSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── CRUD de Preços por Item ────────────────────────────────────────────────
    @action(detail=True, methods=['get', 'post'],
            url_path='itens/(?P<item_pk>[^/.]+)/precos')
    def precos(self, request, pk=None, item_pk=None):
        mapa = self.get_object()
        item = get_object_or_404(ItemMapa, pk=item_pk, mapa=mapa)
        if request.method == 'POST':
            serializer = PrecoColetadoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            preco = serializer.save(item=item)
            # Recalcula o item após novo preço
            item.calcular(metodo=mapa.metodo_calculo)
            mapa.recalcular_total()
            return Response(PrecoColetadoSerializer(preco).data, status=status.HTTP_201_CREATED)
        serializer = PrecoColetadoSerializer(item.precos.all(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='itens/(?P<item_pk>[^/.]+)/precos/(?P<preco_pk>[^/.]+)')
    def preco_detail(self, request, pk=None, item_pk=None, preco_pk=None):
        mapa  = self.get_object()
        item  = get_object_or_404(ItemMapa, pk=item_pk, mapa=mapa)
        preco = get_object_or_404(PrecoColetado, pk=preco_pk, item=item)
        if request.method == 'DELETE':
            preco.delete()
            item.calcular(metodo=mapa.metodo_calculo)
            mapa.recalcular_total()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = PrecoColetadoSerializer(preco, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        item.calcular(metodo=mapa.metodo_calculo)
        mapa.recalcular_total()
        return Response(serializer.data)

    # ── Export PDF ────────────────────────────────────────────────────────────
    @action(detail=True, methods=['get'], url_path='export/pdf')
    def export_pdf(self, request, pk=None):
        mapa = self.get_object()
        from exportacao.pdf_utils import gerar_pdf_mapa, resposta_pdf
        pdf = gerar_pdf_mapa(mapa)
        return resposta_pdf(pdf, f'Mapa-Precos-{mapa.pk}.pdf')
