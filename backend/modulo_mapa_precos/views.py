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
    PrecoColetado, SolicitacaoCotacao, RespostaCotacao,
    TIPO_FONTE_CHOICES, METODO_CALCULO_CHOICES, TRANSICOES_MAPA,
)
from .serializers import (
    MapaComparativoPrecosSerializer, FonteConsultadaSerializer,
    ItemMapaSerializer, PrecoColetadoSerializer,
    SolicitacaoCotacaoSerializer, RespostaCotacaoSerializer,
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

    def _transicao(self, mapa, novo_status, usuario, motivo=None, categoria_motivo=''):
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
            categoria_motivo=categoria_motivo,
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
        FONTES_INSTITUCIONAIS = ('I', 'II', 'HIST')  # SIMPAS/Comprasnet, contratações públicas, histórico próprio
        tem_fonte_institucional = mapa.fontes.filter(infrutífera=False, tipo__in=FONTES_INSTITUCIONAIS).exists()
        if not tem_fonte_institucional and not mapa.parametros_combinados_justificativa.strip():
            return Response({
                'detail': 'A pesquisa usa apenas fontes de mercado/privadas (Parâmetros III/IV/V), sem nenhuma fonte '
                           'institucional (SIMPAS/Comprasnet, contratações públicas similares ou histórico WEBBER). '
                           'O TCU exige priorizar preços públicos numa "cesta de preços" (Acórdão 1875/2021 e '
                           'reiterações); preencha "Justificativa pela não combinação de parâmetros" explicando a '
                           'ausência ou impossibilidade de fontes públicas antes de submeter.',
                'campo': 'parametros_combinados_justificativa',
            }, status=status.HTTP_400_BAD_REQUEST)
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
        if mapa.dfd_id:
            from modulo_tr.models import TR
            from modulo_tr.precos import atualizar_precos
            for tr in TR.objects.filter(etp__dfd_id=mapa.dfd_id, status__in=('Rascunho', 'Devolvido')):
                atualizar_precos(tr)
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
        categoria = request.data.get('categoria_motivo', '')
        mapa = self.get_object()
        self._transicao(mapa, 'Devolvido', request.user, motivo, categoria_motivo=categoria)
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
    def encerrar(self, request, pk=None):
        """Encerra sem prosseguimento (ver core.encerramento)."""
        from core.encerramento import validar_pedido, impedimento_mapa, PAPEIS_ENCERRAR
        if getattr(request, 'papel', None) not in PAPEIS_ENCERRAR:
            return Response({'detail': 'Seu papel não permite encerrar a peça.'}, status=status.HTTP_403_FORBIDDEN)
        mapa = self.get_object()
        try:
            categoria, motivo = validar_pedido(request.data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        impedimento = impedimento_mapa(mapa)
        if impedimento:
            return Response({'detail': impedimento}, status=status.HTTP_400_BAD_REQUEST)
        self._transicao(mapa, 'Encerrado', request.user, motivo, categoria)
        return Response({'detail': 'Mapa encerrado sem prosseguimento.'})

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
            desvio   = _stats.stdev(precos_validos) if len(precos_validos) > 1 else 0.0
            cv_pct   = (desvio / media * 100) if media else 0.0
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
            elif cv_pct > 25:
                metodo = 'mediana'
                motivo = (
                    f'Coeficiente de variação de {cv_pct:.1f}% (> 25%): amostra heterogênea. '
                    'A mediana é indicada quando a dispersão é alta.'
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
                'desvio_padrao':  round(desvio, 2),
                'cv_pct':         round(cv_pct, 1),
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
            r['outliers'] > 0 or r['variacao_pct'] > 20 or r['cv_pct'] > 25
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
        Para cada item do mapa, busca contratações anteriores do MESMO item
        (por código SIMPAS ou similaridade de descrição) em DFDs aprovados.

        Retorna resultados agrupados por item do mapa, permitindo ao pesquisador
        avaliar o histórico de preços efetivamente praticados para aquele item.
        """
        from modulo_demanda.models import DFD, ItemDFD
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q

        mapa = self.get_object()
        dois_anos_atras = (timezone.now() - timedelta(days=730)).date()

        # Base: DFDs aprovados (mesmo órgão + filhos), excluindo o próprio DFD do mapa
        child_ids = list(
            __import__('core.models', fromlist=['Orgao'])
            .__dict__['Orgao']
            .objects.filter(parent_id=request.org_id)
            .values_list('id', flat=True)
        ) if False else []
        try:
            from core.models import Orgao
            child_ids = list(Orgao.objects.filter(parent_id=request.org_id).values_list('id', flat=True))
        except Exception:
            child_ids = []

        base_qs = ItemDFD.objects.filter(
            dfd__status='Aprovada',
            dfd__org_id__in=[request.org_id] + child_ids,
            dfd__created_at__date__gte=dois_anos_atras,
        ).select_related('dfd', 'item_catalogo')
        if mapa.dfd_id:
            base_qs = base_qs.exclude(dfd_id=mapa.dfd_id)

        itens_mapa = mapa.itens.all()
        grupos = []

        for item_mapa in itens_mapa:
            matches_simpas = []
            matches_familia = []
            matches_desc    = []

            # Extrair família do código SIMPAS do item do mapa (ex: "65.10.19..." → "65.10")
            familia_item = ''
            if item_mapa.codigo_simpas:
                partes = item_mapa.codigo_simpas.split('.')
                if len(partes) >= 2:
                    familia_item = f'{partes[0]}.{partes[1]}'

            # Nível 1: match SIMPAS exato (mesmo item)
            if item_mapa.codigo_simpas:
                matches_simpas = list(base_qs.filter(
                    item_catalogo__codigo_simpas=item_mapa.codigo_simpas
                )[:15])

            # Nível 2: match por família SIMPAS — NUNCA cruza famílias diferentes
            # Ex: 65.10 (TI) só compara com outros 65.10, jamais com 38.20 (Segurança)
            if not matches_simpas and familia_item:
                matches_familia = list(base_qs.filter(
                    item_catalogo__codigo_simpas__startswith=familia_item
                ).exclude(
                    item_catalogo__codigo_simpas=item_mapa.codigo_simpas or ''
                )[:15])

            # Nível 3: fallback por palavras-chave da descrição, RESTRITO à mesma família
            # Só ativa quando não há código SIMPAS configurado no item do mapa
            if not matches_simpas and not matches_familia and not item_mapa.codigo_simpas:
                palavras = [
                    p for p in item_mapa.descricao.split()
                    if len(p) > 4 and p.lower() not in ('para', 'com', 'por', 'dos', 'das', 'uma', 'tipo', 'modelo')
                ][:3]
                if palavras:
                    q = Q()
                    for p in palavras:
                        q |= Q(objeto__icontains=p)
                    matches_desc = list(base_qs.filter(q)[:10])

            historico = []
            match_por = 'simpas' if matches_simpas else ('familia' if matches_familia else ('descricao' if matches_desc else 'sem_match'))
            for it in (matches_simpas or matches_familia or matches_desc):
                # Verificar se há contrato resultante deste DFD
                contrato_info = None
                contratos = it.dfd.contratos.filter(status='Vigente').first()
                if contratos:
                    contrato_info = f'{contratos.numero} (vigente até {contratos.data_vigencia_fim})'

                historico.append({
                    'item_dfd_id':        it.pk,
                    'dfd_id':             it.dfd.pk,
                    'dfd_numero_sei':     it.dfd.numero_sei,
                    'dfd_data':           it.dfd.created_at.strftime('%d/%m/%Y'),
                    'item_descricao':     it.objeto,
                    'valor_unitario':     float(it.valor_unitario_estimado),
                    'unidade_medida':     it.unidade_medida,
                    'quantidade':         float(it.quantidade),
                    'contrato':           contrato_info,
                    'match_simpas':       bool(matches_simpas),
                    'origem_label':       f'Histórico Weber-e — DFD {it.dfd.numero_sei}',
                })

            grupos.append({
                'item_mapa_id':    item_mapa.pk,
                'item_descricao':  item_mapa.descricao,
                'codigo_simpas':   item_mapa.codigo_simpas,
                'unidade_medida':  item_mapa.unidade_medida,
                'match_por':       match_por,
                'familia_simpas':  familia_item or None,
                'total':           len(historico),
                'historico':       historico,
            })

        total_geral = sum(g['total'] for g in grupos)
        return Response({
            'total': total_geral,
            'grupos': grupos,
            'nota': (
                'Histórico agrupado por item do mapa. '
                'Itens com código SIMPAS têm match exato; demais por similaridade de descrição. '
                'Use os valores como referência complementar (Parâmetro II interno).'
            ),
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

    @action(detail=True, methods=['get'], url_path='export/historico')
    def export_historico(self, request, pk=None):
        from exportacao.pdf_utils import gerar_pdf_historico, resposta_pdf
        mapa = self.get_object()
        pdf = gerar_pdf_historico(
            titulo='Mapa Comparativo de Preços',
            numero_ref=str(mapa.pk),
            historico_entries=mapa.historico.select_related('usuario').order_by('-criado_em'),
            org_nome=mapa.org_id.nome if mapa.org_id else '',
            org_sigla=mapa.org_id.sigla if mapa.org_id else None,
            criado_por=mapa.created_by,
            created_at=mapa.created_at,
        )
        return resposta_pdf(pdf, f'Historico_Mapa_{mapa.pk}.pdf')

    # ── Integração PNCP ───────────────────────────────────────────────────────
    # Toda pesquisa parte de um item do mapa: a descrição dele é a palavra-chave
    # padrão, a referência da nota de similaridade e o destino dos preços.
    @action(detail=True, methods=['post'], url_path='pncp/preview')
    def pncp_preview(self, request, pk=None):
        """
        Consulta o PNCP e retorna as contratações mais parecidas com o item do mapa.
        Body: {
            item_mapa_id (obrigatório), periodo_inicio, periodo_fim,
            uf (obrigatória sem CNPJ), cnpj_orgao_referencia (opt),
            termo_busca (opt — padrão: descrição do item), modalidades (opt, [6]),
            incluir_contratos (bool — contratações), incluir_atas (bool — só com CNPJ)
        }
        """
        from modulo_pncp.services import buscar_preview, MODALIDADES_PNCP
        from modulo_pncp.models import PNCPImportacao, PNCPRegistro
        from datetime import date, timedelta

        mapa = self.get_object()
        item = get_object_or_404(ItemMapa, pk=request.data.get('item_mapa_id'), mapa=mapa)

        def _d(s):
            try:
                return date.fromisoformat(str(s))
            except (TypeError, ValueError):
                return None

        d_ini = _d(request.data.get('periodo_inicio'))
        d_fim = _d(request.data.get('periodo_fim'))
        if not d_ini or not d_fim:
            return Response({'detail': 'Informe o período (AAAA-MM-DD).'}, status=status.HTTP_400_BAD_REQUEST)
        if d_fim < d_ini:
            return Response({'detail': 'O fim do período deve ser posterior ao início.'}, status=status.HTTP_400_BAD_REQUEST)
        MAX_DIAS = 180
        if (d_fim - d_ini).days > MAX_DIAS:
            return Response({'detail': f'Período máximo: {MAX_DIAS} dias.'}, status=status.HTTP_400_BAD_REQUEST)

        cnpj = ''.join(c for c in str(request.data.get('cnpj_orgao_referencia', '')) if c.isdigit())
        if cnpj and len(cnpj) != 14:
            return Response({'detail': 'CNPJ deve ter 14 dígitos.'}, status=status.HTTP_400_BAD_REQUEST)
        uf = str(request.data.get('uf', '')).strip().upper()[:2]
        if not cnpj and not uf:
            return Response({'detail': 'Sem CNPJ, informe a UF — é o filtro que o PNCP aplica no servidor.'},
                            status=status.HTTP_400_BAD_REQUEST)
        termo = (str(request.data.get('termo_busca') or '').strip() or item.descricao)[:200]
        try:
            modalidades = [int(m) for m in (request.data.get('modalidades') or [6]) if int(m) in MODALIDADES_PNCP]
        except (TypeError, ValueError):
            modalidades = []
        if not modalidades:
            modalidades = [6]
        incluir_contratos = bool(request.data.get('incluir_contratos', True))
        incluir_atas      = bool(request.data.get('incluir_atas', True))

        resultado = buscar_preview(
            d_ini, d_fim, cnpj=cnpj, uf=uf, termo=termo,
            incluir_contratos=incluir_contratos, incluir_atas=incluir_atas,
            modalidades=modalidades,
        )

        importacao = PNCPImportacao.objects.create(
            org_id_id  = request.org_id,
            created_by = request.user,
            updated_by = request.user,
            mapa       = mapa,
            cnpj_orgao_referencia = cnpj,
            uf             = uf,
            termo_busca    = termo,
            periodo_inicio = d_ini,
            periodo_fim    = d_fim,
            tipo_fonte     = 'II',
            status         = 'pendente',
            total_consultados = resultado['total'],
        )

        registros_criados = []
        for reg in resultado['registros']:
            r = PNCPRegistro.objects.create(
                importacao    = importacao,
                numero_pncp   = (reg['numero_pncp'] or '')[:150],
                objeto        = reg['objeto'] or '',
                valor_global  = reg['valor_global'],
                valor_unitario= reg['valor_unitario'],
                quantidade    = reg['quantidade'],
                unidade_medida= reg['unidade_medida'] or '',
                orgao_nome    = (reg['orgao_nome'] or '')[:255],
                orgao_cnpj    = (reg['orgao_cnpj'] or '')[:18],
                uf            = reg['uf'] or '',
                data_referencia= reg['data_referencia'],
                numero_certame = (reg['numero_certame'] or '')[:100],
                modalidade    = (reg['modalidade'] or '')[:100],
                tipo_registro = reg['tipo_registro'],
            )
            registros_criados.append({
                'id':            r.pk,
                'numero_pncp':   r.numero_pncp,
                'objeto':        r.objeto,
                'valor_global':  str(r.valor_global) if r.valor_global else None,
                'orgao_nome':    r.orgao_nome,
                'orgao_cnpj':    r.orgao_cnpj,
                'uf':            r.uf,
                'data_referencia': str(r.data_referencia) if r.data_referencia else None,
                'modalidade':    r.modalidade,
                'tipo_registro': r.tipo_registro,
                'similaridade':  reg.get('similaridade'),
            })

        return Response({
            'importacao_id': importacao.pk,
            'termo_usado':   termo,
            'total':         resultado['total'],
            'registros':     registros_criados,
            'erros_api':     resultado['erros'],
            'varredura':     resultado.get('varredura', []),
        })

    @action(detail=True, methods=['post'], url_path='pncp/itens')
    def pncp_itens(self, request, pk=None):
        """
        Abre uma contratação encontrada e lista os itens com valor unitário homologado,
        ordenados pela similaridade com o item do mapa.
        Body: { importacao_id, registro_id, item_mapa_id }
        """
        from modulo_pncp.models import PNCPImportacao, PNCPRegistro
        from modulo_pncp.services import itens_homologados
        from modulo_pncp.similaridade import ranquear

        mapa = self.get_object()
        item = get_object_or_404(ItemMapa, pk=request.data.get('item_mapa_id'), mapa=mapa)
        importacao = get_object_or_404(PNCPImportacao, pk=request.data.get('importacao_id'), mapa=mapa)
        pai = get_object_or_404(PNCPRegistro, pk=request.data.get('registro_id'), importacao=importacao,
                                tipo_registro='contratacao')
        try:
            linhas = itens_homologados(pai.numero_pncp)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': f'O PNCP não respondeu ({getattr(e, "reason", e)}). Tente novamente.'},
                            status=status.HTTP_502_BAD_GATEWAY)
        linhas = ranquear(linhas, item.descricao, 'descricao')
        un_item = (item.unidade_medida or '').strip().upper()

        saida = []
        for ln in linhas:
            numero = f'{pai.numero_pncp}#{ln["numero_item"]}#{ln["fornecedor_ni"]}'[:150]
            reg, _ = PNCPRegistro.objects.update_or_create(
                importacao=importacao, numero_pncp=numero,
                defaults={
                    'objeto': ln['descricao'],
                    'valor_unitario': ln['valor_unitario'],
                    'quantidade': ln['quantidade'],
                    'unidade_medida': ln['unidade_medida'],
                    'orgao_nome': pai.orgao_nome,
                    'orgao_cnpj': pai.orgao_cnpj,
                    'uf': pai.uf,
                    'data_referencia': ln['data_referencia'] or pai.data_referencia,
                    'numero_certame': f'{pai.numero_pncp} item {ln["numero_item"]}'[:100],
                    'modalidade': pai.modalidade,
                    'tipo_registro': 'item',
                },
            )
            unidade = (ln['unidade_medida'] or '').strip().upper()
            saida.append({
                'id': reg.pk,
                'numero_item': ln['numero_item'],
                'descricao': ln['descricao'],
                'unidade_medida': ln['unidade_medida'],
                'unidade_diverge': bool(un_item and unidade and unidade[:2] != un_item[:2]),
                'quantidade': str(ln['quantidade'] or ''),
                'valor_unitario': str(ln['valor_unitario']),
                'fornecedor': ln['fornecedor'],
                'similaridade': ln['similaridade'],
                'importado': reg.importado,
            })
        return Response({'registro_id': pai.pk, 'itens': saida})

    @action(detail=True, methods=['post'], url_path='pncp/confirmar')
    def pncp_confirmar(self, request, pk=None):
        """
        Efetiva a importação dos itens homologados selecionados para o item do mapa.
        Body: { importacao_id: N, ids: [1, 2, 3], item_mapa_id: N (obrigatório) }
        """
        from modulo_pncp.services import ImportadorPNCP
        from modulo_pncp.models import PNCPImportacao

        mapa = self.get_object()
        if mapa.status not in ('Rascunho', 'Devolvido'):
            return Response({'detail': 'Só é possível importar preços com o mapa em Rascunho ou Devolvido.'},
                            status=status.HTTP_400_BAD_REQUEST)
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids:
            return Response({'detail': 'Selecione ao menos um item homologado.'}, status=400)
        importacao = get_object_or_404(PNCPImportacao, pk=request.data.get('importacao_id'), mapa=mapa)
        item = get_object_or_404(ItemMapa, pk=request.data.get('item_mapa_id'), mapa=mapa)
        importacao._item_override = item

        resultado = ImportadorPNCP().executar(importacao, ids)
        item.calcular(metodo=mapa.metodo_calculo)
        mapa.recalcular_total()
        return Response(resultado)

    # ── Integração Compras.gov.br — preços unitários por CATMAT/CATSER ────────
    # Só o código de catálogo, o período e a UF saem do sistema (ver modulo_pncp.comprasgov).
    @action(detail=True, methods=['get'], url_path='comprasgov/catalogo')
    def comprasgov_catalogo(self, request, pk=None):
        from modulo_pncp.comprasgov import consultar_catalogo, ErroComprasGov
        self.get_object()
        try:
            item = consultar_catalogo(request.query_params.get('tipo'), request.query_params.get('codigo'))
        except ErroComprasGov as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        if not item:
            return Response({'detail': 'Código não encontrado no catálogo do Compras.gov.br.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(item)

    @action(detail=True, methods=['post'], url_path='comprasgov/precos')
    def comprasgov_precos(self, request, pk=None):
        """
        Body: { item_mapa_id, tipo: material|servico, codigo, uf (opt), meses (opt) }
        Retorna os preços homologados do item no período de validade do Parâmetro II,
        já classificados pela faixa de ±30% da mediana. Nada é gravado.
        """
        from modulo_pncp.comprasgov import consultar_precos, classificar, ErroComprasGov
        mapa = self.get_object()
        item = get_object_or_404(ItemMapa, pk=request.data.get('item_mapa_id'), mapa=mapa)
        try:
            resultado = consultar_precos(
                request.data.get('tipo'), request.data.get('codigo'),
                uf=request.data.get('uf', ''), meses=request.data.get('meses'),
            )
        except (ErroComprasGov, ValueError, TypeError) as e:
            msg = str(e) if isinstance(e, ErroComprasGov) else 'Parâmetros inválidos.'
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        ja_importados = set(
            item.precos.filter(observacao__startswith='[Compras.gov.br]')
            .values_list('numero_certame', flat=True)
        )
        from modulo_pncp.similaridade import ranquear
        resultado['estatistica'] = classificar(resultado['registros'], item.unidade_medida)
        resultado['registros'] = ranquear(resultado['registros'], item.descricao, 'descricao')
        for r in resultado['registros']:
            r['ja_importado'] = r['id'] in ja_importados
        return Response(resultado)

    @action(detail=True, methods=['post'], url_path='comprasgov/importar')
    def comprasgov_importar(self, request, pk=None):
        """
        Body: { item_mapa_id, tipo, codigo, uf (opt), meses (opt), ids: [idCompraItem, ...] }
        Os valores NÃO vêm do navegador: a consulta é refeita no servidor (cache de 15 min)
        e só os ids selecionados que constam do retorno oficial são gravados.
        """
        from datetime import date
        from django.db import transaction
        from modulo_pncp.comprasgov import consultar_precos, classificar, valor_2_casas, ErroComprasGov

        mapa = self.get_object()
        if mapa.status not in ('Rascunho', 'Devolvido'):
            return Response({'detail': 'Só é possível importar preços com o mapa em Rascunho ou Devolvido.'},
                            status=status.HTTP_400_BAD_REQUEST)
        item = get_object_or_404(ItemMapa, pk=request.data.get('item_mapa_id'), mapa=mapa)
        ids = request.data.get('ids') or []
        if not isinstance(ids, list) or not ids or len(ids) > 200:
            return Response({'detail': 'Selecione de 1 a 200 registros.'}, status=status.HTTP_400_BAD_REQUEST)
        ids = {str(i) for i in ids}
        try:
            resultado = consultar_precos(
                request.data.get('tipo'), request.data.get('codigo'),
                uf=request.data.get('uf', ''), meses=request.data.get('meses'),
            )
        except (ErroComprasGov, ValueError, TypeError) as e:
            msg = str(e) if isinstance(e, ErroComprasGov) else 'Parâmetros inválidos.'
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

        classificar(resultado['registros'], item.unidade_medida)
        selecionados = [r for r in resultado['registros'] if r['id'] in ids]
        if not selecionados:
            return Response({'detail': 'Nenhum dos registros selecionados consta da consulta oficial. Refaça a busca.'},
                            status=status.HTTP_400_BAD_REQUEST)

        rotulo = 'CATMAT' if resultado['tipo'] == 'material' else 'CATSER'
        hoje = date.today()
        ja_importados = set(
            item.precos.filter(observacao__startswith='[Compras.gov.br]')
            .values_list('numero_certame', flat=True)
        )
        criados, ignorados = 0, []
        with transaction.atomic():
            fonte, _ = FonteConsultada.objects.get_or_create(
                mapa=mapa, tipo='II',
                referencia=f'Compras.gov.br — {rotulo} {resultado["codigo"]} — consulta {hoje:%d/%m/%Y}',
                defaults={
                    'descricao': 'Compras.gov.br — Pesquisa de Preço (Dados Abertos, preços homologados)',
                    'data_consulta': hoje,
                },
            )
            for r in selecionados:
                if r['id'] in ja_importados:
                    ignorados.append(f'{r["id"]}: já importado neste item')
                    continue
                valor = valor_2_casas(r['preco_unitario'])
                if valor <= 0:
                    ignorados.append(f'{r["id"]}: valor abaixo de R$ 0,01')
                    continue
                origem = (
                    f'item {r["numero_item"]} da {r["forma"]} (PNCP {r["ata_pncp"]})'
                    if r['origem'] == 'ata' else f'item da compra {r["numero_item"]}'
                )
                observacao = (
                    f'[Compras.gov.br] {rotulo} {resultado["codigo"]} · {origem} · '
                    f'preço homologado R$ {r["preco_unitario"]} por {r["unidade"] or "—"} · '
                    f'qtd {r["quantidade"] or "—"} · fornecedor {r["fornecedor"] or "—"}'
                    f'{" (" + r["fornecedor_ni"] + ")" if r["fornecedor_ni"] else ""}'
                    f'{" · marca " + r["marca"] if r["marca"] else ""} · forma {r["forma"] or "—"}.'
                )
                if r['unidade_diverge']:
                    observacao += f' ATENÇÃO: unidade de origem ({r["unidade"]}) difere da do item ({item.unidade_medida}).'
                PrecoColetado.objects.create(
                    item=item, fonte=fonte, valor_unitario=valor,
                    origem_orgao_empresa=(
                        f'{r["orgao"] or r["uasg_nome"]} — UASG {r["uasg"]} '
                        f'({r["municipio"]}/{r["uf"]})'
                    )[:255],
                    numero_certame=r['id'][:100],
                    data_referencia=date.fromisoformat(r['data_referencia']) if r['data_referencia'] else hoje,
                    observacao=observacao,
                )
                ja_importados.add(r['id'])
                criados += 1
            item.calcular(metodo=mapa.metodo_calculo)
            mapa.recalcular_total()

        return Response({
            'importados': criados,
            'ignorados': ignorados,
            'detail': f'{criados} preço(s) importado(s) do Compras.gov.br para o item "{item.descricao[:60]}".',
        })

    # ── CRUD de Solicitações de Cotação (Parâmetro V) ──────────────────────────
    @action(detail=True, methods=['get', 'post'], url_path='solicitacoes-cotacao')
    def solicitacoes_cotacao(self, request, pk=None):
        mapa = self.get_object()
        ctx = {'request': request}
        if request.method == 'POST':
            serializer = SolicitacaoCotacaoSerializer(data=request.data, context=ctx)
            serializer.is_valid(raise_exception=True)
            serializer.save(mapa=mapa)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        qs = mapa.solicitacoes_cotacao.select_related('fonte').order_by('-criado_em')
        return Response(SolicitacaoCotacaoSerializer(qs, many=True, context=ctx).data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='solicitacoes-cotacao/(?P<sol_pk>[^/.]+)')
    def solicitacao_cotacao_detail(self, request, pk=None, sol_pk=None):
        mapa = self.get_object()
        sol  = get_object_or_404(SolicitacaoCotacao, pk=sol_pk, mapa=mapa)
        ctx  = {'request': request}
        if request.method == 'DELETE':
            sol.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = SolicitacaoCotacaoSerializer(sol, data=request.data, partial=True, context=ctx)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # ── Respostas individuais de cada fornecedor ao disparo ────────────────────
    @action(detail=True, methods=['get', 'post'],
            url_path='solicitacoes-cotacao/(?P<sol_pk>[^/.]+)/respostas')
    def respostas_cotacao(self, request, pk=None, sol_pk=None):
        mapa = self.get_object()
        sol  = get_object_or_404(SolicitacaoCotacao, pk=sol_pk, mapa=mapa)
        ctx  = {'request': request}
        if request.method == 'POST':
            serializer = RespostaCotacaoSerializer(data=request.data, context=ctx)
            serializer.is_valid(raise_exception=True)
            resposta = serializer.save(solicitacao=sol)
            if resposta.escolhida:
                sol.respostas.exclude(pk=resposta.pk).update(escolhida=False)
            return Response(RespostaCotacaoSerializer(resposta, context=ctx).data, status=status.HTTP_201_CREATED)
        qs = sol.respostas.select_related('fornecedor').order_by('-data_resposta')
        return Response(RespostaCotacaoSerializer(qs, many=True, context=ctx).data)

    @action(detail=True, methods=['patch', 'delete'],
            url_path='solicitacoes-cotacao/(?P<sol_pk>[^/.]+)/respostas/(?P<resp_pk>[^/.]+)')
    def resposta_cotacao_detail(self, request, pk=None, sol_pk=None, resp_pk=None):
        mapa = self.get_object()
        sol  = get_object_or_404(SolicitacaoCotacao, pk=sol_pk, mapa=mapa)
        resp = get_object_or_404(RespostaCotacao, pk=resp_pk, solicitacao=sol)
        ctx  = {'request': request}
        if request.method == 'DELETE':
            resp.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = RespostaCotacaoSerializer(resp, data=request.data, partial=True, context=ctx)
        serializer.is_valid(raise_exception=True)
        resposta = serializer.save()
        if resposta.escolhida:
            sol.respostas.exclude(pk=resposta.pk).update(escolhida=False)
        return Response(serializer.data)
