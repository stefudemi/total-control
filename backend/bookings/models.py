from datetime import timedelta

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models
from django.db.models import F, Func, Q, Value


class TsTzRange(Func):
    """Construye un rango timestamptz de PostgreSQL: TSTZRANGE(inicio, fin, '[)')."""

    function = 'TSTZRANGE'
    output_field = DateTimeRangeField()


class Booking(models.Model):
    """Reserva de una cancha por un cliente."""

    class Status(models.TextChoices):
        CONFIRMED = 'confirmed', 'Confirmada'
        CANCELLED = 'cancelled', 'Cancelada'

    court = models.ForeignKey(
        'courts.Court', on_delete=models.PROTECT, related_name='bookings', verbose_name='cancha'
    )
    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT, related_name='bookings', verbose_name='cliente'
    )
    start_at = models.DateTimeField('inicio')
    duration_minutes = models.PositiveIntegerField('duración (minutos)')
    end_at = models.DateTimeField('fin', editable=False)
    status = models.CharField(
        'estado', max_length=20, choices=Status.choices, default=Status.CONFIRMED
    )
    notes = models.TextField('notas', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='created_bookings', verbose_name='creada por',
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='cancelled_bookings', verbose_name='cancelada por',
    )
    cancelled_at = models.DateTimeField('cancelada el', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at']
        verbose_name = 'reserva'
        verbose_name_plural = 'reservas'
        indexes = [
            models.Index(fields=['court', 'start_at'], name='booking_court_start_idx'),
            models.Index(fields=['start_at'], name='booking_start_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(duration_minutes__gt=0), name='booking_duration_positive'
            ),
            models.CheckConstraint(
                condition=Q(end_at__gt=F('start_at')), name='booking_end_after_start'
            ),
            ExclusionConstraint(
                name='booking_no_overlap_confirmed',
                expressions=[
                    ('court', RangeOperators.EQUAL),
                    (
                        TsTzRange('start_at', 'end_at', Value('[)')),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(status='confirmed'),
            ),
        ]

    def save(self, *args, **kwargs):
        if self.start_at and self.duration_minutes:
            self.end_at = self.start_at + timedelta(minutes=self.duration_minutes)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.court} - {self.start_at:%d/%m/%Y %H:%M} ({self.duration_minutes} min)'
