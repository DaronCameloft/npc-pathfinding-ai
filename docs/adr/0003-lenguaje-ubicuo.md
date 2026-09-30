# ADR 0003 — Motor sin dependencias y lenguaje ubicuo en español

- **Estado:** aceptada
- **Fecha:** 2026-09-29

## Contexto

El informe, la sustentación y el equipo trabajan en español, y el vocabulario del problema (mapa, sesión, frontera, expandido, costo, ruta) aparece en el informe y en las métricas exportadas. Por otro lado, los nombres de capas de arquitectura (`domain`, `application`, `infrastructure`) son convenciones de la industria.

## Decisión

- Carpetas de arquitectura en inglés (convención reconocible por cualquier desarrollador).
- Identificadores del dominio y de los algoritmos en español, iguales a los términos del informe (lenguaje ubicuo de DDD).
- El núcleo del motor usa solo la biblioteca estándar de Python. FastAPI y matplotlib son dependencias opcionales (`[api]`, `[figures]`).

## Consecuencias

- Lo que se lee en el informe se encuentra con el mismo nombre en el código.
- El motor se instala y prueba en segundos en cualquier máquina, en la CI y en Render.
- Las implementaciones de heap, cola y UFDS son propias o de la biblioteca estándar, visibles y explicables.
