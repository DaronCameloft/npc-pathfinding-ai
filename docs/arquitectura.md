# Arquitectura

## Vista general

```
                ┌─────────────────────┐        ┌──────────────────────┐
                │  web/ (Vue + Vite)  │        │  unity/ (C#)         │
                │  dashboard 2D       │        │  personaje 3D        │
                └──────────┬──────────┘        └──────────┬───────────┘
                           │  HTTP / WebSocket (JSON)     │
                           └──────────────┬───────────────┘
                                          ▼
┌───────────────────────────── engine/ (npc_nav) ─────────────────────────────┐
│  api/  cli/             interfaces: traducen peticiones, no tienen lógica   │
│        │                                                                    │
│        ▼                                                                    │
│  application/           casos de uso: ejecutar, comparar, validar, verificar│
│        │           ╲                                                        │
│        ▼            ╲──────────► infrastructure/  (inyectada)               │
│  algorithms/            BFS · Dijkstra · voraz · A* · UFDS   lectores .map  │
│        │                                                     exportadores   │
│        ▼                                                                    │
│  domain/                Mapa · reglas de movimiento · SesionNavegacion      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Regla de dependencias:** cada capa solo importa capas más internas. `domain` no importa nada del proyecto; `algorithms` solo importa `domain`; `application` recibe la infraestructura (el repositorio del dataset) como parámetro en lugar de importarla. Así los algoritmos se prueban con mapas de 3×3 escritos en la prueba, sin archivos.

## Capas

| Capa | Responsabilidad | No debe |
|---|---|---|
| `domain/` | Terreno inmutable, movimiento octil (costos 1 y √2, sin cortar esquinas), heurística octil, obstáculos por sesión con versión. | Leer archivos, medir tiempos, conocer algoritmos. |
| `algorithms/` | Un algoritmo por archivo, con pseudocódigo numerado. Avisa sus pasos a un `Observador`. | Medir, contar, exportar ni validar entradas. |
| `application/` | Orquestar: validar la consulta, inyectar observadores, medir tiempo, producir `Ejecucion`, comparar, verificar contra los `.scen`. | Conocer HTTP, Vue o Unity. |
| `infrastructure/` | Formato Moving AI, repositorio con caché, JSON/CSV y hashes. | Contener reglas del problema. |
| `api/`, `cli/` | Traducir la entrada, llamar un caso de uso y serializar la salida. | Implementar lógica de búsqueda. |

## El observador: algoritmos legibles y medibles

Los algoritmos no contienen cronómetros ni contadores. Reciben un observador y lo llaman en dos momentos: `frontera(pos, g, h, padre)` y `expandido(pos, g, h, padre)`. La aplicación decide qué observador pasar:

- `_Contador`: cuenta nodos expandidos, descubiertos y el tamaño máximo de la frontera. Se usa en la ejecución cronometrada.
- `_Grabador`: guarda los eventos para el dashboard. Se usa en una segunda ejecución, fuera del tiempo medido.

Así el código que se explica en la sustentación coincide línea por línea con el pseudocódigo, y todas las métricas se obtienen de la misma forma para todos los algoritmos, lo que hace justa la comparación.

## Contrato de datos hacia web y Unity

Una búsqueda se serializa como:

```json
{
  "algoritmo": "astar",
  "estado": "encontrada",
  "ruta": [[fila, columna], ...],
  "costo": 148.2548,
  "version_mapa": 0,
  "metricas": { "nodos_expandidos": 2080, "nodos_descubiertos": 2226, "max_frontera": 247, "tiempo_ms": 40.3 },
  "traza": [ { "tipo": "frontera", "posicion": [75, 61], "g": 0.0, "h": 135.95, "padre": null, "linea": 1 }, ... ]
}
```

`linea` es el número de la línea del pseudocódigo del algoritmo que produjo el evento. `GET /algoritmos` entrega ese pseudocódigo (`[{numero, texto, nivel}]`, leído del docstring del algoritmo), de modo que el dashboard puede mostrarlo junto al mapa y resaltar la línea en ejecución mientras reproduce la traza.

Posiciones siempre `(fila, columna)`. Web y Unity reproducen la traza con su propio reloj de animación, independiente de `tiempo_ms`.

## Despliegue

| Parte | Plataforma | Root Directory | Arranque |
|---|---|---|---|
| `engine/` (API) | Render | `engine` | `pip install -e ".[api]"` → `uvicorn npc_nav.api.main:app --host 0.0.0.0 --port $PORT` |
| `web/` | Vercel | `web` | `npm run build` → `dist/` |

Cada plataforma solo redespliega cuando cambia su carpeta. La variable `VITE_API_URL` de Vercel apunta a la URL de Render.

## Decisiones

Las decisiones de arquitectura se registran en [adr/](adr/).
