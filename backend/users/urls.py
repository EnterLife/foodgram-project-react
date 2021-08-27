from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FollowViewSet

router = DefaultRouter()
router.register('users', FollowViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
