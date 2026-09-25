from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ProcessoTramitacaoViewSet, PainelTramitacaoView, IndicadoresTramitacaoView, TemposPorAnoView

router = DefaultRouter()
router.register(r'processos', ProcessoTramitacaoViewSet, basename='processo-tramitacao')

urlpatterns = [
    path('painel/', PainelTramitacaoView.as_view(), name='painel-tramitacao'),
    path('indicadores/', IndicadoresTramitacaoView.as_view(), name='indicadores-tramitacao'),
    path('tempos-por-ano/', TemposPorAnoView.as_view(), name='tempos-por-ano'),
] + router.urls
