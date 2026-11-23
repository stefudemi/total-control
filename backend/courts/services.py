"""Reglas de negocio de canchas: disponibilidad y desactivación."""
from datetime import date, datetime, timedelta

from django.utils import timezone

SLOT_MINUTES = 30


class CourtError(Exception):
    """Error de regla de negocio de canchas (mensaje para el usuario)."""


def get_day_bookings(day: date, court=None, courts=None):
    """Reservas confirmadas que tocan el día (hora local), en una sola consulta."""
    from bookings.models import Booking

    tz = timezone.get_current_timezone()
    day_start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
    qs = Booking.objects.filter(
        status=Booking.Status.CONFIRMED,
        start_at__lt=day_start + timedelta(days=1),
        end_at__gt=day_start,
    ).select_related('court', 'client', 'created_by', 'cancelled_by')
    if court is not None:
        qs = qs.filter(court=court)
    if courts is not None:
        qs = qs.filter(court__in=courts)
    return list(qs.order_by('start_at'))


def get_day_slots(court, day: date, bookings=None) -> list[dict]:
    """Devuelve los turnos de SLOT_MINUTES de la cancha para un día.

    Un turno está disponible si la cancha está activa y no lo cubre una reserva
    confirmada; los ocupados incluyen `booking_id`. `bookings` permite pasar las
    reservas ya cargadas de esa cancha (evita una consulta por cancha).
    """
    if bookings is None:
        bookings = get_day_bookings(day, court=court)
    tz = timezone.get_current_timezone()
    slots = []
    current = datetime.combine(day, court.opening_time)
    closing = datetime.combine(day, court.closing_time)
    step = timedelta(minutes=SLOT_MINUTES)
    while current + step <= closing:
        slot_start = timezone.make_aware(current, tz)
        slot_end = timezone.make_aware(current + step, tz)
        booking = next(
            (b for b in bookings if b.start_at < slot_end and b.end_at > slot_start), None
        )
        slot = {
            'start': current.time().strftime('%H:%M'),
            'end': (current + step).time().strftime('%H:%M'),
            'available': court.is_active and booking is None,
        }
        if booking is not None:
            slot['booking_id'] = booking.id
        slots.append(slot)
        current += step
    return slots


def deactivate_court(court):
    """Desactiva la cancha salvo que tenga reservas futuras confirmadas (RN7)."""
    from bookings.models import Booking

    pending = Booking.objects.filter(
        court=court, status=Booking.Status.CONFIRMED, start_at__gt=timezone.now()
    ).count()
    if pending:
        plural = 's' if pending != 1 else ''
        raise CourtError(
            f'No se puede desactivar la cancha: tiene {pending} reserva{plural} '
            f'futura{plural} confirmada{plural}. Cancelalas primero.'
        )
    court.is_active = False
    court.save(update_fields=['is_active', 'updated_at'])
    return court
