# Revisión del proyecto después de implementar A*

Fecha: 27 de septiembre de 2026, hora de Lima. El resumen de ejecución utiliza UTC y por eso registra el 28 de septiembre.

## Resultado de esta fase

**La base y A* cumplen los criterios de esta etapa.** Se comprobaron los 4 200 escenarios de los tres mapas originales: todos producen rutas legales y costos coincidentes con la referencia dentro de `1e-5`. El directorio contiene fuentes, pruebas, datos y evidencia que permiten repetir la comprobación. El siguiente trabajo es el dashboard inicial.

| Mapa | Escenarios aprobados | Fallidos | Mayor error absoluto |
|---|---:|---:|---:|
| `den011d.map` | 750 / 750 | 0 | `3.09e-8` |
| `brc201d.map` | 2 090 / 2 090 | 0 | `1.07e-7` |
| `brc100d.map` | 1 360 / 1 360 | 0 | `8.95e-8` |

La comprobación incluye extremos, transitabilidad de todos los pasos, ausencia de corte de esquinas y suma de pesos. Se compara el costo, no la forma exacta de la ruta: un escenario puede tener varias rutas óptimas. [El resumen](../results/astar/resumen.json) registra datos, código y entorno; [el CSV](../results/astar/casos.csv) conserva una fila por consulta.

## Revisión por directorio

| Área | Estado y comprobación |
|---|---|
| `data/` | Tres `.map` y sus tres `.map.scen`, sin escenarios ajenos al estudio. Cabeceras, dimensiones, coordenadas, costos y componentes validados. Conteos y hashes coinciden con los resultados. |
| `src/npc_pathfinding/` | Modelos, lectores, motor y A* comparten coordenadas y reglas de movimiento. El CLI del lote comprueba rutas y exporta JSON/CSV. Grafo y UFDS conservan el análisis estático. |
| `tests/` | 27 pruebas pasan. Incluyen entradas inválidas, costos conocidos, diagonales, destino inaccesible, inicio igual a destino, aislamiento de sesiones, obstáculos, traza y detección de un costo de referencia erróneo. Hay un contraste adicional en 30 mapas pequeños con Dijkstra. |
| `results/` | Integridad del dataset, lote A* completo y ejemplo de ruta con traza. Los resultados temporales de instalación están en `results/tmp/`, excluido de Git. |
| `docs/` | Contrato del motor, documentación de A*, plan y revisión actualizados. Se conservan las nueve figuras de TB1 y los PDF disponibles. |
| `web/` | Preparado mediante README y contrato de eventos. Todavía no contiene frontend ni servicio HTTP. |
| `unity/` | Preparado mediante README. Todavía no contiene un proyecto Unity ni integración con Python. |
| Raíz | `pyproject.toml` empaqueta los módulos; README contiene instalación y comandos. La búsqueda de archivos no encontró un `AGENTS.md`. No hay carpeta `.git`: aún no existe historial de Git en este directorio. |

## Instalación y trazabilidad

Se construyó un wheel de `npc-pathfinding-tb2` y se instaló sin dependencias en una carpeta aislada del directorio. Una ejecución con Python en modo aislado importó A* desde esa instalación y calculó correctamente el caso 375 de `den011d`, con ruta, costo y 6 090 eventos. Esto comprueba que los módulos nuevos están incluidos en el paquete; no sustituye la futura prueba de instalación del entregable completo con web y Unity.

El motor, A* y las pruebas usan la biblioteca estándar. La regeneración de figuras necesita la dependencia opcional `matplotlib`; no se ejecutó en esta revisión porque no está instalada en el runtime utilizado. Las figuras existentes se conservaron.

El lote guarda hashes SHA-256 de los tres pares de datos y de los módulos del motor y la búsqueda. La revisión final contrasta esos hashes con los archivos actuales y comprueba el número y el estado de las filas CSV, la estructura del ejemplo JSON y los enlaces locales de Markdown.

La comprobación final aprobó 4 200 consultas únicas, los hashes actuales, 14 enlaces locales y las cabeceras de las nueve imágenes PNG. El registro está en `results/revision_proyecto.json` y la salida de las pruebas en `results/astar/pruebas_unitarias.txt`. La revisión de cabeceras PNG comprueba que los archivos tienen ese formato; no evalúa visualmente la legibilidad de las figuras.

## Observaciones que no bloquean el dashboard de A*

- **Figuras antiguas:** la paleta de componentes reutiliza colores y puede confundir el fondo con una región; `brc201d` tiene 167 componentes. Revisar esa figura antes de reutilizarla en TB2.
- **Herramientas antiguas de figuras:** la selección automática de ventana presupone un lado que cabe en el mapa y no examina todas las posiciones del borde. Los tres mapas actuales admiten el lado predeterminado de 20. Revisar los límites antes de ofrecer ventanas arbitrarias al usuario.
- **Análisis de grafos:** el CLI de estadísticas presupone al menos dos celdas transitables para algunas divisiones. Los tres mapas actuales cumplen esto; los mapas mínimos se prueban mediante el motor, no mediante ese CLI.
- **Informe TB1:** el equipo declaró cerrada su versión editable; el PDF local puede ser una exportación anterior. Reexportar la versión final al preparar TB2.

## Qué se puede afirmar y qué falta

Se puede afirmar que A* coincide con las referencias estáticas conservadas y que sus casos límite comprobados funcionan. No se puede afirmar todavía una ventaja frente a D* Lite, una comparación de replanificación ni un rendimiento en tiempo real: el lote contiene una sola ejecución por escenario y D* Lite no está implementado.

Para el dashboard inicial, el motor ya entrega ruta, costo, métricas y traza. Falta servir el terreno y los escenarios, dibujar las capas y añadir selección de caso, zoom y controles de reproducción. La interfaz deberá distinguir costo ponderado, pasos y tiempo del motor, y mantener el reloj de animación separado.

Para completar todo TB2, después del dashboard inicial siguen la simulación de obstáculos y movimiento, D* Lite, experimentos repetibles, comparación visual, Unity, informe, video y ZIP. El [plan](../PLAN_TB2.md) conserva esas etapas y los criterios de aceptación.
