from rest_framework.routers import DefaultRouter
from .views import ContratoViewSet

router = DefaultRouter()
router.register(r'contrato', ContratoViewSet, basename='contrato')

urlpatterns = router.urls
