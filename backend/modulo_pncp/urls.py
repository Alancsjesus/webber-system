from rest_framework.routers import DefaultRouter
from .views import PNCPImportacaoViewSet

router = DefaultRouter()
router.register(r'importacoes', PNCPImportacaoViewSet, basename='pncp-importacao')

urlpatterns = router.urls
