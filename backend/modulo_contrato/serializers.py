from rest_framework import serializers
from .models import Contrato, Apostila, Aditivo


class ApostilaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Apostila
        fields = ['id', 'numero', 'objeto', 'data', 'created_at']
        read_only_fields = ['id', 'numero', 'created_at']

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)


class AditivoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = Aditivo
        fields = ['id', 'numero', 'tipo', 'tipo_display', 'valor_acrescimo', 'nova_vigencia', 'objeto', 'data', 'created_at']
        read_only_fields = ['id', 'numero', 'tipo_display', 'created_at']

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)


class ContratoSerializer(serializers.ModelSerializer):
    orgao_executor_sigla   = serializers.CharField(source='orgao_executor.sigla',   read_only=True)
    orgao_executor_nome    = serializers.CharField(source='orgao_executor.nome',    read_only=True)
    dfd_numero_sei         = serializers.CharField(source='dfd.numero_sei',         read_only=True)
    fiscal_username        = serializers.CharField(source='fiscal_contrato.username', read_only=True)
    gestor_username        = serializers.CharField(source='gestor_contrato.username', read_only=True)
    ordenador_username     = serializers.CharField(source='ordenador.username',     read_only=True)
    tipo_origem_display    = serializers.CharField(source='get_tipo_origem_display', read_only=True)
    created_by_username    = serializers.CharField(source='created_by.username',    read_only=True)
    apostilas              = ApostilaSerializer(many=True, read_only=True)
    aditivos               = AditivoSerializer(many=True, read_only=True)

    class Meta:
        model  = Contrato
        fields = [
            'id', 'numero', 'exercicio',
            'orgao_executor', 'orgao_executor_sigla', 'orgao_executor_nome',
            'objeto', 'tipo_origem', 'tipo_origem_display',
            'dfd', 'dfd_numero_sei',
            'lotes', 'numero_processo_sei',
            'valor_contrato',
            'data_assinatura', 'data_vigencia_inicio', 'data_vigencia_fim',
            'status',
            'fiscal_contrato', 'fiscal_username',
            'gestor_contrato', 'gestor_username',
            'ordenador', 'ordenador_username',
            'observacoes',
            'org_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'apostilas', 'aditivos',
        ]
        read_only_fields = [
            'id', 'numero', 'org_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'orgao_executor_sigla', 'orgao_executor_nome',
            'dfd_numero_sei', 'fiscal_username', 'gestor_username', 'ordenador_username',
            'tipo_origem_display', 'apostilas', 'aditivos',
        ]

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
