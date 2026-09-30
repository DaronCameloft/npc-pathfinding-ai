# Algoritmos

Esta carpeta contiene **todo lo que el equipo expone en la sustentación**. Cada algoritmo vive en su propio archivo con la misma estructura:

1. Docstring con referencia bibliográfica, **pseudocódigo numerado** y propiedades (optimalidad y complejidad).
2. Código cuyos comentarios `# 1.`, `# 2.`… corresponden a las líneas del pseudocódigo.
3. Nada de medición, archivos ni red: los tiempos y contadores los toma `application/busqueda.py` a través del observador.

| Archivo | Algoritmo | Técnica del curso | ¿Óptimo? | Complejidad | Rol en el proyecto |
|---|---|---|---|---|---|
| [`bfs.py`](bfs.py) | Búsqueda en anchura | Recorridos y búsquedas en grafos | No (minimiza pasos, no costo) | O(V + E) | Línea base sin pesos |
| [`dijkstra.py`](dijkstra.py) | Dijkstra | Recorridos y búsquedas en grafos | Sí | O(E log V) | Óptimo sin heurística |
| [`voraz.py`](voraz.py) | Voraz primero el mejor | Algoritmos voraces | No | O(E log V) | Rápido pero engañable |
| [`astar.py`](astar.py) | A* | Voraces (heurístico) + búsqueda en grafos | Sí | O(E log V) | Algoritmo principal |
| [`ufds.py`](ufds.py) | Union-Find | UFDS | — | O(E · α(V)) | Regiones conectadas / descarte de consultas imposibles |
| `dstar_lite.py` | D* Lite | Búsqueda incremental | Sí | — | Siguiente hito: replanificación ante obstáculos |

Archivos de soporte:

- [`contrato.py`](contrato.py): firma común `algoritmo(grafo, inicio, destino, observador) -> ResultadoBusqueda`, el `Observador` y `reconstruir_ruta`.
- [`catalogo.py`](catalogo.py): registro de algoritmos que usan el CLI, la API y el dashboard.

## Cómo leer una búsqueda

Todos los algoritmos de ruta avisan al observador en dos momentos:

- `frontera(posicion, g, h, padre)`: la celda entra a la frontera o mejora su costo conocido.
- `expandido(posicion, g, h, padre)`: la celda sale de la frontera y se procesan sus vecinos.

`g` es el costo acumulado desde el inicio y `h` la estimación hasta el destino (distancia octil; vale 0 en BFS y Dijkstra). Con esos dos eventos el dashboard dibuja la exploración y resalta la línea del pseudocódigo en ejecución.

## Agregar un algoritmo

1. Crear `nuevo.py` en esta carpeta con la firma de `contrato.Algoritmo` y el mismo formato de docstring.
2. Registrarlo en `catalogo.py`.
3. Las pruebas de `tests/unit/test_algoritmos.py` recorren el catálogo: el nuevo algoritmo queda cubierto por el contrato común automáticamente. Si garantiza optimalidad, también se contrasta con el oráculo.
