from typing import Any
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.http import HttpRequest, HttpResponse, Http404

from user.forms import UserRegistrationForm


class UserRegistrationView(generic.CreateView):
    form_class = UserRegistrationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("user:login")


def logout_post_only(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
    if request.method != "POST":
        raise Http404
    return auth_views.LogoutView.as_view(next_page="theater:home")(
        request, *args, **kwargs
    )
