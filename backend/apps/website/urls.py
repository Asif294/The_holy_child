from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.website.views import (
    AboutSectionAPIView,
    AchievementViewSet,
    HeroSlideViewSet,
    PublicAboutAPIView,
    PublicAchievementYearsAPIView,
    PublicHeroSlideAPIView,
    PublicSuccessfulStudentAPIView,
    SuccessfulStudentViewSet,
)

router = DefaultRouter()
router.register("hero-slides", HeroSlideViewSet, basename="hero-slide")
router.register("achievements", AchievementViewSet, basename="achievement")
router.register("successful-students", SuccessfulStudentViewSet, basename="successful-student")

public_patterns = [
    path("hero-slides/", PublicHeroSlideAPIView.as_view(), name="public-hero-slides"),
    path("about/", PublicAboutAPIView.as_view(), name="public-about"),
    path("successful-students/", PublicSuccessfulStudentAPIView.as_view(), name="public-successful-students"),
    path("successful-students/years/", PublicAchievementYearsAPIView.as_view(), name="public-achievement-years"),
]

urlpatterns = [
    path("website/about/", AboutSectionAPIView.as_view(), name="website-about"),
    path("public/", include(public_patterns)),
    path("", include(router.urls)),
]
