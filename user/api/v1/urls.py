from django.urls import path
from user.api.v1.views import ManageUserView, CreateUserView

urlpatterns = [
    path("me/", ManageUserView.as_view(), name="user_me"),
    path("register/", CreateUserView.as_view(), name="user_register"),
]
