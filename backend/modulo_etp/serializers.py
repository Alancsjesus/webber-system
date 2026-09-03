from rest_framework import serializers
from .models import ETP, HistoricoETP, HistoricoNumeroSEI
from modulo_arp.models import Ata


class HistoricoETPSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoETP
        fields = ['id', 'status_anterior', 'status_novo', 'usuario_username', 'motivo', 'categoria_motivo', 'criado_em']


class HistoricoNumeroSEISerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = HistoricoNumeroSEI
        fields = ['id', 'numero_anterior', 'numero_novo', 'usuario_username', 'motivo', 'criado_em']


class ETPSerializer(serializers.ModelSerializer):
    created_by_username  = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username  = serializers.CharField(source='updated_by.username', read_only=True)
    dfd_numero_sei       = serializers.CharField(source='dfd.numero_sei',    read_only=True)
    dfd_status           = serializers.CharField(source='dfd.status',        read_only=True)
    dfd_descricao        = serializers.CharField(source='dfd.descricao',     read_only=True, allow_null=True, default='')
    dfd_local_entrega    = serializers.CharField(source='dfd.local_entrega', read_only=True, allow_null=True, default='')
    # Optional on create — defaults to DFD's numero_sei when omitted
    numero_sei           = serializers.CharField(required=False, allow_blank=True, default='')
    org_sigla            = serializers.CharField(source='org_id.sigla',   read_only=True)
    historico            = HistoricoETPSerializer(many=True, read_only=True)
    historico_numero_sei = HistoricoNumeroSEISerializer(many=True, read_only=True)
    tr_id                = serializers.SerializerMethodField()
    ata_adesao_numero_ata = serializers.CharField(source='ata_adesao.numero_ata', read_only=True, default=None)
    mesa_atual_label = serializers.SerializerMethodField()

    def get_tr_id(self, obj):
        tr = getattr(obj, 'tr', None)
        return tr.pk if tr else None

    def get_mesa_atual_label(self, obj):
        from core.mesa_atual import mesa_atual_label
        return mesa_atual_label(obj)

    class Meta:
        model  = ETP
        fields = [
            'id',
            'dfd',
            'dfd_numero_sei',
            'dfd_status',
            'dfd_descricao',
            'dfd_local_entrega',
            'numero_sei',
            'necessidade_contratacao',
            'requisitos_contratacao',
            'levantamento_mercado',
            'estimativa_valor',
            'descricao_solucao',
            'justificativa_solucao',
            'ata_adesao',
            'ata_adesao_numero_ata',
            'justificativa_vantajosidade_adesao',
            'riscos',
            'sustentabilidade',
            'tipo_objeto',
            'tipo_parcelamento',
            'parcelamento_justificativa',
            'reserva_cota_me_epp',
            'reserva_cota_justificativa',
            'licitacao_exclusiva_me_epp',
            'posicionamento_conclusivo',
            'classificacao_sensivel',
            'classificacao_sensivel_justificativa',
            'alinhamento_planesp',
            'contratacoes_correlatas',
            'impacto_ambiental',
            'providencias_pre_contrato',
            'compra_vs_locacao',
            'status',
            'motivo_devolucao',
            'dispensa_motivo',
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
            'mesa_atual_label',
            'data_mesa_atual',
        ]
        read_only_fields = [
            'id', 'org_id', 'org_sigla',
            'created_by', 'created_by_username',
            'updated_by', 'updated_by_username',
            'created_at', 'updated_at',
            'dfd_numero_sei', 'dfd_status', 'dfd_descricao', 'dfd_local_entrega',
            'motivo_devolucao',
            'historico', 'historico_numero_sei', 'tr_id',
            'ata_adesao_numero_ata',
            'mesa_atual_label', 'data_mesa_atual',
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

    def validate_ata_adesao(self, value):
        if value and value.tipo_origem not in Ata.TIPOS_ORIGEM_EXTERNA:
            raise serializers.ValidationError(
                'O ETP só aceita Ata gerenciada por outro órgão (participante ou carona) — '
                'para saque de Ata gerenciada por esta Secretaria, vincule na Necessidade de Planejamento.'
            )
        return value

    def validate(self, attrs):
        ata_adesao = attrs.get('ata_adesao', getattr(self.instance, 'ata_adesao', None))
        justificativa = attrs.get(
            'justificativa_vantajosidade_adesao',
            getattr(self.instance, 'justificativa_vantajosidade_adesao', ''),
        )
        if ata_adesao and not (justificativa or '').strip():
            raise serializers.ValidationError({
                'justificativa_vantajosidade_adesao': 'Obrigatória quando uma Ata de adesão é informada — Art. 86, §2º.',
            })
        return attrs

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
