# ADR 0001 — Monorepo para motor, web y Unity

- **Estado:** aceptada
- **Fecha:** 2026-09-29

## Contexto

El proyecto tiene tres componentes: el motor Python, el dashboard web y el cliente Unity. Los tres dependen de un mismo contrato de datos (ruta, métricas y traza de eventos). El enunciado exige entregar una sola carpeta de código fuente, y el equipo es de tres personas con un único calendario de entregas.

## Decisión

Un solo repositorio con carpetas `engine/`, `web/` y `unity/`. Cada una se despliega por separado configurando el *Root Directory* de su plataforma (Render para `engine/`, Vercel para `web/`). La CI filtra por ruta.

## Consecuencias

- Un cambio en el contrato de eventos actualiza motor, web y Unity en un mismo commit y un mismo Pull Request.
- Un solo historial, README y flujo Git Flow para todo el equipo.
- El ZIP de la entrega final se arma directamente desde el repositorio.
- Hay que cuidar el `.gitignore` de cada tecnología (`node_modules/`, `Library/` de Unity, `.venv/`).
- Se descarta separar en dos repos: tiene sentido con equipos o ciclos de entrega independientes, que no es el caso.
