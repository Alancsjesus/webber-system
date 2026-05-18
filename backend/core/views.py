from rest_framework import viewsets, serializers as drf_serializers, filters, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q, Prefetch
from django.contrib.auth.models import User
from core.models import Orgao, UnidadeOrganizacional, UserProfile, ParametroSistema, AreaAtuacao, SecaoArtefato, ItemCatalogo, CategoriaItem
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

        # Não-admin só pode editar o próprio perfil
        if papel != 'admin' and serializer.instance.user != self.request.user:
            raise PermissionDenied('Sem permissão para editar este usuário.')

        # Não-admin não pode alterar papel, org_id nem unidade (prevenção de escalada)
        if papel != 'admin':
            for campo in ('papel', 'org_id', 'unidade'):
                if campo in serializer.validated_data:
                    raise PermissionDenied(
                        f'O campo "{campo}" só pode ser alterado por um administrador.'
                    )

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
        fields = [
            'id', 'chave', 'valor', 'descricao',
            'norma_base', 'data_vigencia',
            'atualizado_em', 'atualizado_por_username',
        ]
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


class UserSimpleSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class UserListView(ListAPIView):
    """Lista todos os usuários ativos — usado nos selects de fiscal/gestor."""
    serializer_class   = UserSimpleSerializer
    permission_classes = [IsAuthenticated]
    queryset           = User.objects.filter(is_active=True).order_by('username')


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


class AreaAtuacaoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model  = AreaAtuacao
        fields = ['id', 'codigo', 'nome', 'ativa']


class AreaAtuacaoViewSet(viewsets.ModelViewSet):
    serializer_class   = AreaAtuacaoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['codigo', 'nome']
    ordering           = ['nome']

    def get_queryset(self):
        mostrar_inativas = self.request.query_params.get('inativas') == 'true'
        qs = AreaAtuacao.objects.all()
        if not mostrar_inativas:
            qs = qs.filter(ativa=True)
        return qs

    def _check_perm(self, request):
        if getattr(request, 'papel', None) not in ('admin', 'gestor_planejamento') \
                and getattr(request, 'tipo_unidade', None) != 'planejamento':
            raise PermissionDenied('Apenas Admin ou Planejamento podem gerenciar áreas de atuação.')

    def perform_create(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_perm(self.request)
        instance.ativa = False
        instance.save()


class CategoriaItemSerializer(drf_serializers.ModelSerializer):
    caminho_completo = drf_serializers.CharField(read_only=True)
    nivel            = drf_serializers.IntegerField(read_only=True)
    pai_nome         = drf_serializers.CharField(source='pai.nome', read_only=True, default=None)
    tem_filhos       = drf_serializers.SerializerMethodField()

    class Meta:
        model  = CategoriaItem
        fields = ['id', 'nome', 'codigo', 'pai', 'pai_nome', 'caminho_completo', 'nivel', 'tem_filhos']

    def get_tem_filhos(self, obj):
        return obj.filhos.exists()


class CategoriaItemViewSet(viewsets.ModelViewSet):
    serializer_class   = CategoriaItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = None   # categorias são poucos registros — sem paginação
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nome', 'codigo']
    ordering_fields    = ['nome']
    ordering           = ['nome']

    def get_queryset(self):
        qs = CategoriaItem.objects.select_related('pai').all()
        pai = self.request.query_params.get('pai')
        if pai == 'null':
            qs = qs.filter(pai__isnull=True)
        elif pai:
            qs = qs.filter(pai_id=pai)
        return qs

    def _check_perm(self, request):
        if getattr(request, 'papel', None) not in ('admin', 'analista', 'gestor_planejamento'):
            raise PermissionDenied('Apenas administradores e analistas podem gerenciar categorias.')

    def perform_create(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_perm(self.request)
        if instance.filhos.exists():
            raise PermissionDenied('Remova as subcategorias antes de excluir esta categoria.')
        if instance.itens.exists():
            raise PermissionDenied('Existem itens vinculados a esta categoria. Desvincule-os antes.')
        instance.delete()


class ItemCatalogoSerializer(drf_serializers.ModelSerializer):
    categoria_nome          = drf_serializers.CharField(source='categoria.nome', read_only=True, default=None)
    categoria_path          = drf_serializers.CharField(source='categoria.caminho_completo', read_only=True, default=None)
    classificacao_tipo_display = drf_serializers.CharField(source='get_classificacao_tipo_display', read_only=True)

    class Meta:
        model  = ItemCatalogo
        fields = [
            'id', 'codigo_interno', 'codigo_simpas', 'familia',
            'categoria', 'categoria_nome', 'categoria_path',
            'nome', 'descricao', 'unidade_medida', 'ativo',
            'item_sustentavel', 'item_luxo',
            'classificacao_tipo', 'classificacao_tipo_display',
            'valor_referencia', 'data_referencia', 'num_licitacao_ref',
        ]
        read_only_fields = ['id', 'codigo_interno', 'familia', 'classificacao_tipo_display']


class _CatalogoPaginacao(drf_serializers.Serializer):
    """Paginação do catálogo com page_size configurável pelo cliente (máx 500)."""
    pass

from rest_framework.pagination import PageNumberPagination

class CatalogoPaginacao(PageNumberPagination):
    page_size            = 50
    page_size_query_param = 'page_size'
    max_page_size        = 500


class ItemCatalogoViewSet(viewsets.ModelViewSet):
    serializer_class   = ItemCatalogoSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = CatalogoPaginacao
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['codigo_interno', 'codigo_simpas', 'familia', 'nome']
    ordering_fields    = ['familia', 'nome', 'codigo_interno']
    ordering           = ['familia', 'nome']

    def get_queryset(self):
        qs   = ItemCatalogo.objects.select_related('categoria__pai').all()
        p    = self.request.query_params
        if p.get('inativas') != 'true':
            qs = qs.filter(ativo=True)
        if p.get('familia'):
            qs = qs.filter(familia=p['familia'])
        if p.get('categoria'):
            qs = qs.filter(categoria_id=p['categoria'])
        if p.get('classificacao_tipo'):
            qs = qs.filter(classificacao_tipo=p['classificacao_tipo'])
        if p.get('item_sustentavel') == 'true':
            qs = qs.filter(item_sustentavel=True)
        if p.get('item_luxo') == 'true':
            qs = qs.filter(item_luxo=True)
        return qs

    def _check_perm(self, request):
        if getattr(request, 'papel', None) not in ('admin', 'analista', 'gestor_planejamento'):
            raise PermissionDenied('Apenas administradores e analistas podem gerenciar o catálogo.')

    def perform_create(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_perm(self.request)
        instance.ativo = False
        instance.save()

    @action(detail=False, methods=['post'], url_path='importar-csv')
    def importar_csv(self, request):
        import csv, json
        from decimal import Decimal, InvalidOperation
        from datetime import datetime
        from django.db import transaction

        self._check_perm(request)

        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            return Response({'erro': 'Arquivo não enviado.'}, status=400)

        dry_run = str(request.data.get('dry_run', 'true')).lower() in ('true', '1')
        # mapeamento manual familia_desc→cat_id (usado apenas no modo ComprasNet)
        try:
            mapeamento_manual = json.loads(request.data.get('mapeamento', '{}'))
        except Exception:
            mapeamento_manual = {}

        # ── decodificação ─────────────────────────────────────────────────────
        conteudo = arquivo.read()
        texto = None
        for enc in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
            try:
                texto = conteudo.decode(enc)
                break
            except Exception:
                continue
        if texto is None:
            return Response({'erro': 'Encoding do arquivo não suportado.'}, status=400)

        linhas = texto.splitlines()
        if not linhas:
            return Response({'erro': 'Arquivo vazio.'}, status=400)

        # pular "sep=;" do Excel
        if linhas[0].strip().lower().startswith('sep='):
            linhas = linhas[1:]

        reader   = csv.reader(linhas, delimiter=';', quotechar='"')
        cabecalho = next(reader, None)
        if not cabecalho:
            return Response({'erro': 'Arquivo sem cabeçalho.'}, status=400)

        cab = [c.strip().lower() for c in cabecalho]

        # ── detectar formato pelo cabeçalho ───────────────────────────────────
        # SIMPAS: tem 'num_item' ou 'cod_grup'
        # ComprasNet: tem 'código item' ou 'nome básico'
        def _idx(keys):
            for k in keys:
                for i, h in enumerate(cab):
                    if k in h:
                        return i
            return None

        FORMATO_SIMPAS = any('num_item' in h or 'cod_grup' in h for h in cab)

        if FORMATO_SIMPAS:
            # Mapeamento de colunas da planilha SIMPAS:
            # Col 0  "Item"            → código SIMPAS completo (ex: 65.15.00.00207748-3)
            # Col 1  "Cod_Grup"        → código do grupo (ex: 65)
            # Col 2  "Descricao"       → descrição do grupo
            # Col 3  "Num_Fam"         → número da família (ex: 15)
            # Col 4  "Descricao"       → descrição da família
            # Col 5  "Cod_secre"       → código da secretaria (ignorado)
            # Col 6  "Descricao"       → descrição da secretaria (ignorada)
            # Col 7  "Num_item"        → número sequencial do item DENTRO da família (ex: 207748)
            #                           ← NÃO é o código completo, apenas parte dele
            # Col 8  "Nome_Ba"         → nome básico
            # Col 9  "Nome_Mc"         → nome modificador
            # Col 10 "Descricao"       → descrição padrão
            # Col 11 "Unid"            → unidade de medida
            # Col 12 "Tipo_Item"       → tipo (M=Material, S=Serviço)
            # Col 13 "Situacao"        → situação (Ativo/Inativo)
            # Col 14 "Data_Cadastro"   → ignorada
            # Col 15 "Item_Sust"       → item sustentável (S/N)
            # Col 16 "Item_Lux"        → item de luxo (S/N)
            # Col 17 "Data_Alteracao"  → ignorada
            # Col 18 "ClassificaTipo"  → classificação (Consumo/Permanente/Serviço)
            # Col 19 "Data_Ultima_RMRS"→ data do valor de referência
            # Col 20 "Sit_item_I"      → ignorada
            # Col 21 "Validade_"       → ignorada
            # Col 22 "Nr_Licit"        → nº licitação de referência
            # Col 23 "Data_Pr"         → ignorada
            # Col 24 "Valor_Refe"      → valor de referência SIMPAS
            #
            # IMPORTANTE: o código completo está SEMPRE na coluna 0 ("Item"),
            # independentemente do nome do cabeçalho.
            iCOD_SIMPAS  = 0   # coluna A = código completo (ex: 65.15.00.00207748-3)
            iCOD_GRUP    = _idx(['cod_grup'])    or 1
            iDESC_GRUP   = _idx(['desc_grup'])   or 2
            iNUM_FAM     = _idx(['num_fam'])      or 3
            iDESC_FAM    = _idx(['desc_fam'])     or 4
            # col 7 "Num_item" é o seq. interno — NÃO usar como codigo_simpas
            iNOME_BA     = _idx(['nome_ba'])      or 8
            iNOME_MC     = _idx(['nome_mc', 'nome_mod']) or 9
            iDESC        = _idx(['descricao'])    or 10
            iUNID        = _idx(['unid'])         or 11
            iSITUACAO    = _idx(['situac'])       or 13
            iSUST        = _idx(['item_sust', 'sust'])    or 15
            iLUXO        = _idx(['item_lux', 'luxo'])     or 16
            iCLASS       = _idx(['classifica', 'classif']) or 18
            iDATA_REF    = _idx(['data_ultima_rmrs', 'data_rmrs']) or 19
            iNR_LICIT    = _idx(['nr_licit', 'num_licit', 'n_licit', 'licit']) or 22
            iVALOR_REF   = _idx(['valor_refe', 'valor_ref']) or 24
        else:
            # Formato ComprasNet — código completo está na coluna 1
            iCOD_SIMPAS = _idx(['código item', 'codigo item', 'cod_item']) or 1
            iNOME_BA    = _idx(['nome básico', 'nome basico', 'nome_ba'])  or 2
            iNOME_MC    = _idx(['nome modificador', 'nome_mc'])            or 3
            iDESC       = _idx(['descrição padrão', 'descricao padrao'])   or 4
            iSITUACAO   = _idx(['situação', 'situacao'])                   or 7
            iUNID       = _idx(['unidade', 'um', 'unid'])                  or 8
            iCOD_GRUP   = iDESC_GRUP = iNUM_FAM = iDESC_FAM = None
            iSUST = iLUXO = iCLASS = iDATA_REF = iNR_LICIT = iVALOR_REF = None

        # ── helpers ───────────────────────────────────────────────────────────
        def col(row, i, default=''):
            return row[i].strip() if i is not None and i < len(row) else default

        def parse_bool_sn(v):
            return v.strip().upper() in ('S', 'SIM', 'YES', 'TRUE', '1')

        def parse_classificacao(v):
            v = v.lower()
            if 'consumo' in v:   return 'consumo'
            if 'permanente' in v: return 'permanente'
            if 'servi' in v:     return 'servico'
            return ''

        def parse_data(v):
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                try:
                    return datetime.strptime(v.strip(), fmt).date()
                except Exception:
                    pass
            return None

        def parse_decimal(v):
            v = v.strip().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try:
                return Decimal(v)
            except InvalidOperation:
                return None

        # ── pré-carregar códigos existentes ───────────────────────────────────
        codigos_existentes = set(
            ItemCatalogo.objects.exclude(codigo_simpas='')
                                .values_list('codigo_simpas', flat=True)
        )

        itens_novos      = []
        itens_existentes = []
        # hierarquia SIMPAS: {cod_grupo: {desc, familias: {num_fam: desc}}}
        grupos_vistos    = {}
        familias_plano   = {}   # desc_familia_comprasnet → {familia_simpas, count}
        linhas_invalidas = 0

        for row in reader:
            if len(row) < 3:
                linhas_invalidas += 1
                continue

            codigo_simpas = col(row, iCOD_SIMPAS)   # coluna A = código completo XX.XX.XX.XXXXXXXX-X
            nome_basico   = col(row, iNOME_BA)

            if not codigo_simpas or not nome_basico:
                linhas_invalidas += 1
                continue

            nome_mod    = col(row, iNOME_MC)
            desc_padrao = col(row, iDESC)
            situacao    = col(row, iSITUACAO)
            um          = col(row, iUNID) or 'UN'

            ativo = situacao.lower() not in ('inativo', 'cancelado', 'suspenso', 'inativa')

            nome = nome_basico
            if nome_mod and nome_mod.upper() != nome_basico.upper():
                nome = f'{nome_basico} {nome_mod}'.strip()
            nome = nome[:300]

            familia_simpas = ItemCatalogo.extrair_familia(codigo_simpas)

            # dados exclusivos do SIMPAS
            item_sust  = parse_bool_sn(col(row, iSUST))    if iSUST      else False
            item_luxo  = parse_bool_sn(col(row, iLUXO))    if iLUXO      else False
            classif    = parse_classificacao(col(row, iCLASS)) if iCLASS  else ''
            data_ref   = parse_data(col(row, iDATA_REF))   if iDATA_REF  else None
            nr_licit   = col(row, iNR_LICIT)               if iNR_LICIT   else ''
            valor_ref  = parse_decimal(col(row, iVALOR_REF)) if iVALOR_REF else None

            # hierarquia SIMPAS
            if FORMATO_SIMPAS and iCOD_GRUP is not None:
                cod_grupo  = col(row, iCOD_GRUP)
                desc_grupo = col(row, iDESC_GRUP) if iDESC_GRUP else ''
                num_fam    = col(row, iNUM_FAM)   if iNUM_FAM   else ''
                desc_fam   = col(row, iDESC_FAM)  if iDESC_FAM  else ''
                if cod_grupo and cod_grupo not in grupos_vistos:
                    grupos_vistos[cod_grupo] = {'desc': desc_grupo, 'familias': {}}
                if cod_grupo and num_fam and num_fam not in grupos_vistos[cod_grupo]['familias']:
                    grupos_vistos[cod_grupo]['familias'][num_fam] = desc_fam
                desc_familia_chave = f'{cod_grupo}_{num_fam}'
            else:
                desc_familia_chave = familia_simpas
                if desc_familia_chave not in familias_plano:
                    familias_plano[desc_familia_chave] = {'familia_simpas': familia_simpas, 'count': 0}
                familias_plano[desc_familia_chave]['count'] += 1

            if codigo_simpas in codigos_existentes:
                itens_existentes.append({'codigo_simpas': codigo_simpas, 'nome': nome[:80]})
            else:
                codigos_existentes.add(codigo_simpas)
                itens_novos.append({
                    'codigo_simpas':    codigo_simpas,
                    'familia':          familia_simpas,
                    'nome':             nome,
                    'descricao':        desc_padrao[:2000],
                    'unidade_medida':   um,
                    'ativo':            ativo,
                    'item_sustentavel': item_sust,
                    'item_luxo':        item_luxo,
                    'classificacao_tipo': classif,
                    'valor_referencia': valor_ref,
                    'data_referencia':  data_ref,
                    'num_licitacao_ref': nr_licit[:100],
                    # para categorização automática SIMPAS
                    '_cod_grupo': col(row, iCOD_GRUP) if iCOD_GRUP else '',
                    '_num_fam':   col(row, iNUM_FAM)  if iNUM_FAM  else '',
                    # para mapeamento manual ComprasNet
                    '_desc_familia': desc_familia_chave,
                })

        # ── dry-run ───────────────────────────────────────────────────────────
        if dry_run:
            if FORMATO_SIMPAS:
                familias_resp = []
                for cod_g, g in sorted(grupos_vistos.items()):
                    for num_f, desc_f in sorted(g['familias'].items()):
                        count = sum(
                            1 for it in itens_novos
                            if it['_cod_grupo'] == cod_g and it['_num_fam'] == num_f
                        )
                        familias_resp.append({
                            'desc':         f"{g['desc']} › {desc_f}",
                            'cod_grupo':    cod_g,
                            'desc_grupo':   g['desc'],
                            'num_fam':      num_f,
                            'desc_fam':     desc_f,
                            'familia_simpas': f'{cod_g}.{num_f}',
                            'count':        count,
                        })
            else:
                familias_resp = sorted(
                    [{'desc': k, 'familia_simpas': v['familia_simpas'], 'count': v['count']}
                     for k, v in familias_plano.items()],
                    key=lambda x: x['desc']
                )
            sustentaveis = sum(1 for it in itens_novos if it['item_sustentavel'])
            com_luxo     = sum(1 for it in itens_novos if it['item_luxo'])
            com_preco    = sum(1 for it in itens_novos if it['valor_referencia'])
            return Response({
                'dry_run':      True,
                'formato':      'SIMPAS' if FORMATO_SIMPAS else 'ComprasNet',
                'total_lidos':  len(itens_novos) + len(itens_existentes),
                'novos':        len(itens_novos),
                'duplicados':   len(itens_existentes),
                'invalidos':    linhas_invalidas,
                'sustentaveis': sustentaveis,
                'com_luxo':     com_luxo,
                'com_preco':    com_preco,
                'familias':     familias_resp,
                'preview_novos':      itens_novos[:20],
                'preview_duplicados': itens_existentes[:10],
            })

        # ── import real ───────────────────────────────────────────────────────
        cat_cache = {}

        def _get_ou_criar_categoria(cod_grupo, desc_grupo, num_fam, desc_fam):
            chave = f'{cod_grupo}_{num_fam}'
            if chave in cat_cache:
                return cat_cache[chave]
            # nível raiz = grupo
            grupo_cat, _ = CategoriaItem.objects.get_or_create(
                codigo=str(cod_grupo),
                pai=None,
                defaults={'nome': desc_grupo or f'Grupo {cod_grupo}'},
            )
            # nível filho = família
            fam_cat, _ = CategoriaItem.objects.get_or_create(
                codigo=str(num_fam),
                pai=grupo_cat,
                defaults={'nome': desc_fam or f'Família {num_fam}'},
            )
            cat_cache[chave] = fam_cat
            return fam_cat

        def _get_categoria_manual(desc_fam_chave):
            if desc_fam_chave in cat_cache:
                return cat_cache[desc_fam_chave]
            cat_id = mapeamento_manual.get(desc_fam_chave)
            cat = None
            if cat_id:
                try:
                    cat = CategoriaItem.objects.get(id=int(cat_id))
                except CategoriaItem.DoesNotExist:
                    pass
            cat_cache[desc_fam_chave] = cat
            return cat

        with transaction.atomic():
            ultimo = ItemCatalogo.objects.count()
            objs = []
            for i, it in enumerate(itens_novos):
                if FORMATO_SIMPAS and it['_cod_grupo']:
                    # buscar grupo/família do grupos_vistos
                    g_info = grupos_vistos.get(it['_cod_grupo'], {})
                    desc_g = g_info.get('desc', '')
                    desc_f = g_info.get('familias', {}).get(it['_num_fam'], '')
                    cat = _get_ou_criar_categoria(
                        it['_cod_grupo'], desc_g, it['_num_fam'], desc_f
                    )
                else:
                    cat = _get_categoria_manual(it['_desc_familia'])

                objs.append(ItemCatalogo(
                    codigo_interno    = f'WBR-{ultimo + i + 1:05d}',
                    codigo_simpas     = it['codigo_simpas'],
                    familia           = it['familia'],
                    categoria         = cat,
                    nome              = it['nome'],
                    descricao         = it['descricao'],
                    unidade_medida    = it['unidade_medida'],
                    ativo             = it['ativo'],
                    item_sustentavel  = it['item_sustentavel'],
                    item_luxo         = it['item_luxo'],
                    classificacao_tipo = it['classificacao_tipo'],
                    valor_referencia  = it['valor_referencia'],
                    data_referencia   = it['data_referencia'],
                    num_licitacao_ref = it['num_licitacao_ref'],
                ))
            ItemCatalogo.objects.bulk_create(objs, ignore_conflicts=True)

        return Response({
            'dry_run':              False,
            'criados':              len(objs),
            'duplicados_ignorados': len(itens_existentes),
            'categorias_criadas':   len(cat_cache),
        })


class SecaoArtefatoSerializer(drf_serializers.ModelSerializer):
    tipo_display = drf_serializers.CharField(source='get_tipo_display', read_only=True)

    class Meta:
        model  = SecaoArtefato
        fields = ['id', 'tipo', 'tipo_display', 'codigo', 'titulo', 'descricao',
                  'ordem', 'ativo', 'obrigatorio', 'aplica_modalidades', 'aplica_tipo_objeto']


class SecaoArtefatoViewSet(viewsets.ModelViewSet):
    serializer_class   = SecaoArtefatoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['titulo', 'codigo']
    ordering_fields    = ['tipo', 'ordem']
    ordering           = ['tipo', 'ordem']

    def get_queryset(self):
        # Para operações de detalhe (retrieve/update/delete), retorna todas — inclusive inativas
        # Para listagem, aplica filtro de ativo conforme parâmetro
        if self.action in ('retrieve', 'update', 'partial_update', 'destroy'):
            return SecaoArtefato.objects.all()

        qs   = SecaoArtefato.objects.all()
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        if self.request.query_params.get('inativas') != 'true':
            qs = qs.filter(ativo=True)
        return qs

    def _check_perm(self, request):
        if getattr(request, 'papel', None) != 'admin':
            raise PermissionDenied('Apenas administradores podem gerenciar seções de artefatos.')

    def perform_create(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_update(self, serializer):
        self._check_perm(self.request)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_perm(self.request)
        instance.ativo = False
        instance.save()


class VerificarDocumentoView(APIView):
    """
    Endpoint público de verificação de autenticidade de documentos gerados pelo WEBBER.
    GET /api/verificar/<hash_code>/
    Retorna os metadados do documento identificado pelo código de verificação.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, hash_code):
        from exportacao.pdf_utils import _hash_documento, _dados_hash_usuario
        from modulo_demanda.models import DFD
        from modulo_etp.models import ETP
        from modulo_tr.models import TR
        from modulo_orcamento.models import IndicacaoOrcamentaria

        hash_code = hash_code.upper()

        # Tenta encontrar o documento cujo hash coincide
        for Model, tipo, campos_fn in [
            (DFD, 'DFD', lambda o: {
                'tipo': 'DFD', 'id': str(o.pk), 'sei': o.numero_sei,
                'valor': str(o.valor_estimado), **_dados_hash_usuario(o),
            }),
            (ETP, 'ETP', lambda o: {
                'tipo': 'ETP', 'id': str(o.pk), 'sei': o.numero_sei,
                'valor': str(o.estimativa_valor), **_dados_hash_usuario(o),
            }),
            (TR, 'TR', lambda o: {
                'tipo': 'TR', 'id': str(o.pk), 'sei': o.numero_sei,
                'valor': str(o.estimativa_valor), **_dados_hash_usuario(o),
            }),
            (IndicacaoOrcamentaria, 'DOD', lambda o: {
                'tipo': 'DOD', 'id': str(o.pk), 'numero': o.numero,
                'exercicio': str(o.exercicio_fiscal), 'valor': str(o.valor_total),
                **_dados_hash_usuario(o, aprovador=o.ordenador),
            }),
        ]:
            for obj in Model.objects.select_related('created_by', 'org_id').all():
                try:
                    if _hash_documento(campos_fn(obj)) == hash_code:
                        criador = obj.created_by
                        return Response({
                            'valido':      True,
                            'tipo':        tipo,
                            'id':          obj.pk,
                            'orgao':       obj.org_id.nome if obj.org_id else '—',
                            'criador':     criador.get_full_name() or criador.username if criador else '—',
                            'criado_em':   obj.created_at.strftime('%d/%m/%Y %H:%M') if obj.created_at else '—',
                            'status':      getattr(obj, 'status', '—'),
                            'hash':        hash_code,
                            'mensagem':    'Documento autêntico gerado pelo Sistema WEBBER.',
                        })
                except Exception:
                    continue

        return Response({
            'valido':   False,
            'hash':     hash_code,
            'mensagem': 'Código de verificação não encontrado. O documento pode ter sido adulterado ou não pertence a este sistema.',
        }, status=status.HTTP_404_NOT_FOUND)
