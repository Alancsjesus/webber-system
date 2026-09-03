from rest_framework import serializers

from modulo_orcamento.models import FonteRecurso

from .models import ProcessoTramitacao, HistoricoTramitacaoProcesso


class HistoricoTramitacaoProcessoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()
    setor_anterior_display = serializers.SerializerMethodField()
    setor_novo_display = serializers.CharField(source='get_setor_novo_display', read_only=True)

    class Meta:
        model = HistoricoTramitacaoProcesso
        fields = [
            'id', 'setor_anterior', 'setor_anterior_display', 'fase_anterior',
            'setor_novo', 'setor_novo_display', 'fase_nova',
            'usuario_nome', 'motivo', 'criado_em',
        ]

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'

    def get_setor_anterior_display(self, obj):
        return dict(ProcessoTramitacao.SETOR_CHOICES).get(obj.setor_anterior, obj.setor_anterior or '—')


class ProcessoTramitacaoSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    setor_atual_display = serializers.CharField(source='get_setor_atual_display', read_only=True)
    dfd_numero_sei = serializers.CharField(source='dfd.numero_sei', read_only=True, default=None)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    fontes_recurso_nomes = serializers.SerializerMethodField()
    historico = HistoricoTramitacaoProcessoSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessoTramitacao
        fields = [
            'id', 'numero_sei', 'objeto', 'fontes_recurso', 'fontes_recurso_nomes',
            'setor_atual', 'setor_atual_display', 'fase_atual', 'data_entrada_fase',
            'dfd', 'dfd_numero_sei', 'ativo', 'observacoes', 'historico',
            'org_id', 'org_nome', 'created_by', 'created_by_username', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'org_id', 'created_by', 'created_at', 'updated_at']

    def get_fontes_recurso_nomes(self, obj):
        return [f.nome for f in obj.fontes_recurso.all()]

    def create(self, validated_data):
        request = self.context['request']
        fontes = validated_data.pop('fontes_recurso', [])
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        processo = super().create(validated_data)
        if fontes:
            processo.fontes_recurso.set(fontes)
        return processo

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ProcessoTramitacaoResumoSerializer(serializers.ModelSerializer):
    """Serializer enxuto para o painel agregado (evita serializar `historico` por linha)."""
    setor_atual_display = serializers.CharField(source='get_setor_atual_display', read_only=True)
    fontes_recurso_nomes = serializers.SerializerMethodField()

    class Meta:
        model = ProcessoTramitacao
        fields = [
            'id', 'numero_sei', 'objeto', 'fontes_recurso_nomes',
            'setor_atual', 'setor_atual_display', 'fase_atual', 'data_entrada_fase',
        ]
        read_only_fields = fields

    def get_fontes_recurso_nomes(self, obj):
        return [f.nome for f in obj.fontes_recurso.all()]
