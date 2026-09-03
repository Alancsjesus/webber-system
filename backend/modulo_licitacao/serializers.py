from decimal import Decimal
from datetime import date, timedelta
from rest_framework import serializers
from .models import (
    Procedimento, HistoricoProcedimento, TramitacaoExterna, ResultadoLote,
    PRAZO_LEGAL_DIAS_UTEIS, TETO_DISPENSA_BENS_SERVICOS, TETO_DISPENSA_OBRAS,
)


class HistoricoProcedimentoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model  = HistoricoProcedimento
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class TramitacaoExternaSerializer(serializers.ModelSerializer):
    status        = serializers.CharField(read_only=True)
    orgao_label   = serializers.CharField(read_only=True)
    registrado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model  = TramitacaoExterna
        fields = [
            'id', 'orgao_externo', 'orgao_descricao', 'orgao_label',
            'tipo', 'numero_sei',
            'data_envio', 'prazo_esperado', 'data_retorno',
            'status', 'observacoes',
            'registrado_por', 'registrado_por_nome', 'criado_em',
        ]
        read_only_fields = ['id', 'status', 'orgao_label', 'registrado_por_nome', 'criado_em']

    def get_registrado_por_nome(self, obj):
        if obj.registrado_por:
            return obj.registrado_por.get_full_name() or obj.registrado_por.username
        return '—'


class ResultadoLoteSerializer(serializers.ModelSerializer):
    lote_numero          = serializers.CharField(source='lote.numero',     read_only=True)
    lote_descricao       = serializers.CharField(source='lote.descricao',  read_only=True)
    percentual_desconto  = serializers.FloatField(read_only=True)
    resultado_display    = serializers.CharField(source='get_resultado_display', read_only=True)
    contrato_numero      = serializers.CharField(source='contrato_gerado.numero', read_only=True)

    class Meta:
        model  = ResultadoLote
        fields = [
            'id', 'lote', 'lote_numero', 'lote_descricao', 'descricao_lote',
            'resultado', 'resultado_display', 'fornecedor',
            'empresa_vencedora', 'cnpj_vencedor',
            'valor_estimado', 'valor_final', 'percentual_desconto',
            'contrato_gerado', 'contrato_numero',
            'observacoes', 'criado_em',
        ]
        read_only_fields = [
            'id', 'lote_numero', 'lote_descricao', 'percentual_desconto',
            'resultado_display', 'contrato_numero', 'contrato_gerado', 'criado_em',
        ]


class ProcedimentoSerializer(serializers.ModelSerializer):
    created_by_username      = serializers.CharField(source='created_by.username',          read_only=True)
    updated_by_username      = serializers.CharField(source='updated_by.username',          read_only=True)
    modalidade_display       = serializers.CharField(source='get_modalidade_display',       read_only=True)
    status_display           = serializers.CharField(source='get_status_display',           read_only=True)
    dfd_numero_sei           = serializers.CharField(source='dfd.numero_sei',               read_only=True)
    tr_numero_sei            = serializers.CharField(source='tr.numero_sei',                read_only=True)
    org_sigla                = serializers.CharField(source='org_id.sigla',                 read_only=True)
    unidade_gestora_sigla    = serializers.CharField(source='unidade_gestora.sigla', read_only=True, allow_null=True, default=None)
    unidade_gestora_nome     = serializers.CharField(source='unidade_gestora.nome',  read_only=True, allow_null=True, default=None)
    transicoes_disponiveis   = serializers.ListField(read_only=True)
    historico            = HistoricoProcedimentoSerializer(many=True, read_only=True)
    tramitacoes          = TramitacaoExternaSerializer(many=True, read_only=True)
    resultados           = ResultadoLoteSerializer(many=True, read_only=True)
    alerta_prazo         = serializers.SerializerMethodField()
    alerta_teto_dispensa = serializers.SerializerMethodField()
    dias_ate_abertura    = serializers.SerializerMethodField()
    pecas_instutorias    = serializers.SerializerMethodField()
    divergencia_valor_pncp = serializers.BooleanField(read_only=True)
    mesa_atual_label       = serializers.SerializerMethodField()

    def get_mesa_atual_label(self, obj):
        from core.mesa_atual import mesa_atual_label
        return mesa_atual_label(obj)

    class Meta:
        model  = Procedimento
        fields = [
            'id', 'numero', 'exercicio', 'modalidade', 'modalidade_display',
            'status', 'status_display', 'transicoes_disponiveis',
            'dfd', 'dfd_numero_sei', 'tr', 'tr_numero_sei',
            'objeto', 'valor_estimado',
            'fundamento_dispensa', 'fundamento_inexigibilidade', 'justificativa',
            'numero_sei',
            'numero_controle_pncp', 'valor_publicado_pncp', 'divergencia_valor_pncp',
            'data_publicacao', 'data_abertura', 'data_homologacao',
            'prazo_minimo_dias_uteis',
            'motivo_revogacao', 'observacoes',
            'org_id', 'org_sigla',
            'unidade_gestora', 'unidade_gestora_sigla', 'unidade_gestora_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'alerta_prazo', 'alerta_teto_dispensa', 'dias_ate_abertura',
            'pecas_instutorias',
            'historico', 'tramitacoes', 'resultados',
            'mesa_atual_label', 'data_mesa_atual',
        ]
        read_only_fields = [
            'id', 'numero', 'org_id', 'org_sigla',
            'unidade_gestora_sigla', 'unidade_gestora_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'prazo_minimo_dias_uteis', 'modalidade_display', 'status_display',
            'dfd_numero_sei', 'tr_numero_sei', 'transicoes_disponiveis',
            'historico', 'tramitacoes', 'resultados',
            'mesa_atual_label', 'data_mesa_atual',
        ]

    def get_alerta_prazo(self, obj):
        if not obj.data_publicacao or not obj.data_abertura:
            return None
        prazo = obj.prazo_minimo_dias_uteis
        if prazo == 0:
            return None
        # Contagem simples (dias corridos como aproximação)
        dias = (obj.data_abertura - obj.data_publicacao).days
        dias_uteis_aprox = int(dias * 5 / 7)
        if dias_uteis_aprox < prazo:
            return (
                f'Prazo insuficiente: {dias_uteis_aprox} dias úteis entre publicação e '
                f'abertura. Mínimo legal: {prazo} dias úteis (Lei 14.133, art. 55).'
            )
        return None

    def get_alerta_teto_dispensa(self, obj):
        if not obj.eh_dispensa:
            return None
        alerta, _ = obj.verificar_teto_dispensa()
        return alerta or None

    def get_dias_ate_abertura(self, obj):
        if not obj.data_abertura:
            return None
        delta = (obj.data_abertura - date.today()).days
        return delta

    def get_pecas_instutorias(self, obj):
        """Status unificado das peças instrutórias — inclui pk para ações diretas."""
        ACOES = {
            # tipo → (pode_aprovar_nos_status, pode_devolver_nos_status)
            'DFD':           (['Em Análise'],        ['Em Análise']),
            'ETP':           (['Em Análise'],        ['Em Análise']),
            'TR':            (['Em Análise'],        ['Em Análise']),
            'Mapa de Preços':(['Em Análise'],        ['Em Análise']),
        }
        pecas = []
        if obj.dfd:
            dfd = obj.dfd
            pecas.append({
                'tipo': 'DFD', 'pk': dfd.pk,
                'numero_sei': dfd.numero_sei,
                'status': dfd.status,
                'ok': dfd.status == 'Aprovada',
                'pode_aprovar': dfd.status in ACOES['DFD'][0],
                'pode_devolver': dfd.status in ACOES['DFD'][1],
                'url': f'/demanda/dfd/{dfd.pk}',
            })
            etp = getattr(dfd, 'etp', None)
            if etp:
                pecas.append({
                    'tipo': 'ETP', 'pk': etp.pk,
                    'numero_sei': etp.numero_sei,
                    'status': etp.status,
                    'ok': etp.status in ('Aprovado', 'Dispensado'),
                    'pode_aprovar': etp.status in ACOES['ETP'][0],
                    'pode_devolver': etp.status in ACOES['ETP'][1],
                    'url': f'/etp/etps/{etp.pk}',
                })
                tr = getattr(etp, 'tr', None)
                if tr:
                    pecas.append({
                        'tipo': 'TR', 'pk': tr.pk,
                        'numero_sei': tr.numero_sei,
                        'status': tr.status,
                        'ok': tr.status == 'Aprovado',
                        'pode_aprovar': tr.status in ACOES['TR'][0],
                        'pode_devolver': tr.status in ACOES['TR'][1],
                        'url': f'/analise-tecnica/trs/{tr.pk}',
                    })
                for mapa in dfd.mapas_preco.all():
                    pecas.append({
                        'tipo': 'Mapa de Preços', 'pk': mapa.pk,
                        'numero_sei': f'Mapa #{mapa.pk}',
                        'status': mapa.status,
                        'ok': mapa.status == 'Aprovado',
                        'pode_aprovar': mapa.status in ACOES['Mapa de Preços'][0],
                        'pode_devolver': mapa.status in ACOES['Mapa de Preços'][1],
                        'url': f'/pesquisa/mapa/{mapa.pk}',
                    })
        return pecas

    def validate(self, attrs):
        if self.instance is None:  # só valida na criação
            tr = attrs.get('tr')
            dfd = attrs.get('dfd')
            eh_formacao_arp = bool(tr and tr.sistema_registro_precos)
            if dfd is not None and not eh_formacao_arp:
                if not dfd.indicacoes.filter(status='Aprovada').exists():
                    raise serializers.ValidationError({
                        'dfd': 'Este DFD não possui Indicação Orçamentária aprovada (DOD) — '
                               'registre e aprove a indicação de recurso antes de abrir o '
                               'procedimento. Exceção: procedimentos vinculados a um TR de '
                               'Sistema de Registro de Preços não exigem DOD, pois a Ata ainda '
                               'não compromete orçamento — o recurso só é indicado no saque.',
                    })

            # Controle de teto de dispensa por família SIMPAS (Lei 14.133, Art. 75) —
            # bloqueia por padrão; só prossegue se o cliente confirmar explicitamente
            # (evita fracionamento de despesa "sem querer", mas não impede um caso
            # legítimo já analisado pelo usuário).
            from .models import Procedimento
            alerta, acumulado, teto, familias = Procedimento.calcular_teto_dispensa(
                org_id=self.context['request'].org_id,
                exercicio=attrs.get('exercicio'),
                modalidade=attrs.get('modalidade'),
                dfd=dfd, tr=tr, valor_estimado=attrs.get('valor_estimado'),
            )
            if alerta and 'EXCEDIDO' in alerta:
                confirmado = str(self.context['request'].data.get('confirmar_teto_excedido', '')).lower() in ('1', 'true')
                if not confirmado:
                    raise serializers.ValidationError({
                        'valor_estimado': alerta,
                        'codigo': 'teto_dispensa_excedido',
                    })
                nota = (f'[Teto de dispensa excedido — confirmado explicitamente pelo usuário. '
                        f'Acumulado no exercício para a(s) família(s) {", ".join(sorted(familias))}: '
                        f'R$ {acumulado:,.2f} + este procedimento R$ {(attrs.get("valor_estimado") or 0):,.2f} '
                        f'> teto R$ {teto:,.2f}.]')
                attrs['observacoes'] = (attrs.get('observacoes') or '').rstrip()
                attrs['observacoes'] = (attrs['observacoes'] + '\n' + nota).strip() if attrs['observacoes'] else nota
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        instance = super().create(validated_data)
        HistoricoProcedimento.objects.create(
            procedimento=instance,
            status_anterior='',
            status_novo=instance.status,
            usuario=request.user,
            motivo='Procedimento criado.',
        )
        return instance

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ProcedimentoListSerializer(serializers.ModelSerializer):
    """Versão compacta para listagem."""
    modalidade_display     = serializers.CharField(source='get_modalidade_display', read_only=True)
    status_display         = serializers.CharField(source='get_status_display',     read_only=True)
    dfd_numero_sei         = serializers.CharField(source='dfd.numero_sei',          read_only=True)
    unidade_gestora_sigla  = serializers.CharField(source='unidade_gestora.sigla', read_only=True, allow_null=True, default=None)
    tramitacoes_pendentes  = serializers.SerializerMethodField()

    class Meta:
        model  = Procedimento
        fields = [
            'id', 'numero', 'exercicio', 'modalidade', 'modalidade_display',
            'status', 'status_display',
            'dfd', 'dfd_numero_sei',
            'unidade_gestora', 'unidade_gestora_sigla',
            'objeto', 'valor_estimado',
            'data_publicacao', 'data_abertura',
            'tramitacoes_pendentes',
            'created_at', 'updated_at',
        ]

    def get_tramitacoes_pendentes(self, obj):
        return obj.tramitacoes.filter(data_retorno__isnull=True).count()
