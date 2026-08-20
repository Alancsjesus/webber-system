from rest_framework.routers import DefaultRouter
from .views import (
    AcaoOrcamentariaViewSet,
    ElementoDespesaViewSet,
    NaturezaDespesaViewSet,
    FonteRecursoViewSet,
    DotacaoOrcamentariaViewSet,
    IndicacaoOrcamentariaViewSet,
    TipoAcaoOrcamentariaViewSet,
    TipoFonteRecursoViewSet,
)

router = DefaultRouter()
router.register(r'acao', AcaoOrcamentariaViewSet, basename='acao-orcamentaria')
router.register(r'elemento-despesa', ElementoDespesaViewSet, basename='elemento-despesa')
router.register(r'natureza-despesa', NaturezaDespesaViewSet, basename='natureza-despesa')
router.register(r'fonte-recurso', FonteRecursoViewSet, basename='fonte-recurso')
router.register(r'dotacao', DotacaoOrcamentariaViewSet, basename='dotacao-orcamentaria')
router.register(r'indicacao', IndicacaoOrcamentariaViewSet, basename='indicacao-orcamentaria')
router.register(r'tipo-acao', TipoAcaoOrcamentariaViewSet, basename='tipo-acao-orcamentaria')
router.register(r'tipo-fonte', TipoFonteRecursoViewSet, basename='tipo-fonte-recurso')

urlpatterns = router.urls
