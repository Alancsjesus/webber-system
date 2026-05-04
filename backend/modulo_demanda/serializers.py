from rest_framework import serializers
from .models import DFD, HistoricoTramitacao, ItemDFD, NumeroProcesso
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class HistoricoTramitacaoSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = HistoricoTramitacao
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_username', 'motivo', 'categoria_motivo', 'criado_em']


class ItemDFDSerializer(serializers.ModelSerializer):
    valor_total_estimado    = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    catalogo_codigo_interno = serializers.CharField(source='item_catalogo.codigo_interno', read_only=True)
    catalogo_codigo_simpas  = serializers.CharField(source='item_catalogo.codigo_simpas',  read_only=True)
    catalogo_familia        = serializers.CharField(source='item_catalogo.familia',         read_only=True)
    catalogo_nome           = serializers.CharField(source='item_catalogo.nome',            read_only=True)

    class Meta:
        model = ItemDFD
        fields = [
            'id', 'item_catalogo',
            'catalogo_codigo_interno', 'catalogo_codigo_simpas',
            'catalogo_familia', 'catalogo_nome',
            'objeto', 'unidade_medida', 'quantidade',
            'valor_unitario_estimado', 'valor_total_estimado', 'observacao',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'valor_total_estimado', 'created_at', 'updated_at',
            'catalogo_codigo_interno', 'catalogo_codigo_simpas',
            'catalogo_familia', 'catalogo_nome',
        ]

    def create(self, validated_data):
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class NumeroProcessoSerializer(serializers.ModelSerializer):
    etapa_display = serializers.CharField(source='get_etapa_display', read_only=True)

    class Meta:
        model = NumeroProcesso
        fields = [
            'id', 'numero', 'etapa', 'etapa_display',
            'descricao', 'data_abertura', 'created_at',
        ]
        read_only_fields = ['id', 'etapa_display', 'created_at']

    def create(self, validated_data):
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class NecessidadeResumoSerializer(serializers.Serializer):
    """Resumo da necessidade de planejamento vinculada ao DFD (read-only)."""
    id      = serializers.IntegerField(read_only=True)
    titulo  = serializers.CharField(read_only=True)
    status  = serializers.CharField(read_only=True)
    exercicio_fiscal = serializers.IntegerField(read_only=True)


class DFDSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    org_nome            = serializers.CharField(source='org_id.nome', read_only=True)
    historico           = HistoricoTramitacaoSerializer(many=True, read_only=True)
    itens               = ItemDFDSerializer(many=True, read_only=True)
    processos           = NumeroProcessoSerializer(many=True, read_only=True)
    necessidade_origem  = NecessidadeResumoSerializer(read_only=True)

    org_gestor_sigla         = serializers.CharField(source='org_gestor.sigla', read_only=True)
    org_gestor_nome          = serializers.CharField(source='org_gestor.nome',  read_only=True)
    orgao_compras_sigla      = serializers.CharField(source='orgao_compras.sigla', read_only=True)
    orgao_compras_nome       = serializers.CharField(source='orgao_compras.nome',  read_only=True)
    etp_id                   = serializers.SerializerMethodField()
    etp_dispensado           = serializers.SerializerMethodField()
    modalidade_display       = serializers.CharField(source='get_modalidade_aquisicao_display', read_only=True)
    unidade_demandante_nome  = serializers.SerializerMethodField()
    unidade_licitante_nome   = serializers.SerializerMethodField()
    unidade_contratante_nome = serializers.SerializerMethodField()

    fiscal_contrato_username = serializers.CharField(source='fiscal_contrato.username', read_only=True, default=None)
    fiscal_suplente_username = serializers.CharField(source='fiscal_suplente.username', read_only=True, default=None)
    gestor_contrato_username = serializers.CharField(source='gestor_contrato.username', read_only=True, default=None)
    gestor_suplente_username = serializers.CharField(source='gestor_suplente.username', read_only=True, default=None)

    def get_etp_id(self, obj):
        etp = getattr(obj, 'etp', None)
        return etp.pk if etp else None

    def get_etp_dispensado(self, obj):
        etp = getattr(obj, 'etp', None)
        return etp.status == 'Dispensado' if etp else False

    def get_unidade_demandante_nome(self, obj):
        return str(obj.unidade_demandante) if obj.unidade_demandante_id else None

    def get_unidade_licitante_nome(self, obj):
        return str(obj.unidade_licitante) if obj.unidade_licitante_id else None

    def get_unidade_contratante_nome(self, obj):
        return str(obj.unidade_contratante) if obj.unidade_contratante_id else None

    class Meta:
        model = DFD
        fields = [
            'id',
            'numero_sei',
            'descricao',
            'valor_estimado',
            'area_aplicacao',
            'prazo_necessidade',
            'status',
            'observacoes',
            'local_entrega',
            'motivo_devolucao',
            'modalidade_aquisicao',
            'modalidade_display',
            'justificativa_sem_planejamento',
            'necessidade_origem',
            'org_gestor',
            'org_gestor_sigla',
            'org_gestor_nome',
            'orgao_compras',
            'orgao_compras_sigla',
            'orgao_compras_nome',
            'etp_id',
            'etp_dispensado',
            'unidade_demandante',
            'unidade_demandante_nome',
            'unidade_licitante',
            'unidade_licitante_nome',
            'unidade_contratante',
            'unidade_contratante_nome',
            'org_id',
            'org_nome',
            'created_by',
            'created_by_username',
            'updated_by',
            'updated_by_username',
            'created_at',
            'updated_at',
            'historico',
            'itens',
            'processos',
            'fiscal_contrato',
            'fiscal_contrato_username',
            'fiscal_suplente',
            'fiscal_suplente_username',
            'gestor_contrato',
            'gestor_contrato_username',
            'gestor_suplente',
            'gestor_suplente_username',
        ]
        read_only_fields = [
            'id', 'org_id', 'created_by', 'updated_by',
            'created_at', 'updated_at', 'motivo_devolucao',
            'historico', 'itens', 'processos', 'necessidade_origem',
            'org_gestor', 'org_gestor_sigla', 'org_gestor_nome',
            'orgao_compras', 'orgao_compras_sigla', 'orgao_compras_nome',
            'etp_id', 'etp_dispensado', 'modalidade_display',
            'unidade_demandante',
            'unidade_demandante_nome', 'unidade_licitante_nome', 'unidade_contratante_nome',
            'fiscal_contrato_username', 'fiscal_suplente_username',
            'gestor_contrato_username', 'gestor_suplente_username',
        ]

    def validate_area_aplicacao(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("Pelo menos uma área de aplicação é obrigatória")
        valid_areas = [choice[0] for choice in DFD.AREA_CHOICES]
        for area in value:
            if area not in valid_areas:
                raise serializers.ValidationError(f"Área inválida: {area}")
        return value

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id']  = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        if getattr(request, 'unidade_id', None) and 'unidade_demandante_id' not in validated_data:
            validated_data['unidade_demandante_id'] = request.unidade_id
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
