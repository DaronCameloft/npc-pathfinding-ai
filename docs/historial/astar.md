# A*: búsqueda, verificación y datos para la web

Implementación en `src/npc_pathfinding/astar.py`. Utiliza el estado actual de `MotorNavegacion`: ocho direcciones, costo cardinal 1, diagonal raíz de 2 y diagonales permitidas solo si ambas celdas laterales están libres.

## Cómo encuentra la ruta

1. Valida que el inicio y el destino sean transitables.
2. Guarda el mejor costo conocido `g` desde el inicio y el padre de cada celda.
3. Prioriza la frontera mediante `f = g + h`, donde `h` es la distancia octil al destino:

   `h = max(df, dc) + (sqrt(2) - 1) * min(df, dc)`.

4. Extrae la celda de menor `f`, descarta entradas antiguas de la cola y mejora los costos de sus vecinos legales.
5. Al extraer el destino, reconstruye la ruta siguiendo los padres. Si se agota la frontera, devuelve `sin_ruta`.

La heurística octil es admisible y consistente con estos costos: estima el trayecto sin obstáculos, y los obstáculos solo eliminan movimientos. Por eso las celdas cerradas no necesitan reabrirse. En empates de `f`, se prefiere menor `h` y después el orden de inserción. Una misma consulta produce la misma ruta y los mismos eventos; el tiempo medido puede variar.

El grafo se consulta de forma implícita, sin construir toda la adyacencia para cada búsqueda. Con una cola binaria y entradas antiguas descartadas al extraerlas, el límite es `O((V + E) log V)` en tiempo y `O(V + E)` en memoria. En esta cuadrícula cada celda tiene como máximo ocho vecinos, por lo que se reduce a `O(V log V)` y `O(V)`. La traza opcional también ocupa memoria y no debe activarse en las mediciones por lotes.

## API Python

```python
from npc_pathfinding import MotorNavegacion, leer_mapa, leer_escenarios
from npc_pathfinding.astar import buscar_astar

mapa = leer_mapa('data/maps/den011d.map')
caso = leer_escenarios('data/scenarios/den011d.map.scen')[375]
motor = MotorNavegacion(mapa)
resultado = buscar_astar(motor, caso.inicio, caso.destino, registrar_traza=True)

assert resultado.estado == 'encontrada'
assert abs(motor.costo_ruta(resultado.ruta) - resultado.costo) <= 1e-5
```

Las posiciones son `(fila, columna)`. Los lectores convierten el `(x, y)` del `.scen`. Los índices de caso empiezan en cero; no son el campo `bucket`, que agrupa consultas del archivo.

`ResultadoBusqueda` contiene:

| Campo | Significado |
|---|---|
| `estado` | `encontrada` o `sin_ruta`. Un extremo inválido provoca `ValueError`. |
| `ruta` | Posiciones desde el inicio hasta el destino, incluidos ambos; vacía si no hay ruta. |
| `costo` | Suma de pesos de los pasos; `None` si no hay ruta, que se exporta como `null` en JSON. |
| `version_mapa` | Versión de los obstáculos al iniciar el cálculo. |
| `metricas` | Contadores y tiempo de esta búsqueda. |
| `traza` | Eventos para reproducir la exploración; vacía cuando no se solicita. |

Inicio igual a destino produce una ruta de una celda y costo cero. Un destino libre en otra componente produce `sin_ruta`. Después de bloquear o liberar celdas puede llamarse de nuevo a A*: realiza una búsqueda completa sobre el nuevo estado. Esto todavía no implementa una simulación continua del agente ni D* Lite. Los cambios deben aplicarse entre búsquedas; si la versión cambia durante el cálculo, se rechaza el resultado.

## Métricas

| Métrica | Definición |
|---|---|
| `nodos_expandidos` | Celdas extraídas con costo vigente para procesarlas, incluido el destino aunque no se generen sus vecinos. Cada celda se cuenta una vez. |
| `nodos_descubiertos` | Celdas distintas con un costo conocido, incluido el inicio. |
| `extracciones_cola` | Todas las extracciones del heap, incluidas las entradas antiguas descartadas. |
| `max_frontera` | Máximo de celdas distintas pendientes; no cuenta duplicados antiguos del heap. |
| `tiempo_ms` | Desde la preparación de la búsqueda hasta reconstruir la ruta y convertir la traza. Excluye lectura de archivos, validación externa de la ruta, exportación, red y animación. |

Con traza activada, el tiempo incluye crear los eventos. Las mediciones por lotes desactivan la traza. El costo de la ruta es distinto de su cantidad de pasos, pues los pasos diagonales pesan más.

## Traza para el dashboard

Cada evento tiene `tipo`, `posicion`, `g`, `h` y `padre`. El cliente puede calcular `f = g + h`.

- `frontera`: se descubre una celda o mejora su costo. Puede aparecer varias veces para la misma celda; el cliente actualiza sus datos.
- `expandido`: se procesa una celda con su mejor costo conocido. El cliente la retira de la frontera y la dibuja como examinada.

El resultado final proporciona la ruta para dibujarla y mover al agente. Estos eventos describen la búsqueda; los eventos de sesión, movimiento y obstáculos se añadirán con la simulación. La reproducción puede pausarse o avanzar paso a paso después del cálculo. Su reloj debe ser independiente de `tiempo_ms`.

Se conserva un ejemplo real en [../results/astar/ejemplo_den011d.json](../results/astar/ejemplo_den011d.json). El JSON incluye nombre de mapa, índice de caso, escenario original y resultado. Para dibujar el terreno, la web necesitará además las celdas del mapa mediante la futura API.

## Comandos reproducibles

Desde la raíz, después de instalar el paquete:

```powershell
python -m unittest discover -s tests -v
python -m npc_pathfinding.verificar_astar --output-dir results/astar
python -m npc_pathfinding.astar --mapa data/maps/den011d.map --escenarios data/scenarios/den011d.map.scen --caso 375 --traza --output results/astar/ejemplo_den011d.json
```

La verificación completa primero comprueba la integridad del dataset. Después calcula cada escenario estático, comprueba los extremos y todos los pasos de la ruta, vuelve a sumar sus pesos y contrasta el costo con la referencia. La tolerancia absoluta es `1e-5`: permite el redondeo decimal del `.scen` y la acumulación de números de punto flotante. Puede ajustarse con `--tolerancia`; debe ser positiva y finita.

Se producen `casos.csv` y `resumen.json`, con estado por consulta, error absoluto, métricas, entorno de ejecución y hashes SHA-256 de datos y fuentes. El comando termina con código 1 si encuentra discrepancias o datos inválidos. El resumen usa una ejecución por escenario; sus tiempos son descriptivos y no prueban comportamiento en tiempo real ni superioridad frente a otro algoritmo.

Las pruebas pequeñas cubren costos conocidos, esquinas, destinos inaccesibles, extremos inválidos, inicio igual a destino, cambios de obstáculos y traza. También contrastan 30 cuadrículas con una implementación de Dijkstra utilizada únicamente como oráculo de pruebas. Los `.scen` siguen siendo la referencia para los tres mapas originales; tras un cambio de obstáculos hay que calcular el nuevo óptimo.
