from rest_framework import serializers

from .models import Relationship, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "full_name",
            "alias",
            "tax_id",
            "national_id",
            "birth_date",
            "under_investigation",
            "notes",
        ]


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relationship
        fields = [
            "id",
            "from_subject",
            "to_subject",
            "relationship_type",
            "strength",
            "created_at",
        ]
