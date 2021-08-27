from django.urls import include, re_path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    re_path(r'^', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
