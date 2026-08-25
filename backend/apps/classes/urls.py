from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.classes.views import AcademicSessionViewSet, SchoolClassViewSet, SectionViewSet

router = DefaultRouter()
router.register("classes", SchoolClassViewSet, basename="class")
router.register("sections", SectionViewSet, basename="section")
router.register("academic-sessions", AcademicSessionViewSet, basename="academic-session")

urlpatterns = [path("", include(router.urls))]
