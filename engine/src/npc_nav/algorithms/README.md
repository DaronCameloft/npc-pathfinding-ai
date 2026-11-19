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
| [`dstar_lite.py`](dstar_lite.py) | D* Lite | Búsqueda incremental en grafos (programación dinámica) | Sí | O(E log V) la primera vez; luego solo lo afectado | Replanificación ante obstáculos dinámicos |
| [`kruskal.py`](kruskal.py) | Kruskal | Árbol de expansión mínima (voraz + UFDS) | Sí (árbol mínimo) | O(E log E) | Red de patrullaje entre puntos de interés |
| [`edmonds_karp.py`](edmonds_karp.py) | Edmonds-Karp | Flujo en redes | Sí (flujo máximo) | O(V · E²) | NPC simultáneos en un pasillo y celdas críticas (corte mínimo) |
| [`mochila.py`](mochila.py) | Mochila 0/1 | Programación dinámica | Sí | O(n · W) | Botín que carga el NPC |

Archivos de soporte:

- [`contrato.py`](contrato.py): firma común `algoritmo(grafo, inicio, destino, observador) -> ResultadoBusqueda`, el `Observador` y `reconstruir_ruta`.
- [`pseudocodigo.py`](pseudocodigo.py): lee del docstring las líneas numeradas del pseudocódigo (número, texto y nivel de sangría).
- [`catalogo.py`](catalogo.py): registro de algoritmos que usan el CLI, la API y el dashboard (`ALGORITMOS` para rutas, `COMPLEMENTARIOS` para los otros tres).

## Cómo leer una búsqueda

Todos los algoritmos de ruta avisan al observador en dos momentos:

- `frontera(posicion, g, h, padre, linea)`: la celda entra a la frontera o mejora su costo conocido.
- `expandido(posicion, g, h, padre, linea)`: la celda sale de la frontera y se procesan sus vecinos.

`g` es el costo acumulado desde el inicio y `h` la estimación hasta el destino (distancia octil; vale 0 en BFS y Dijkstra). `linea` es el número de la línea del pseudocódigo (el docstring del archivo) que se está ejecutando: el inicio es la 1, extraer de la frontera es la 3 y descubrir o mejorar un vecino es la 9 en A* y Dijkstra (la 7 en BFS y voraz). Con esos eventos el dashboard dibuja la exploración y resalta la línea del pseudocódigo en ejecución; [`pseudocodigo.py`](pseudocodigo.py) lee esas líneas del docstring y la API las entrega en `/algoritmos`.

## D* Lite: búsqueda con memoria

`dstar_lite.py` tiene dos formas de uso:

- `dstar_lite(grafo, inicio, destino, observador)`: la firma común, para `/buscar`, `/comparar` y `npc-nav verificar`. Es una búsqueda sin cambios.
- `DStarLite(grafo, inicio, meta)`: el planificador con estado. `planificar()` hace la primera búsqueda y `replanificar(posicion, cambiadas)` repara tras cada cambio de obstáculos. Lo usa `application/navegacion.py`.

Diferencias con los demás algoritmos al leer la traza:

- Busca **desde la meta hacia el NPC**: el primer evento es la meta y el último expandido es la posición del NPC.
- `g` es el costo **hasta la meta**, y `h` la distancia octil desde el NPC. `g` puede ser `None` (infinito) cuando una celda pierde su camino.
- `frontera` = la celda queda inconsistente y entra a la cola (línea 5, o 9 si se reinserta). `expandido` = se extrae de la cola y se corrige (línea 8).
- Usa aritmética exacta `a + b·√2`, así los empates de clave son exactos (ver el docstring).

## Algoritmos complementarios: Kruskal, Edmonds-Karp y mochila

No buscan una ruta origen→destino, así que no usan la firma común ni entran en `/comparar`. Cada uno tiene su caso de uso en `application/` y su endpoint:

| Algoritmo | Caso de uso | Endpoint | CLI |
|---|---|---|---|
| Kruskal | `application/patrullaje.py`: A* da el costo de cada par de puntos de interés y Kruskal elige la red más corta que los une | `POST /patrullaje` | `npc-nav patrullaje` |
| Edmonds-Karp | `application/pasillo.py`: cada celda de una zona tiene capacidad 1; el flujo máximo es cuántos NPC cruzan a la vez y el corte mínimo, qué celdas cerrar | `POST /pasillo` | `npc-nav pasillo` |
| Mochila 0/1 | `application/botin.py`: la programación dinámica elige el botín; el voraz por densidad se muestra como contraste | `POST /botin` | `npc-nav botin` |

Avisan sus decisiones con `observador.paso(linea, **datos)` (`contrato.ObservadorPasos`): Kruskal en la línea 5 (entra al árbol) o 7 (ciclo), Edmonds-Karp en la 8 (cada camino aumentante) y la 9 (corte), la mochila en la 6 (fila completa) y la 9 (objeto elegido). `GET /complementarios` entrega su pseudocódigo.

## Agregar un algoritmo

1. Crear `nuevo.py` en esta carpeta con la firma de `contrato.Algoritmo` y el mismo formato de docstring. Cada aviso al observador lleva el número de la línea del pseudocódigo que ejecuta; las pruebas comprueban que ese número existe y que su texto corresponde al evento.
2. Registrarlo en `catalogo.py`.
3. Las pruebas de `tests/unit/test_algoritmos.py` recorren el catálogo: el nuevo algoritmo queda cubierto por el contrato común automáticamente. Si garantiza optimalidad, también se contrasta con el oráculo.
