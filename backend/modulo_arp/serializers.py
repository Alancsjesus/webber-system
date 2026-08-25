from decimal import Decimal

from rest_framework import serializers

from .models import Ata, ItemAta, HistoricoAta


class ItemAtaSerializer(serializers.ModelSerializer):
    saldo_disponivel = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    catalogo_codigo_interno = serializers.CharField(source='item_catalogo.codigo_interno', read_only=True)
    catalogo_codigo_simpas = serializers.CharField(source='item_catalogo.codigo_simpas', read_only=True)
    catalogo_nome = serializers.CharField(source='item_catalogo.nome', read_only=True)
    fornecedor_nome = serializers.CharField(source='fornecedor.nome_razao_social', read_only=True)

    class Meta:
        model = ItemAta
        fields = [
            'id', 'ata', 'item_catalogo', 'catalogo_codigo_interno', 'catalogo_codigo_simpas',
            'catalogo_nome', 'objeto', 'unidade_medida', 'fornecedor', 'fornecedor_nome',
            'quantidade_registrada', 'valor_unitario_registrado', 'quantidade_consumida',
            'saldo_disponivel', 'observacoes',
        ]
        read_only_fields = ['id', 'ata', 'quantidade_consumida']


class HistoricoAtaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoAta
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class AtaSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    tipo_origem_display = serializers.CharField(source='get_tipo_origem_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    procedimento_numero = serializers.CharField(source='procedimento.numero', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    itens = ItemAtaSerializer(many=True, read_only=True)
    historico = HistoricoAtaSerializer(many=True, read_only=True)
    saldo_total = serializers.SerializerMethodField()

    class Meta:
        model = Ata
        fields = [
            'id', 'tipo_origem', 'tipo_origem_display', 'numero_ata', 'procedimento', 'procedimento_numero',
            'numero_pncp', 'orgao_gerenciador_nome', 'orgao_gerenciador_cnpj', 'orgao_gerenciador_uf',
            'objeto', 'status', 'status_display',
            'data_assinatura', 'data_vigencia_inicio', 'data_vigencia_fim', 'observacoes',
            'itens', 'historico', 'saldo_total',
            'org_id', 'org_nome', 'created_by', 'created_by_username', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'org_id', 'created_by', 'created_at', 'updated_at']

    def get_saldo_total(self, obj):
        return sum((item.saldo_disponivel for item in obj.itens.all()), Decimal('0'))

    def validate(self, attrs):
        tipo_origem = attrs.get('tipo_origem', getattr(self.instance, 'tipo_origem', None))
        if tipo_origem == 'propria' and not attrs.get('procedimento', getattr(self.instance, 'procedimento', None)):
            pass  # procedimento é recomendado mas não obrigatório (ata própria pode nascer antes do vínculo)
        if tipo_origem == 'carona':
            campos_obrigatorios = ['numero_pncp', 'orgao_gerenciador_nome']
            faltando = [c for c in campos_obrigatorios if not (attrs.get(c) or getattr(self.instance, c, ''))]
            if faltando:
                raise serializers.ValidationError({
                    c: 'Obrigatório para ata de carona.' for c in faltando
                })
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class AtaResumoSerializer(serializers.ModelSerializer):
    """Serializer enxuto para pickers/listas aninhadas."""

    class Meta:
        model = Ata
        fields = ['id', 'numero_ata', 'tipo_origem', 'status', 'objeto']
        read_only_fields = fields
