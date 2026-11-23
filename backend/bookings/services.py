"""Reglas de negocio de reservas (RN2–RN6, RN8)."""
from datetime import datetime, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from clients.models import Client, normalize_phone
from courts.models import Court
from courts.services import SLOT_MINUTES

from .models import Booking


class BookingError(Exception):
    """Error de regla de negocio; el mensaje está pensado para mostrarse al usuario."""


def _fmt_time(value) -> str:
    return timezone.localtime(value).strftime('%H:%M')


def _overlap_message(court, start_at, end_at) -> str | None:
    conflict = (
        Booking.objects.filter(
            court=court, status=Booking.Status.CONFIRMED,
            start_at__lt=end_at, end_at__gt=start_at,
        )
        .order_by('start_at')
        .first()
    )
    if conflict is None:
        return None
    day = timezone.localtime(conflict.start_at).strftime('%d/%m/%Y')
    return (
        f'La cancha ya está reservada el {day} de '
        f'{_fmt_time(conflict.start_at)} a {_fmt_time(conflict.end_at)}.'
    )


def _validate(court, start_at, duration_minutes, now):
    max_duration = settings.MAX_DURATION_MINUTES
    # RN3
    if not court.is_active:
        raise BookingError('La cancha está inactiva y no admite reservas.')
    # RN4
    if (
        duration_minutes % SLOT_MINUTES != 0
        or not SLOT_MINUTES <= duration_minutes <= max_duration
    ):
        raise BookingError(
            f'La duración debe ser múltiplo de {SLOT_MINUTES} minutos, '
            f'entre {SLOT_MINUTES} y {max_duration}.'
        )
    local_start = timezone.localtime(start_at)
    if local_start.minute not in (0, SLOT_MINUTES) or local_start.second or local_start.microsecond:
        raise BookingError('El horario de inicio debe ser en punto o y media (:00 o :30).')
    # RN5
    if start_at < now:
        raise BookingError('No se puede reservar en el pasado.')
    # RN8
    tz = timezone.get_current_timezone()
    local_end = local_start + timedelta(minutes=duration_minutes)
    opening = datetime.combine(local_start.date(), court.opening_time, tzinfo=tz)
    closing = datetime.combine(local_start.date(), court.closing_time, tzinfo=tz)
    if local_start < opening or local_end > closing:
        raise BookingError(
            'La reserva debe estar dentro del horario de la cancha '
            f'({court.opening_time:%H:%M} a {court.closing_time:%H:%M}).'
        )


def _resolve_client(client, client_data) -> Client:
    if client is not None:
        return client
    phone = normalize_phone(client_data['phone'])
    found, _ = Client.objects.get_or_create(
        phone=phone,
        defaults={
            'first_name': client_data['first_name'],
            'last_name': client_data['last_name'],
            'email': client_data.get('email', ''),
        },
    )
    return found


def create_booking(
    *, court, start_at, duration_minutes, created_by=None,
    client=None, client_data=None, notes='', now=None,
) -> Booking:
    """Crea una reserva confirmada validando las reglas de negocio.

    Se bloquea la fila de la cancha para serializar reservas concurrentes; la
    restricción de exclusión de PostgreSQL es la última defensa.
    """
    if client is None and not client_data:
        raise BookingError('Falta indicar el cliente.')
    now = now or timezone.now()
    with transaction.atomic():
        court = Court.objects.select_for_update().get(pk=court.pk)
        _validate(court, start_at, duration_minutes, now)
        end_at = start_at + timedelta(minutes=duration_minutes)
        message = _overlap_message(court, start_at, end_at)
        if message:
            raise BookingError(message)
        resolved = _resolve_client(client, client_data)
        try:
            with transaction.atomic():
                booking = Booking.objects.create(
                    court=court, client=resolved, start_at=start_at,
                    duration_minutes=duration_minutes, notes=notes, created_by=created_by,
                )
        except IntegrityError:
            raise BookingError(
                _overlap_message(court, start_at, end_at)
                or 'La cancha ya está reservada en ese horario.'
            )
    return booking


def cancel_booking(booking, user=None) -> Booking:
    """Cancela una reserva confirmada (RN6: no se borra)."""
    with transaction.atomic():
        booking = Booking.objects.select_for_update().get(pk=booking.pk)
        if booking.status != Booking.Status.CONFIRMED:
            raise BookingError('La reserva ya está cancelada.')
        booking.status = Booking.Status.CANCELLED
        booking.cancelled_by = user
        booking.cancelled_at = timezone.now()
        booking.save(update_fields=['status', 'cancelled_by', 'cancelled_at', 'updated_at'])
    return booking
