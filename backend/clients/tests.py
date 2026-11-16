from rest_framework.test import APITestCase

from accounts.tests import make_employee

from .models import Client, normalize_phone


def make_client(**kwargs):
    data = dict(first_name='Juan', last_name='Pérez', phone='2215551234')
    data.update(kwargs)
    return Client.objects.create(**data)


class NormalizePhoneTests(APITestCase):
    def test_normaliza(self):
        self.assertEqual(normalize_phone('+54 9 (221) 555-1234'), '+5492215551234')
        self.assertEqual(normalize_phone('221 555-1234'), '2215551234')


class ClientAPITests(APITestCase):
    url = '/api/clients/'

    def setUp(self):
        self.client.force_authenticate(make_employee())
        self.payload = {
            'first_name': 'Ana', 'last_name': 'López', 'phone': '221 555-0000',
        }

    def test_requiere_autenticacion(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_crear_normaliza_telefono(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['phone'], '2215550000')

    def test_telefono_duplicado(self):
        make_client(phone='2215550000')
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('phone', res.data)

    def test_telefono_invalido(self):
        self.payload['phone'] = '12'
        self.assertEqual(self.client.post(self.url, self.payload, format='json').status_code, 400)

    def test_editar_y_no_borrar(self):
        c = make_client()
        res = self.client.patch(f'{self.url}{c.id}/', {'first_name': 'Pedro'}, format='json')
        self.assertEqual(res.status_code, 200)
        # Editar sin cambiar el teléfono no cuenta como duplicado.
        res = self.client.put(f'{self.url}{c.id}/', {**self.payload, 'phone': '2215551234'}, format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.client.delete(f'{self.url}{c.id}/').status_code, 405)

    def test_listado_paginado_y_busqueda(self):
        make_client()
        make_client(first_name='María', last_name='Gómez', phone='2216660000')
        res = self.client.get(self.url)
        self.assertEqual(res.data['count'], 2)
        self.assertIn('results', res.data)
        for term, expected in [('gómez', 1), ('Juan', 1), ('666', 1), ('zzz', 0)]:
            res = self.client.get(self.url, {'search': term})
            self.assertEqual(res.data['count'], expected, term)
