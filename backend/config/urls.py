from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.serializers import WebberTokenObtainPairView
from modulo_demanda.views import DFDViewSet
from modulo_planejamento.views import NecessidadeViewSet, PlanoOrcamentarioViewSet
from core.views import (
    DashboardStatsView, OrgaoViewSet, UnidadeViewSet,
    UserManagementViewSet, PainelOrgaoPaiView, ParametroSistemaViewSet,
    VerificarDocumentoView, AreaAtuacaoViewSet, UserListView,
    SecaoArtefatoViewSet,
)
from core.views_indicadores import IndicadoresOrcamentoView, IndicadoresDevolucoesView

router = DefaultRouter()
router.register(r'demanda/dfd', DFDViewSet, basename='dfd')
router.register(r'core/parametros', ParametroSistemaViewSet, basename='parametro')
router.register(r'planejamento/necessidade',       NecessidadeViewSet,       basename='necessidade')
router.register(r'planejamento/planoorcamentario', PlanoOrcamentarioViewSet, basename='planoorcamentario')
router.register(r'core/orgaos',    OrgaoViewSet,           basename='orgao')
router.register(r'core/unidades',  UnidadeViewSet,         basename='unidade')
router.register(r'core/usuarios',  UserManagementViewSet,  basename='usuario')
router.register(r'core/areas',     AreaAtuacaoViewSet,      basename='area-atuacao')
router.register(r'core/secoes',    SecaoArtefatoViewSet,    basename='secao-artefato')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', WebberTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('api/indicadores/orcamento/',   IndicadoresOrcamentoView.as_view(),   name='indicadores-orcamento'),
    path('api/indicadores/devolucoes/',  IndicadoresDevolucoesView.as_view(),  name='indicadores-devolucoes'),
    path('api/painel/', PainelOrgaoPaiView.as_view(), name='painel-orgao-pai'),
    path('api/verificar/<str:hash_code>/', VerificarDocumentoView.as_view(), name='verificar-documento'),
    path('api/core/users-list/', UserListView.as_view(), name='user-list'),
    path('api/', include(router.urls)),
    path('api/orcamento/', include('modulo_orcamento.urls')),
    path('api/etp/',       include('modulo_etp.urls')),
    path('api/tr/',        include('modulo_tr.urls')),
    path('api/pesquisa/',   include('modulo_mapa_precos.urls')),
    path('api/contratos/',  include('modulo_contrato.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)