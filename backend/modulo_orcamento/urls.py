from rest_framework.routers import DefaultRouter
from .views import (
    AcaoOrcamentariaViewSet,
    ElementoDespesaViewSet,
    FonteRecursoViewSet,
    DotacaoOrcamentariaViewSet,
)

router = DefaultRouter()
router.register(r'acao', AcaoOrcamentariaViewSet, basename='acao-orcamentaria')
router.register(r'elemento-despesa', ElementoDespesaViewSet, basename='elemento-despesa')
router.register(r'fonte-recurso', FonteRecursoViewSet, basename='fonte-recurso')
router.register(r'dotacao', DotacaoOrcamentariaViewSet, basename='dotacao-orcamentaria')

urlpatterns = router.urls
