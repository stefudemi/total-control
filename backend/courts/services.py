"""Reglas de negocio de canchas: cálculo de disponibilidad."""
from datetime import date, datetime, timedelta

SLOT_MINUTES = 30


def get_day_slots(court, day: date) -> list[dict]:
    """Devuelve los turnos de SLOT_MINUTES de la cancha para un día.

    Cada turno indica si está disponible. Por ahora solo se considera el
    horario de la cancha y su estado; al incorporar reservas se descontarán
    los horarios ocupados.
    """
    slots = []
    current = datetime.combine(day, court.opening_time)
    closing = datetime.combine(day, court.closing_time)
    step = timedelta(minutes=SLOT_MINUTES)
    while current + step <= closing:
        slots.append({
            'start': current.time().strftime('%H:%M'),
            'end': (current + step).time().strftime('%H:%M'),
            'available': court.is_active,
        })
        current += step
    return slots
