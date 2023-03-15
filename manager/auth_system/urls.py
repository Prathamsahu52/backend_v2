from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.UserRegister.as_view(), name="register"),
    path("login/", views.UserLogin.as_view(), name="login"),
    path("logout/", views.UserLogout.as_view(), name="logout"),
    path("user/", views.UserView.as_view(), name="user"),
    path("password-reset/", views.PasswordReset.as_view(), name="password-reset"),
    path("password-reset/<str:encoded_pk>/<str:token>/", views.ResetPasswordAPI.as_view(), name="reset-password"),
]
