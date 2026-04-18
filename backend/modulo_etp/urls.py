from rest_framework.routers import DefaultRouter
from .views import ETPViewSet

router = DefaultRouter()
router.register(r'etp', ETPViewSet, basename='etp')

urlpatterns = router.urls
