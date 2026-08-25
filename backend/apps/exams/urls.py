from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.exams.views import ExamScheduleViewSet, ExamTypeViewSet, ExamViewSet, ResultViewSet

router = DefaultRouter()
router.register("exams", ExamViewSet, basename="exam")
router.register("exam-types", ExamTypeViewSet, basename="exam-type")
router.register("exam-schedules", ExamScheduleViewSet, basename="exam-schedule")
router.register("results", ResultViewSet, basename="result")

urlpatterns = [path("", include(router.urls))]
