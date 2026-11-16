# API REST — Total Control

Contrato para el frontend. Base: `/api/`. Formato JSON. Zona horaria: `America/Argentina/Buenos_Aires`.

## Convenciones

- **Autenticación (RN9):** todo requiere el header `Authorization: Token <token>`, salvo `POST /api/auth/login/`.
- **Roles:** `admin` (`is_staff`) y `employee` (usuario activo del grupo "Empleados"). "Personal" = ambos.
- **Fechas:** `date` = `YYYY-MM-DD`. `start_at` se **envía sin offset** (`2030-05-01T18:00:00`) y se interpreta en hora de Buenos Aires. Las respuestas traen offset (`2030-05-01T18:00:00-03:00`).
- **Paginación:** solo `/api/clients/`: `{count, next, previous, results}` (`?page=`, 20 por página). El resto devuelve listas simples.
- **Errores:**
  - `400` validación: `{"campo": ["mensaje"]}`; errores de regla de negocio: `{"detail": "mensaje"}` o `{"campo": [...]}` (se indica abajo).
  - `401` sin token o token inválido: `{"detail": "Las credenciales de autenticación no se proveyeron."}`
  - `403` sin permiso: `{"detail": "Usted no tiene permiso para realizar esta acción."}`
  - `404` no existe. `405` método no permitido (no hay DELETE en ningún recurso).

## Autenticación (RF01)

| Método | Ruta | Permiso |
|---|---|---|
| POST | `/api/auth/login/` | público |
| POST | `/api/auth/logout/` | autenticado |
| GET | `/api/auth/me/` | autenticado |

`POST /api/auth/login/` body `{"username": "ana", "password": "secreto123"}` → `200`
```json
{"token": "9944b09199c6...", "user": {"id": 2, "username": "ana", "first_name": "Ana", "last_name": "Pérez", "role": "employee"}}
```
Errores `400`: credenciales inválidas o usuario inactivo → `{"detail": "Usuario o contraseña incorrectos."}` / `{"detail": "El usuario está desactivado."}`.

`POST /api/auth/logout/` → `204`. El token deja de ser válido.
`GET /api/auth/me/` → `200` el objeto `user` de arriba.

## Usuarios (RF02) — solo admin

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/users/` | listar (lista simple) |
| POST | `/api/users/` | crear (queda en el grupo Empleados) |
| GET | `/api/users/{id}/` | ver |
| PUT/PATCH | `/api/users/{id}/` | editar |
| POST | `/api/users/{id}/activate/` | activar |
| POST | `/api/users/{id}/deactivate/` | desactivar |

Body de creación: `{"username": "luis", "password": "Clave-segura-91", "first_name": "Luis", "last_name": "Gómez", "email": "luis@x.com"}` → `201`
```json
{"id": 3, "username": "luis", "first_name": "Luis", "last_name": "Gómez", "email": "luis@x.com", "is_active": true, "role": "employee"}
```
`password` es de solo escritura y pasa los validadores de Django (`400 {"password": [...]}`). `username` duplicado → `400`. `is_active` y `role` son de solo lectura (usar activate/deactivate). Un admin que se desactiva a sí mismo → `400 {"detail": "No podés desactivarte a vos mismo."}`. Empleado → `403`.

## Canchas

| Método | Ruta | Permiso |
|---|---|---|
| GET | `/api/courts/` (`?active=true\|false`) | personal |
| GET | `/api/courts/{id}/` | personal |
| GET | `/api/courts/{id}/availability/?date=` | personal |
| POST | `/api/courts/` | admin |
| PUT/PATCH | `/api/courts/{id}/` | admin |
| POST | `/api/courts/{id}/activate/` · `/deactivate/` | admin |

Cancha: `{"id": 1, "name": "Cancha 1", "court_type": "covered|uncovered", "description": "", "opening_time": "09:00:00", "closing_time": "23:00:00", "is_active": true, "created_at": "...", "updated_at": "..."}`.

`availability` → `{"court": 1, "date": "2030-05-01", "is_active": true, "slots": [{"start": "09:00", "end": "09:30", "available": true}, {"start": "09:30", "end": "10:00", "available": false, "booking_id": 12}]}`. Las franjas ocupadas por una reserva confirmada traen `available: false` y `booking_id`.

`deactivate` con reservas futuras confirmadas (RN7) → `400 {"detail": "No se puede desactivar la cancha: tiene 3 reservas futuras confirmadas. Cancelalas primero."}`.

## Clientes (RF07, RF08)

| Método | Ruta | Permiso |
|---|---|---|
| GET | `/api/clients/` (`?search=` nombre, apellido o teléfono; paginado) | personal |
| POST | `/api/clients/` | personal |
| GET | `/api/clients/{id}/` | personal |
| PUT/PATCH | `/api/clients/{id}/` | personal |
| GET | `/api/clients/{id}/bookings/` | personal (historial, más reciente primero, lista simple de reservas) |

Body: `{"first_name": "Juan", "last_name": "Pérez", "phone": "+54 9 221 555-1234", "email": ""}` → `201`
```json
{"id": 1, "first_name": "Juan", "last_name": "Pérez", "phone": "+5492215551234", "email": "", "created_at": "...", "updated_at": "..."}
```
El teléfono se normaliza (solo dígitos y `+`). Teléfono duplicado → `400 {"phone": ["Ya existe un cliente con ese teléfono."]}`.

## Reservas (RF09–RF12, RF14)

| Método | Ruta | Permiso |
|---|---|---|
| GET | `/api/bookings/` (`?date=`, `?court=<id>`, `?client=<id>`, `?status=confirmed\|cancelled`) | personal |
| POST | `/api/bookings/` | personal |
| GET | `/api/bookings/{id}/` | personal |
| POST | `/api/bookings/{id}/cancel/` | personal |

Sin PUT/PATCH/DELETE (`405`). Listado: lista simple ordenada por `start_at`.

`POST /api/bookings/` con cliente existente:
```json
{"court": 1, "start_at": "2030-05-01T18:00:00", "duration_minutes": 90, "client_id": 4, "notes": ""}
```
o con cliente nuevo/reutilizable (se busca por teléfono; si no existe se crea):
```json
{"court": 1, "start_at": "2030-05-01T18:00:00", "duration_minutes": 90,
 "client": {"first_name": "Juan", "last_name": "Pérez", "phone": "221 555-1234", "email": "j@x.com"}}
```
Hay que enviar `client_id` **o** `client`. → `201`
```json
{
  "id": 12,
  "court": {"id": 1, "name": "Cancha 1"},
  "client": {"id": 4, "full_name": "Juan Pérez", "phone": "+5492215551234"},
  "start_at": "2030-05-01T18:00:00-03:00",
  "duration_minutes": 90,
  "end_at": "2030-05-01T19:30:00-03:00",
  "status": "confirmed",
  "notes": "",
  "created_by": {"username": "ana", "full_name": "Ana Pérez"},
  "created_at": "2030-04-20T10:00:00-03:00",
  "cancelled_by": null,
  "cancelled_at": null
}
```
Errores `400 {"detail": "..."}` (en este orden de validación):

| Regla | Mensaje (ejemplo) |
|---|---|
| RN3 | `La cancha está inactiva.` |
| RN4 | `La duración debe ser múltiplo de 30 minutos, entre 30 y 180.` / `El horario de inicio debe ser en punto o y media.` |
| RN5 | `No se puede reservar en el pasado.` |
| RN8 | `La reserva debe estar dentro del horario de la cancha (09:00 a 23:00).` |
| RN2 | `La cancha ya está reservada de 18:00 a 19:30.` |

Campos faltantes o mal formados → `400 {"campo": [...]}`.

`POST /api/bookings/{id}/cancel/` (sin body) → `200` la reserva con `status: "cancelled"`, `cancelled_by`, `cancelled_at`. Ya cancelada → `400 {"detail": "La reserva ya está cancelada."}`.

## Agenda (RF13)

`GET /api/agenda/?date=YYYY-MM-DD` — personal. Canchas **activas** con sus franjas y reservas confirmadas del día.
```json
{
  "date": "2030-05-01",
  "courts": [
    {
      "id": 1, "name": "Cancha 1", "court_type": "covered",
      "opening_time": "09:00:00", "closing_time": "23:00:00",
      "slots": [{"start": "09:00", "end": "09:30", "available": true}],
      "bookings": [ { "...": "mismo objeto que en /api/bookings/" } ]
    }
  ]
}
```
`date` faltante o inválida → `400 {"date": [...]}`.
