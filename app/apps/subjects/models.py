from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Subject(models.Model):
    full_name = models.CharField(max_length=255)
    alias = models.CharField(max_length=120, blank=True)
    tax_id = models.CharField(max_length=18, unique=True)
    national_id = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    under_investigation = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "subjects_subject"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.tax_id})"


class Relationship(models.Model):
    class RelationshipType(models.TextChoices):
        FAMILY = "Family", "Family"
        BUSINESS_PARTNER = "BusinessPartner", "Business Partner"
        CRIMINAL = "Criminal", "Criminal"
        FINANCIAL = "Financial", "Financial"
        OTHER = "Other", "Other"

    from_subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    to_subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(
        max_length=20, choices=RelationshipType.choices
    )
    strength = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subjects_relationship"

    def __str__(self) -> str:
        return (
            f"{self.from_subject.full_name} -> "
            f"{self.to_subject.full_name} ({self.relationship_type})"
        )
