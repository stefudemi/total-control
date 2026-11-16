from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .roles import EMPLOYEES_GROUP

User = get_user_model()


def make_admin(username='admin', **kwargs):
    return User.objects.create_user(username, password='pass1234', is_staff=True, **kwargs)


def make_employee(username='empleado', **kwargs):
    user = User.objects.create_user(username, password='pass1234', **kwargs)
    user.groups.add(Group.objects.get(name=EMPLOYEES_GROUP))
    return user


class AuthTests(APITestCase):
    login_url = '/api/auth/login/'

    def test_grupo_empleados_existe(self):
        self.assertTrue(Group.objects.filter(name=EMPLOYEES_GROUP).exists())

    def test_login_ok(self):
        make_employee(first_name='Ana', last_name='Pérez')
        res = self.client.post(self.login_url, {'username': 'empleado', 'password': 'pass1234'})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['token'])
        self.assertEqual(res.data['user']['role'], 'employee')
        self.assertEqual(res.data['user']['first_name'], 'Ana')

    def test_login_admin_devuelve_rol_admin(self):
        make_admin()
        res = self.client.post(self.login_url, {'username': 'admin', 'password': 'pass1234'})
        self.assertEqual(res.data['user']['role'], 'admin')

    def test_login_invalido(self):
        make_employee()
        res = self.client.post(self.login_url, {'username': 'empleado', 'password': 'mal'})
        self.assertEqual(res.status_code, 400)
        res = self.client.post(self.login_url, {'username': 'empleado'})
        self.assertEqual(res.status_code, 400)

    def test_login_usuario_inactivo(self):
        make_employee(is_active=False)
        res = self.client.post(self.login_url, {'username': 'empleado', 'password': 'pass1234'})
        self.assertEqual(res.status_code, 400)
        self.assertIn('desactivado', res.data['detail'])

    def test_me(self):
        user = make_employee()
        self.client.force_authenticate(user)
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.data['username'], 'empleado')

    def test_logout_invalida_el_token(self):
        make_employee()
        token = self.client.post(
            self.login_url, {'username': 'empleado', 'password': 'pass1234'}
        ).data['token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout/').status_code, 204)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.assertFalse(Token.objects.exists())

    def test_endpoints_requieren_autenticacion(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)
        self.assertEqual(self.client.get('/api/users/').status_code, 401)


class UserAPITests(APITestCase):
    url = '/api/users/'

    def setUp(self):
        self.admin = make_admin()
        self.client.force_authenticate(self.admin)
        self.payload = {
            'username': 'luis', 'password': 'Clave-segura-91',
            'first_name': 'Luis', 'last_name': 'Gómez',
        }

    def test_empleado_no_puede_usar_users(self):
        self.client.force_authenticate(make_employee())
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)

    def test_crear_usuario_queda_en_grupo_empleados(self):
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertNotIn('password', res.data)
        self.assertEqual(res.data['role'], 'employee')
        user = User.objects.get(username='luis')
        self.assertTrue(user.check_password('Clave-segura-91'))
        self.assertTrue(user.groups.filter(name=EMPLOYEES_GROUP).exists())

    def test_password_debil_se_rechaza(self):
        self.payload['password'] = '1234'
        res = self.client.post(self.url, self.payload, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('password', res.data)

    def test_listar_ver_y_editar(self):
        make_employee()
        self.assertEqual(len(self.client.get(self.url).data), 2)
        user = User.objects.get(username='empleado')
        self.assertEqual(self.client.get(f'{self.url}{user.id}/').status_code, 200)
        res = self.client.patch(
            f'{self.url}{user.id}/',
            {'first_name': 'Nuevo', 'password': 'Otra-clave-77'},
            format='json',
        )
        self.assertEqual(res.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Nuevo')
        self.assertTrue(user.check_password('Otra-clave-77'))

    def test_no_permite_borrar(self):
        self.assertEqual(self.client.delete(f'{self.url}{self.admin.id}/').status_code, 405)

    def test_activar_y_desactivar(self):
        emp = make_employee()
        res = self.client.post(f'{self.url}{emp.id}/deactivate/')
        self.assertFalse(res.data['is_active'])
        res = self.client.post(f'{self.url}{emp.id}/activate/')
        self.assertTrue(res.data['is_active'])

    def test_admin_no_puede_desactivarse_a_si_mismo(self):
        res = self.client.post(f'{self.url}{self.admin.id}/deactivate/')
        self.assertEqual(res.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
