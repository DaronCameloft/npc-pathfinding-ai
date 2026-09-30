# Resultados del motor

Evidencia reproducible que sustenta las cifras del informe. Cada archivo se regenera con un comando de `npc-nav`; no editar a mano.

| Archivo | Contenido | Comando |
|---|---|---|
| `validacion_dataset.json` | Integridad de los 3 mapas y sus 4 200 consultas, con hashes SHA-256. No calcula rutas. | `npc-nav validar --output results/validacion_dataset.json` |
| `astar/resumen.json` | Verificación de A*: resultado global y por mapa, tolerancia, entorno y hashes del código. | `npc-nav verificar --algoritmo astar` |
| `astar/casos.csv` | Una fila por escenario: costo de referencia, costo obtenido, error, estado y métricas. | (mismo comando) |
| `astar/ejemplo_den011d.json` | Caso 375 de `den011d` con ruta y traza completa, para el dashboard. | `npc-nav buscar --mapa den011d --caso 375 --algoritmo astar --traza --output results/astar/ejemplo_den011d.json` |

Los tiempos provienen de una ejecución por escenario y dependen de la máquina: sirven para describir, no para afirmar rendimiento en tiempo real ni una ventaja frente a otro algoritmo. La comparación con obstáculos dinámicos (A* frente a D* Lite) se guardará aquí en su propia carpeta, con semillas y lista de eventos.

`tmp/` es para salidas descartables y está excluida de Git.
