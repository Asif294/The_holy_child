from apps.common.schema import crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.subjects.models import ClassSubject, Subject
from apps.subjects.serializers import ClassSubjectSerializer, SubjectSerializer


@crud_schema(tag="Subjects", resource="subject", serializer=SubjectSerializer)
class SubjectViewSet(RBACModelViewSet):
    """The school's subject catalogue."""

    permission_module = "subject"
    serializer_class = SubjectSerializer
    queryset = Subject.objects.filter(is_deleted=False)
    search_fields = ["name", "name_bn", "code"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]
    filterset_fields = ["category", "is_active"]


@crud_schema(tag="Subjects", resource="class subject", plural="class-subject assignments",
             serializer=ClassSubjectSerializer)
class ClassSubjectViewSet(RBACModelViewSet):
    """Which subjects a class takes, and who teaches each one."""

    permission_module = "subject"
    serializer_class = ClassSubjectSerializer
    search_fields = ["subject__name", "subject__code", "school_class__name", "teacher__full_name"]
    ordering_fields = ["created_at"]
    filterset_fields = ["school_class", "subject", "teacher", "is_active"]

    def get_queryset(self):
        return ClassSubject.objects.filter(is_deleted=False).select_related("school_class", "subject", "teacher")
