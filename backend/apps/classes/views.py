from apps.classes.models import AcademicSession, SchoolClass, Section
from apps.classes.serializers import AcademicSessionSerializer, SchoolClassSerializer, SectionSerializer
from apps.common.schema import crud_schema
from apps.common.viewsets import RBACModelViewSet


@crud_schema(tag="Classes", resource="academic session", plural="academic sessions",
             serializer=AcademicSessionSerializer)
class AcademicSessionViewSet(RBACModelViewSet):
    """
    School years. Marking a session current automatically clears the flag on the
    previous one, so "the current session" is always unambiguous.
    """

    permission_module = "class"
    serializer_class = AcademicSessionSerializer
    queryset = AcademicSession.objects.filter(is_deleted=False)
    search_fields = ["name"]
    ordering_fields = ["start_date", "name"]
    filterset_fields = ["is_current", "is_active"]


@crud_schema(tag="Classes", resource="class", plural="classes", serializer=SchoolClassSerializer)
class SchoolClassViewSet(RBACModelViewSet):
    """Grade levels offered by the school, Play Group through Class 10."""

    permission_module = "class"
    serializer_class = SchoolClassSerializer
    search_fields = ["name", "name_bn", "code"]
    ordering_fields = ["order", "name", "created_at"]
    ordering = ["order"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        return SchoolClass.objects.filter(is_deleted=False).prefetch_related("sections__class_teacher")


@crud_schema(tag="Classes", resource="section", serializer=SectionSerializer)
class SectionViewSet(RBACModelViewSet):
    """Sections within a class, each optionally led by a class teacher."""

    permission_module = "class"
    serializer_class = SectionSerializer
    search_fields = ["name", "school_class__name", "room_number"]
    ordering_fields = ["name", "created_at"]
    filterset_fields = ["school_class", "class_teacher", "is_active"]

    def get_queryset(self):
        return Section.objects.filter(is_deleted=False).select_related("school_class", "class_teacher")
