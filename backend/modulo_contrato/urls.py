from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ContratoViewSet, NotificacaoViewSet, PainelContratosView

router = DefaultRouter()
router.register(r'contrato', ContratoViewSet, basename='contrato')
router.register(r'notificacao', NotificacaoViewSet, basename='notificacao')

urlpatterns = router.urls + [
    path('painel/', PainelContratosView.as_view(), name='painel-contratos'),
]
