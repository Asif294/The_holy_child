from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.dashboard.views import (
    DashboardViewSet,
    SchoolEventViewSet,
    SchoolInfoAPIView,
    SchoolProfileAPIView,
)

router = DefaultRouter()
router.register("dashboard", DashboardViewSet, basename="dashboard")
router.register("events", SchoolEventViewSet, basename="event")

urlpatterns = [
    path("school/info/", SchoolInfoAPIView.as_view(), name="school-info"),
    path("school/profile/", SchoolProfileAPIView.as_view(), name="school-profile"),
    path("", include(router.urls)),
]
