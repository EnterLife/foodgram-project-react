from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

from .views import FollowViewSet

router = DefaultRouter()
router.register('users', FollowViewSet, basename='users')

urlpatterns = [
    re_path(r'^', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
