from rest_framework import serializers
from .models import ETP, HistoricoETP, HistoricoNumeroSEI


class HistoricoETPSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoETP
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_username', 'motivo', 'criado_em']


class HistoricoNumeroSEISerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoNumeroSEI
        fields = ['id', 'numero_anterior', 'numero_novo', 'usuario_username', 'motivo', 'criado_em']


class ETPSerializer(serializers.ModelSerializer):
    created_by_username  = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username  = serializers.CharField(source='updated_by.username', read_only=True)
    dfd_numero_sei       = serializers.CharField(source='dfd.numero_sei', read_only=True)
    # Optional on create — defaults to DFD's numero_sei when omitted
    numero_sei           = serializers.CharField(required=False, allow_blank=True, default='')
    dfd_status           = serializers.CharField(source='dfd.status',     read_only=True)
    org_sigla            = serializers.CharField(source='org_id.sigla',   read_only=True)
    historico            = HistoricoETPSerializer(many=True, read_only=True)
    historico_numero_sei = HistoricoNumeroSEISerializer(many=True, read_only=True)
    tr_id                = serializers.SerializerMethodField()

    def get_tr_id(self, obj):
        tr = getattr(obj, 'tr', None)
        return tr.pk if tr else None

    class Meta:
        model  = ETP
        fields = [
            'id',
            'dfd',
            'dfd_numero_sei',
            'dfd_status',
            'numero_sei',
            'necessidade_contratacao',
            'requisitos_contratacao',
            'levantamento_mercado',
            'estimativa_valor',
            'descricao_solucao',
            'justificativa_solucao',
            'riscos',
            'sustentabilidade',
            'status',
            'motivo_devolucao',
            'observacoes',
            'org_id',
            'org_sigla',
            'created_by',
            'created_by_username',
            'updated_by',
            'updated_by_username',
            'created_at',
            'updated_at',
            'historico',
            'historico_numero_sei',
            'tr_id',
        ]
        read_only_fields = [
            'id', 'org_id', 'org_sigla',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'dfd_numero_sei', 'dfd_status',
            'motivo_devolucao',
            'historico', 'historico_numero_sei', 'tr_id',
        ]

    def validate_dfd(self, dfd):
        if dfd.status != 'Aprovada':
            raise serializers.ValidationError(
                'ETP só pode ser criado para DFDs com status "Aprovada".'
            )
        if hasattr(dfd, 'etp'):
            raise serializers.ValidationError(
                'Este DFD já possui um ETP associado.'
            )
        return dfd

    def create(self, validated_data):
        request = self.context['request']
        # Pre-fill numero_sei from DFD if not explicitly provided
        if not validated_data.get('numero_sei'):
            validated_data['numero_sei'] = validated_data['dfd'].numero_sei
        validated_data['org_id_id']  = request.org_id
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        novo_numero = validated_data.get('numero_sei')
        if novo_numero and novo_numero != instance.numero_sei:
            motivo = request.data.get('motivo_numero_sei', '')
            HistoricoNumeroSEI.objects.create(
                etp=instance,
                numero_anterior=instance.numero_sei,
                numero_novo=novo_numero,
                usuario=request.user,
                motivo=motivo,
            )
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)
