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
│   └── api/             FastAPI para la web y Unity (feature/engine-api)
├── tests/
│   ├── unit/            dominio, algoritmos, casos de uso y lectores
│   └── integration/     dataset real, validación, verificación y CLI
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
| `traza` | Eventos `frontera` / `expandido` con `posicion`, `g`, `h`, `padre`; vacía si no se pidió. |

**Medición:** `tiempo_ms` se toma en una ejecución que solo cuenta nodos. Si se pide traza, el algoritmo se ejecuta otra vez para grabar los eventos; como es determinista, la traza corresponde exactamente a la ejecución medida y el tiempo nunca incluye la grabación, la red ni la animación.
