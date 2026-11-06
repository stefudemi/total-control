# Roadmap y plan de entregas — Total Control (≈ 10–12 semanas)

| Semanas | Etapa / Hito | Contenido | Entregable TFI |
|---|---|---|---|
| 1 | **Etapa 0 – Diseño** | Arquitectura, ER, roadmap, documentación base | **Propuesta del proyecto** |
| 2 | **Etapa 1.1 – Canchas** | Setup Django + PostgreSQL, modelo/API/tests de canchas | |
| 3 | **Etapa 1.2 – Autenticación** | Login por token, permisos, roles | |
| 4–5 | **Etapa 1.3 – Clientes y turnos** | Reservas, disponibilidad, superposición, cancelación, tests | **Informe de avance 1** (modelo de datos, ER, backend) |
| 6 | **Cierre backend** | Endpoints agenda/día, documentación API, Postman, cobertura | Backend funcional |
| 7–8 | **Etapa 2.1 – Frontend base** | Vite+React, layout, login, dashboard, canchas | **Informe de avance 2** |
| 9 | **Etapa 2.2 – Turnos** | Formulario de reservas, agenda/calendario, manejo de errores | |
| 10 | **Etapa 3 – Integración** | Flujos completos, correcciones, seguridad básica, UX | |
| 11 | **Documentación final** | Manual de usuario, informe final, README | **Informe final** |
| 12 | **Presentación** | Video 5–10 min, ensayo de coloquio | **Video + coloquio** |

## Orden dentro del backend (Etapa 1)
1. Configuración inicial + PostgreSQL → 2. Canchas → 3. Autenticación → 4. Clientes → 5. Turnos y disponibilidad → 6. Cierre y documentación de la API.

## Criterios de avance
No se inicia un módulo si el anterior tiene tests fallando. Cada módulo termina con tests verdes, `PROJECT_CONTEXT.md` y `CHANGELOG.md` actualizados y commits pequeños en español.
