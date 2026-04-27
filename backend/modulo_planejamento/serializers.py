from datetime import date
from django.db.models import Sum
from rest_framework import serializers
from .models import NecessidadePlanejamento, PlanoOrcamentario, ItemPlanoOrcamentario
from core.models import Orgao


class NecessidadeSerializer(serializers.ModelSerializer):
    created_by_username  = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username  = serializers.CharField(source='updated_by.username', read_only=True)
    org_nome             = serializers.CharField(source='org_id.nome', read_only=True)
    org_sigla            = serializers.CharField(source='org_id.sigla', read_only=True)
    dfd_numero_sei       = serializers.CharField(source='dfd.numero_sei', read_only=True)
    orgao_executor_sigla = serializers.CharField(source='orgao_executor.sigla', read_only=True)
    orgao_executor_nome  = serializers.CharField(source='orgao_executor.nome',  read_only=True)
    org_gestor_sigla     = serializers.CharField(source='org_gestor.sigla',     read_only=True)
    org_gestor_nome      = serializers.CharField(source='org_gestor.nome',      read_only=True)
    itens_plano_count    = serializers.SerializerMethodField()
    planos_ids           = serializers.PrimaryKeyRelatedField(source='planos', many=True, read_only=True)
    origem               = serializers.SerializerMethodField()

    def get_itens_plano_count(self, obj):
        return obj.itens_plano.count()

    def get_origem(self, obj):
        """'herdada' if the necessidade came from a child org, 'propria' otherwise."""
        request = self.context.get('request')
        if request and obj.org_id_id != request.org_id:
            return 'herdada'
        return 'propria'

    class Meta:
        model = NecessidadePlanejamento
        fields = [
            'id',
            'titulo',
            'descricao',
            'area_aplicacao',
            'valor_estimado',
            'departamento_solicitante',
            'exercicio_fiscal',
            'prioridade',
            'status',
            'tipo_execucao',
            'prazo_desejado',
            'observacoes',
            'itens_plano_count',
            'planos_ids',
            'origem',
            'dfd',
            'dfd_numero_sei',
            'orgao_executor',
            'orgao_executor_sigla',
            'orgao_executor_nome',
            'org_gestor',
            'org_gestor_sigla',
            'org_gestor_nome',
            'unidade_demandante',
            'aceite_pai',
            'org_id',
            'org_nome',
            'org_sigla',
            'created_by',
            'created_by_username',
            'updated_by',
            'updated_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'org_id', 'created_by', 'updated_by',
            'created_at', 'updated_at',
            'org_gestor', 'org_gestor_sigla', 'org_gestor_nome',
            'orgao_executor_sigla', 'orgao_executor_nome',
            'dfd_numero_sei', 'itens_plano_count', 'planos_ids', 'origem',
        ]

    def validate_prazo_desejado(self, value):
        if value and value < date.today():
            raise serializers.ValidationError(
                'O prazo desejado deve ser uma data futura (maior que hoje).'
            )
        return value

    def validate_area_aplicacao(self, value):
        if not value:
            raise serializers.ValidationError('Pelo menos uma área de aplicação é obrigatória.')
        valid = [c[0] for c in NecessidadePlanejamento.AREA_CHOICES]
        for area in value:
            if area not in valid:
                raise serializers.ValidationError(f'Área inválida: {area}')
        return value

    def create(self, validated_data):
        request = self.context['request']
        validated_data['org_id_id'] = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        if validated_data.get('tipo_execucao') == 'externa':
            try:
                org = Orgao.objects.get(pk=request.org_id)
                if org.parent_id:
                    if not validated_data.get('orgao_executor_id'):
                        validated_data['orgao_executor_id'] = org.parent_id
                    validated_data['aceite_pai'] = 'pendente'
            except Orgao.DoesNotExist:
                pass
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        # Se mudou para externa, inicializar aceite_pai
        novo_tipo = validated_data.get('tipo_execucao')
        if novo_tipo == 'externa' and instance.tipo_execucao != 'externa':
            try:
                org = Orgao.objects.get(pk=instance.org_id_id)
                if org.parent_id:
                    if not validated_data.get('orgao_executor_id') and not instance.orgao_executor_id:
                        validated_data['orgao_executor_id'] = org.parent_id
                    validated_data['aceite_pai'] = 'pendente'
            except Orgao.DoesNotExist:
                pass
        elif novo_tipo == 'interna':
            validated_data['aceite_pai'] = None
            validated_data['orgao_executor_id'] = None
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class ItemPlanoSerializer(serializers.ModelSerializer):
    necessidade_titulo   = serializers.CharField(source='necessidade.titulo',      read_only=True)
    necessidade_status   = serializers.CharField(source='necessidade.status',      read_only=True)
    orgao_origem_sigla   = serializers.CharField(source='necessidade.org_id.sigla', read_only=True)
    valor_estimado       = serializers.DecimalField(
        source='necessidade.valor_estimado', max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = ItemPlanoOrcamentario
        fields = [
            'id', 'necessidade', 'necessidade_titulo', 'necessidade_status',
            'orgao_origem_sigla', 'valor_estimado', 'origem',
        ]


class PlanoOrcamentarioSerializer(serializers.ModelSerializer):
    itens          = ItemPlanoSerializer(many=True, read_only=True)
    orgao_sigla    = serializers.CharField(source='orgao.sigla', read_only=True)
    orgao_nome     = serializers.CharField(source='orgao.nome',  read_only=True)
    dotacao_utilizada = serializers.SerializerMethodField()

    def get_dotacao_utilizada(self, obj):
        total = obj.necessidades.aggregate(t=Sum('valor_estimado'))['t']
        return total or 0

    class Meta:
        model = PlanoOrcamentario
        fields = [
            'id', 'orgao', 'orgao_sigla', 'orgao_nome',
            'exercicio_fiscal', 'descricao', 'dotacao_total', 'dotacao_utilizada',
            'itens', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = [
            'id', 'orgao_sigla', 'orgao_nome', 'itens',
            'dotacao_utilizada', 'criado_em', 'atualizado_em',
        ]
