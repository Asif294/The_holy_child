"""
Two faces on the same content.

Every model in this app is read by anonymous visitors and written by staff, so
each one gets a pair of views: an ``AllowAny`` read-only endpoint under
``/public/`` that exposes only presentation fields, and a permission-gated
:class:`RBACModelViewSet` that owns create, update and delete. Nothing shares a
serializer between the two — the public shape is a deliberate subset.
"""
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import HasActionPermission
from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.website.models import AboutSection, Achievement, HeroSlide, SuccessfulStudent
from apps.website.serializers import (
    AboutPublicSerializer,
    AboutSectionSerializer,
    AchievementSerializer,
    HeroSlidePublicSerializer,
    HeroSlideSerializer,
    SuccessfulStudentPublicSerializer,
    SuccessfulStudentSerializer,
)

# --------------------------------------------------------------------------- #
# Management
# --------------------------------------------------------------------------- #


@crud_schema(
    tag="Website",
    resource="hero slide",
    plural="hero slides",
    serializer=HeroSlideSerializer,
    descriptions={
        "list": "The hero slider's images, in display order. Requires the `content.view` permission.",
        "create": (
            "Adds an image to the hero slider. Send `multipart/form-data` with the `image` file. "
            "Requires the `content.create` permission."
        ),
    },
)
class HeroSlideViewSet(RBACModelViewSet):
    """The landing page's hero slider."""

    permission_module = "content"
    serializer_class = HeroSlideSerializer
    queryset = HeroSlide.objects.filter(is_deleted=False)
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ["title", "subtitle", "caption"]
    ordering_fields = ["order", "created_at"]
    ordering = ["order"]
    filterset_fields = ["is_active"]


@crud_schema(
    tag="Website",
    resource="achievement",
    serializer=AchievementSerializer,
    descriptions={"list": "School achievements shown beside the About section."},
)
class AchievementViewSet(RBACModelViewSet):
    """Milestones displayed with the About section."""

    permission_module = "content"
    serializer_class = AchievementSerializer
    queryset = Achievement.objects.filter(is_deleted=False)
    search_fields = ["title", "description", "year"]
    ordering_fields = ["order", "year", "title"]
    ordering = ["order"]
    filterset_fields = ["year", "is_active"]


@extend_schema(tags=["Website"])
class AboutSectionAPIView(RetrieveUpdateAPIView):
    """
    The About-the-School copy.

    A singleton, so it is a detail endpoint rather than a collection:
    ``content.view`` to read, ``content.update`` to change, resolved from the
    request method by :class:`HasActionPermission`.
    """

    serializer_class = AboutSectionSerializer
    permission_classes = [IsAuthenticated, HasActionPermission]
    permission_module = "content"
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_object(self):
        return AboutSection.load()

    @extend_schema(summary="Read the About section", responses={200: AboutSectionSerializer, **PROTECTED_RESPONSES})
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Replace the About section",
        description="Requires `content.update`. Send multipart to replace the image.",
        responses={200: AboutSectionSerializer, **PROTECTED_RESPONSES},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update the About section",
        responses={200: AboutSectionSerializer, **PROTECTED_RESPONSES},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@crud_schema(
    tag="Website",
    resource="successful student",
    plural="successful students",
    serializer=SuccessfulStudentSerializer,
    descriptions={
        "list": (
            "The results honour board. Filter by `academic_year`, `exam_name` or `is_featured`. "
            "Requires the `achiever.view` permission."
        ),
        "create": (
            "Adds a student to the honour board. Send `multipart/form-data` to include a photo. "
            "Requires the `achiever.create` permission."
        ),
    },
)
class SuccessfulStudentViewSet(RBACModelViewSet):
    """The publicly celebrated results board."""

    permission_module = "achiever"
    permission_map = {"years": "achiever.view"}
    serializer_class = SuccessfulStudentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ["full_name", "student_class", "result", "achievement", "exam_name"]
    ordering_fields = ["academic_year", "full_name", "order", "gpa"]
    ordering = ["-academic_year", "-is_featured", "order", "full_name"]
    filterset_fields = ["academic_year", "exam_name", "is_featured", "is_active"]

    def get_queryset(self):
        return SuccessfulStudent.objects.filter(is_deleted=False).select_related("student")


# --------------------------------------------------------------------------- #
# Public
# --------------------------------------------------------------------------- #
class PublicAPIView(APIView):
    """Base for the anonymous endpoints: no authentication, no permission codes."""

    permission_classes = [AllowAny]
    authentication_classes = []


@extend_schema(
    tags=["Public site"],
    summary="Hero slider images",
    description=(
        "Unauthenticated endpoint feeding the landing page's hero slider. "
        "Returns active slides in display order; an empty list is a valid answer "
        "and the page falls back to its built-in banner."
    ),
    responses={200: HeroSlidePublicSerializer(many=True)},
)
class PublicHeroSlideAPIView(PublicAPIView):
    def get(self, request):
        queryset = HeroSlide.objects.filter(is_deleted=False, is_active=True).order_by("order", "-created_at")
        return Response(HeroSlidePublicSerializer(queryset, many=True, context={"request": request}).data)


@extend_schema(
    tags=["Public site"],
    summary="About the school",
    description="Unauthenticated endpoint returning the school's story, mission, vision and achievements.",
    responses={200: AboutPublicSerializer},
)
class PublicAboutAPIView(PublicAPIView):
    def get(self, request):
        about = AboutSection.load()
        return Response(AboutPublicSerializer(about, context={"request": request}).data)


@extend_schema(
    tags=["Public site"],
    summary="Successful students",
    description=(
        "Unauthenticated honour board. Pass `?year=2025` to filter to one academic "
        "year; omit it for every year, newest first."
    ),
    parameters=[OpenApiParameter("year", str, description="Academic year to filter by, e.g. `2025`.")],
    responses={200: SuccessfulStudentPublicSerializer(many=True)},
)
class PublicSuccessfulStudentAPIView(PublicAPIView):
    def get(self, request):
        queryset = SuccessfulStudent.objects.filter(is_deleted=False, is_active=True)
        year = (request.query_params.get("year") or "").strip()
        if year and year.lower() != "all":
            queryset = queryset.filter(academic_year=year)
        return Response(
            SuccessfulStudentPublicSerializer(queryset, many=True, context={"request": request}).data
        )


@extend_schema(
    tags=["Public site"],
    summary="Academic years on the honour board",
    description="The distinct years the public results board holds, newest first — powers the year filter.",
    responses={200: OpenApiResponse(description="A list of year strings.")},
)
class PublicAchievementYearsAPIView(PublicAPIView):
    def get(self, request):
        years = (
            SuccessfulStudent.objects.filter(is_deleted=False, is_active=True)
            .values_list("academic_year", flat=True)
            .distinct()
        )
        return Response(sorted({year for year in years if year}, reverse=True))
