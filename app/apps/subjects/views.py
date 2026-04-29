from rest_framework import viewsets

from .models import Relationship, Subject
from .serializers import RelationshipSerializer, SubjectSerializer


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subject.objects.all().order_by("full_name")
    serializer_class = SubjectSerializer


class RelationshipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Relationship.objects.select_related("from_subject", "to_subject")
        .all()
        .order_by("-created_at")
    )
    serializer_class = RelationshipSerializer
