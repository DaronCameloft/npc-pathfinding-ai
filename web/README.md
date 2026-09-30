# web — dashboard de comparación (Vue 3 + Vite + TypeScript)

Se implementa en la rama `feature/web-dashboard`. Muestra el mapa, la exploración de cada algoritmo paso a paso, la ruta final y las métricas comparadas. No contiene lógica de búsqueda: todo viene de la API del motor.

## Estructura prevista

```
web/
├── src/
│   ├── core/                 tipos del contrato (Ejecucion, Evento, Metricas) y cliente HTTP
│   ├── features/
│   │   ├── mapa/             render del terreno en Canvas, zoom y selección de celdas
│   │   ├── reproduccion/     reloj de animación sobre la traza (play, pausa, paso, velocidad)
│   │   ├── comparacion/      paneles lado a lado y gráficos de métricas
│   │   └── pseudocodigo/     panel que resalta la línea en ejecución
│   ├── shared/               componentes de UI y utilidades
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── package.json
└── vite.config.ts
```

## Configuración

- `VITE_API_URL`: URL de la API (Render en producción, `http://localhost:8000` en local).
- Despliegue en Vercel con *Root Directory* = `web`.

## Reglas

- El reloj de animación es independiente de `tiempo_ms`, que se muestra tal cual lo mide el motor.
- Las posiciones llegan como `[fila, columna]`.
- Mostrar un estado de carga mientras la API de Render despierta.
