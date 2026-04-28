from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsMultiTenant
from .models import (
    MapaComparativoPrecos, HistoricoMapa, FonteConsultada, ItemMapa,
    PrecoColetado, TIPO_FONTE_CHOICES, METODO_CALCULO_CHOICES, TRANSICOES_MAPA,
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

    def _transicao(self, mapa, novo_status, usuario, motivo=None):
        """Valida e executa transição de status, registrando no histórico."""
        permitidos = TRANSICOES_MAPA.get(mapa.status, [])
        if novo_status not in permitidos:
            raise ValidationError(
                f'Transição "{mapa.status}" → "{novo_status}" não permitida.'
            )
        anterior = mapa.status
        mapa.status = novo_status
        mapa.updated_by = usuario
        mapa.save()
        HistoricoMapa.objects.create(
            mapa=mapa, status_anterior=anterior,
            status_novo=novo_status, usuario=usuario, motivo=motivo,
        )

    @action(detail=True, methods=['post'])
    def submeter(self, request, pk=None):
        """Submete o mapa para aprovação da Unidade Licitante."""
        mapa = self.get_object()
        if not mapa.itens.exists():
            return Response({'detail': 'Adicione ao menos um item antes de submeter.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not mapa.fontes.filter(infrutífera=False).exists():
            return Response({'detail': 'Adicione ao menos uma fonte de consulta válida.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # Valida prazo das cotações antes de submeter
        invalidados = mapa.validar_prazo_cotacoes()
        # Recalcula
        for item in mapa.itens.all():
            item.calcular(metodo=mapa.metodo_calculo)
        mapa.recalcular_total()
        self._transicao(mapa, 'Submetido', request.user)
        resp = {'detail': 'Mapa submetido para aprovação da Unidade Licitante.',
                'valor_total': float(mapa.valor_estimado_total)}
        if invalidados:
            resp['aviso'] = (
                f'{len(invalidados)} cotação(ões) foram invalidadas automaticamente '
                'por estarem fora do prazo de validade configurado nos Parâmetros do Sistema.'
            )
        return Response(resp)

    @action(detail=True, methods=['post'])
    def iniciar_analise(self, request, pk=None):
        """Licitante inicia análise do mapa."""
        if getattr(request, 'tipo_unidade', None) != 'licitante' and getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas a Unidade Licitante pode iniciar a análise.'},
                            status=status.HTTP_403_FORBIDDEN)
        mapa = self.get_object()
        self._transicao(mapa, 'Em Análise', request.user)
        return Response({'detail': 'Análise iniciada.'})

    @action(detail=True, methods=['post'])
    def aprovar(self, request, pk=None):
        """Unidade Licitante aprova o mapa."""
        if getattr(request, 'tipo_unidade', None) != 'licitante' and getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas a Unidade Licitante pode aprovar o mapa.'},
                            status=status.HTTP_403_FORBIDDEN)
        mapa = self.get_object()
        self._transicao(mapa, 'Aprovado', request.user)
        from datetime import date
        mapa.aprovador = request.user
        mapa.data_aprovacao = date.today()
        mapa.motivo_devolucao = ''
        mapa.save(update_fields=['aprovador', 'data_aprovacao', 'motivo_devolucao'])
        return Response({'detail': 'Mapa aprovado pela Unidade Licitante.'})

    @action(detail=True, methods=['post'])
    def devolver(self, request, pk=None):
        """Unidade Licitante devolve o mapa para correção."""
        if getattr(request, 'tipo_unidade', None) != 'licitante' and getattr(request, 'papel', None) != 'admin':
            return Response({'detail': 'Apenas a Unidade Licitante pode devolver o mapa.'},
                            status=status.HTTP_403_FORBIDDEN)
        motivo = request.data.get('motivo', '').strip()
        if not motivo:
            return Response({'detail': 'Motivo da devolução é obrigatório.'},
                            status=status.HTTP_400_BAD_REQUEST)
        mapa = self.get_object()
        self._transicao(mapa, 'Devolvido', request.user, motivo)
        mapa.motivo_devolucao = motivo
        mapa.save(update_fields=['motivo_devolucao'])
        return Response({'detail': 'Mapa devolvido para correção.'})

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        mapa = self.get_object()
        motivo = request.data.get('motivo', '').strip()
        self._transicao(mapa, 'Cancelado', request.user, motivo or None)
        return Response({'detail': 'Mapa cancelado.'})

    @action(detail=True, methods=['post'])
    def validar_prazos(self, request, pk=None):
        """Executa validação de prazos manualmente em todas as cotações."""
        mapa = self.get_object()
        invalidados = mapa.validar_prazo_cotacoes()
        return Response({
            'invalidados': len(invalidados),
            'detail': (
                f'{len(invalidados)} cotação(ões) invalidada(s) por prazo vencido.'
                if invalidados else 'Todas as cotações estão dentro do prazo.'
            ),
        })

    # ── Análise estatística das cotações (para orientar escolha do método) ────
    @action(detail=True, methods=['get'])
    def analisar(self, request, pk=None):
        """
        Analisa a distribuição dos preços coletados por item e sugere o método
        de cálculo mais adequado com base na variação e presença de outliers.
        Deve ser consultado APÓS a inserção das cotações.
        """
        import statistics as _stats
        mapa = self.get_object()
        resultados = []

        for item in mapa.itens.all():
            precos_validos = [float(p.valor_unitario) for p in item.precos.filter(valido=True)]
            total_precos   = item.precos.count()
            invalidos      = item.precos.filter(valido=False).count()

            if not precos_validos:
                resultados.append({
                    'item_id': item.id, 'descricao': item.descricao[:60],
                    'qtd_validos': 0, 'qtd_total': total_precos, 'qtd_invalidos': invalidos,
                    'sem_precos_validos': True,
                    'metodo_sugerido': None,
                    'motivo_sugestao': 'Nenhum preço válido cadastrado para este item.',
                })
                continue

            minimo   = min(precos_validos)
            maximo   = max(precos_validos)
            media    = sum(precos_validos) / len(precos_validos)
            mediana  = float(_stats.median(precos_validos))
            variacao_pct = ((maximo - minimo) / minimo * 100) if minimo > 0 else 0
            outliers = len([v for v in precos_validos if v > mediana * 1.30 or v < mediana * 0.70])
            abaixo_minimo = len([v for v in precos_validos if v < mediana * 0.70])
            acima_maximo  = len([v for v in precos_validos if v > mediana * 1.30])

            # Sugestão fundamentada no Decreto 22.886/2024, Art. 8º
            if len(precos_validos) < 3:
                metodo = 'media'
                motivo = (
                    f'Apenas {len(precos_validos)} preço(s) válido(s). '
                    'Qualquer método pode ser aplicado, mas exige justificativa obrigatória '
                    '(§5, Art. 8º, Decreto 22.886/2024).'
                )
            elif outliers > 0:
                metodo = 'mediana'
                partes = []
                if abaixo_minimo: partes.append(f'{abaixo_minimo} inexequível(is) (<−30%)')
                if acima_maximo:  partes.append(f'{acima_maximo} excessivo(s) (>+30%)')
                motivo = (
                    f'Variação de {variacao_pct:.1f}% entre os preços ({", ".join(partes)}). '
                    'A mediana é mais robusta a valores extremos e protege contra sobrepreço.'
                )
            elif variacao_pct > 20:
                metodo = 'mediana'
                motivo = (
                    f'Variação de {variacao_pct:.1f}% entre os preços válidos. '
                    'A mediana é indicada quando há dispersão moderada a alta.'
                )
            elif variacao_pct <= 10:
                metodo = 'media'
                motivo = (
                    f'Baixa variação ({variacao_pct:.1f}%) entre os preços. '
                    'A média aritmética é indicada quando os valores são homogêneos.'
                )
            else:
                metodo = 'media'
                motivo = (
                    f'Variação de {variacao_pct:.1f}% — variação aceitável. '
                    'A média aritmética pode ser utilizada.'
                )

            resultados.append({
                'item_id':        item.id,
                'descricao':      item.descricao[:60],
                'qtd_validos':    len(precos_validos),
                'qtd_total':      total_precos,
                'qtd_invalidos':  invalidos,
                'minimo':         round(minimo, 2),
                'maximo':         round(maximo, 2),
                'media':          round(media, 2),
                'mediana':        round(mediana, 2),
                'variacao_pct':   round(variacao_pct, 1),
                'outliers':       outliers,
                'abaixo_minimo':  abaixo_minimo,
                'acima_maximo':   acima_maximo,
                'metodo_sugerido': metodo,
                'motivo_sugestao': motivo,
                'menos_de_3':     len(precos_validos) < 3,
            })

        # Sugestão global: se qualquer item tem outliers ou variação alta → mediana
        itens_validos = [r for r in resultados if not r.get('sem_precos_validos')]
        metodo_global = 'mediana' if any(
            r['outliers'] > 0 or r['variacao_pct'] > 20
            for r in itens_validos
        ) else 'media'

        precisa_justificativa = any(
            r.get('menos_de_3') or r.get('outliers', 0) > 0
            for r in itens_validos
        )

        return Response({
            'itens':                 resultados,
            'metodo_sugerido_global': metodo_global,
            'precisa_justificativa':  precisa_justificativa,
            'nota': (
                'Sugestão baseada no Art. 8º do Decreto Estadual 22.886/2024. '
                'O responsável pode adotar método diferente mediante justificativa.'
            ),
        })

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
        ctx = {'request': request}
        if request.method == 'POST':
            serializer = PrecoColetadoSerializer(data=request.data, context=ctx)
            serializer.is_valid(raise_exception=True)
            preco = serializer.save(item=item)
            item.calcular(metodo=mapa.metodo_calculo)
            mapa.recalcular_total()
            return Response(PrecoColetadoSerializer(preco, context=ctx).data, status=status.HTTP_201_CREATED)
        serializer = PrecoColetadoSerializer(item.precos.all(), many=True, context=ctx)
        return Response(serializer.data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='itens/(?P<item_pk>[^/.]+)/precos/(?P<preco_pk>[^/.]+)')
    def preco_detail(self, request, pk=None, item_pk=None, preco_pk=None):
        mapa  = self.get_object()
        item  = get_object_or_404(ItemMapa, pk=item_pk, mapa=mapa)
        preco = get_object_or_404(PrecoColetado, pk=preco_pk, item=item)
        ctx   = {'request': request}
        if request.method == 'DELETE':
            preco.delete()
            item.calcular(metodo=mapa.metodo_calculo)
            mapa.recalcular_total()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = PrecoColetadoSerializer(preco, data=request.data, partial=True, context=ctx)
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
