import os

from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.contrib import admin
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("theater.urls", namespace="theater")),
    path("accounts/", include("user.urls", namespace="user")),
    path("captcha/", include("captcha.urls")),
    path("ajax/", include(("theater.ajax.urls", "ajax"), namespace="ajax")),
    # API (legacy Django views)
    path("api/", include(("theater.api.urls", "api"), namespace="api")),
    # API v1 (DRF)
    path("api/v1/", include(("theater.api.v1.urls", "api_v1"), namespace="api_v1")),
    path(
        "api/v1/accounts/",
        include(("user.api.v1.urls", "user_api_v1"), namespace="user_api_v1"),
    ),
    # API v1 Auth (JWT)
    path("api/v1/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API v1 Docs: schema / swagger / redoc
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/docs/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

handler404 = "theater.views.custom_page_not_found_view"

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG is True or os.environ.get("RENDER") == "true":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
