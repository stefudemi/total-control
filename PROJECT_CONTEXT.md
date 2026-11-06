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
_Ninguno todavía._

## Funcionalidades
- Completadas: Etapa 0 (documentación de diseño).
- Pendientes: todo el backend (canchas → auth → clientes → turnos), frontend, integración.

## Decisiones técnicas
- Auth por token DRF (nativo). Roles con `is_staff` / grupo Empleados.
- Anti-superposición: validación en servicio + `ExclusionConstraint` PostgreSQL.
- Cliente se crea/reutiliza desde la reserva (por teléfono).
- Commits en español, Conventional Commits, pequeños y frecuentes.

## Problemas conocidos
- `psql` no está en el PATH (está en `C:\Program Files\PostgreSQL\18\bin`).
- Se necesitan credenciales de PostgreSQL del usuario (se guardan en `backend/.env`, no versionado).

## Estado actual
Etapa 0 completa. Iniciando Etapa 1, módulo Canchas.

## Próximo paso concreto
Crear entorno virtual, proyecto Django `config`, configurar PostgreSQL por variables de entorno y app `courts`.
