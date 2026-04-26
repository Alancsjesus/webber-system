from rest_framework.routers import DefaultRouter
from .views import MapaComparativoPrecosViewSet

router = DefaultRouter()
router.register(r'mapa', MapaComparativoPrecosViewSet, basename='mapa-precos')

urlpatterns = router.urls
