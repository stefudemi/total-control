# Modelo de datos — Total Control

## Diagrama entidad-relación

```mermaid
erDiagram
    USER ||--o{ BOOKING : "crea (created_by)"
    USER ||--o{ BOOKING : "cancela (cancelled_by)"
    COURT ||--o{ BOOKING : "tiene"
    CLIENT ||--o{ BOOKING : "realiza"

    USER {
        int id PK
        string username
        string password
        bool is_staff
        bool is_active
    }
    COURT {
        int id PK
        string name UK
        string court_type "techada / descubierta"
        string description
        time opening_time
        time closing_time
        bool is_active
        datetime created_at
        datetime updated_at
    }
    CLIENT {
        int id PK
        string first_name
        string last_name
        string phone
        string email "opcional"
        datetime created_at
        datetime updated_at
    }
    BOOKING {
        int id PK
        int court_id FK
        int client_id FK
        int created_by_id FK
        datetime start_at
        int duration_minutes
        datetime end_at "calculado"
        string status "confirmed / cancelled"
        string notes
        int cancelled_by_id FK "nullable"
        datetime cancelled_at "nullable"
        datetime created_at
        datetime updated_at
    }
```

## Relaciones
- **Court 1—N Booking**: una cancha tiene muchas reservas (`on_delete=PROTECT`).
- **Client 1—N Booking**: un cliente puede tener muchas reservas (`PROTECT`).
- **User 1—N Booking**: auditoría de quién creó (`created_by`) y quién canceló (`cancelled_by`, con `cancelled_at`) la reserva (`SET_NULL`).
- Cliente se registra dentro del flujo de reserva: se busca por teléfono y, si no existe, se crea (`get_or_create` en el servicio).

## Restricciones
- `Court.name` único.
- `Court`: `opening_time < closing_time`.
- `Client.phone` único, normalizado (solo dígitos y `+` inicial).
- `Booking`: `duration_minutes` > 0 y `end_at > start_at` (CheckConstraints); el múltiplo de 30 y el máximo se validan en el servicio (RN4). `end_at` se persiste.
- `Booking`: `ExclusionConstraint` PostgreSQL: no hay dos filas con la misma `court` y rangos `[start_at, end_at)` solapados cuando `status='confirmed'` (requiere extensión `btree_gist`).
- Índices: `(court, start_at)`, `start_at`.
