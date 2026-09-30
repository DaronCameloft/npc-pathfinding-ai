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
npc-nav comparar  --mapa den011d --caso 375          # los 4 algoritmos sobre la misma consulta
npc-nav buscar    --mapa den011d --caso 375 --algoritmo astar --traza --output results/astar/ejemplo_den011d.json
npc-nav validar   --output results/validacion_dataset.json
npc-nav verificar --algoritmo astar                  # 4 200 escenarios → results/astar/
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
| `algoritmo` | Clave del catálogo (`bfs`, `dijkstra`, `voraz`, `astar`). |
| `estado` | `encontrada` o `sin_ruta`. Un extremo no transitable lanza `ValueError`. |
| `ruta` | Posiciones del inicio al destino, ambos incluidos; vacía si no hay ruta. |
| `costo` | Suma de pesos; `None` sin ruta. No es el número de pasos. |
| `version_mapa` | Versión de los obstáculos usada en el cálculo. |
| `metricas` | `nodos_expandidos`, `nodos_descubiertos`, `max_frontera`, `tiempo_ms`. |
| `traza` | Eventos `frontera` / `expandido` con `posicion`, `g`, `h`, `padre` y `linea` (línea del pseudocódigo que los produjo); vacía si no se pidió. |

**Medición:** `tiempo_ms` se toma en una ejecución que solo cuenta nodos. Si se pide traza, el algoritmo se ejecuta otra vez para grabar los eventos; como es determinista, la traza corresponde exactamente a la ejecución medida y el tiempo nunca incluye la grabación, la red ni la animación.

## API HTTP

Servidor FastAPI que consumen el dashboard web y, más adelante, Unity. Solo traduce peticiones a `application/`; no contiene lógica de búsqueda.

```powershell
python -m pip install -e ".[api]"
uvicorn npc_nav.api.main:app --reload        # http://localhost:8000  (documentación interactiva en /docs)
```

Variable de entorno `CORS_ORIGINS`: orígenes adicionales separados por coma (por ejemplo, el dominio de Vercel). `http://localhost:5173` siempre está permitido. Las respuestas se comprimen con gzip.

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/health` | `{"estado": "ok", "version": "0.2.0"}` |
| GET | `/algoritmos` | Catálogo: `clave`, `nombre`, `garantiza_optimo`, `tecnica`, `complejidad`, `referencia` y `pseudocodigo` (`[{numero, texto, nivel}]`, el mismo del docstring). |
| GET | `/mapas` | Lista con `nombre`, `alto`, `ancho`, `vertices`, `escenarios`. |
| GET | `/mapas/{nombre}` | `alto`, `ancho` y `filas` de terreno (para dibujar en Canvas). |
| GET | `/mapas/{nombre}/escenarios?desde=0&limite=100` | Página de escenarios: `indice`, `bucket`, `inicio`, `destino`, `optimo`; `limite` máximo 1000. |
| POST | `/buscar` | Una `Ejecucion` (ver arriba). |
| POST | `/comparar` | Lista de `Ejecucion`, una por algoritmo, sobre la misma consulta y el mismo estado del mapa. |
| GET | `/evidencia` | Algoritmos con evidencia de verificación publicada (`engine/results/<algoritmo>/`). |
| GET | `/evidencia/{algoritmo}` | Resultado de `npc-nav verificar`: cifras globales, detalle por mapa, entorno, huellas del código y una nube de puntos (costo, nodos expandidos, tiempo) por escenario. 404 si no hay evidencia. |

Cuerpo de `POST /buscar`: `mapa`, `algoritmo` (por defecto `astar`), la consulta como `caso` (índice del `.scen`) **o** como `inicio` + `destino`, `traza` (bool) y `bloqueadas` (lista de celdas). `POST /comparar` recibe `algoritmos` en lugar de `algoritmo` (vacío = todos). Las posiciones son siempre `[fila, columna]`.

La API no guarda estado: cada petición crea su propia `SesionNavegacion` y aplica `bloqueadas` antes de buscar. Para replanificar tras un obstáculo, el cliente vuelve a enviar el conjunto completo de celdas bloqueadas.

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

Despliegue en Render: el `render.yaml` de la raíz define el servicio (root `engine`, build `pip install -e ".[api]"`, health check en `/health`); en el panel hay que asignar `CORS_ORIGINS`.
