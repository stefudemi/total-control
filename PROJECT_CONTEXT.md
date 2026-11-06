# PROJECT_CONTEXT — Total Control

> Archivo para retomar el proyecto en cualquier sesión. Actualizar al cerrar cada módulo.

## Objetivo
Sistema web de gestión de turnos y canchas de pádel (TFI – Tecnicatura Universitaria en Programación, UTN-FRLP). Usuario inicial: administrador/empleado de un complejo genérico. Sin reservas públicas en v1.

## Arquitectura
SPA React (Vite) → API REST Django/DRF → PostgreSQL. Lógica de negocio solo en el backend. Detalle: `docs/ARQUITECTURA.md`. Modelo: `docs/MODELO_DATOS.md`. Plan: `docs/ROADMAP.md`.

## Stack
Python 3.11, Django, DRF, PostgreSQL 18 (local, servicio `postgresql-x64-18`), React + JavaScript, Git. Entorno: Windows 11, VS Code.

## Estructura
`backend/` (config, accounts, courts, clients, bookings) · `frontend/` · `docs/` · `docs/tfi/`.

## Modelos / relaciones
Court 1—N Booking · Client 1—N Booking · User 1—N Booking (created_by). Ver ER en `docs/MODELO_DATOS.md`.

## Endpoints implementados
Todos bajo `/api/` y requieren autenticación.
- `GET/POST /api/courts/` (filtro `?active=true|false`)
- `GET/PUT/PATCH /api/courts/{id}/` (sin DELETE: se desactivan)
- `POST /api/courts/{id}/activate/` · `POST /api/courts/{id}/deactivate/`
- `GET /api/courts/{id}/availability/?date=YYYY-MM-DD` (turnos de 30 min; aún sin descontar reservas)

## Funcionalidades
- Completadas: Etapa 0 (diseño); Etapa 1.1 módulo Canchas (modelo, API, servicio de disponibilidad, 15 tests, ~99 % cobertura).
- Pendientes: autenticación (login por token), clientes, turnos, RN7 (no desactivar cancha con reservas futuras), frontend, integración.

## Decisiones técnicas
- Auth por token DRF (nativo). Roles con `is_staff` / grupo Empleados.
- Anti-superposición: validación en servicio + `ExclusionConstraint` PostgreSQL.
- Cliente se crea/reutiliza desde la reserva (por teléfono).
- Commits en español, Conventional Commits, pequeños y frecuentes.

## Problemas conocidos
- `psql` no está en el PATH (está en `C:\Program Files\PostgreSQL\18\bin`).
- Se necesitan credenciales de PostgreSQL del usuario (se guardan en `backend/.env`, no versionado).

## Estado actual
Módulo Canchas completo y probado.

## Próximo paso concreto
Crear app `accounts`: `rest_framework.authtoken`, endpoints login/logout/me, grupo Empleados y tests.
