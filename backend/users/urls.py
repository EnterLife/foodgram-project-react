from django.urls import path, include


from .views import CustomAuthToken, Logout

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/token/login/', CustomAuthToken.as_view()),
    path('auth/token/logout/', Logout.as_view())
]
