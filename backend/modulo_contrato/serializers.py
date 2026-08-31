from decimal import Decimal
from rest_framework import serializers
from modulo_fornecedor.models import Fornecedor
from .models import Contrato, Apostila, Aditivo, CronogramaEntrega, Medicao, Pagamento, Notificacao


class ApostilaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Apostila
        fields = ['id', 'numero', 'objeto', 'data', 'numero_processo_sei', 'created_at']
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
        fields = ['id', 'numero', 'tipo', 'tipo_display', 'valor_acrescimo', 'nova_vigencia', 'objeto', 'data', 'numero_processo_sei', 'created_at']
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
            'is_atrasado', 'observacoes', 'numero_processo_sei', 'created_at',
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
            'observacoes', 'numero_processo_sei', 'created_at',
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
    aditivo_referencia_numero = serializers.CharField(source='aditivo_referencia.numero', read_only=True, default='')

    class Meta:
        model  = Medicao
        fields = [
            'id', 'numero', 'competencia_inicio', 'competencia_fim', 'data_medicao',
            'percentual_executado', 'valor_medido',
            'fiscal_responsavel', 'fiscal_responsavel_username',
            'status', 'status_display', 'parecer_fiscal', 'data_aprovacao',
            'houve_alteracao_planilha', 'aditivo_referencia', 'aditivo_referencia_numero',
            'pagamentos', 'numero_processo_sei', 'created_at',
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


class NotificacaoSerializer(serializers.ModelSerializer):
    # required=False: na criação aninhada em ContratoViewSet.add_notificacao o
    # contrato já vem da URL e é injetado via serializer.save(contrato=...);
    # só é obrigatório de fato no endpoint plano (NotificacaoViewSet), que
    # valida isso em perform_create.
    contrato = serializers.PrimaryKeyRelatedField(queryset=Contrato.objects.all(), required=False)
    fornecedor = serializers.PrimaryKeyRelatedField(queryset=Fornecedor.objects.all(), required=False, allow_null=True)
    status_display           = serializers.CharField(source='get_status_display', read_only=True)
    categoria_objeto_display = serializers.CharField(source='get_categoria_objeto_display', read_only=True)
    tipo_acao_display        = serializers.CharField(source='get_tipo_acao_display', read_only=True)
    contrato_numero          = serializers.CharField(source='contrato.numero', read_only=True)
    fornecedor_nome          = serializers.SerializerMethodField()
    fornecedor_documento     = serializers.SerializerMethodField()

    class Meta:
        model  = Notificacao
        fields = [
            'id', 'contrato', 'contrato_numero',
            'numero', 'exercicio', 'tipo_acao', 'tipo_acao_display',
            'categoria_objeto', 'categoria_objeto_display',
            'numero_processo_sei', 'numero_sei_comunicacao', 'numero_sei_notificacao',
            'data_notificacao', 'resumo_fato', 'status', 'status_display', 'observacoes',
            'fornecedor', 'fornecedor_nome', 'fornecedor_documento',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'status_display', 'categoria_objeto_display', 'tipo_acao_display', 'contrato_numero',
            'fornecedor_nome', 'fornecedor_documento', 'created_at', 'updated_at',
        ]

    def _fornecedor(self, obj):
        # A notificação pode ter fornecedor próprio (quando o contrato não tem
        # um vinculado, ou é diferente); senão cai no fornecedor do contrato.
        return obj.fornecedor or (obj.contrato.fornecedor if obj.contrato_id else None)

    def get_fornecedor_nome(self, obj):
        f = self._fornecedor(obj)
        return f.nome_razao_social if f else None

    def get_fornecedor_documento(self, obj):
        f = self._fornecedor(obj)
        return f.documento if f else None

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
    notificacoes           = NotificacaoSerializer(many=True, read_only=True)

    valor_medido_total = serializers.SerializerMethodField()
    valor_pago_total    = serializers.SerializerMethodField()
    saldo_a_pagar       = serializers.SerializerMethodField()

    garantia_tipo_display = serializers.CharField(source='get_garantia_tipo_display', read_only=True, default='')
    tipo_instrumento_display = serializers.CharField(source='get_tipo_instrumento_display', read_only=True)

    class Meta:
        model  = Contrato
        fields = [
            'id', 'numero', 'exercicio',
            'orgao_executor', 'orgao_executor_sigla', 'orgao_executor_nome',
            'objeto', 'tipo_origem', 'tipo_origem_display',
            'tipo_instrumento', 'tipo_instrumento_display', 'numero_afm',
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
            'cronograma', 'medicoes', 'pagamentos', 'notificacoes',
            'valor_medido_total', 'valor_pago_total', 'saldo_a_pagar',
        ]
        read_only_fields = [
            'id', 'numero', 'org_id', 'created_by', 'created_by_username',
            'created_at', 'updated_at',
            'orgao_executor_sigla', 'orgao_executor_nome',
            'dfd_numero_sei', 'fiscal_username', 'gestor_username', 'ordenador_username',
            'tipo_origem_display', 'tipo_instrumento_display', 'garantia_tipo_display', 'apostilas', 'aditivos',
            'cronograma', 'medicoes', 'pagamentos', 'notificacoes',
            'valor_medido_total', 'valor_pago_total', 'saldo_a_pagar',
        ]

    def get_valor_medido_total(self, obj):
        return sum((m.valor_medido for m in obj.medicoes.all() if m.status == 'aprovada'), Decimal('0'))

    def get_valor_pago_total(self, obj):
        return sum((p.valor_pago for p in obj.pagamentos.all() if p.status == 'pago'), Decimal('0'))

    def get_saldo_a_pagar(self, obj):
        return self.get_valor_medido_total(obj) - self.get_valor_pago_total(obj)

    def validate(self, attrs):
        def _valor(campo, default=None):
            if campo in attrs:
                return attrs[campo]
            return getattr(self.instance, campo, default)

        if _valor('tipo_instrumento', 'contrato') == 'afm':
            numero_afm = _valor('numero_afm', '')
            if not (numero_afm or '').strip():
                raise serializers.ValidationError({
                    'numero_afm': 'Obrigatório quando o tipo de instrumento é AFM.',
                })

        garantia_percentual = _valor('garantia_percentual')
        if garantia_percentual is not None and garantia_percentual > 5:
            justificativa = _valor('garantia_justificativa_acima_5', '')
            if not (justificativa or '').strip():
                raise serializers.ValidationError({
                    'garantia_justificativa_acima_5': 'Obrigatória quando o percentual de garantia é superior a 5% (Art. 96, §3º).',
                })

        return attrs

    def create(self, validated_data):
        req = self.context['request']
        validated_data['org_id_id']  = req.org_id
        validated_data['created_by'] = req.user
        validated_data['updated_by'] = req.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
