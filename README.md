# Total Control

Sistema web de gestión de turnos y canchas de pádel. Trabajo Final Integrador – Tecnicatura Universitaria en Programación, UTN-FRLP.

## Stack
Python · Django · Django REST Framework · PostgreSQL · React · JavaScript · HTML5/CSS3 · Git.

## Requisitos
Python 3.11+, Node.js 20+, PostgreSQL 15+.

## Instalación y ejecución
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scriptsctivate          # Windows
pip install -r requirements.txt
copy .env.example .env           # completar SECRET_KEY y DB_PASSWORD
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo         # datos de demo (requiere DEMO_PASSWORD en .env)
python manage.py runserver
python manage.py test            # ejecutar tests
```
### Base de datos
Crear en PostgreSQL el rol y la base:
```sql
CREATE ROLE total_control LOGIN PASSWORD 'tu_clave' CREATEDB;
CREATE DATABASE total_control OWNER total_control;
```
Las reservas usan una restricción de exclusión que requiere la extensión `btree_gist`; la migración de `bookings` la crea con `CREATE EXTENSION` (PostgreSQL 13+ la permite al dueño de la base, sin superusuario).

`seed_demo` es idempotente: crea 4 canchas, 15 clientes, reservas de la semana y el empleado `empleado_demo` (contraseña = `DEMO_PASSWORD`).

Contrato de la API: [docs/API.md](docs/API.md).

### Frontend
_Se completará en la Etapa 2._

## Funcionalidades (MVP)
Gestión de canchas · Gestión de turnos sin superposición · Clientes · Panel administrativo · Autenticación de staff.

## Documentación
- [Arquitectura](docs/ARQUITECTURA.md) · [Modelo de datos](docs/MODELO_DATOS.md) · [Roadmap](docs/ROADMAP.md)
- [Contexto del proyecto](PROJECT_CONTEXT.md) · [Changelog](CHANGELOG.md) · [Documentos TFI](docs/tfi/)
