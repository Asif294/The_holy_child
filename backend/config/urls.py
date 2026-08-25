from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

admin.site.site_header = "The Holy Child Pre-Cadet & High School"
admin.site.site_title = "Holy Child Administration"
admin.site.index_title = "School management"

# API v1 — every resource lives under /api/v1/ and is namespaced for versioning.
api_v1_patterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.principal.urls")),
    path("", include("apps.teachers.urls")),
    path("", include("apps.students.urls")),
    path("", include("apps.classes.urls")),
    path("", include("apps.subjects.urls")),
    path("", include("apps.attendance.urls")),
    path("", include("apps.fees.urls")),
    path("", include("apps.exams.urls")),
    path("", include("apps.website.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1_patterns, "v1"), namespace="v1")),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
