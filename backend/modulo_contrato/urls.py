from rest_framework.routers import DefaultRouter
from .views import ContratoViewSet, NotificacaoViewSet

router = DefaultRouter()
router.register(r'contrato', ContratoViewSet, basename='contrato')
router.register(r'notificacao', NotificacaoViewSet, basename='notificacao')

urlpatterns = router.urls
