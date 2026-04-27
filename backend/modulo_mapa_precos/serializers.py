from rest_framework import serializers
from .models import MapaComparativoPrecos, HistoricoMapa, FonteConsultada, ItemMapa, PrecoColetado


class HistoricoMapaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model  = HistoricoMapa
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class PrecoColetadoSerializer(serializers.ModelSerializer):
    fonte_tipo        = serializers.CharField(source='fonte.tipo',      read_only=True)
    fonte_descricao   = serializers.CharField(source='fonte.descricao', read_only=True)
    motivo_exclusao_display = serializers.CharField(
        source='get_motivo_exclusao_display', read_only=True
    )

    class Meta:
        model  = PrecoColetado
        fields = [
            'id', 'fonte', 'fonte_tipo', 'fonte_descricao',
            'valor_unitario',
            'origem_orgao_empresa', 'numero_certame', 'data_referencia',
            'valido', 'motivo_exclusao', 'motivo_exclusao_display',
            'sugestao_exclusao', 'justificativa_exclusao', 'observacao',
        ]
        read_only_fields = ['id', 'sugestao_exclusao']


class ItemMapaSerializer(serializers.ModelSerializer):
    precos = PrecoColetadoSerializer(many=True, read_only=True)

    class Meta:
        model  = ItemMapa
        fields = [
            'id', 'ordem', 'descricao', 'codigo_simpas',
            'unidade_medida', 'quantidade',
            'valor_unitario_calculado', 'valor_total_calculado',
            'metodo_aplicado', 'qtd_precos_validos',
            'justificativa_item', 'alerta',
            'precos',
        ]
        read_only_fields = [
            'id', 'valor_unitario_calculado', 'valor_total_calculado',
            'metodo_aplicado', 'qtd_precos_validos', 'alerta',
        ]


class FonteConsultadaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = FonteConsultada
        fields = [
            'id', 'tipo', 'tipo_display', 'descricao', 'referencia',
            'data_consulta', 'documento_sei',
            'infrutífera', 'justificativa_infrutífera',
        ]
        read_only_fields = ['id']


class MapaComparativoPrecosSerializer(serializers.ModelSerializer):
    org_nome              = serializers.CharField(source='org_id.nome',          read_only=True)
    created_by_username   = serializers.CharField(source='created_by.username',  read_only=True)
    responsavel_nome      = serializers.SerializerMethodField()
    dfd_numero_sei        = serializers.CharField(source='dfd.numero_sei',       read_only=True)
    metodo_display        = serializers.CharField(source='get_metodo_calculo_display', read_only=True)
    status_display        = serializers.CharField(source='get_status_display',   read_only=True)
    aprovador_nome        = serializers.SerializerMethodField()
    fontes                = FonteConsultadaSerializer(many=True, read_only=True)
    itens                 = ItemMapaSerializer(many=True, read_only=True)
    historico             = HistoricoMapaSerializer(many=True, read_only=True)
    qtd_itens             = serializers.IntegerField(source='itens.count',       read_only=True)
    qtd_fontes            = serializers.IntegerField(source='fontes.count',      read_only=True)

    class Meta:
        model  = MapaComparativoPrecos
        fields = [
            'id', 'objeto', 'exercicio_fiscal',
            'dfd', 'dfd_numero_sei',
            'status', 'status_display',
            'metodo_calculo', 'metodo_display',
            'valor_estimado_total',
            'responsavel', 'responsavel_nome',
            'aprovador', 'aprovador_nome', 'data_aprovacao', 'motivo_devolucao',
            'justificativa_metodologia', 'observacoes',
            'fontes', 'itens', 'historico',
            'qtd_itens', 'qtd_fontes',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'valor_estimado_total',
            'aprovador', 'data_aprovacao', 'motivo_devolucao',
            'org_id', 'created_by', 'created_at', 'updated_at',
        ]

    def get_responsavel_nome(self, obj):
        if obj.responsavel:
            return obj.responsavel.get_full_name() or obj.responsavel.username
        return None

    def get_aprovador_nome(self, obj):
        if obj.aprovador:
            return obj.aprovador.get_full_name() or obj.aprovador.username
        return None

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id']   = request.org_id
        validated_data['created_by']  = request.user
        validated_data['updated_by']  = request.user
        if not validated_data.get('responsavel'):
            validated_data['responsavel'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
