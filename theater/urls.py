from django.urls import path
from theater.views import (
    HomePageListView
)

app_name = "theater"


urlpatterns = [
    path("", HomePageListView.as_view(), name="home"),
]
