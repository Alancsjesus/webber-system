from rest_framework.routers import DefaultRouter
from .views import TRViewSet

router = DefaultRouter()
router.register(r'tr', TRViewSet, basename='tr')
urlpatterns = router.urls
