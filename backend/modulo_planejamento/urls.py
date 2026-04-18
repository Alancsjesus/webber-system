from rest_framework.routers import DefaultRouter
from .views import NecessidadeViewSet, PlanoOrcamentarioViewSet

router = DefaultRouter()
router.register(r'necessidade',      NecessidadeViewSet,       basename='necessidade')
router.register(r'planoorcamentario', PlanoOrcamentarioViewSet, basename='planoorcamentario')

urlpatterns = router.urls
