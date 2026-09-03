from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ProcessoTramitacaoViewSet, PainelTramitacaoView

router = DefaultRouter()
router.register(r'processos', ProcessoTramitacaoViewSet, basename='processo-tramitacao')

urlpatterns = [
    path('painel/', PainelTramitacaoView.as_view(), name='painel-tramitacao'),
] + router.urls
