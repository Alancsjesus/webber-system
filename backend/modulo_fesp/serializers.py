from rest_framework import serializers
from .models import (
    InstrumentoFinanceiro, HistoricoInstrumentoFinanceiro,
    ComposicaoConselhoGestor, ReuniaoConselhoGestor,
    PlanoAplicacao, HistoricoPlanoAplicacao, MetaEspecifica,
    GrupoConsolidacaoItem, ItemPlanoAplicacao,
)


class HistoricoInstrumentoFinanceiroSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoInstrumentoFinanceiro
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class InstrumentoFinanceiroSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    tipo_instrumento_display = serializers.CharField(source='get_tipo_instrumento_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    fonte_recurso_nome = serializers.CharField(source='fonte_recurso.nome', read_only=True)
    historico = HistoricoInstrumentoFinanceiroSerializer(many=True, read_only=True)

    class Meta:
        model = InstrumentoFinanceiro
        fields = [
            'id', 'tipo_instrumento', 'tipo_instrumento_display', 'numero_instrumento',
            'objeto', 'orgao_concedente_nome',
            'fonte_recurso', 'fonte_recurso_nome',
            'valor_total_pactuado', 'valor_contrapartida',
            'data_assinatura', 'vigencia_inicio', 'vigencia_fim',
            'numero_processo_sei', 'status', 'status_display', 'dados_especificos', 'observacoes',
            'historico',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'org_id', 'created_by', 'updated_by', 'created_at', 'updated_at',
        ]

    def validate_fonte_recurso(self, fonte):
        if fonte is None:
            return fonte
        request = self.context['request']
        if str(fonte.org_id_id) != str(request.org_id):
            raise serializers.ValidationError('Fonte de recurso não pertence à organização.')
        return fonte

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ComposicaoConselhoGestorSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    cargo_display = serializers.CharField(source='get_cargo_display', read_only=True)
    usuario_nome = serializers.SerializerMethodField()
    orgao_representado_sigla = serializers.CharField(source='orgao_representado.sigla', read_only=True)

    class Meta:
        model = ComposicaoConselhoGestor
        fields = [
            'id', 'usuario', 'usuario_nome', 'cargo', 'cargo_display',
            'orgao_representado', 'orgao_representado_sigla', 'nome_orgao_externo',
            'portaria_nomeacao', 'data_inicio_mandato', 'data_fim_mandato', 'ativo',
            'org_id', 'org_nome', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'org_id', 'created_at', 'updated_at']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return None

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ReuniaoConselhoGestorSerializer(serializers.ModelSerializer):
    presentes_detail = ComposicaoConselhoGestorSerializer(many=True, read_only=True, source='presentes')

    class Meta:
        model = ReuniaoConselhoGestor
        fields = [
            'id', 'plano', 'numero_ata', 'tipo', 'data_reuniao',
            'quorum_atingido', 'deliberacao', 'presentes', 'presentes_detail',
            'created_at',
        ]
        read_only_fields = ['id', 'plano', 'created_at']


class HistoricoPlanoAplicacaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model = HistoricoPlanoAplicacao
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class GrupoConsolidacaoItemSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = GrupoConsolidacaoItem
        fields = [
            'id', 'plano', 'chave_agrupamento', 'titulo', 'descricao', 'status', 'status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ItemPlanoAplicacaoSerializer(serializers.ModelSerializer):
    natureza_display = serializers.CharField(source='get_natureza_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    org_beneficiaria_sigla = serializers.CharField(source='org_beneficiaria.sigla', read_only=True)
    unidade_beneficiaria_nome = serializers.CharField(source='unidade_beneficiaria.nome', read_only=True)
    instrumento_numero = serializers.CharField(source='instrumento.numero_instrumento', read_only=True)
    item_catalogo_familia = serializers.CharField(source='item_catalogo.familia', read_only=True)

    class Meta:
        model = ItemPlanoAplicacao
        fields = [
            'id', 'meta_especifica', 'instrumento', 'instrumento_numero',
            'org_beneficiaria', 'org_beneficiaria_sigla',
            'unidade_beneficiaria', 'unidade_beneficiaria_nome', 'destinacao',
            'item_catalogo', 'item_catalogo_familia', 'codigo_senasp',
            'bem_servico', 'descricao', 'base_legal', 'natureza', 'natureza_display',
            'unidade_medida', 'quantidade', 'valor_unitario_estimado', 'valor_total_estimado',
            'aprovado', 'grupo_consolidacao', 'necessidade_gerada', 'status', 'status_display',
            'observacoes', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'valor_total_estimado', 'grupo_consolidacao', 'necessidade_gerada',
            'status', 'created_at', 'updated_at',
        ]

    def validate(self, attrs):
        request = self.context['request']
        instrumento = attrs.get('instrumento') or getattr(self.instance, 'instrumento', None)
        meta_especifica = attrs.get('meta_especifica') or getattr(self.instance, 'meta_especifica', None)
        if instrumento and str(instrumento.org_id_id) != str(request.org_id):
            raise serializers.ValidationError({'instrumento': 'Instrumento não pertence à organização.'})
        if instrumento and meta_especifica and instrumento.tipo_instrumento != meta_especifica.plano.natureza:
            raise serializers.ValidationError({
                'instrumento': (
                    f'O instrumento é do tipo "{instrumento.get_tipo_instrumento_display()}", mas o plano '
                    f'tem natureza "{meta_especifica.plano.get_natureza_display()}".'
                ),
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


class MetaEspecificaSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    itens = ItemPlanoAplicacaoSerializer(many=True, read_only=True)

    class Meta:
        model = MetaEspecifica
        fields = [
            'id', 'plano', 'numero', 'titulo', 'descricao_meta', 'status', 'status_display',
            'descricao_indicador', 'formula_indicador', 'valor_referencia',
            'periodo_referencia', 'fonte_indicador', 'periodicidade',
            'carteira_politicas_mjsp', 'meta_pnsp', 'meta_pesp',
            'valor_total', 'itens', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'numero', 'valor_total', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class PlanoAplicacaoSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    natureza_display = serializers.CharField(source='get_natureza_display', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    historico = HistoricoPlanoAplicacaoSerializer(many=True, read_only=True)
    reuniao_aprovacao_detail = ReuniaoConselhoGestorSerializer(source='reuniao_aprovacao', read_only=True)
    metas_especificas = MetaEspecificaSerializer(many=True, read_only=True)
    checklist = serializers.SerializerMethodField()
    valor_planejado_total = serializers.SerializerMethodField()

    class Meta:
        model = PlanoAplicacao
        fields = [
            'id', 'numero', 'natureza', 'natureza_display',
            'exercicio_fiscal', 'ementa', 'descricao', 'status', 'status_display',
            'declaracao_nao_pessoal', 'declaracao_nao_unidade_administrativa',
            'declaracao_sem_contingenciamento',
            'reuniao_aprovacao', 'reuniao_aprovacao_detail', 'motivo_devolucao_conselho',
            'numero_ato', 'data_ato', 'numero_processo_sei_ato',
            'responsavel_gestao_nome', 'responsavel_gestao_email',
            'responsavel_gestao_cargo', 'responsavel_gestao_telefone',
            'responsavel_elaboracao_nome', 'responsavel_elaboracao_email',
            'responsavel_elaboracao_cargo', 'responsavel_elaboracao_telefone',
            'diagnostico', 'meta_geral', 'justificativa',
            'indicador_geral_descricao', 'indicador_geral_formula',
            'indicador_geral_valor_referencia', 'indicador_geral_periodo_referencia',
            'indicador_geral_fonte',
            'valor_originario_investimento', 'valor_originario_custeio',
            'valor_suplementar_investimento', 'valor_suplementar_custeio',
            'valor_rendimento_investimento', 'valor_rendimento_custeio',
            'valor_planejado_investimento', 'valor_planejado_custeio', 'valor_planejado_total',
            'metas_especificas', 'historico', 'checklist',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'status', 'reuniao_aprovacao', 'motivo_devolucao_conselho',
            'numero_ato', 'data_ato', 'numero_processo_sei_ato',
            'valor_planejado_investimento', 'valor_planejado_custeio',
            'org_id', 'created_by', 'created_at', 'updated_at',
        ]

    def validate_natureza(self, value):
        if self.instance and value != self.instance.natureza:
            raise serializers.ValidationError('A natureza do plano não pode ser alterada após a criação.')
        return value

    def get_valor_planejado_total(self, obj):
        return obj.valor_planejado_investimento + obj.valor_planejado_custeio

    def get_checklist(self, obj):
        from core.checklist_engine import ChecklistEngine
        from dataclasses import asdict
        resultado = ChecklistEngine.avaliar_plano_aplicacao(obj)
        return {
            'score': resultado.score,
            'total': resultado.total,
            'percentual': resultado.percentual,
            'pode_submeter': resultado.pode_submeter,
            'bloqueadores': [asdict(r) for r in resultado.bloqueadores],
            'avisos': [asdict(r) for r in resultado.avisos],
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)
