# Resultados del motor

Evidencia reproducible que sustenta las cifras del informe. Cada archivo se regenera con un comando de `npc-nav`; no editar a mano.

| Archivo | Contenido | Comando |
|---|---|---|
| `validacion_dataset.json` | Integridad de los 3 mapas y sus 4 200 consultas, con hashes SHA-256. No calcula rutas. | `npc-nav validar --output results/validacion_dataset.json` |
| `astar/resumen.json` | Verificación de A*: resultado global y por mapa, tolerancia, entorno y hashes del código. | `npc-nav verificar --algoritmo astar` |
| `astar/casos.csv` | Una fila por escenario: costo de referencia, costo obtenido, error, estado y métricas. | (mismo comando) |
| `dstar_lite/resumen.json`, `dstar_lite/casos.csv` | Verificación de D* Lite con los mismos criterios que A*: 4 200/4 200 correctos. | `npc-nav verificar --algoritmo dstar_lite` |
| `dinamico/resumen.json` | Experimento con obstáculos dinámicos, A* (recálculo completo) frente a D* Lite: 30 escenarios × 5 eventos por mapa, semilla 2026. Medianas y totales por mapa y por tipo de evento, entorno y hashes. | `npc-nav experimentar` |
| `dinamico/planificaciones.csv` | Una fila por algoritmo y planificación: tipo de evento, celdas cambiadas, distancia al NPC, ruta afectada, costo, nodos y tiempo. | (mismo comando) |
| `astar/ejemplo_den011d.json` | Caso 375 de `den011d` con ruta y traza completa, para el dashboard. | `npc-nav buscar --mapa den011d --caso 375 --algoritmo astar --traza --output results/astar/ejemplo_den011d.json` |

Los tiempos provienen de una ejecución por escenario y dependen de la máquina: sirven para describir, no para afirmar rendimiento en tiempo real ni una ventaja frente a otro algoritmo. En `dinamico/` ambos algoritmos reciben los mismos cambios desde la misma posición del NPC, y cada par de planificaciones se comprueba con el mismo costo.

`tmp/` es para salidas descartables y está excluida de Git.
