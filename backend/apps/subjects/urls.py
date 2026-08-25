from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.subjects.views import ClassSubjectViewSet, SubjectViewSet

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("class-subjects", ClassSubjectViewSet, basename="class-subject")

urlpatterns = [path("", include(router.urls))]
