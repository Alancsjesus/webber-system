from decimal import Decimal
from rest_framework import serializers
from .models import TR, HistoricoTR, LoteTR, ItemLoteTR


class HistoricoTRSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoTR
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_username', 'motivo', 'categoria_motivo', 'criado_em']


class ItemLoteTRSerializer(serializers.ModelSerializer):
    item_objeto         = serializers.CharField(source='item_dfd.objeto',                   read_only=True)
    item_unidade        = serializers.CharField(source='item_dfd.unidade_medida',           read_only=True)
    item_valor_est      = serializers.DecimalField(source='item_dfd.valor_unitario_estimado',
                                                   max_digits=15, decimal_places=2, read_only=True)
    catalogo_familia    = serializers.CharField(source='item_dfd.catalogo_familia',         read_only=True)
    catalogo_nome       = serializers.CharField(source='item_dfd.catalogo_nome',            read_only=True)
    preco_origem_display = serializers.CharField(source='get_preco_origem_display',         read_only=True)
    valor_unitario_efetivo = serializers.SerializerMethodField()
    valor_total          = serializers.SerializerMethodField()

    class Meta:
        model  = ItemLoteTR
        fields = ['id', 'item_dfd', 'item_objeto', 'item_unidade',
                  'item_valor_est', 'catalogo_familia', 'catalogo_nome',
                  'quantidade', 'valor_unitario_ref', 'preco_origem',
                  'preco_origem_display', 'valor_unitario_efetivo', 'valor_total']
        read_only_fields = ['id', 'item_objeto', 'item_unidade', 'item_valor_est',
                            'catalogo_familia', 'catalogo_nome', 'preco_origem_display',
                            'valor_unitario_efetivo', 'valor_total',
                            'valor_unitario_ref', 'preco_origem']

    def get_valor_unitario_efetivo(self, obj):
        return float(obj.valor_unitario_efetivo)

    def get_valor_total(self, obj):
        return float(obj.valor_total)


class LoteTRSerializer(serializers.ModelSerializer):
    itens                    = ItemLoteTRSerializer(many=True, read_only=True)
    modalidade_display       = serializers.CharField(source='get_modalidade_display', read_only=True)
    lote_origem_numero       = serializers.CharField(source='lote_origem.numero',     read_only=True)
    valor_total_lote         = serializers.SerializerMethodField()
    alerta_agrupamento       = serializers.SerializerMethodField()

    class Meta:
        model  = LoteTR
        fields = ['id', 'numero', 'descricao', 'modalidade', 'modalidade_display',
                  'percentual_cota', 'lote_origem', 'lote_origem_numero',
                  'ordem', 'justificativa_agrupamento', 'observacoes',
                  'valor_total_lote', 'alerta_agrupamento', 'itens']
        read_only_fields = ['id', 'numero', 'modalidade_display',
                            'lote_origem_numero', 'valor_total_lote',
                            'alerta_agrupamento', 'itens']

    def get_valor_total_lote(self, obj):
        return float(obj.valor_total)

    def get_alerta_agrupamento(self, obj):
        """Sinaliza se o lote tem > 1 item sem justificativa de agrupamento."""
        if obj.itens.count() > 1 and not obj.justificativa_agrupamento:
            return 'Lote com múltiplos itens requer justificativa de agrupamento (padronização, economia de escala ou interdependência).'
        return None

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)


class TRSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    etp_numero_sei              = serializers.CharField(source='etp.numero_sei',                   read_only=True)
    etp_dfd_id                  = serializers.IntegerField(source='etp.dfd.id',                    read_only=True)
    etp_status                  = serializers.CharField(source='etp.status',                       read_only=True)
    dfd_numero_sei              = serializers.CharField(source='etp.dfd.numero_sei',               read_only=True)
    etp_tipo_parcelamento       = serializers.CharField(source='etp.tipo_parcelamento',            read_only=True)
    etp_tipo_objeto             = serializers.CharField(source='etp.tipo_objeto',                  read_only=True)
    etp_reserva_cota_me_epp     = serializers.BooleanField(source='etp.reserva_cota_me_epp',      read_only=True)
    etp_licitacao_exclusiva_me  = serializers.BooleanField(source='etp.licitacao_exclusiva_me_epp', read_only=True)
    org_sigla           = serializers.CharField(source='org_id.sigla',   read_only=True)
    historico           = HistoricoTRSerializer(many=True, read_only=True)
    lotes               = LoteTRSerializer(many=True, read_only=True)
    alerta_cota_me_epp  = serializers.SerializerMethodField()
    # Optional on create — defaults to ETP's numero_sei when omitted
    numero_sei          = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model  = TR
        fields = [
            'id', 'etp', 'etp_numero_sei', 'etp_status', 'etp_dfd_id', 'dfd_numero_sei',
            'etp_tipo_parcelamento', 'etp_tipo_objeto',
            'etp_reserva_cota_me_epp', 'etp_licitacao_exclusiva_me',
            'alerta_cota_me_epp',
            'numero_sei',
            'objeto_contratacao', 'justificativa', 'requisitos_contratacao',
            'obrigacoes_contratada', 'obrigacoes_contratante',
            'criterios_selecao', 'criterios_medicao',
            'tipo_prazo_vigencia', 'prazo_meses', 'instrumento_inicio', 'prazo_observacao',
            'local_entrega', 'garantia_contrato',
            'estimativa_valor',
            'status', 'motivo_devolucao', 'observacoes',
            'org_id', 'org_sigla',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'historico',
            'lotes',
        ]
        read_only_fields = [
            'id', 'org_id', 'org_sigla',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'etp_numero_sei', 'etp_status', 'etp_dfd_id', 'dfd_numero_sei',
            'etp_tipo_parcelamento', 'etp_tipo_objeto',
            'etp_reserva_cota_me_epp', 'etp_licitacao_exclusiva_me',
            'alerta_cota_me_epp',
            'motivo_devolucao', 'historico', 'lotes',
        ]

    def get_alerta_cota_me_epp(self, obj):
        """Sinaliza quando o ETP tem valor estimado > R$80k sem reserva de cota configurada."""
        etp = obj.etp
        if (
            not etp.reserva_cota_me_epp
            and not etp.licitacao_exclusiva_me_epp
            and etp.estimativa_valor
            and etp.estimativa_valor > 80000
            and not etp.reserva_cota_justificativa
        ):
            return 'ETP com estimativa acima de R$80.000 sem reserva de cota ME/EPP e sem justificativa para não reserva.'
        return None

    def validate(self, data):
        instrumento = data.get('instrumento_inicio', getattr(self.instance, 'instrumento_inicio', ''))
        etp = data.get('etp', getattr(self.instance, 'etp', None))
        tipo_objeto = etp.tipo_objeto if etp else ''
        if instrumento and tipo_objeto:
            if instrumento == 'afm' and tipo_objeto not in ('bens',):
                raise serializers.ValidationError({
                    'instrumento_inicio': 'AFM é exclusivo para objetos do tipo "Bens".'
                })
            if instrumento == 'aps' and tipo_objeto not in ('servicos', 'servicos_engenharia'):
                raise serializers.ValidationError({
                    'instrumento_inicio': 'APS é exclusivo para "Serviços Comuns" ou "Serviços de Engenharia".'
                })
        return data

    def validate_etp(self, etp):
        if etp.status != 'Aprovado':
            raise serializers.ValidationError(
                'TR só pode ser criado para ETPs com status "Aprovado".'
            )
        if hasattr(etp, 'tr'):
            raise serializers.ValidationError('Este ETP já possui um TR associado.')
        return etp

    def create(self, validated_data):
        request = self.context['request']
        if not validated_data.get('numero_sei'):
            validated_data['numero_sei'] = validated_data['etp'].numero_sei
        validated_data['org_id_id']  = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
