from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.attendance.views import StudentAttendanceViewSet, TeacherAttendanceViewSet

router = DefaultRouter()
router.register("attendance", StudentAttendanceViewSet, basename="attendance")
router.register("teacher-attendance", TeacherAttendanceViewSet, basename="teacher-attendance")

urlpatterns = [path("", include(router.urls))]
