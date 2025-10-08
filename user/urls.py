from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from user.views import UserRegistrationView, logout_post_only
from user.forms import (
    UserAuthenticationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)


app_name = "user"


urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(form_class=UserAuthenticationForm),
        name="login",
    ),
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("logout/", logout_post_only, name="logout"),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            form_class=CustomPasswordResetForm,
            success_url=reverse_lazy("user:password-reset-done"),
        ),
        name="password-reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password-reset-done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=CustomSetPasswordForm,
            success_url=reverse_lazy("user:password-reset-complete"),
        ),
        name="password-reset-confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password-reset-complete",
    ),
]
