# engine — motor de navegación (Python)

Paquete `npc_nav`: modela los mapas Moving AI como grafos, ejecuta los algoritmos de búsqueda y mide su trabajo. El núcleo usa **solo la biblioteca estándar** de Python 3.10+.

## Estructura

```
engine/
├── src/npc_nav/
│   ├── algorithms/      ← BFS, Dijkstra, voraz, A*, UFDS (ver su README)
│   ├── domain/          mapa, reglas de movimiento octil, sesión con obstáculos
│   ├── application/     casos de uso: ejecutar, comparar, analizar, validar, verificar
│   ├── infrastructure/  lectores .map/.scen, repositorio del dataset, exportadores
│   ├── cli/             comando npc-nav
│   └── api/             FastAPI para la web y Unity (main, rutas, esquemas)
├── tests/
│   ├── unit/            dominio, algoritmos, casos de uso y lectores
│   └── integration/     dataset real, validación, verificación, CLI y API
├── tools/tb1/           generación de figuras del informe TB1 (matplotlib)
├── data/                mapas y escenarios de Dragon Age: Origins
└── results/             evidencia reproducible (JSON/CSV)
```

Regla de dependencias: `cli/api → application → algorithms → domain`, con `infrastructure` inyectada desde afuera. `domain` y `algorithms` no importan nada de las capas externas. Detalle en [docs/arquitectura.md](../docs/arquitectura.md).

## Instalación

Desde `engine/`, en PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Extras opcionales: `pip install -e ".[api]"` para el servidor y `pip install -e ".[figures]"` para las figuras del TB1.

En PyCharm: *Settings → Python Interpreter → Add Interpreter → Existing* y elige `engine\.venv\Scripts\python.exe`; luego clic derecho en `engine/src` → *Mark Directory as → Sources Root* y en `engine/tests` → *Test Sources Root*.

## Uso

```powershell
npc-nav algoritmos                                   # catálogo
npc-nav analizar  --mapa brc201d                     # estadísticas del grafo (TB1)
npc-nav comparar  --mapa den011d --caso 375          # los 5 algoritmos sobre la misma consulta
npc-nav buscar    --mapa den011d --caso 375 --algoritmo astar --traza --output results/astar/ejemplo_den011d.json
npc-nav validar   --output results/validacion_dataset.json
npc-nav verificar --algoritmo astar                  # 4 200 escenarios → results/astar/
npc-nav verificar --algoritmo dstar_lite             # 4 200 escenarios → results/dstar_lite/
npc-nav experimentar                                 # obstáculos dinámicos A* vs D* Lite → results/dinamico/
npc-nav patrullaje --mapa den011d                    # Kruskal: red de patrullaje entre 7 puntos de interés
npc-nav pasillo --mapa den011d --zona 24,156,71,203 --direccion vertical   # Edmonds-Karp: flujo 3, corte de 3 celdas
npc-nav botin --capacidad 20                         # mochila 0/1: PD 113 frente a voraz 99
```

Pruebas:

```powershell
python -m unittest discover -s tests -t .
```

Desde Python:

```python
from npc_nav.application import ejecutar_busqueda
from npc_nav.domain import SesionNavegacion
from npc_nav.infrastructure import RepositorioDataset

repo = RepositorioDataset()
caso = repo.escenario('den011d', 375)
sesion = SesionNavegacion(repo.mapa('den011d'))

ejecucion = ejecutar_busqueda(sesion, 'astar', caso.inicio, caso.destino, con_traza=True)
sesion.actualizar_obstaculos(bloquear=[ejecucion.ruta[40]])            # obstáculo dinámico
replanificada = ejecutar_busqueda(sesion, 'astar', ejecucion.ruta[39], caso.destino)
```

## Reglas del modelo

- Posiciones `(fila, columna)` con origen arriba a la izquierda. Los `.scen` usan `(x, y)` y se convierten al leerlos.
- Solo `.` y `G` son transitables; `@ O T S W` son obstáculos.
- 4 movimientos cardinales de costo 1 y 4 diagonales de costo √2; una diagonal exige libres las dos celdas laterales (no se cortan esquinas).
- La distancia octil `max(df, dc) + (√2 − 1)·min(df, dc)` es la heurística admisible y consistente.
- Cada `SesionNavegacion` tiene sus propios obstáculos y una `version` que aumenta con cada cambio efectivo.

## Resultado de una búsqueda

`ejecutar_busqueda` devuelve una `Ejecucion`:

| Campo | Significado |
|---|---|
| `algoritmo` | Clave del catálogo (`bfs`, `dijkstra`, `voraz`, `astar`, `dstar_lite`). |
| `estado` | `encontrada` o `sin_ruta`. Un extremo no transitable lanza `ValueError`. |
| `ruta` | Posiciones del inicio al destino, ambos incluidos; vacía si no hay ruta. |
| `costo` | Suma de pesos; `None` sin ruta. No es el número de pasos. |
| `version_mapa` | Versión de los obstáculos usada en el cálculo. |
| `metricas` | `nodos_expandidos`, `nodos_descubiertos`, `max_frontera`, `tiempo_ms`. |
| `traza` | Eventos `frontera` / `expandido` con `posicion`, `g`, `h`, `padre` y `linea` (línea del pseudocódigo que los produjo); vacía si no se pidió. |

**Medición:** `tiempo_ms` se toma en una ejecución que solo cuenta nodos. Si se pide traza, el algoritmo se ejecuta otra vez para grabar los eventos; como es determinista, la traza corresponde exactamente a la ejecución medida y el tiempo nunca incluye la grabación, la red ni la animación.

## API HTTP

Servidor FastAPI que consumen el dashboard web y Unity. Solo traduce peticiones a `application/`; no contiene lógica de búsqueda.

```powershell
python -m pip install -e ".[api]"
uvicorn npc_nav.api.main:app --reload        # http://localhost:8000  (documentación interactiva en /docs)
```

Variable de entorno `CORS_ORIGINS`: orígenes adicionales separados por coma (por ejemplo, el dominio de Vercel). `http://localhost:5173` siempre está permitido. Las respuestas se comprimen con gzip.

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/health` | `{"estado": "ok", "version": "1.1.0"}` |
| GET | `/algoritmos` | Catálogo: `clave`, `nombre`, `garantiza_optimo`, `incremental`, `tecnica`, `complejidad`, `referencia` y `pseudocodigo` (`[{numero, texto, nivel}]`, el mismo del docstring). |
| GET | `/mapas` | Lista con `nombre`, `alto`, `ancho`, `vertices`, `escenarios`. |
| GET | `/mapas/{nombre}` | `alto`, `ancho` y `filas` de terreno (para dibujar en Canvas). |
| GET | `/mapas/{nombre}/escenarios?desde=0&limite=100` | Página de escenarios: `indice`, `bucket`, `inicio`, `destino`, `optimo`; `limite` máximo 1000. |
| POST | `/buscar` | Una `Ejecucion` (ver arriba). |
| POST | `/comparar` | Lista de `Ejecucion`, una por algoritmo, sobre la misma consulta y el mismo estado del mapa. |
| POST | `/simular` | Navegación dinámica completa y sin estado: el NPC recorre la ruta y los `cambios` ocurren a su paso (ver abajo). |
| POST | `/sesiones` | Abre una navegación con estado (201). |
| GET | `/sesiones/{id}` | Estado de la sesión. |
| POST | `/sesiones/{id}/avanzar` | `{"pasos": n}`: el NPC avanza por la ruta del guía. |
| POST | `/sesiones/{id}/obstaculos` | `{"bloquear": [...], "liberar": [...], "traza": false}`: replanifica todos los algoritmos desde la posición actual. |
| DELETE | `/sesiones/{id}` | Cierra la sesión (204). |
| GET | `/complementarios` | Kruskal, Edmonds-Karp y mochila 0/1: `clave`, `nombre`, `tecnica`, `complejidad`, `referencia`, `caso_de_uso` y `pseudocodigo`. |
| POST | `/patrullaje` | Kruskal: red de patrullaje entre puntos de interés (ver abajo). |
| POST | `/pasillo` | Edmonds-Karp: flujo máximo y corte mínimo de una zona (ver abajo). |
| POST | `/botin` | Mochila 0/1 por programación dinámica, con el voraz como contraste (ver abajo). |
| GET | `/evidencia` | Algoritmos con evidencia de verificación publicada (`engine/results/<algoritmo>/`). |
| GET | `/evidencia/{algoritmo}` | Resultado de `npc-nav verificar`: cifras globales, detalle por mapa, entorno, huellas del código y una nube de puntos (costo, nodos expandidos, tiempo) por escenario. 404 si no hay evidencia. |

Cuerpo de `POST /buscar`: `mapa`, `algoritmo` (por defecto `astar`), la consulta como `caso` (índice del `.scen`) **o** como `inicio` + `destino`, `traza` (bool) y `bloqueadas` (lista de celdas). `POST /comparar` recibe `algoritmos` en lugar de `algoritmo` (vacío = todos). Las posiciones son siempre `[fila, columna]`.

`/buscar` y `/comparar` no guardan estado: cada petición crea su propia `SesionNavegacion` y aplica `bloqueadas` antes de buscar.

### Obstáculos dinámicos: `/simular` y `/sesiones`

Ambos usan `application/navegacion.py`: **un NPC, un estado de obstáculos y varios planificadores** que reciben los mismos cambios desde la misma posición. `algoritmos` (por defecto `["astar", "dstar_lite"]`) define cuáles; el primero es el **guía** y el NPC sigue su ruta. A* (y cualquier algoritmo no incremental) vuelve a buscar desde cero; D* Lite conserva su estado y solo repara lo afectado.

- `POST /simular`: `mapa`, `caso` o `inicio`/`destino`, `algoritmos`, `bloqueadas`, `traza` y `cambios: [{"paso": n, "bloquear": [...], "liberar": [...]}]`. Devuelve `recorrido`, `distancia_recorrida`, `llegado`, `costos_coinciden`, un `resumen` por algoritmo (replanificaciones, celdas y tiempo de la búsqueda inicial y de las replanificaciones) y el `historial` de planificaciones. No depende de que el servidor recuerde nada: es lo que usa el dashboard.
- `/sesiones`: para clientes en tiempo real (Unity). Cada respuesta trae `posicion`, `ruta_restante`, `bloqueadas`, `vigentes` (la última planificación de cada algoritmo) y `nuevas` (las producidas por esa llamada). Cada planificación tiene `motivo`, `estado`, `posicion`, `paso` (movimientos que llevaba el NPC), `ruta`, `costo`, `celdas_cambiadas`, `ruta_afectada` y `metricas`. Las sesiones viven en memoria: expiran tras 30 min sin uso o si el servidor se reinicia (Render se duerme), y entonces responden 404 y el cliente abre otra.

No se puede bloquear la celda del NPC ni el destino (422).

### Algoritmos complementarios: `/patrullaje`, `/pasillo` y `/botin`

No buscan una ruta origen→destino; cada uno tiene su caso de uso en `application/` (ver `src/npc_nav/algorithms/README.md`).

- `POST /patrullaje`: `mapa` y `puntos` (2 a 10 celdas) **o** `cantidad` + `semilla` para sortearlos en la región más grande. A* da el costo de cada par y Kruskal elige el árbol. Devuelve `puntos`, `candidatas` (pares con ruta, de menor a mayor costo), `sin_ruta`, `decisiones` (`aceptada` y `linea`: 5 entra al árbol, 7 cerraría un ciclo), `arbol`, `costo_arbol`, `costo_candidatas`, `componentes` y los tiempos de A* y de Kruskal.
- `POST /pasillo`: `mapa`, `zona` `[fila0, col0, fila1, col1]` (máximo 64 celdas por lado), `direccion` (`horizontal` o `vertical`) y `bloqueadas`. Cada celda tiene capacidad 1. Devuelve `flujo_maximo` (NPC que cruzan a la vez sin compartir celdas), `caminos`, `corte` (celdas que cierran el paso), `aumentos` (cada camino aumentante), `entradas`, `salidas`, `celdas` y `tiempo_ms`.
- `POST /botin`: `capacidad` (0 a 100) y `objetos` opcionales (`nombre`, `peso`, `valor`; sin ellos se usa el botín de ejemplo). Devuelve `optima` (programación dinámica), `voraz` (por valor/peso), la `tabla` completa y la `reconstruccion`.

Errores: mapa o algoritmo inexistente → `404`; caso fuera de rango, extremos no transitables, bloqueos inválidos o una consulta que mezcla `caso` con `inicio`/`destino` → `422` con el mensaje en español en `detail`.

```powershell
curl -X POST http://localhost:8000/buscar -H "Content-Type: application/json" `
  -d '{"mapa": "den011d", "caso": 375, "algoritmo": "astar", "bloqueadas": [[81, 63]]}'
```

```json
{
  "algoritmo": "astar",
  "estado": "encontrada",
  "ruta": [[75, 61], [76, 62], [77, 63], [78, 63], "..."],
  "costo": 148.8406,
  "version_mapa": 1,
  "metricas": {"nodos_expandidos": 2094, "nodos_descubiertos": "...", "max_frontera": "...", "tiempo_ms": "..."},
  "traza": []
}
```

(Sin `bloqueadas` el caso 375 cuesta 148.2548 con 2 080 expandidos; al bloquear la celda `[81, 63]`, que estaba en la ruta, A* rodea el obstáculo y el costo sube a 148.8406.) Con `"traza": true` el campo `traza` trae los eventos `{"tipo": "frontera" | "expandido", "posicion", "g", "h", "padre", "linea"}`; el caso 375 genera unos 6 000. `linea` es el número de `pseudocodigo` que se ejecuta en ese evento; el dashboard resalta esa línea mientras reproduce la traza.

## Experimento dinámico

```powershell
npc-nav experimentar                     # 30 escenarios × 5 eventos por mapa, semilla 2026
npc-nav experimentar --mapa den011d --casos 10 --eventos 3 --output-dir ruta/
```

Para cada escenario (elegido con la semilla entre la mitad con rutas más largas) el NPC avanza y ocurren eventos `bloqueo_ruta`, `pasillo` (bloque de 3×3 en la ruta), `lejano` (no toca la ruta) y `desbloqueo`. A* y D* Lite reciben los mismos cambios y se comprueba que cada par de planificaciones tenga el mismo costo. Salida en `results/dinamico/`: `resumen.json` (medianas y totales por mapa y por tipo de evento, entorno y huellas del código) y `planificaciones.csv` (una fila por algoritmo y planificación).

Despliegue en Render: el `render.yaml` de la raíz define el servicio (root `engine`, build `pip install -e ".[api]"`, health check en `/health`); en el panel hay que asignar `CORS_ORIGINS`.
