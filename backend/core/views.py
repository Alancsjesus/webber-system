from rest_framework import viewsets, serializers as drf_serializers, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q, Prefetch
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional, UserProfile, ParametroSistema
from core.permissions import IsMultiTenant


# ── Serializers ────────────────────────────────────────────────────────────────

class OrgaoSerializer(drf_serializers.ModelSerializer):
    parent_sigla = drf_serializers.CharField(source='parent.sigla', read_only=True)
    parent_nome  = drf_serializers.CharField(source='parent.nome',  read_only=True)

    class Meta:
        model  = Orgao
        fields = ['id', 'sigla', 'nome', 'parent', 'parent_sigla', 'parent_nome', 'ativa']


class UnidadeSerializer(drf_serializers.ModelSerializer):
    orgao_sigla = drf_serializers.CharField(source='orgao.sigla', read_only=True)
    orgao_nome  = drf_serializers.CharField(source='orgao.nome',  read_only=True)

    class Meta:
        model  = UnidadeOrganizacional
        fields = ['id', 'orgao', 'orgao_sigla', 'orgao_nome', 'sigla', 'nome', 'tipo', 'ativa']


class UserProfileSerializer(drf_serializers.ModelSerializer):
    username   = drf_serializers.CharField(source='user.username')
    first_name = drf_serializers.CharField(source='user.first_name', required=False, default='')
    last_name  = drf_serializers.CharField(source='user.last_name',  required=False, default='')
    email      = drf_serializers.EmailField(source='user.email',     required=False, default='')
    password   = drf_serializers.CharField(source='user.password',   write_only=True, required=False, default='')
    org_sigla  = drf_serializers.CharField(source='org_id.sigla',    read_only=True)
    unidade_sigla = drf_serializers.CharField(source='unidade.sigla', read_only=True)
    unidade_nome  = drf_serializers.CharField(source='unidade.nome',  read_only=True)
    unidade_tipo  = drf_serializers.CharField(source='unidade.tipo',  read_only=True)

    class Meta:
        model  = UserProfile
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'password',
            'papel', 'org_id', 'org_sigla', 'unidade', 'unidade_sigla', 'unidade_nome', 'unidade_tipo',
        ]

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        password  = user_data.pop('password', '')
        user = User.objects.create_user(
            username   = user_data['username'],
            first_name = user_data.get('first_name', ''),
            last_name  = user_data.get('last_name', ''),
            email      = user_data.get('email', ''),
            password   = password or 'changeme123',
        )
        profile = UserProfile.objects.get(user=user)
        profile.papel   = validated_data.get('papel', 'solicitante')
        profile.org_id  = validated_data.get('org_id')
        profile.unidade = validated_data.get('unidade')
        profile.save()
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        password  = user_data.pop('password', '')
        user = instance.user
        for field in ('first_name', 'last_name', 'email'):
            if field in user_data:
                setattr(user, field, user_data[field])
        if password:
            user.set_password(password)
        user.save()
        instance.papel   = validated_data.get('papel', instance.papel)
        instance.org_id  = validated_data.get('org_id', instance.org_id)
        instance.unidade = validated_data.get('unidade', instance.unidade)
        instance.save()
        return instance


# ── ViewSets ─────────────────────────────────────────────────────────────────

def _require_admin(request):
    if getattr(request, 'papel', None) != 'admin':
        raise PermissionDenied('Apenas administradores podem executar esta ação.')


class OrgaoViewSet(viewsets.ModelViewSet):
    serializer_class   = OrgaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nome', 'sigla']
    ordering_fields    = ['sigla', 'nome']
    ordering           = ['sigla']
    queryset           = Orgao.objects.all().select_related('parent')

    def perform_create(self, serializer):
        _require_admin(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _require_admin(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _require_admin(self.request)
        instance.ativa = False
        instance.save()


class UnidadeViewSet(viewsets.ModelViewSet):
    serializer_class   = UnidadeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nome', 'sigla', 'orgao__sigla']
    ordering_fields    = ['sigla', 'nome', 'tipo']
    ordering           = ['orgao__sigla', 'sigla']

    def get_queryset(self):
        qs   = UnidadeOrganizacional.objects.all().select_related('orgao')
        tipo = self.request.query_params.get('tipo')
        org  = self.request.query_params.get('orgao')
        ativa = self.request.query_params.get('ativa', 'true')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if org:
            qs = qs.filter(orgao_id=org)
        if ativa == 'true':
            qs = qs.filter(ativa=True)
        return qs

    def perform_create(self, serializer):
        _require_admin(self.request)
        serializer.save()

    def perform_update(self, serializer):
        _require_admin(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        _require_admin(self.request)
        instance.ativa = False
        instance.save()


class UserManagementViewSet(viewsets.ModelViewSet):
    serializer_class   = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    ordering           = ['user__username']

    def get_queryset(self):
        papel = getattr(self.request, 'papel', None)
        qs = UserProfile.objects.select_related('user', 'org_id', 'unidade')
        if papel != 'admin':
            # Non-admins only see their own profile
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        _require_admin(self.request)
        serializer.save()

    def perform_update(self, serializer):
        papel = getattr(self.request, 'papel', None)
        if papel != 'admin' and serializer.instance.user != self.request.user:
            raise PermissionDenied('Sem permissão para editar este usuário.')
        serializer.save()

    def perform_destroy(self, instance):
        _require_admin(self.request)
        instance.user.is_active = False
        instance.user.save()


class ParametroSistemaSerializer(drf_serializers.ModelSerializer):
    atualizado_por_username = drf_serializers.CharField(
        source='atualizado_por.username', read_only=True
    )

    class Meta:
        model  = ParametroSistema
        fields = ['id', 'chave', 'valor', 'descricao', 'atualizado_em', 'atualizado_por_username']
        read_only_fields = ['id', 'atualizado_em', 'atualizado_por_username']


class ParametroSistemaViewSet(viewsets.ModelViewSet):
    serializer_class   = ParametroSistemaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['chave', 'descricao']
    ordering           = ['chave']
    queryset           = ParametroSistema.objects.all()

    def _check_permissao(self, request):
        papel       = getattr(request, 'papel', None)
        tipo_unid   = getattr(request, 'tipo_unidade', None)
        if papel not in ('admin', 'gestor_planejamento', 'analista') and tipo_unid != 'licitante':
            raise PermissionDenied('Apenas administradores, gestores de planejamento e unidade licitante podem alterar parâmetros.')

    def perform_create(self, serializer):
        self._check_permissao(self.request)
        serializer.save(atualizado_por=self.request.user)

    def perform_update(self, serializer):
        self._check_permissao(self.request)
        serializer.save(atualizado_por=self.request.user)

    def perform_destroy(self, instance):
        self._check_permissao(self.request)
        instance.delete()


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import DFD
        from modulo_planejamento.models import NecessidadePlanejamento
        from modulo_orcamento.models import DotacaoOrcamentaria
        from modulo_etp.models import ETP
        from modulo_tr.models import TR

        org_id  = request.org_id
        orgao   = Orgao.objects.filter(pk=org_id).first()
        filhos  = list(Orgao.objects.filter(parent_id=org_id).values('id', 'sigla', 'nome'))
        filhos_ids = [f['id'] for f in filhos]

        # ── Necessidades ─────────────────────────────────────────────────────
        nec_proprias = NecessidadePlanejamento.objects.filter(org_id=org_id)
        nec_externas = (
            NecessidadePlanejamento.objects.filter(org_id__in=filhos_ids, tipo_execucao='externa')
            if filhos_ids else NecessidadePlanejamento.objects.none()
        )
        necessidades = (nec_proprias | nec_externas).distinct()

        nec_stats      = necessidades.aggregate(total=Count('id'), valor_total=Sum('valor_estimado'))
        nec_por_status = {i['status']: i['count'] for i in necessidades.values('status').annotate(count=Count('id'))}
        recentes_nec   = list(
            necessidades.order_by('-created_at')[:5].values(
                'id', 'titulo', 'status', 'prioridade', 'valor_estimado', 'created_at', 'org_id__sigla',
            )
        )

        # ── DFDs ─────────────────────────────────────────────────────────────
        dfds = DFD.objects.filter(
            Q(org_id=org_id) | Q(unidade_licitante__orgao_id=org_id) | Q(org_gestor=org_id)
        ).distinct()

        dfd_stats      = dfds.aggregate(total=Count('id'), valor_total=Sum('valor_estimado'))
        dfd_por_status = {i['status']: i['count'] for i in dfds.values('status').annotate(count=Count('id'))}
        recentes_dfds  = list(
            dfds.order_by('-created_at')[:5].values(
                'id', 'numero_sei', 'descricao', 'status', 'valor_estimado', 'created_at', 'org_id__sigla',
            )
        )

        # ── Dotações ─────────────────────────────────────────────────────────
        dotacoes       = DotacaoOrcamentaria.objects.filter(org_id=org_id)
        dot_stats      = dotacoes.aggregate(total=Count('id'), valor_total=Sum('valor_dotado'))
        dot_por_status = {i['status']: i['count'] for i in dotacoes.values('status').annotate(count=Count('id'))}
        recentes_dot   = list(
            dotacoes.order_by('-created_at')[:5].values(
                'id', 'exercicio_fiscal', 'status', 'valor_dotado',
                'acao__codigo', 'acao__nome', 'elemento_despesa__codigo',
            )
        )

        # ── ETPs ─────────────────────────────────────────────────────────────
        etps = ETP.objects.filter(
            Q(org_id=org_id) | Q(dfd__org_gestor=org_id) | Q(dfd__unidade_licitante__orgao_id=org_id)
        ).distinct()
        etp_stats      = etps.aggregate(total=Count('id'))
        etp_por_status = {i['status']: i['count'] for i in etps.values('status').annotate(count=Count('id'))}
        recentes_etps  = list(
            etps.order_by('-created_at')[:5].values(
                'id', 'numero_sei', 'status', 'estimativa_valor', 'created_at',
                'dfd__org_id__sigla',
            )
        )

        # ── TRs ──────────────────────────────────────────────────────────────
        trs = TR.objects.filter(
            Q(etp__org_id=org_id) |
            Q(etp__dfd__org_gestor=org_id) |
            Q(etp__dfd__unidade_licitante__orgao_id=org_id)
        ).distinct()
        tr_stats      = trs.aggregate(total=Count('id'))
        tr_por_status = {i['status']: i['count'] for i in trs.values('status').annotate(count=Count('id'))}

        # ── Aceites pendentes (necessidades de filhos aguardando aceite) ─────
        aceites_pendentes = (
            NecessidadePlanejamento.objects.filter(
                org_id__in=filhos_ids, tipo_execucao='externa', aceite_pai='pendente'
            ).count()
            if filhos_ids else 0
        )

        # ── Breakdown por órgão (apenas quando há filhos) ────────────────────
        por_orgao = []
        if filhos_ids and orgao:
            por_orgao.append({
                'orgao_id':    org_id,
                'orgao_sigla': orgao.sigla,
                'orgao_nome':  orgao.nome,
                'eh_filho':    False,
                'necessidades_total': nec_proprias.count(),
                'dfds_total':  DFD.objects.filter(org_id=org_id).distinct().count(),
                'etps_total':  ETP.objects.filter(org_id=org_id).count(),
                'trs_total':   TR.objects.filter(etp__org_id=org_id).count(),
                'valor_total': float(nec_proprias.aggregate(v=Sum('valor_estimado'))['v'] or 0),
                'aceites_pendentes': 0,
            })
            for filho in filhos:
                fid        = filho['id']
                nec_f_ext  = NecessidadePlanejamento.objects.filter(org_id=fid, tipo_execucao='externa')
                por_orgao.append({
                    'orgao_id':              fid,
                    'orgao_sigla':           filho['sigla'],
                    'orgao_nome':            filho['nome'],
                    'eh_filho':              True,
                    'necessidades_total':    nec_f_ext.count(),
                    'dfds_total':            DFD.objects.filter(org_id=fid).count(),
                    'etps_total':            ETP.objects.filter(org_id=fid).count(),
                    'trs_total':             TR.objects.filter(etp__org_id=fid).count(),
                    'valor_total':           float(nec_f_ext.aggregate(v=Sum('valor_estimado'))['v'] or 0),
                    'aceites_pendentes':     nec_f_ext.filter(aceite_pai='pendente').count(),
                })

        return Response({
            'necessidades': {
                'total':       nec_stats['total'] or 0,
                'valor_total': float(nec_stats['valor_total'] or 0),
                'por_status':  nec_por_status,
                'recentes':    recentes_nec,
            },
            'dfds': {
                'total':       dfd_stats['total'] or 0,
                'valor_total': float(dfd_stats['valor_total'] or 0),
                'por_status':  dfd_por_status,
                'recentes':    recentes_dfds,
            },
            'dotacoes': {
                'total':       dot_stats['total'] or 0,
                'valor_total': float(dot_stats['valor_total'] or 0),
                'por_status':  dot_por_status,
                'recentes':    recentes_dot,
            },
            'etps': {
                'total':      etp_stats['total'] or 0,
                'por_status': etp_por_status,
                'recentes':   recentes_etps,
            },
            'trs': {
                'total':      tr_stats['total'] or 0,
                'por_status': tr_por_status,
            },
            'aceites_pendentes': aceites_pendentes,
            'por_orgao':         por_orgao,
        })


class PainelOrgaoPaiView(APIView):
    """
    Painel consolidado do órgão pai: documentos organizados por órgão e unidade demandante.
    Retorna necessidades, DFDs e ETPs de todos os órgãos filhos + próprio.
    """
    permission_classes = [IsAuthenticated, IsMultiTenant]

    def get(self, request):
        from modulo_demanda.models import DFD
        from modulo_planejamento.models import NecessidadePlanejamento
        from modulo_etp.models import ETP

        oid = request.org_id
        orgao = Orgao.objects.filter(pk=oid).first()
        if not orgao:
            return Response({'detail': 'Órgão não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Collect all relevant org IDs: own + children
        filhos = list(Orgao.objects.filter(parent_id=oid).values('id', 'sigla', 'nome'))
        todos_org_ids = [oid] + [f['id'] for f in filhos]

        result = []
        for org_info in [{'id': oid, 'sigla': orgao.sigla, 'nome': orgao.nome}] + filhos:
            oid_loop = org_info['id']

            # Necessidades from this org that are visible to parent
            if oid_loop == oid:
                necs = NecessidadePlanejamento.objects.filter(org_id=oid_loop)
            else:
                necs = NecessidadePlanejamento.objects.filter(
                    org_id=oid_loop, tipo_execucao='externa'
                )

            nec_data = list(necs.order_by('-created_at').values(
                'id', 'titulo', 'status', 'prioridade', 'valor_estimado',
                'tipo_execucao', 'unidade_demandante__sigla', 'unidade_demandante__nome',
                'dfd__id', 'dfd__numero_sei', 'dfd__status',
            ))

            # DFDs from this org (visible to parent as licitante)
            dfds = DFD.objects.filter(
                Q(org_id=oid_loop) |
                Q(unidade_licitante__orgao_id=oid)
            ).filter(org_id=oid_loop).distinct()

            dfd_data = []
            for dfd in dfds.order_by('-created_at').select_related('etp'):
                etp_info = None
                if hasattr(dfd, 'etp'):
                    etp_info = {
                        'id': dfd.etp.pk,
                        'numero_sei': dfd.etp.numero_sei,
                        'status': dfd.etp.status,
                    }
                dfd_data.append({
                    'id': dfd.id,
                    'numero_sei': dfd.numero_sei,
                    'status': dfd.status,
                    'valor_estimado': float(dfd.valor_estimado or 0),
                    'unidade_demandante': str(dfd.unidade_demandante) if dfd.unidade_demandante_id else None,
                    'etp': etp_info,
                })

            result.append({
                'orgao_id':   oid_loop,
                'orgao_sigla': org_info['sigla'],
                'orgao_nome':  org_info['nome'],
                'eh_filho':    oid_loop != oid,
                'necessidades': nec_data,
                'dfds': dfd_data,
            })

        return Response(result)
