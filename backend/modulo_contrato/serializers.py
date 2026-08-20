from decimal import Decimal
from rest_framework import serializers
from .models import Contrato, Apostila, Aditivo, CronogramaEntrega, Medicao, Pagamento


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


class CronogramaEntregaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_atrasado    = serializers.BooleanField(read_only=True)

    class Meta:
        model  = CronogramaEntrega
        fields = [
            'id', 'numero', 'descricao', 'quantidade', 'unidade_medida',
            'data_prevista', 'data_realizada', 'status', 'status_display',
            'is_atrasado', 'observacoes', 'created_at',
        ]
        read_only_fields = ['id', 'numero', 'status_display', 'is_atrasado', 'created_at']

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class PagamentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    medicao_numero = serializers.CharField(source='medicao.numero', read_only=True, default='')

    class Meta:
        model  = Pagamento
        fields = [
            'id', 'numero', 'medicao', 'medicao_numero',
            'numero_empenho', 'numero_nota_fiscal', 'valor_pago',
            'data_vencimento', 'data_pagamento', 'status', 'status_display',
            'observacoes', 'created_at',
        ]
        read_only_fields = ['id', 'numero', 'status_display', 'medicao_numero', 'created_at']

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class MedicaoSerializer(serializers.ModelSerializer):
    status_display          = serializers.CharField(source='get_status_display', read_only=True)
    fiscal_responsavel_username = serializers.CharField(source='fiscal_responsavel.username', read_only=True, default='')
    pagamentos               = PagamentoSerializer(many=True, read_only=True)

    class Meta:
        model  = Medicao
        fields = [
            'id', 'numero', 'competencia_inicio', 'competencia_fim', 'data_medicao',
            'percentual_executado', 'valor_medido',
            'fiscal_responsavel', 'fiscal_responsavel_username',
            'status', 'status_display', 'parecer_fiscal', 'data_aprovacao',
            'pagamentos', 'created_at',
        ]
        read_only_fields = ['id', 'numero', 'status_display', 'fiscal_responsavel_username', 'pagamentos', 'created_at']

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ContratoSerializer(serializers.ModelSerializer):
    orgao_executor_sigla   = serializers.CharField(source='orgao_executor.sigla',   read_only=True)
    orgao_executor_nome    = serializers.CharField(source='orgao_executor.nome',    read_only=True)
    dfd_numero_sei         = serializers.CharField(source='dfd.numero_sei',         read_only=True)
    fiscal_username        = serializers.CharField(source='fiscal_contrato.username', read_only=True)
    gestor_username        = serializers.CharField(source='gestor_contrato.username', read_only=True)
    ordenador_username     = serializers.CharField(source='ordenador.username',     read_only=True)
    tipo_origem_display    = serializers.CharField(source='get_tipo_origem_display', read_only=True)
    fornecedor_nome        = serializers.CharField(source='fornecedor.nome_razao_social', read_only=True, default='')
    created_by_username    = serializers.CharField(source='created_by.username',    read_only=True)
    apostilas              = ApostilaSerializer(many=True, read_only=True)
    aditivos               = AditivoSerializer(many=True, read_only=True)
    cronograma             = CronogramaEntregaSerializer(many=True, read_only=True)
    medicoes               = MedicaoSerializer(many=True, read_only=True)
    pagamentos             = PagamentoSerializer(many=True, read_only=True)

    valor_medido_total = serializers.SerializerMethodField()
    valor_pago_total    = serializers.SerializerMethodField()
    saldo_a_pagar       = serializers.SerializerMethodField()

    garantia_tipo_display = serializers.CharField(source='get_garantia_tipo_display', read_only=True, default='')

    class Meta:
        model  = Contrato
        fields = [
            'id', 'numero', 'exercicio',
            'orgao_executor', 'orgao_executor_sigla', 'orgao_executor_nome',
            'objeto', 'tipo_origem', 'tipo_origem_display',
            'fornecedor', 'fornecedor_nome',
            'dfd', 'dfd_numero_sei',
            'lotes', 'numero_processo_sei',
            'valor_contrato',
            'data_assinatura', 'data_vigencia_inicio', 'data_vigencia_fim',
            'status',
            'fiscal_contrato', 'fiscal_username',
            'gestor_contrato', 'gestor_username',
            'ordenador', 'ordenador_username',
            'observacoes',
            'garantia_exigida', 'garantia_tipo', 'garantia_tipo_display',
            'garantia_percentual', 'garantia_apolice',
            'garantia_vigencia_inicio', 'garantia_vigencia_fim',
            'garantia_justificativa_acima_5',
            'org_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'apostilas', 'aditivos',
            'cronograma', 'medicoes', 'pagamentos',
            'valor_medido_total', 'valor_pago_total', 'saldo_a_pagar',
        ]
        read_only_fields = [
            'id', 'numero', 'org_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'orgao_executor_sigla', 'orgao_executor_nome',
            'dfd_numero_sei', 'fiscal_username', 'gestor_username', 'ordenador_username',
            'tipo_origem_display', 'garantia_tipo_display', 'apostilas', 'aditivos',
            'cronograma', 'medicoes', 'pagamentos',
            'valor_medido_total', 'valor_pago_total', 'saldo_a_pagar',
        ]

    def get_valor_medido_total(self, obj):
        return sum((m.valor_medido for m in obj.medicoes.all() if m.status == 'aprovada'), Decimal('0'))

    def get_valor_pago_total(self, obj):
        return sum((p.valor_pago for p in obj.pagamentos.all() if p.status == 'pago'), Decimal('0'))

    def get_saldo_a_pagar(self, obj):
        return self.get_valor_medido_total(obj) - self.get_valor_pago_total(obj)

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
