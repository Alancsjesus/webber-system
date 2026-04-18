from rest_framework import serializers
from modulo_planejamento.models import NecessidadePlanejamento
from .models import AcaoOrcamentaria, ElementoDespesa, FonteRecurso, DotacaoOrcamentaria


class AcaoOrcamentariaSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = AcaoOrcamentaria
        fields = [
            'id', 'codigo', 'nome', 'tipo', 'descricao', 'ativa',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'org_id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ElementoDespesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElementoDespesa
        fields = ['id', 'codigo', 'descricao', 'ativo']
        read_only_fields = ['id', 'codigo', 'descricao', 'ativo']


class FonteRecursoSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = FonteRecurso
        fields = [
            'id', 'codigo', 'nome', 'tipo', 'exercicio_anterior',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'org_id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class NecessidadeResumoSerializer(serializers.ModelSerializer):
    """Resumo de NecessidadePlanejamento para exibição em dotações."""
    class Meta:
        model = NecessidadePlanejamento
        fields = ['id', 'titulo', 'status', 'prioridade', 'valor_estimado', 'exercicio_fiscal']
        read_only_fields = fields


class DotacaoOrcamentariaSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    acao_codigo = serializers.CharField(source='acao.codigo', read_only=True)
    acao_nome = serializers.CharField(source='acao.nome', read_only=True)
    acao_tipo = serializers.CharField(source='acao.tipo', read_only=True)

    elemento_codigo = serializers.IntegerField(source='elemento_despesa.codigo', read_only=True)
    elemento_descricao = serializers.CharField(source='elemento_despesa.descricao', read_only=True)

    fonte_codigo = serializers.IntegerField(source='fonte_recurso.codigo', read_only=True)
    fonte_nome = serializers.CharField(source='fonte_recurso.nome', read_only=True)
    fonte_tipo = serializers.CharField(source='fonte_recurso.tipo', read_only=True)

    necessidades_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=NecessidadePlanejamento.objects.all(),
        source='necessidades',
        required=False,
    )
    necessidades_detail = NecessidadeResumoSerializer(
        many=True, read_only=True, source='necessidades'
    )

    class Meta:
        model = DotacaoOrcamentaria
        fields = [
            'id',
            'exercicio_fiscal',
            'acao', 'acao_codigo', 'acao_nome', 'acao_tipo',
            'elemento_despesa', 'elemento_codigo', 'elemento_descricao',
            'fonte_recurso', 'fonte_codigo', 'fonte_nome', 'fonte_tipo',
            'valor_dotado',
            'status',
            'eixo',
            'objetivo_estrategico',
            'observacoes',
            'necessidades_ids',
            'necessidades_detail',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'org_id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        ]

    def validate(self, attrs):
        request = self.context['request']
        org_id = request.org_id

        # Validate acao belongs to same org
        acao = attrs.get('acao')
        if acao and str(acao.org_id_id) != str(org_id):
            raise serializers.ValidationError({'acao': 'Ação não pertence à organização.'})

        # Validate fonte_recurso belongs to same org
        fonte = attrs.get('fonte_recurso')
        if fonte and str(fonte.org_id_id) != str(org_id):
            raise serializers.ValidationError({'fonte_recurso': 'Fonte de recurso não pertence à organização.'})

        # Validate all linked necessidades belong to same org
        necessidades = attrs.get('necessidades', [])
        for nec in necessidades:
            if str(nec.org_id_id) != str(org_id):
                raise serializers.ValidationError(
                    {'necessidades_ids': f'Necessidade "{nec.titulo}" não pertence à organização.'}
                )

        return attrs

    def create(self, validated_data):
        necessidades = validated_data.pop('necessidades', [])
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        instance = super().create(validated_data)
        instance.necessidades.set(necessidades)
        return instance

    def update(self, instance, validated_data):
        necessidades = validated_data.pop('necessidades', None)
        validated_data['updated_by'] = self.context['request'].user
        instance = super().update(instance, validated_data)
        if necessidades is not None:
            instance.necessidades.set(necessidades)
        return instance


class VincularNecessidadeSerializer(serializers.Serializer):
    necessidade_id = serializers.IntegerField()
