from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Fornecedor
from .validators import validar_documento


class FornecedorSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Fornecedor
        fields = [
            'id', 'tipo_pessoa', 'documento', 'nome_razao_social', 'nome_fantasia',
            'porte_empresa', 'email', 'telefone', 'municipio', 'uf', 'ativo', 'observacoes',
            'created_by', 'created_by_username', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        tipo_pessoa = attrs.get('tipo_pessoa', getattr(self.instance, 'tipo_pessoa', None))
        documento = attrs.get('documento', getattr(self.instance, 'documento', None))
        try:
            attrs['documento'] = validar_documento(documento, tipo_pessoa)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'documento': e.messages})
        return attrs

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FornecedorResumoSerializer(serializers.ModelSerializer):
    """Serializer enxuto para uso em pickers/autocomplete e listas aninhadas."""

    class Meta:
        model = Fornecedor
        fields = ['id', 'tipo_pessoa', 'documento', 'nome_razao_social', 'nome_fantasia', 'ativo']
        read_only_fields = fields
