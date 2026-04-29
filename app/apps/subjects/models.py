from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Subject(models.Model):
    nome_completo = models.CharField(max_length=255)
    vulgo = models.CharField(max_length=120, blank=True)
    cpf_cnpj = models.CharField(max_length=18, unique=True)
    rg = models.CharField(max_length=20, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    sob_investigacao = models.BooleanField(default=False)
    observacoes = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.nome_completo} ({self.cpf_cnpj})"


class Relationship(models.Model):
    class RelationshipType(models.TextChoices):
        FAMILIAR = "Familiar", "Familiar"
        SOCIO = "Socio", "Sócio"
        CRIMINAL = "Criminal", "Criminal"
        FINANCEIRO = "Financeiro", "Financeiro"
        OUTRO = "Outro", "Outro"

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
    tipo = models.CharField(max_length=20, choices=RelationshipType.choices)
    forca = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return (
            f"{self.from_subject.nome_completo} -> "
            f"{self.to_subject.nome_completo} ({self.tipo})"
        )
