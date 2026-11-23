# Modelo de datos — Total Control

Hay cuatro entidades. La central es la **reserva**: une una cancha con un cliente y guarda qué usuario la creó y quién la canceló.

```mermaid
erDiagram
    USER ||--o{ BOOKING : "crea / cancela"
    COURT ||--o{ BOOKING : "tiene"
    CLIENT ||--o{ BOOKING : "realiza"

    USER {
        int id PK
        string username
        bool is_staff
        bool is_active
    }
    COURT {
        int id PK
        string name UK
        string court_type "techada / descubierta"
        time opening_time
        time closing_time
        bool is_active
    }
    CLIENT {
        int id PK
        string first_name
        string last_name
        string phone UK
        string email "opcional"
    }
    BOOKING {
        int id PK
        int court_id FK
        int client_id FK
        int created_by_id FK
        datetime start_at
        int duration_minutes
        datetime end_at
        string status "confirmed / cancelled"
        int cancelled_by_id FK "nullable"
        datetime cancelled_at "nullable"
    }
```

La imagen del DER está en `docs/tfi/diagramas/der.png`.

## Detalles que vale la pena aclarar

- No se pueden borrar canchas ni clientes que tengan reservas (`PROTECT`).
- El teléfono del cliente es único. Lo guardamos solo con números, así el mismo cliente no queda cargado dos veces.
- Si se reserva para alguien nuevo, el cliente se crea en el mismo paso, buscándolo por teléfono.
- Guardamos `end_at` calculado. Una restricción de PostgreSQL (`ExclusionConstraint`, con `btree_gist`) impide que dos reservas confirmadas se pisen en la misma cancha.
