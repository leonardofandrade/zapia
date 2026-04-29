from __future__ import annotations

from typing import Any

from django.db.models import Q, QuerySet

from .models import Relationship, Subject


def create_subject(data: dict[str, Any]) -> Subject:
    return Subject.objects.create(**data)


def link_subjects(
    from_id: int,
    to_id: int,
    rel_type: str,
    strength: int,
    description: str,
) -> Relationship:
    if from_id == to_id:
        raise ValueError("A subject cannot be linked to itself.")
    if not isinstance(description, str):
        raise ValueError("Relationship description must be a string.")
    normalized_description = description.strip()
    if not normalized_description:
        raise ValueError("Relationship description cannot be empty.")

    from_subject = Subject.objects.get(pk=from_id)
    to_subject = Subject.objects.get(pk=to_id)
    return Relationship.objects.create(
        from_subject=from_subject,
        to_subject=to_subject,
        relationship_type=rel_type,
        strength=strength,
    )


def get_subject_network(subject_id: int) -> QuerySet[Relationship]:
    return Relationship.objects.filter(
        Q(from_subject_id=subject_id) | Q(to_subject_id=subject_id)
    ).select_related("from_subject", "to_subject")
