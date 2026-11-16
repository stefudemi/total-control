# Changelog

## [Sin publicar]
### Agregado
- Documentación de la Etapa 0: arquitectura, modelo de datos, roadmap y contexto del proyecto.
- Proyecto Django con PostgreSQL, DRF y CORS configurados por variables de entorno.
- Autenticación por token (login, logout, me), roles admin/empleado y gestión de usuarios (solo admin).
- Módulo Clientes: alta, edición, listado paginado con búsqueda y teléfono normalizado único.
- Módulo Reservas: creación con validación de RN2–RN5 y RN8, cancelación con auditoría, filtros e historial por cliente; restricción de exclusión en PostgreSQL (`btree_gist`).
- Agenda diaria (`/api/agenda/`) y disponibilidad que descuenta reservas confirmadas.
- RN7: no se puede desactivar una cancha con reservas futuras confirmadas.
- Comando `seed_demo` y documentación del contrato de la API (`docs/API.md`).
### Cambiado
- Crear, editar y activar/desactivar canchas pasó a ser exclusivo de administradores.
- Módulo Canchas: modelo, endpoints (crear, listar, editar, activar/desactivar, disponibilidad) y tests.
