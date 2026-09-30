# Navegación de NPCs — Complejidad Algorítmica

Proyecto del curso **1ACC0184 Complejidad Algorítmica** (UPC, 2026-20), caso *Juegos y AI (pathfinding)*: un sistema de navegación para NPCs que encuentra rutas óptimas, evita obstáculos dinámicos y es eficiente en tiempo real, sobre mapas reales de *Dragon Age: Origins* (Moving AI Lab).

Un motor en Python calcula las rutas y mide cada algoritmo. Un dashboard web muestra la exploración paso a paso y compara los resultados, y Unity representa a un personaje recorriendo el mapa.

## Monorepo

```
.
├── engine/     Motor Python: dominio, algoritmos, casos de uso, CLI y API
│   └── src/npc_nav/algorithms/   ← BFS, Dijkstra, voraz, A*, UFDS
├── web/        Dashboard (Vue 3 + Vite + TypeScript)        → Vercel
├── unity/      Cliente 3D (Unity, C#)                       → siguiente hito
└── docs/       Arquitectura, ADR, plan, informe y figuras
```

Web y Unity no contienen lógica de búsqueda: consumen la API del motor. Detalle en [docs/arquitectura.md](docs/arquitectura.md).

## Algoritmos

| Algoritmo | Archivo | ¿Óptimo? |
|---|---|---|
| BFS | [`bfs.py`](engine/src/npc_nav/algorithms/bfs.py) | No |
| Dijkstra | [`dijkstra.py`](engine/src/npc_nav/algorithms/dijkstra.py) | Sí |
| Voraz primero el mejor | [`voraz.py`](engine/src/npc_nav/algorithms/voraz.py) | No |
| A* | [`astar.py`](engine/src/npc_nav/algorithms/astar.py) | Sí |
| UFDS (regiones) | [`ufds.py`](engine/src/npc_nav/algorithms/ufds.py) | — |
| D* Lite | siguiente hito | Sí |

Cada archivo incluye su pseudocódigo numerado, complejidad y referencia. Índice completo en [algorithms/README.md](engine/src/npc_nav/algorithms/README.md).

## Inicio rápido

```powershell
cd engine
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m unittest discover -s tests -t .
npc-nav comparar --mapa den011d --caso 375
```

Para ver el dashboard (necesita la API y Node 20 o superior):

```powershell
cd engine
python -m pip install -e ".[api]"
uvicorn npc_nav.api.main:app --reload      # API en http://localhost:8000  (documentación en /docs)

cd ..\web                                   # en otra terminal
npm install
npm run dev                                 # dashboard en http://localhost:5173
```

## Estado

| Componente | Estado |
|---|---|
| Motor, dominio y dataset | Listo: 3 mapas, 71 174 vértices, 4 200 escenarios validados |
| BFS, Dijkstra, voraz, A*, UFDS | Listos y probados; A* coincide con los 4 200 óptimos publicados |
| API (FastAPI) | Lista: búsqueda, comparación, mapas, escenarios y evidencia de verificación; `render.yaml` para Render |
| Dashboard web (ArcadiaLabs) | Listo: Inicio, Explorar, Comparar, Resultados y Acerca; pendiente su despliegue en Vercel (entrega del 4 de octubre) |
| D* Lite y obstáculos dinámicos | Hito 2 |
| Unity | Hito 2 |

## Equipo

| Código | Integrante |
|---|---|
| u202416274 | Victor Paredes Maza |
| u202415749 | Diana Carolina Li Gayoso |
| u202412248 | Jahat Jassiel Trinidad León |

Flujo de trabajo, ramas y convención de commits en [CONTRIBUTING.md](CONTRIBUTING.md).

## Datos

Mapas y escenarios de [Moving AI Lab](https://www.movingai.com/benchmarks/dao/index.html) (Sturtevant, 2012), redistribuidos con permiso de BioWare bajo Open Data Commons Attribution. Ver [engine/data/README.md](engine/data/README.md).
