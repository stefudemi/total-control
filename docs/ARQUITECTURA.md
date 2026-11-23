# Arquitectura — Total Control

Total Control es un sistema web para que los complejos de pádel dejen de manejar los turnos por WhatsApp o en un cuaderno. El objetivo principal es que nunca se pisen dos reservas en la misma cancha.

## Cómo está armado

Son tres capas separadas:

```
React (Vite)  ──JSON──▶  Django + DRF (API)  ──ORM──▶  PostgreSQL
```

- **Frontend:** solo muestra datos y llama a la API. No tiene lógica de negocio.
- **Backend:** acá viven todas las reglas. Cada app tiene sus `models`, `serializers`, `services`, `views` y `tests`.
- **Login:** con token de DRF. Hay dos roles: administrador (`is_staff`) y empleado (grupo "Empleados").

Como todo pasa por la API, si más adelante sumamos una app móvil o reservas públicas, se pueden reutilizar los mismos endpoints.

## Módulos

| App | Qué hace |
|---|---|
| `accounts` | Login, logout, usuarios y roles |
| `courts` | Canchas, horarios y disponibilidad |
| `clients` | Datos e historial de clientes |
| `bookings` | Reservas, control de superposición y cancelación |

El diagrama de módulos está en `docs/tfi/diagramas/modulos.png`.

## Reglas principales

- No puede haber dos reservas confirmadas que se pisen en la misma cancha. Dos turnos seguidos sí se permiten.
- No se reserva en el pasado, ni en una cancha inactiva, ni fuera de su horario.
- Los turnos duran entre 30 y 180 minutos, en bloques de 30.
- Cancelar no borra la reserva: cambia el estado y libera el horario.
- No se puede desactivar una cancha que tenga reservas futuras.

La superposición se controla dos veces: en el servicio, para devolver un mensaje claro, y en la base con una restricción de PostgreSQL, para que dos reservas simultáneas no se cuelen.

## Tests

Usamos los tests de Django/DRF por módulo, con foco en los casos borde de las reservas (turnos seguidos, cancelados, canchas inactivas). Para el frontend usamos Vitest más pruebas manuales del flujo completo.
