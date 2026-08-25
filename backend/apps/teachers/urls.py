from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.teachers.views import (
    DepartmentViewSet,
    DesignationViewSet,
    PublicTeacherAPIView,
    TeacherViewSet,
)

router = DefaultRouter()
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("designations", DesignationViewSet, basename="designation")
router.register("departments", DepartmentViewSet, basename="department")

urlpatterns = [
    path("public/teachers/", PublicTeacherAPIView.as_view(), name="public-teachers"),
    path("", include(router.urls)),
]
