from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.principal.views import (
    ApprovalRequestViewSet,
    NoticeViewSet,
    PrincipalViewSet,
    PublicAdministrationAPIView,
    PublicPrincipalViewSet,
)

router = DefaultRouter()
router.register("principals", PrincipalViewSet, basename="principal")
router.register("notices", NoticeViewSet, basename="notice")
router.register("approval-requests", ApprovalRequestViewSet, basename="approval-request")
router.register("public/principal", PublicPrincipalViewSet, basename="public-principal")

urlpatterns = [
    path("public/administration/", PublicAdministrationAPIView.as_view(), name="public-administration"),
    path("", include(router.urls)),
]
