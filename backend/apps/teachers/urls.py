from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.teachers.views import DepartmentViewSet, DesignationViewSet, TeacherViewSet

router = DefaultRouter()
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("designations", DesignationViewSet, basename="designation")
router.register("departments", DepartmentViewSet, basename="department")

urlpatterns = [path("", include(router.urls))]
