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
Todos bajo `/api/` y requieren token (`Authorization: Token ...`), salvo login. Contrato completo: `docs/API.md`.
- Auth: `POST auth/login/` · `POST auth/logout/` · `GET auth/me/`
- Usuarios (solo admin): `users/` (list/create/retrieve/update) · `users/{id}/activate|deactivate/`
- Canchas: lectura y `availability` para todo el personal; crear/editar/activar/desactivar solo admin. `deactivate` aplica RN7.
- Clientes: `clients/` (paginado, `?search=`) · `clients/{id}/` · `clients/{id}/bookings/`
- Reservas: `bookings/` (filtros `date`, `court`, `client`, `status`) · `bookings/{id}/` · `bookings/{id}/cancel/`
- Agenda: `agenda/?date=`

## Funcionalidades
- Completadas: Etapa 0 (diseño); canchas; accounts (RF01, RF02); clientes (RF07, RF08); reservas (RF09–RF12, RF14); agenda (RF13); RN1–RN9; `seed_demo`. 82 tests, `services.py` al 100 % de cobertura.
- Pendientes: frontend e integración.

## Decisiones técnicas
- Auth por token DRF (nativo). Admin = `is_staff`; empleado = usuario activo del grupo "Empleados" (creado por data migration). Usuarios nuevos quedan en ese grupo.
- Anti-superposición: validación en servicio (con `select_for_update` de la cancha) + `ExclusionConstraint` PostgreSQL (`btree_gist`, rango `[)`, solo confirmadas). Un `IntegrityError` se traduce al mismo error de superposición.
- Cliente se crea/reutiliza desde la reserva (por teléfono); si el teléfono existe se reutiliza el cliente sin modificar sus datos.
- Errores de reglas de negocio: `400 {"detail": "..."}` (`BookingError` / `CourtError` en los servicios).
- `start_at` entra sin offset y se interpreta en America/Argentina/Buenos_Aires; `MAX_DURATION_MINUTES` (180) en settings.
- Teléfono: se normaliza a dígitos y `+` inicial; debe tener 6–15 dígitos. Búsqueda de clientes con `SearchFilter` (el término se compara tal cual contra el teléfono normalizado).
- RN5: "pasado" = `start_at < ahora`. RN7: "futuras" = `start_at > ahora`, solo confirmadas.
- Desactivar un usuario borra su token. Un admin no puede desactivarse a sí mismo.
- Paginación solo en clientes (20 por página); el resto devuelve listas simples.
- `seed_demo` usa semilla fija y omite reservas que ya existen, estén en el pasado o se superpongan; empleado `empleado_demo` con `DEMO_PASSWORD`.
- Commits en español, Conventional Commits, pequeños y frecuentes.

## Problemas conocidos
- `psql` no está en el PATH (está en `C:\Program Files\PostgreSQL\18\bin`).
- Para `seed_demo` hay que definir `DEMO_PASSWORD` en `backend/.env`.
- Se necesitan credenciales de PostgreSQL del usuario (se guardan en `backend/.env`, no versionado).

## Estado actual
Backend completo para el Informe de Avance 2 (rama `feature/backend-informe-2`), probado.

## Próximo paso concreto
Frontend (React/Vite) consumiendo `docs/API.md`; luego integración.
