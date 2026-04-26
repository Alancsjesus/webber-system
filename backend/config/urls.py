from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from core.serializers import WebberTokenObtainPairView
from modulo_demanda.views import DFDViewSet
from modulo_planejamento.views import NecessidadeViewSet, PlanoOrcamentarioViewSet
from core.views import (
    DashboardStatsView, OrgaoViewSet, UnidadeViewSet,
    UserManagementViewSet, PainelOrgaoPaiView, ParametroSistemaViewSet,
    VerificarDocumentoView,
)

router = DefaultRouter()
router.register(r'demanda/dfd', DFDViewSet, basename='dfd')
router.register(r'core/parametros', ParametroSistemaViewSet, basename='parametro')
router.register(r'planejamento/necessidade',       NecessidadeViewSet,       basename='necessidade')
router.register(r'planejamento/planoorcamentario', PlanoOrcamentarioViewSet, basename='planoorcamentario')
router.register(r'core/orgaos',    OrgaoViewSet,           basename='orgao')
router.register(r'core/unidades',  UnidadeViewSet,         basename='unidade')
router.register(r'core/usuarios',  UserManagementViewSet,  basename='usuario')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', WebberTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/dashboard/stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('api/painel/', PainelOrgaoPaiView.as_view(), name='painel-orgao-pai'),
    path('api/verificar/<str:hash_code>/', VerificarDocumentoView.as_view(), name='verificar-documento'),
    path('api/', include(router.urls)),
    path('api/orcamento/', include('modulo_orcamento.urls')),
    path('api/etp/',      include('modulo_etp.urls')),
    path('api/tr/',       include('modulo_tr.urls')),
]