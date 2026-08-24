from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    InstrumentoFinanceiroViewSet,
    ComposicaoConselhoGestorViewSet,
    ReuniaoConselhoGestorViewSet,
    PlanoAplicacaoViewSet,
    MetaEspecificaViewSet,
    GrupoConsolidacaoItemViewSet,
    ItemPlanoAplicacaoViewSet,
    IndicadoresExecucaoFespView,
    RelatorioItensPlanoAplicacaoView,
)

router = DefaultRouter()
router.register(r'instrumento', InstrumentoFinanceiroViewSet, basename='instrumento-financeiro')
router.register(r'composicao-conselho', ComposicaoConselhoGestorViewSet, basename='composicao-conselho-fesp')
router.register(r'reuniao-conselho', ReuniaoConselhoGestorViewSet, basename='reuniao-conselho-fesp')
router.register(r'plano-aplicacao', PlanoAplicacaoViewSet, basename='plano-aplicacao-fesp')
router.register(r'meta-especifica', MetaEspecificaViewSet, basename='meta-especifica-fesp')
router.register(r'grupo-consolidacao', GrupoConsolidacaoItemViewSet, basename='grupo-consolidacao-fesp')
router.register(r'item-plano', ItemPlanoAplicacaoViewSet, basename='item-plano-aplicacao-fesp')

urlpatterns = router.urls + [
    path('indicadores/execucao/', IndicadoresExecucaoFespView.as_view(), name='fesp-indicadores-execucao'),
    path('relatorio-itens/', RelatorioItensPlanoAplicacaoView.as_view(), name='fesp-relatorio-itens'),
]
