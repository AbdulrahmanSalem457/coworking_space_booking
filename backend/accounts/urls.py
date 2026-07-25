from django.urls import path

from .views import DecoratedTokenObtainPairView, DecoratedTokenRefreshView, MeView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", DecoratedTokenObtainPairView.as_view(), name="auth-login"),
    path("refresh/", DecoratedTokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
