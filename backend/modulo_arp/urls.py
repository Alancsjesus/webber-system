from rest_framework.routers import DefaultRouter

from .views import AtaViewSet

router = DefaultRouter()
router.register(r'', AtaViewSet, basename='ata')

urlpatterns = router.urls
