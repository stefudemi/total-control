"""Carga datos de demostración (idempotente): canchas, clientes, reservas y un empleado."""
import random
from datetime import datetime, time, timedelta

from decouple import config
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.roles import EMPLOYEES_GROUP
from bookings.services import BookingError, create_booking
from clients.models import Client
from courts.models import Court

COURTS = [
    ('Cancha 1', Court.CourtType.COVERED),
    ('Cancha 2', Court.CourtType.COVERED),
    ('Cancha 3', Court.CourtType.UNCOVERED),
    ('Cancha 4', Court.CourtType.UNCOVERED),
]

CLIENTS = [
    ('Juan', 'Pérez'), ('María', 'Gómez'), ('Lucas', 'Fernández'), ('Sofía', 'Rodríguez'),
    ('Martín', 'López'), ('Valentina', 'Díaz'), ('Mateo', 'Martínez'), ('Camila', 'Sosa'),
    ('Nicolás', 'Romero'), ('Lucía', 'Álvarez'), ('Tomás', 'Torres'), ('Julieta', 'Ruiz'),
    ('Agustín', 'Acosta'), ('Paula', 'Benítez'), ('Federico', 'Castro'),
]

DEMO_USERNAME = 'empleado_demo'


class Command(BaseCommand):
    help = 'Carga datos de demostración (se puede ejecutar varias veces).'

    def handle(self, *args, **options):
        password = config('DEMO_PASSWORD', default='')
        if not password:
            raise CommandError('Definí DEMO_PASSWORD en el archivo .env.')

        courts = [self._court(name, kind) for name, kind in COURTS]
        clients = [self._client(i, first, last) for i, (first, last) in enumerate(CLIENTS)]
        user = self._employee(password)
        created = self._bookings(courts, clients, user)
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {len(courts)} canchas, {len(clients)} clientes, '
            f'{created} reservas nuevas, empleado "{DEMO_USERNAME}".'
        ))

    def _court(self, name, kind):
        court, _ = Court.objects.get_or_create(
            name=name,
            defaults={
                'court_type': kind, 'opening_time': time(9, 0), 'closing_time': time(23, 0),
            },
        )
        return court

    def _client(self, index, first, last):
        client, _ = Client.objects.get_or_create(
            phone=f'22155510{index:02d}',
            defaults={'first_name': first, 'last_name': last},
        )
        return client

    def _employee(self, password):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={'first_name': 'Empleado', 'last_name': 'Demo'},
        )
        user.set_password(password)
        user.save()
        group, _ = Group.objects.get_or_create(name=EMPLOYEES_GROUP)
        user.groups.add(group)
        return user

    def _bookings(self, courts, clients, user):
        rng = random.Random(2024)  # semilla fija: mismo plan en cada ejecución
        today = timezone.localdate()
        created = 0
        for offset in range(7):
            for court in courts:
                for hour in range(10, 22, 2):
                    if rng.random() > 0.5:
                        continue
                    start = timezone.make_aware(
                        datetime.combine(today + timedelta(days=offset), time(hour))
                    )
                    try:
                        create_booking(
                            court=court, client=rng.choice(clients), start_at=start,
                            duration_minutes=rng.choice([60, 90]), created_by=user,
                        )
                        created += 1
                    except BookingError:
                        pass  # ya existe, está en el pasado o se superpone
        return created
