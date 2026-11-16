import random
from datetime import datetime, time, timedelta
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.tests import make_admin, make_employee
from clients.models import Client
from clients.tests import make_client
from courts.models import Court
from courts.services import get_day_slots

from . import services
from .models import Booking
from .services import BookingError, cancel_booking, create_booking


def make_court(**kwargs):
    data = dict(name='Cancha 1', opening_time=time(9, 0), closing_time=time(23, 0))
    data.update(kwargs)
    return Court.objects.create(**data)


def day(offset):
    """Fecha local de hoy + offset días."""
    return timezone.localdate() + timedelta(days=offset)


def at(offset, hour, minute=0):
    """Datetime aware (hora local) de hoy + offset días."""
    naive = datetime.combine(day(offset), time(hour, minute))
    return timezone.make_aware(naive)


def naive_iso(offset, hour, minute=0):
    return datetime.combine(day(offset), time(hour, minute)).isoformat()


def book(court, client, offset=1, hour=18, minutes=60, **kwargs):
    return create_booking(
        court=court, client=client, start_at=at(offset, hour), duration_minutes=minutes, **kwargs
    )


class BookingServiceTests(TestCase):
    def setUp(self):
        self.court = make_court()
        self.client_obj = make_client()
        self.user = make_employee()

    def test_crear_reserva_calcula_fin_y_guarda_auditoria(self):
        booking = book(self.court, self.client_obj, minutes=90, created_by=self.user)
        self.assertEqual(booking.end_at, at(1, 19, 30))
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.created_by, self.user)
        self.assertIsNone(booking.cancelled_by)

    def test_cancha_inactiva(self):
        self.court.is_active = False
        self.court.save()
        with self.assertRaisesMessage(BookingError, 'inactiva'):
            book(self.court, self.client_obj)

    def test_duracion_invalida(self):
        for minutes in (0, 15, 45, 210, 181):
            with self.assertRaisesMessage(BookingError, 'duración'):
                book(self.court, self.client_obj, minutes=minutes)

    def test_duracion_maxima_permitida(self):
        self.assertEqual(book(self.court, self.client_obj, minutes=180).duration_minutes, 180)

    def test_minuto_de_inicio_invalido(self):
        with self.assertRaisesMessage(BookingError, ':00 o :30'):
            create_booking(
                court=self.court, client=self.client_obj,
                start_at=at(1, 18, 15), duration_minutes=60,
            )

    def test_inicio_y_medio_es_valido(self):
        booking = create_booking(
            court=self.court, client=self.client_obj,
            start_at=at(1, 18, 30), duration_minutes=60,
        )
        self.assertEqual(booking.end_at, at(1, 19, 30))

    def test_en_el_pasado(self):
        with self.assertRaisesMessage(BookingError, 'pasado'):
            book(self.court, self.client_obj, offset=-1)

    def test_fuera_de_horario_antes_y_despues(self):
        with self.assertRaisesMessage(BookingError, 'horario de la cancha'):
            book(self.court, self.client_obj, hour=8, minutes=60)
        with self.assertRaisesMessage(BookingError, 'horario de la cancha'):
            book(self.court, self.client_obj, hour=22, minutes=90)

    def test_justo_dentro_del_horario(self):
        book(self.court, self.client_obj, hour=9, minutes=60)
        book(self.court, self.client_obj, hour=22, minutes=60)

    def test_superposicion_total_y_parcial(self):
        book(self.court, self.client_obj, hour=18, minutes=90)  # 18:00-19:30
        with self.assertRaisesMessage(BookingError, '18:00 a 19:30'):
            book(self.court, self.client_obj, hour=18, minutes=90)  # total
        with self.assertRaisesMessage(BookingError, 'ya está reservada'):
            create_booking(  # parcial: 19:00-20:00
                court=self.court, client=self.client_obj,
                start_at=at(1, 19), duration_minutes=60,
            )
        with self.assertRaisesMessage(BookingError, 'ya está reservada'):
            create_booking(  # parcial: 17:00-18:30
                court=self.court, client=self.client_obj,
                start_at=at(1, 17), duration_minutes=90,
            )
        with self.assertRaisesMessage(BookingError, 'ya está reservada'):
            book(self.court, self.client_obj, hour=18, minutes=30)  # contenida

    def test_turnos_contiguos_permitidos(self):
        book(self.court, self.client_obj, hour=18, minutes=60)  # 18-19
        book(self.court, self.client_obj, hour=19, minutes=60)  # 19-20
        book(self.court, self.client_obj, hour=17, minutes=60)  # 17-18
        self.assertEqual(Booking.objects.count(), 3)

    def test_misma_hora_en_otra_cancha_permitida(self):
        other = make_court(name='Cancha 2')
        book(self.court, self.client_obj)
        book(other, self.client_obj)
        self.assertEqual(Booking.objects.count(), 2)

    def test_superposicion_con_cancelada_permitida(self):
        first = book(self.court, self.client_obj)
        cancel_booking(first, self.user)
        again = book(self.court, self.client_obj)
        self.assertEqual(again.status, Booking.Status.CONFIRMED)

    def test_cliente_nuevo_y_reutilizado(self):
        data = {'first_name': 'Ana', 'last_name': 'López', 'phone': '+54 221 555-0000'}
        first = create_booking(
            court=self.court, client_data=data, start_at=at(1, 10), duration_minutes=60,
        )
        self.assertEqual(first.client.phone, '+542215550000')
        # Mismo teléfono con otro formato: se reutiliza, no se duplica ni se pisa.
        data2 = {'first_name': 'Otro', 'last_name': 'Nombre', 'phone': '+54221 5550000'}
        second = create_booking(
            court=self.court, client_data=data2, start_at=at(1, 12), duration_minutes=60,
        )
        self.assertEqual(second.client_id, first.client_id)
        self.assertEqual(Client.objects.filter(phone='+542215550000').count(), 1)
        self.assertEqual(second.client.first_name, 'Ana')

    def test_sin_cliente(self):
        with self.assertRaisesMessage(BookingError, 'cliente'):
            create_booking(court=self.court, start_at=at(1, 10), duration_minutes=60)

    def test_error_validacion_no_deja_cliente_huerfano(self):
        data = {'first_name': 'Ana', 'last_name': 'López', 'phone': '2215550000'}
        with self.assertRaises(BookingError):
            create_booking(
                court=self.court, client_data=data, start_at=at(-1, 10), duration_minutes=60,
            )
        self.assertFalse(Client.objects.filter(phone='2215550000').exists())

    def test_integrity_error_se_traduce_al_mismo_error(self):
        book(self.court, self.client_obj)
        # Simula una carrera: la validación del servicio no ve el conflicto.
        with mock.patch.object(services, '_overlap_message', side_effect=[None, None]):
            with self.assertRaisesMessage(BookingError, 'ya está reservada'):
                book(self.court, self.client_obj)
        self.assertEqual(Booking.objects.count(), 1)

    def test_cancelar_guarda_auditoria_y_no_borra(self):
        booking = book(self.court, self.client_obj)
        cancel_booking(booking, self.user)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertEqual(booking.cancelled_by, self.user)
        self.assertIsNotNone(booking.cancelled_at)
        self.assertEqual(Booking.objects.count(), 1)

    def test_cancelar_dos_veces(self):
        booking = book(self.court, self.client_obj)
        cancel_booking(booking, self.user)
        with self.assertRaisesMessage(BookingError, 'ya está cancelada'):
            cancel_booking(booking, self.user)


class BookingConstraintTests(TestCase):
    """La base de datos protege la integridad aunque se evite el servicio."""

    def setUp(self):
        self.court = make_court()
        self.client_obj = make_client()

    def make(self, start, minutes, **kwargs):
        return Booking.objects.create(
            court=self.court, client=self.client_obj, start_at=start,
            duration_minutes=minutes, **kwargs,
        )

    def test_bd_rechaza_reservas_solapadas_creadas_con_el_orm(self):
        self.make(at(1, 18), 60)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.make(at(1, 18, 30), 60)

    def test_bd_permite_contiguas_y_solapadas_si_una_esta_cancelada(self):
        self.make(at(1, 18), 60)
        self.make(at(1, 19), 60)
        self.make(at(1, 18), 60, status=Booking.Status.CANCELLED)
        self.assertEqual(Booking.objects.count(), 3)

    def test_bd_rechaza_duracion_no_positiva(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(
                court=self.court, client=self.client_obj, start_at=at(1, 18),
                duration_minutes=0, end_at=at(1, 18),
            )

    def test_un_mes_de_reservas_simuladas_sin_solapamientos(self):
        rng = random.Random(42)
        courts = [self.court, make_court(name='Cancha 2')]
        accepted = 0
        for _ in range(250):
            try:
                create_booking(
                    court=rng.choice(courts), client=self.client_obj,
                    start_at=at(rng.randint(1, 30), rng.randint(9, 22), rng.choice([0, 30])),
                    duration_minutes=rng.choice([30, 60, 90, 120]),
                )
                accepted += 1
            except BookingError:
                pass
        self.assertGreater(accepted, 20)
        for court in courts:
            bookings = list(
                Booking.objects.filter(court=court, status='confirmed').order_by('start_at')
            )
            for previous, current in zip(bookings, bookings[1:]):
                self.assertLessEqual(previous.end_at, current.start_at)


class BookingAPITests(APITestCase):
    url = '/api/bookings/'

    def setUp(self):
        self.user = make_employee(first_name='Ana', last_name='Pérez')
        self.client.force_authenticate(self.user)
        self.court = make_court()
        self.customer = make_client()
        self.payload = {
            'court': self.court.id, 'start_at': naive_iso(1, 18),
            'duration_minutes': 90, 'client_id': self.customer.id,
        }

    def post(self, **changes):
        return self.client.post(self.url, {**self.payload, **changes}, format='json')

    def test_requiere_autenticacion(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 401)

    def test_crear_con_client_id(self):
        res = self.post()
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['court'], {'id': self.court.id, 'name': 'Cancha 1'})
        self.assertEqual(res.data['client']['full_name'], 'Juan Pérez')
        self.assertEqual(res.data['created_by'], {'username': 'empleado', 'full_name': 'Ana Pérez'})
        self.assertIsNone(res.data['cancelled_by'])
        self.assertEqual(res.data['status'], 'confirmed')
        # start_at sin offset se interpreta en hora de Buenos Aires.
        self.assertTrue(res.data['start_at'].endswith('-03:00'))
        self.assertIn('T18:00:00', res.data['start_at'])
        self.assertIn('T19:30:00', res.data['end_at'])

    def test_crear_con_cliente_nuevo_y_reutilizarlo(self):
        client_data = {'first_name': 'Ana', 'last_name': 'López', 'phone': '221 555-0000'}
        payload = {k: v for k, v in self.payload.items() if k != 'client_id'}
        res = self.client.post(self.url, {**payload, 'client': client_data}, format='json')
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data['client']['phone'], '2215550000')
        res2 = self.client.post(
            self.url,
            {**payload, 'start_at': naive_iso(1, 12), 'client': client_data},
            format='json',
        )
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.data['client']['id'], res.data['client']['id'])
        self.assertEqual(Client.objects.count(), 2)

    def test_cliente_requerido_exactamente_uno(self):
        payload = {k: v for k, v in self.payload.items() if k != 'client_id'}
        self.assertEqual(self.client.post(self.url, payload, format='json').status_code, 400)
        both = {**self.payload, 'client': {'first_name': 'A', 'last_name': 'B', 'phone': '2215550000'}}
        self.assertEqual(self.client.post(self.url, both, format='json').status_code, 400)

    def test_errores_de_reglas_devuelven_detail(self):
        self.assertIn('pasado', self.post(start_at=naive_iso(-1, 18)).data['detail'])
        self.assertIn('duración', self.post(duration_minutes=45).data['detail'])
        self.assertIn(':00 o :30', self.post(start_at=naive_iso(1, 18, 15)).data['detail'])
        self.assertIn('horario', self.post(start_at=naive_iso(1, 8)).data['detail'])
        self.assertEqual(self.post().status_code, 201)
        res = self.post()
        self.assertEqual(res.status_code, 400)
        self.assertIn('18:00 a 19:30', res.data['detail'])

    def test_cancha_inactiva_o_inexistente(self):
        self.court.is_active = False
        self.court.save()
        self.assertEqual(self.post().status_code, 400)
        self.assertEqual(self.post(court=9999).status_code, 400)

    def test_sin_edicion_ni_borrado(self):
        booking = self.post().data
        url = f'{self.url}{booking["id"]}/'
        self.assertEqual(self.client.put(url, self.payload, format='json').status_code, 405)
        self.assertEqual(self.client.patch(url, {'notes': 'x'}, format='json').status_code, 405)
        self.assertEqual(self.client.delete(url).status_code, 405)

    def test_cancelar_y_cancelar_dos_veces(self):
        booking_id = self.post().data['id']
        res = self.client.post(f'{self.url}{booking_id}/cancel/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['status'], 'cancelled')
        self.assertEqual(res.data['cancelled_by']['username'], 'empleado')
        self.assertIsNotNone(res.data['cancelled_at'])
        res = self.client.post(f'{self.url}{booking_id}/cancel/')
        self.assertEqual(res.status_code, 400)
        self.assertIn('ya está cancelada', res.data['detail'])
        # El horario quedó libre.
        self.assertEqual(self.post().status_code, 201)

    def test_detalle_y_filtros(self):
        other_court = make_court(name='Cancha 2')
        other_client = make_client(phone='2216660000')
        first = self.post().data
        self.post(court=other_court.id, client_id=other_client.id, start_at=naive_iso(2, 10))
        cancelled = self.post(start_at=naive_iso(3, 10)).data
        self.client.post(f'{self.url}{cancelled["id"]}/cancel/')

        self.assertEqual(self.client.get(f'{self.url}{first["id"]}/').status_code, 200)
        self.assertEqual(self.client.get(self.url).data.__len__(), 3)

        def ids(**params):
            return [b['id'] for b in self.client.get(self.url, params).data]

        self.assertEqual(ids(date=day(1).isoformat()), [first['id']])
        self.assertEqual(len(ids(court=other_court.id)), 1)
        self.assertEqual(len(ids(client=other_client.id)), 1)
        self.assertEqual(ids(status='cancelled'), [cancelled['id']])
        self.assertEqual(self.client.get(self.url, {'status': 'xx'}).status_code, 400)
        self.assertEqual(self.client.get(self.url, {'date': 'xx'}).status_code, 400)

    def test_historial_del_cliente(self):
        self.post()
        self.post(start_at=naive_iso(2, 18))
        res = self.client.get(f'/api/clients/{self.customer.id}/bookings/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        self.assertGreater(res.data[0]['start_at'], res.data[1]['start_at'])


class AgendaAndAvailabilityTests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(make_employee())
        self.court = make_court(opening_time=time(9, 0), closing_time=time(12, 0))
        self.customer = make_client()

    def test_disponibilidad_descuenta_reservas(self):
        booking = create_booking(
            court=self.court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
        )
        slots = get_day_slots(self.court, day(1))
        busy = [s for s in slots if not s['available']]
        self.assertEqual([s['start'] for s in busy], ['10:00', '10:30'])
        self.assertTrue(all(s['booking_id'] == booking.id for s in busy))
        self.assertNotIn('booking_id', slots[0])
        res = self.client.get(f'/api/courts/{self.court.id}/availability/', {'date': day(1)})
        self.assertEqual(sum(not s['available'] for s in res.data['slots']), 2)

    def test_reserva_cancelada_libera_franjas(self):
        booking = create_booking(
            court=self.court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
        )
        cancel_booking(booking)
        self.assertTrue(all(s['available'] for s in get_day_slots(self.court, day(1))))

    def test_agenda_solo_canchas_activas_con_franjas_y_reservas(self):
        inactive = make_court(name='Cancha 2', is_active=False)
        other = make_court(name='Cancha 3', opening_time=time(9, 0), closing_time=time(12, 0))
        create_booking(
            court=self.court, client=self.customer, start_at=at(1, 9), duration_minutes=30,
        )
        create_booking(
            court=other, client=self.customer, start_at=at(1, 11), duration_minutes=60,
        )
        create_booking(  # otro día: no aparece
            court=other, client=self.customer, start_at=at(2, 11), duration_minutes=60,
        )
        res = self.client.get('/api/agenda/', {'date': day(1).isoformat()})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([c['id'] for c in res.data['courts']], [self.court.id, other.id])
        self.assertNotIn(inactive.id, [c['id'] for c in res.data['courts']])
        first, second = res.data['courts']
        self.assertEqual(len(first['bookings']), 1)
        self.assertEqual(len(first['slots']), 6)
        self.assertFalse(first['slots'][0]['available'])
        self.assertEqual(first['slots'][0]['booking_id'], first['bookings'][0]['id'])
        self.assertEqual(len(second['bookings']), 1)

    def test_agenda_usa_una_sola_consulta_de_reservas(self):
        for n in range(4):
            court = make_court(name=f'C{n}')
            create_booking(
                court=court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
            )
        with CaptureQueriesContext(connection) as ctx:
            self.client.get('/api/agenda/', {'date': day(1).isoformat()})
        booking_queries = [q for q in ctx.captured_queries if 'bookings_booking' in q['sql']]
        self.assertEqual(len(booking_queries), 1)

    def test_agenda_requiere_fecha_valida_y_autenticacion(self):
        self.assertEqual(self.client.get('/api/agenda/').status_code, 400)
        self.assertEqual(self.client.get('/api/agenda/', {'date': 'xx'}).status_code, 400)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get('/api/agenda/', {'date': '2030-01-01'}).status_code, 401)


class CourtDeactivationRN7Tests(APITestCase):
    def setUp(self):
        self.client.force_authenticate(make_admin())
        self.court = make_court()
        self.customer = make_client()

    def url(self):
        return f'/api/courts/{self.court.id}/deactivate/'

    def test_rechaza_con_reservas_futuras_confirmadas(self):
        create_booking(
            court=self.court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
        )
        create_booking(
            court=self.court, client=self.customer, start_at=at(2, 10), duration_minutes=60,
        )
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 400)
        self.assertIn('2 reservas futuras confirmadas', res.data['detail'])
        self.court.refresh_from_db()
        self.assertTrue(self.court.is_active)

    def test_singular(self):
        create_booking(
            court=self.court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
        )
        res = self.client.post(self.url())
        self.assertIn('1 reserva futura confirmada', res.data['detail'])

    def test_permite_si_solo_hay_canceladas_o_pasadas(self):
        booking = create_booking(
            court=self.court, client=self.customer, start_at=at(1, 10), duration_minutes=60,
        )
        cancel_booking(booking)
        Booking.objects.create(  # reserva pasada confirmada (creada directo)
            court=self.court, client=self.customer, start_at=at(-2, 10), duration_minutes=60,
        )
        res = self.client.post(self.url())
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data['is_active'])
