from django.db import models
from django.db.models import F, Q


class Court(models.Model):
    """Cancha de pádel del complejo."""

    class CourtType(models.TextChoices):
        COVERED = 'covered', 'Techada'
        UNCOVERED = 'uncovered', 'Descubierta'

    name = models.CharField('nombre', max_length=100, unique=True)
    court_type = models.CharField(
        'tipo', max_length=20, choices=CourtType.choices, default=CourtType.COVERED
    )
    description = models.TextField('descripción', blank=True)
    opening_time = models.TimeField('hora de apertura')
    closing_time = models.TimeField('hora de cierre')
    is_active = models.BooleanField('activa', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'cancha'
        verbose_name_plural = 'canchas'
        constraints = [
            models.CheckConstraint(
                condition=Q(opening_time__lt=F('closing_time')),
                name='court_opening_before_closing',
            ),
        ]

    def __str__(self):
        return self.name
