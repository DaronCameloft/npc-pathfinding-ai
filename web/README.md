# web — Arcadia Ariadna Labs (Vue 3 + Vite + TypeScript)

Dashboard que muestra la exploración de cada algoritmo paso a paso, la ruta final y las métricas comparadas. No contiene lógica de búsqueda: todo viene de la API del motor.

## Pantallas

| Ruta | Contenido |
|---|---|
| `/` | Inicio: presentación, cifras del dataset y accesos rápidos. |
| `/explorar` | Un algoritmo sobre un caso: mapa en Canvas (zoom, arrastre, hover), pseudocódigo con la línea en ejecución y conteos, narración, métricas y bloqueo de celdas con recálculo. |
| `/comparar` | BFS, Dijkstra, voraz y A* sobre la misma consulta con una sola línea de tiempo, y resumen con barras. |
| `/resultados` | Evidencia de la verificación (pendiente). |
| `/acerca` | Algoritmos, datos, equipo y declaración de uso de IA. |

Atajos en Explorar y Comparar: `Espacio` reproduce o pausa, `←` `→` avanzan un evento (con `Shift`, 50), `Inicio` y `Fin` saltan a los extremos.

## Desarrollo

```powershell
cd web
npm install
npm run dev          # http://localhost:5173  (el puerto es fijo: la API solo permite ese origen)
npm run typecheck
npm run build
```

Requiere la API en marcha (`uvicorn npc_nav.api.main:app --reload` desde `engine/`). `VITE_API_URL` apunta a la API (`http://localhost:8000` por defecto; en Vercel, la URL de Render). Ver `.env.example`.

## Estructura

```
web/src/
├── core/            contrato de datos (types.ts), cliente HTTP (api.ts) y estado del motor (motor.ts)
├── features/
│   ├── mapa/            MapCanvas: terreno y exploración en lienzos fuera de pantalla, ruta animada
│   ├── reproduccion/    usePlayback (reloj de animación) y PlaybackDock
│   ├── pseudocodigo/    panel con la línea activa, conteos por línea y narración
│   └── comparacion/     panel por algoritmo y resumen
├── shared/          Sidebar, Segmented, CasoSelector, AnimatedNumber, iconos
├── styles/          tokens de diseño (color, vidrio, movimiento) y base
└── views/           una vista por ruta
```

## Reglas

- El reloj de animación es independiente de `tiempo_ms`, que se muestra tal cual lo mide el motor.
- Las posiciones llegan como `[fila, columna]`.
- Mientras la API de Render despierta, la barra lateral muestra «Despertando el motor…».
- Diseño: tipografía Newsreader (titulares), Poppins (interfaz) y JetBrains Mono (pseudocódigo); tema claro; movimiento con curvas de resorte que respeta `prefers-reduced-motion`.

## Despliegue

Vercel con *Root Directory* = `web`. `vercel.json` reenvía todas las rutas a `index.html`.
