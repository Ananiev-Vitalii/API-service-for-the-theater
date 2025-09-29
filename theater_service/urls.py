from django.conf.urls.static import static
from django.urls import path, include
from django.conf import settings
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("theater.urls", namespace="theater")),
    path("accounts/", include("user.urls", namespace="user")),
    path("ajax/", include(("theater.ajax.urls", "ajax"), namespace="ajax")),
    # API (legacy Django views)
    path("api/", include(("theater.api.urls", "api"), namespace="api")),
    # API v1 (DRF)
    path("api/v1/", include(("theater.api.v1.urls", "api_v1"), namespace="api_v1")),
    path("captcha/", include("captcha.urls")),
]

handler404 = "theater.views.custom_page_not_found_view"

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
