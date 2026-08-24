from rest_framework import serializers
from modulo_planejamento.models import NecessidadePlanejamento
from .models import (
    AcaoOrcamentaria, ElementoDespesa, NaturezaDespesa, FonteRecurso, SubFonteRecurso,
    DotacaoOrcamentaria, IndicacaoOrcamentaria, IndicacaoDotacao, HistoricoIndicacao,
    DescentralizacaoOrcamentaria, ConcessaoOrcamentaria,
    EmpenhoOrcamentario, LiquidacaoOrcamentaria, PagamentoOrcamentario,
    TipoAcaoOrcamentaria, TipoFonteRecurso,
)


class TipoAcaoOrcamentariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoAcaoOrcamentaria
        fields = ['id', 'descricao', 'ativo']


class TipoFonteRecursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoFonteRecurso
        fields = ['id', 'descricao', 'ativo']


class AcaoOrcamentariaSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    tipo_descricao = serializers.CharField(source='tipo.descricao', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = AcaoOrcamentaria
        fields = [
            'id', 'codigo', 'nome', 'tipo', 'tipo_descricao', 'descricao', 'ativa',
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


class NaturezaDespesaSerializer(serializers.ModelSerializer):
    elemento_codigo = serializers.IntegerField(source='elemento_despesa.codigo', read_only=True)
    elemento_descricao = serializers.CharField(source='elemento_despesa.descricao', read_only=True)
    formato = serializers.CharField(read_only=True)

    class Meta:
        model = NaturezaDespesa
        fields = [
            'id', 'codigo', 'formato', 'descricao', 'ativa',
            'elemento_despesa', 'elemento_codigo', 'elemento_descricao',
        ]
        read_only_fields = ['id', 'formato']


class FonteRecursoSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    tipo_descricao = serializers.CharField(source='tipo.descricao', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = FonteRecurso
        fields = [
            'id', 'codigo', 'nome', 'tipo', 'tipo_descricao', 'exercicio_anterior',
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


class SubFonteRecursoSerializer(serializers.ModelSerializer):
    org_nome = serializers.CharField(source='org_id.nome', read_only=True)
    fonte_codigo = serializers.IntegerField(source='fonte_recurso.codigo', read_only=True)
    fonte_nome = serializers.CharField(source='fonte_recurso.nome', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = SubFonteRecurso
        fields = [
            'id', 'fonte_recurso', 'fonte_codigo', 'fonte_nome', 'codigo', 'nome', 'ativa',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'org_id', 'created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_fonte_recurso(self, fonte):
        request = self.context['request']
        if str(fonte.org_id_id) != str(request.org_id):
            raise serializers.ValidationError('Fonte de recurso não pertence à organização.')
        return fonte

    def create(self, validated_data):
        validated_data['org_id_id'] = self.context['request'].org_id
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class NecessidadeResumoSerializer(serializers.ModelSerializer):
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

    # Opcional na entrada — quando natureza_despesa é informada, validate() a deriva dela.
    elemento_despesa = serializers.PrimaryKeyRelatedField(
        queryset=ElementoDespesa.objects.all(), required=False,
    )
    elemento_codigo = serializers.IntegerField(source='elemento_despesa.codigo', read_only=True)
    elemento_descricao = serializers.CharField(source='elemento_despesa.descricao', read_only=True)

    natureza_formato = serializers.CharField(source='natureza_despesa.formato', read_only=True)
    natureza_descricao = serializers.CharField(source='natureza_despesa.descricao', read_only=True)

    fonte_codigo = serializers.IntegerField(source='fonte_recurso.codigo', read_only=True)
    fonte_nome = serializers.CharField(source='fonte_recurso.nome', read_only=True)
    fonte_tipo = serializers.CharField(source='fonte_recurso.tipo', read_only=True)

    subfonte_recurso = serializers.PrimaryKeyRelatedField(
        queryset=SubFonteRecurso.objects.all(), required=False, allow_null=True,
    )
    subfonte_codigo = serializers.CharField(source='subfonte_recurso.codigo', read_only=True)
    subfonte_nome = serializers.CharField(source='subfonte_recurso.nome', read_only=True)

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
            'natureza_despesa', 'natureza_formato', 'natureza_descricao',
            'fonte_recurso', 'fonte_codigo', 'fonte_nome', 'fonte_tipo',
            'subfonte_recurso', 'subfonte_codigo', 'subfonte_nome',
            'valor_dotado', 'valor_indicado', 'valor_descentralizado', 'valor_concedido',
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

        acao = attrs.get('acao')
        if acao and str(acao.org_id_id) != str(org_id):
            raise serializers.ValidationError({'acao': 'Ação não pertence à organização.'})

        fonte = attrs.get('fonte_recurso')
        if fonte and str(fonte.org_id_id) != str(org_id):
            raise serializers.ValidationError({'fonte_recurso': 'Fonte de recurso não pertence à organização.'})

        # Subfonte precisa pertencer à fonte selecionada (ou já vinculada, em edição parcial)
        subfonte = attrs.get('subfonte_recurso')
        if subfonte:
            fonte_referencia = fonte or (self.instance.fonte_recurso if self.instance else None)
            if fonte_referencia and subfonte.fonte_recurso_id != fonte_referencia.id:
                raise serializers.ValidationError({
                    'subfonte_recurso': (
                        f'A subfonte {subfonte.codigo} pertence à fonte {subfonte.fonte_recurso.codigo}, '
                        f'não à fonte {fonte_referencia.codigo}.'
                    )
                })

        # Natureza contém o Elemento — auto-preenche elemento a partir da natureza
        natureza = attrs.get('natureza_despesa')
        elemento = attrs.get('elemento_despesa')
        if natureza:
            elemento_da_natureza = natureza.elemento_despesa
            if elemento and elemento != elemento_da_natureza:
                raise serializers.ValidationError({
                    'natureza_despesa': (
                        f'A natureza {natureza.formato} pertence ao elemento '
                        f'{elemento_da_natureza.codigo:02d}, '
                        f'não ao elemento {elemento.codigo:02d}.'
                    )
                })
            # Auto-preenche elemento a partir da natureza
            attrs['elemento_despesa'] = elemento_da_natureza
        elif not elemento and not self.partial:
            raise serializers.ValidationError(
                {'natureza_despesa': 'Selecione uma natureza de despesa ou um elemento de despesa.'}
            )

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


# ── Indicação Orçamentária / DOD ───────────────────────────────────────────────

class DescentralizacaoSerializer(serializers.ModelSerializer):
    registrada_por_username = serializers.CharField(source='registrada_por.username', read_only=True)

    class Meta:
        model  = DescentralizacaoOrcamentaria
        fields = ['id', 'numero_npo', 'data_emissao', 'valor',
                  'cancelada', 'data_cancelamento', 'motivo_cancelamento',
                  'observacoes', 'registrada_por_username', 'criado_em']
        read_only_fields = ['id', 'cancelada', 'data_cancelamento', 'registrada_por_username', 'criado_em']


class ConcessaoSerializer(serializers.ModelSerializer):
    registrada_por_username = serializers.CharField(source='registrada_por.username', read_only=True)

    class Meta:
        model  = ConcessaoOrcamentaria
        fields = ['id', 'numero_doc', 'data_emissao', 'valor',
                  'cancelada', 'data_cancelamento', 'motivo_cancelamento',
                  'observacoes', 'registrada_por_username', 'criado_em']
        read_only_fields = ['id', 'cancelada', 'data_cancelamento', 'registrada_por_username', 'criado_em']


class EmpenhoSerializer(serializers.ModelSerializer):
    registrada_por_username = serializers.CharField(source='registrada_por.username', read_only=True)

    class Meta:
        model  = EmpenhoOrcamentario
        fields = ['id', 'numero_doc', 'data_emissao', 'valor',
                  'cancelada', 'data_cancelamento', 'motivo_cancelamento',
                  'observacoes', 'registrada_por_username', 'criado_em']
        read_only_fields = ['id', 'cancelada', 'data_cancelamento', 'registrada_por_username', 'criado_em']


class LiquidacaoSerializer(serializers.ModelSerializer):
    registrada_por_username = serializers.CharField(source='registrada_por.username', read_only=True)

    class Meta:
        model  = LiquidacaoOrcamentaria
        fields = ['id', 'numero_doc', 'data_emissao', 'valor',
                  'cancelada', 'data_cancelamento', 'motivo_cancelamento',
                  'observacoes', 'registrada_por_username', 'criado_em']
        read_only_fields = ['id', 'cancelada', 'data_cancelamento', 'registrada_por_username', 'criado_em']


class PagamentoSerializer(serializers.ModelSerializer):
    registrada_por_username = serializers.CharField(source='registrada_por.username', read_only=True)

    class Meta:
        model  = PagamentoOrcamentario
        fields = ['id', 'numero_doc', 'data_emissao', 'valor',
                  'cancelada', 'data_cancelamento', 'motivo_cancelamento',
                  'observacoes', 'registrada_por_username', 'criado_em']
        read_only_fields = ['id', 'cancelada', 'data_cancelamento', 'registrada_por_username', 'criado_em']


class IndicacaoDotacaoSerializer(serializers.ModelSerializer):
    acao_codigo        = serializers.CharField(source='dotacao.acao.codigo',       read_only=True)
    acao_nome          = serializers.CharField(source='dotacao.acao.nome',         read_only=True)
    elemento_codigo    = serializers.IntegerField(source='dotacao.elemento_despesa.codigo', read_only=True)
    elemento_descricao = serializers.CharField(source='dotacao.elemento_despesa.descricao', read_only=True)
    natureza_formato   = serializers.SerializerMethodField()
    natureza_descricao = serializers.SerializerMethodField()
    fonte_codigo       = serializers.IntegerField(source='dotacao.fonte_recurso.codigo', read_only=True)
    fonte_nome         = serializers.CharField(source='dotacao.fonte_recurso.nome', read_only=True)
    dotacao_id         = serializers.IntegerField(source='dotacao.id',             read_only=True)
    item_dfd_objeto    = serializers.CharField(source='item_dfd.objeto', read_only=True, default=None)
    valor_descentralizado = serializers.SerializerMethodField()
    valor_concedido       = serializers.SerializerMethodField()
    valor_empenhado       = serializers.SerializerMethodField()
    valor_liquidado       = serializers.SerializerMethodField()
    valor_pago             = serializers.SerializerMethodField()
    saldo                   = serializers.SerializerMethodField()
    status_execucao          = serializers.SerializerMethodField()
    descentralizacoes     = DescentralizacaoSerializer(many=True, read_only=True)
    concessoes            = ConcessaoSerializer(many=True, read_only=True)
    empenhos              = EmpenhoSerializer(many=True, read_only=True)
    liquidacoes           = LiquidacaoSerializer(many=True, read_only=True)
    pagamentos            = PagamentoSerializer(many=True, read_only=True)

    class Meta:
        model  = IndicacaoDotacao
        fields = [
            'id', 'dotacao_id', 'valor_indicado',
            'item_dfd', 'item_dfd_objeto', 'em_diligencia',
            'valor_descentralizado', 'valor_concedido',
            'valor_empenhado', 'valor_liquidado', 'valor_pago', 'saldo', 'status_execucao',
            'acao_codigo', 'acao_nome',
            'elemento_codigo', 'elemento_descricao',
            'natureza_formato', 'natureza_descricao',
            'fonte_codigo', 'fonte_nome',
            'descentralizacoes', 'concessoes', 'empenhos', 'liquidacoes', 'pagamentos',
        ]

    def get_natureza_formato(self, obj):
        nd = obj.dotacao.natureza_despesa
        return nd.formato if nd else None

    def get_natureza_descricao(self, obj):
        nd = obj.dotacao.natureza_despesa
        return nd.descricao if nd else None

    def get_valor_descentralizado(self, obj):
        total = sum(
            d.valor for d in obj.descentralizacoes.filter(cancelada=False)
        )
        return float(total)

    def get_valor_concedido(self, obj):
        total = sum(
            c.valor for c in obj.concessoes.filter(cancelada=False)
        )
        return float(total)

    def get_valor_empenhado(self, obj):
        total = sum(e.valor for e in obj.empenhos.filter(cancelada=False))
        return float(total)

    def get_valor_liquidado(self, obj):
        total = sum(l.valor for l in obj.liquidacoes.filter(cancelada=False))
        return float(total)

    def get_valor_pago(self, obj):
        total = sum(p.valor for p in obj.pagamentos.filter(cancelada=False))
        return float(total)

    def get_saldo(self, obj):
        return float(obj.valor_indicado) - self.get_valor_pago(obj)

    def get_status_execucao(self, obj):
        if self.get_valor_pago(obj) > 0:
            return 'Pago'
        if self.get_valor_liquidado(obj) > 0:
            return 'Liquidado'
        if self.get_valor_empenhado(obj) > 0:
            return 'Empenhado'
        if obj.em_diligencia:
            return 'Em Diligência'
        if obj.valor_indicado > 0:
            return 'Indicado'
        return 'Sem Execução'


class HistoricoIndicacaoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField()

    class Meta:
        model  = HistoricoIndicacao
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_nome', 'motivo', 'criado_em']

    def get_usuario_nome(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return '—'


class IndicacaoOrcamentariaSerializer(serializers.ModelSerializer):
    org_nome            = serializers.CharField(source='org_id.nome',         read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    ordenador_nome      = serializers.SerializerMethodField()
    dfd_numero_sei      = serializers.CharField(source='dfd.numero_sei',      read_only=True)
    necessidade_titulo  = serializers.CharField(source='necessidade.titulo',  read_only=True)
    itens               = IndicacaoDotacaoSerializer(many=True, read_only=True)
    historico           = HistoricoIndicacaoSerializer(many=True, read_only=True)

    class Meta:
        model  = IndicacaoOrcamentaria
        fields = [
            'id', 'numero', 'exercicio_fiscal',
            'dfd', 'dfd_numero_sei',
            'necessidade', 'necessidade_titulo',
            'valor_total', 'status', 'observacoes',
            'ordenador', 'ordenador_nome', 'data_aprovacao', 'motivo_cancelamento',
            'itens', 'historico',
            'org_id', 'org_nome',
            'created_by', 'created_by_username',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'numero', 'valor_total', 'status',
            'ordenador', 'data_aprovacao', 'motivo_cancelamento',
            'org_id', 'created_by', 'created_at', 'updated_at',
        ]

    def get_ordenador_nome(self, obj):
        if obj.ordenador:
            return obj.ordenador.get_full_name() or obj.ordenador.username
        return None

    def create(self, validated_data):
        from datetime import date
        request = self.context['request']
        org_id  = request.org_id
        exercicio = validated_data.get('exercicio_fiscal', date.today().year)

        # Gerar número sequencial: IND-2026-001
        count = IndicacaoOrcamentaria.objects.filter(
            org_id=org_id, exercicio_fiscal=exercicio
        ).count()
        numero = f'IND-{exercicio}-{str(count + 1).zfill(3)}'

        validated_data['org_id_id'] = org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        validated_data['numero']     = numero
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class VincularDotacaoSerializer(serializers.Serializer):
    dotacao_id     = serializers.IntegerField()
    valor_indicado = serializers.DecimalField(max_digits=15, decimal_places=2)
    item_dfd_id    = serializers.IntegerField(required=False, allow_null=True)
    em_diligencia  = serializers.BooleanField(required=False, default=False)
