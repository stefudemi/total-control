# Documento de arquitectura — Total Control

## 1. Descripción formal
**Total Control** es un sistema web de gestión de turnos para complejos deportivos con canchas de pádel. Permite que administradores y empleados gestionen canchas, consulten disponibilidad y administren las reservas de los clientes desde un panel administrativo.

## 2. Problema
Muchos complejos gestionan sus turnos por mensajería, planillas o cuadernos: se producen **reservas superpuestas**, no hay visión unificada de la agenda del día y se pierde el historial de clientes. Total Control centraliza la información y valida automáticamente la disponibilidad.

## 3. Objetivos
**General:** desarrollar un sistema web que permita administrar canchas y turnos de un complejo de pádel, evitando superposiciones y brindando una visión clara de la agenda.

**Específicos:**
1. Modelar canchas, clientes y reservas en una base de datos relacional.
2. Exponer una API REST con validaciones de negocio (sin superposición de turnos).
3. Autenticar administradores y empleados y proteger la API.
4. Construir un panel React con dashboard, agenda y formularios.
5. Cubrir las reglas de negocio con tests automatizados.
6. Documentar el sistema para su presentación académica.

## 4. Alcance del MVP
**Incluye:** CRUD de canchas (con activar/desactivar y consulta de disponibilidad); CRUD/cancelación de reservas con validación de superposición; clientes registrados desde la reserva y consultables; panel con reservas del día / por fecha; autenticación de staff.

**Excluye (v1):** pagos online, notificaciones, estadísticas avanzadas, app móvil, reservas públicas de clientes.

## 5. Arquitectura
Arquitectura cliente-servidor desacoplada, de tres capas:

```
 React SPA (Vite)  ──HTTP/JSON──▶  Django + DRF (API REST)  ──ORM──▶  PostgreSQL
 presentación                      lógica de negocio                    persistencia
```

- **Frontend (React):** solo presentación y consumo de la API. **No contiene lógica de negocio**.
- **Backend (Django/DRF):** apps por dominio. Dentro de cada app: `models` (datos), `serializers` (validación/forma), `services` (reglas de negocio complejas, p. ej. disponibilidad), `views` (HTTP), `permissions`, `tests`.
- **Autenticación:** la API usa **tokens** (DRF `TokenAuthentication`, nativo de DRF/Django), usuarios con el modelo `User` de Django; roles mediante grupos/`is_staff` (administrador = `is_superuser`/`is_staff`, empleado = usuario activo del grupo "Empleados").
- **Extensibilidad:** al ser una API, una futura interfaz pública de reservas o una app móvil consumirían los mismos endpoints; agregar un rol "Cliente" no requiere reescribir.

### Módulos (apps Django)
| App | Responsabilidad |
|---|---|
| `accounts` | Login/logout, usuario actual, roles |
| `courts` | Canchas y disponibilidad |
| `clients` | Datos de clientes |
| `bookings` | Reservas, reglas de superposición, cancelación |

## 6. Stack y justificación
| Tecnología | Justificación |
|---|---|
| Python + Django | ORM, admin, auth y migraciones nativas; ideal para TFI |
| Django REST Framework | Serializers, viewsets, permisos y browsable API |
| PostgreSQL | Soporta restricciones de exclusión (evita superposición a nivel BD) |
| React + Vite | SPA moderna, build rápido, componentes reutilizables |
| React Router, fetch/axios | Navegación y consumo de API |
| python-decouple (o `os.environ`) | Configuración por variables de entorno, sin secretos en el repo |
| django-cors-headers | Necesaria para que el frontend en otro origen consuma la API |
| psycopg | Driver de PostgreSQL |

Librerías adicionales se justificarán en `CHANGELOG`/`PROJECT_CONTEXT` al incorporarlas.

## 7. Reglas de negocio
- **RN1** Una reserva pertenece a exactamente una cancha.
- **RN2** No pueden existir dos reservas *confirmadas* superpuestas en la misma cancha (intervalo semiabierto `[inicio, fin)`; dos turnos consecutivos son válidos).
- **RN3** No se puede reservar en una cancha inactiva.
- **RN4** La duración se expresa en minutos (múltiplos de 30, mínimo 30, máximo configurable); `fin = inicio + duración`.
- **RN5** Una reserva no puede crearse en el pasado (se admite edición administrativa de reservas existentes).
- **RN6** Cancelar no borra: cambia el estado a `cancelada` y libera el horario.
- **RN7** Desactivar una cancha con reservas futuras confirmadas requiere resolverlas primero (se rechaza con error claro).
- **RN8** Los reservas deben caer dentro del horario de apertura de la cancha (`hora_apertura`–`hora_cierre`).
- **RN9** Toda la API (salvo login) requiere autenticación.

La superposición se valida **en el servicio** (mensaje de error claro) y se refuerza con una **restricción de exclusión de PostgreSQL** (`ExclusionConstraint` sobre `cancha` + rango de tiempo, solo para estado confirmada) para evitar condiciones de carrera.

## 8. Riesgos técnicos
| Riesgo | Mitigación |
|---|---|
| Condiciones de carrera en reservas concurrentes | `ExclusionConstraint` + transacción atómica |
| Zonas horarias / DST | `USE_TZ=True`, `TIME_ZONE='America/Argentina/Buenos_Aires'`, datetimes aware |
| Complejidad del calendario en React | Agenda en grilla propia simple por cancha/hora antes de evaluar librerías |
| CORS/CSRF y auth SPA↔API | Token auth + CORS restringido a origen del frontend |
| Alcance excesivo | Lista de mejoras futuras; no implementar fuera del MVP |
| Tiempo (2–3 meses) | Roadmap con hitos y backend completo antes del frontend |
| Entorno (PostgreSQL local, credenciales) | `.env.example` y documentación de instalación |

## 9. Estrategia de testing
- **Backend:** tests de Django/DRF (`APITestCase`) por módulo: modelos, validaciones, servicios (disponibilidad/superposición, incluidos casos borde: turnos contiguos, cancelados, canchas inactivas), permisos y endpoints. Objetivo: >80 % cobertura en reglas de negocio (`coverage`).
- **API manual:** colección Postman exportada a `docs/postman/`.
- **Frontend:** pruebas de componentes críticos (Vitest + Testing Library) y checklist de pruebas manuales end-to-end.
- **Integración (Etapa 3):** recorrido completo del flujo demo.

## 10. Estructura de carpetas
```
total-control/
├── backend/
│   ├── manage.py
│   ├── config/            # settings, urls, wsgi
│   ├── accounts/  courts/  clients/  bookings/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/ (api/, components/, pages/, hooks/, styles/)
├── docs/
│   ├── ARQUITECTURA.md  MODELO_DATOS.md  ROADMAP.md
│   └── tfi/               # propuesta, informes, manual de usuario
├── PROJECT_CONTEXT.md  README.md  CHANGELOG.md
└── .gitignore
```

## 11. Estructura inicial de documentación
`README.md`, `PROJECT_CONTEXT.md`, `CHANGELOG.md`, `docs/ARQUITECTURA.md`, `docs/MODELO_DATOS.md`, `docs/ROADMAP.md`, `docs/tfi/` (propuesta, informes de avance, informe final, manual de usuario), `docs/postman/`.

## 12. Mejoras futuras (no implementadas)
Reservas públicas con cuenta de cliente; recordatorios por WhatsApp/email; pagos/señas online; precios por franja y tarifas; turnos fijos recurrentes; estadísticas de ocupación; multi-complejo; exportación a PDF/Excel; app móvil.
