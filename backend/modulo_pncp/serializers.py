from rest_framework import serializers
from .models import PNCPImportacao, PNCPRegistro


class PNCPRegistroSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PNCPRegistro
        fields = [
            'id', 'numero_pncp', 'objeto', 'valor_global', 'valor_unitario',
            'quantidade', 'unidade_medida', 'orgao_nome', 'orgao_cnpj', 'uf',
            'data_referencia', 'numero_certame', 'modalidade', 'tipo_registro',
            'importado',
        ]
        read_only_fields = fields


class PNCPImportacaoSerializer(serializers.ModelSerializer):
    registros = PNCPRegistroSerializer(many=True, read_only=True)

    class Meta:
        model  = PNCPImportacao
        fields = [
            'id', 'mapa', 'cnpj_orgao_referencia', 'uf', 'termo_busca',
            'periodo_inicio', 'periodo_fim', 'tipo_fonte',
            'status', 'total_consultados', 'total_importados',
            'erro_mensagem', 'log', 'registros', 'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'total_consultados', 'total_importados',
            'erro_mensagem', 'log', 'registros', 'created_at',
        ]
