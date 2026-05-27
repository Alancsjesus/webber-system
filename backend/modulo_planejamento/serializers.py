from datetime import date
from django.db.models import Sum
from rest_framework import serializers
from .models import NecessidadePlanejamento, HistoricoNecessidade, PlanoOrcamentario, ItemPlanoOrcamentario
from core.models import Orgao


class HistoricoNecessidadeSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoNecessidade
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_username', 'motivo', 'criado_em']


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
    historico            = HistoricoNecessidadeSerializer(many=True, read_only=True)

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
            'historico',
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
            'dfd_numero_sei', 'itens_plano_count', 'planos_ids', 'origem', 'historico',
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

    # Campos que pertencem ao órgão filho — pai não pode alterar
    CAMPOS_FILHO = frozenset([
        'titulo', 'descricao', 'valor_estimado',
        'departamento_solicitante', 'tipo_execucao',
    ])
    # Campos que o pai pode ajustar nas necessidades aceitas dos filhos
    CAMPOS_PAI_PERMITIDOS = frozenset([
        'exercicio_fiscal', 'prioridade', 'prazo_desejado',
        'unidade_demandante', 'observacoes', 'area_aplicacao',
    ])

    def _is_edicao_pai(self, instance):
        """Retorna True quando o órgão pai está editando necessidade de filho."""
        request = self.context.get('request')
        if not request:
            return False
        oid = request.org_id
        # É necessidade de filho (org_id diferente do editor) aceita pelo pai
        return (
            instance.org_id_id != oid
            and instance.aceite_pai == 'aceita'
            and instance.orgao_executor_id == oid
        )

    def update(self, instance, validated_data):
        request = self.context['request']

        # Restrição: pai só pode editar campos de planejamento
        if self._is_edicao_pai(instance):
            campos_proibidos = set(validated_data.keys()) & self.CAMPOS_FILHO
            if campos_proibidos:
                raise serializers.ValidationError({
                    campo: 'Este campo pertence ao órgão de origem e não pode ser alterado pelo órgão executor.'
                    for campo in campos_proibidos
                })
            # Remove silenciosamente qualquer outro campo não permitido
            for campo in list(validated_data.keys()):
                if campo not in self.CAMPOS_PAI_PERMITIDOS:
                    validated_data.pop(campo, None)

        else:
            # Edição pelo próprio filho: lógica original de tipo_execucao
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
    necessidade_titulo    = serializers.CharField(source='necessidade.titulo',               read_only=True)
    necessidade_status    = serializers.CharField(source='necessidade.status',               read_only=True)
    necessidade_descricao = serializers.CharField(source='necessidade.descricao',            read_only=True)
    necessidade_areas     = serializers.JSONField(source='necessidade.area_aplicacao',       read_only=True)
    necessidade_prioridade= serializers.CharField(source='necessidade.prioridade',           read_only=True)
    orgao_origem_sigla    = serializers.CharField(source='necessidade.org_id.sigla',         read_only=True)
    unidade_demandante_sigla = serializers.CharField(
        source='necessidade.unidade_demandante.sigla', read_only=True, default=None)
    departamento_solicitante = serializers.CharField(
        source='necessidade.departamento_solicitante', read_only=True)
    valor_estimado        = serializers.DecimalField(
        source='necessidade.valor_estimado', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = ItemPlanoOrcamentario
        fields = [
            'id', 'necessidade', 'necessidade_titulo', 'necessidade_status',
            'necessidade_descricao', 'necessidade_areas', 'necessidade_prioridade',
            'orgao_origem_sigla', 'unidade_demandante_sigla', 'departamento_solicitante',
            'valor_estimado', 'origem',
            # Campos PCA
            'categoria_orcamentaria', 'programa_acao',
            'data_estimada_inicio', 'vinculacao_pgi', 'numero_sequencial_pca',
        ]
        read_only_fields = [
            'id', 'necessidade_titulo', 'necessidade_status', 'necessidade_descricao',
            'necessidade_areas', 'necessidade_prioridade', 'orgao_origem_sigla',
            'unidade_demandante_sigla', 'departamento_solicitante',
            'valor_estimado', 'numero_sequencial_pca',
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
            'status_pca', 'itens', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = [
            'id', 'orgao', 'orgao_sigla', 'orgao_nome', 'itens',
            'dotacao_utilizada', 'status_pca', 'criado_em', 'atualizado_em',
        ]
