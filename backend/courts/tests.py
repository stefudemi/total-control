from datetime import date, time

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import Court
from .services import get_day_slots

User = get_user_model()


def make_court(**kwargs):
    data = dict(name='Cancha 1', opening_time=time(9, 0), closing_time=time(23, 0))
    data.update(kwargs)
    return Court.objects.create(**data)


class CourtModelTests(TestCase):
    def test_nombre_unico(self):
        make_court()
        with self.assertRaises(IntegrityError):
            make_court()

    def test_apertura_debe_ser_anterior_al_cierre(self):
        with self.assertRaises(IntegrityError):
            make_court(opening_time=time(20, 0), closing_time=time(10, 0))


class CourtServiceTests(TestCase):
    def test_genera_turnos_de_30_minutos(self):
        court = make_court(opening_time=time(9, 0), closing_time=time(11, 0))
        slots = get_day_slots(court, date(2030, 1, 1))
        self.assertEqual(len(slots), 4)
        self.assertEqual(slots[0], {'start': '09:00', 'end': '09:30', 'available': True})
        self.assertEqual(slots[-1]['end'], '11:00')

    def test_cancha_inactiva_sin_turnos_disponibles(self):
        court = make_court(is_active=False)
        slots = get_day_slots(court, date(2030, 1, 1))
        self.assertFalse(any(s['available'] for s in slots))


class CourtAPITests(APITestCase):
    url = '/api/courts/'

    def setUp(self):
        self.user = User.objects.create_user('admin', password='pass1234', is_staff=True)
        self.client.force_authenticate(self.user)
        self.payload = {
            'name': 'Cancha Central', 'court_type': 'covered',
            'opening_time': '09:00', 'closing_time': '23:00',
        }

    def test_requiere_autenticacion(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_crear_cancha(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data['is_active'])
        self.assertEqual(Court.objects.count(), 1)

    def test_crear_con_horario_invalido(self):
        self.payload.update(opening_time='22:00', closing_time='10:00')
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('closing_time', res.data)

    def test_nombre_duplicado(self):
        make_court(name='Cancha Central')
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 400)

    def test_listar_y_filtrar_por_activas(self):
        make_court(name='A')
        make_court(name='B', is_active=False)
        self.assertEqual(len(self.client.get(self.url).data), 2)
        res = self.client.get(self.url, {'active': 'true'})
        self.assertEqual([c['name'] for c in res.data], ['A'])

    def test_editar_cancha(self):
        court = make_court()
        res = self.client.patch(f'{self.url}{court.id}/', {'name': 'Nueva'}, format='json')
        self.assertEqual(res.status_code, 200)
        court.refresh_from_db()
        self.assertEqual(court.name, 'Nueva')

    def test_no_se_puede_activar_por_edicion_directa(self):
        court = make_court()
        self.client.patch(f'{self.url}{court.id}/', {'is_active': False}, format='json')
        court.refresh_from_db()
        self.assertTrue(court.is_active)

    def test_no_permite_borrar(self):
        court = make_court()
        self.assertEqual(self.client.delete(f'{self.url}{court.id}/').status_code, 405)

    def test_activar_y_desactivar(self):
        court = make_court()
        res = self.client.post(f'{self.url}{court.id}/deactivate/')
        self.assertFalse(res.data['is_active'])
        res = self.client.post(f'{self.url}{court.id}/activate/')
        self.assertTrue(res.data['is_active'])

    def test_disponibilidad(self):
        court = make_court(opening_time=time(9, 0), closing_time=time(10, 0))
        res = self.client.get(f'{self.url}{court.id}/availability/', {'date': '2030-05-01'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['slots']), 2)

    def test_disponibilidad_requiere_fecha_valida(self):
        court = make_court()
        res = self.client.get(f'{self.url}{court.id}/availability/', {'date': 'xx'})
        self.assertEqual(res.status_code, 400)
        res = self.client.get(f'{self.url}{court.id}/availability/')
        self.assertEqual(res.status_code, 400)


class CourtPermissionTests(APITestCase):
    url = '/api/courts/'

    def setUp(self):
        from accounts.tests import make_employee
        self.client.force_authenticate(make_employee())

    def test_empleado_puede_leer_y_ver_disponibilidad(self):
        court = make_court()
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get(f'{self.url}{court.id}/').status_code, 200)
        res = self.client.get(f'{self.url}{court.id}/availability/', {'date': '2030-05-01'})
        self.assertEqual(res.status_code, 200)

    def test_empleado_no_puede_crear_editar_ni_desactivar(self):
        court = make_court()
        payload = {'name': 'X', 'court_type': 'covered', 'opening_time': '09:00', 'closing_time': '23:00'}
        self.assertEqual(self.client.post(self.url, payload, format='json').status_code, 403)
        self.assertEqual(self.client.patch(f'{self.url}{court.id}/', {'name': 'Y'}).status_code, 403)
        self.assertEqual(self.client.post(f'{self.url}{court.id}/deactivate/').status_code, 403)
        self.assertEqual(self.client.post(f'{self.url}{court.id}/activate/').status_code, 403)
