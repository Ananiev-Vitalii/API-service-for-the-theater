from django.urls import path
from theater.views import performance_info

app_name = "api"

urlpatterns = [
    path("performance-info/<int:pk>/", performance_info, name="performance-info"),
]
