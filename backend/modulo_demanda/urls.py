from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DFDViewSet

router = DefaultRouter()
router.register(r'dfd', DFDViewSet, basename='dfd')

urlpatterns = [
    path('', include(router.urls)),
]