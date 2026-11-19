# Plan de acción — navegación de NPCs

Actualizado: 14 de noviembre de 2026. D* Lite, la navegación con obstáculos dinámicos y el experimento comparativo están terminados en el motor. Las fechas de la tabla conservan los objetivos originales; la columna de evidencia indica los avances comprobados.

## Resultado esperado

Un motor de navegación en Python que compare A* con recálculo completo y D* Lite con actualización incremental sobre los mismos mapas, consultas y obstáculos. Un dashboard web debe mostrar la búsqueda y el movimiento, y Unity debe representar una demostración tridimensional conectada al mismo motor. El informe final debe presentar pruebas reproducibles y conclusiones basadas en los resultados medidos.

## Punto de partida comprobado

- TB1: informe cerrado por el equipo; el docente confirmó que portada e índice no cuentan para el máximo de diez páginas de contenido.
- Datos: `den011d.map` (14 506 vértices), `brc201d.map` (25 645) y `brc100d.map` (31 023). En total hay 71 174 vértices.
- Monorepo organizado por capas (ver [arquitectura.md](arquitectura.md)): `engine/` con `domain/`, `algorithms/`, `application/`, `infrastructure/` y `cli/`; `web/` y `unity/` preparados.
- Datos en `engine/data/`: `den011d.map.scen` (750 consultas), `brc201d.map.scen` (2 090) y `brc100d.map.scen` (1 360), 4 200 consultas de referencia. Integridad validada en `engine/results/validacion_dataset.json`.
- Algoritmos listos en `engine/src/npc_nav/algorithms/`: BFS, Dijkstra, voraz, A* y UFDS, con contrato común y observador de métricas.
- A* verificado con el código nuevo: 4 200/4 200 rutas legales con costo coincidente con los `.scen` (tolerancia `1e-5`). Evidencia en `engine/results/astar/`.
- Las pruebas automatizadas cubren dominio, lectores, contrato común de todos los algoritmos, optimalidad frente a un oráculo, suboptimalidad esperada de BFS y voraz, casos de uso y CLI.
- API y dashboard construidos. Arcadia en Unity ya consume el motor, dibuja `den011d`, mueve a Auri y recalcula después de cambiar obstáculos. Validación: 56 aserciones del cliente y 13 pruebas reales en Play Mode; [evidencia](../unity/docs/play-checks.json).
- D* Lite (versión optimizada, costos exactos `a + b·√2`) verificado con 4 200/4 200 escenarios ([evidencia](../engine/results/dstar_lite/resumen.json)). Navegación dinámica en `application/navegacion.py`, `POST /simular` y `/sesiones` con estado; experimento reproducible en [results/dinamico](../engine/results/dinamico/resumen.json). 88 pruebas.
- Kruskal (`POST /patrullaje`, red de patrullaje entre puntos de interés con costos A*), Edmonds-Karp (`POST /pasillo`, flujo máximo y corte mínimo de una zona con capacidad 1 por celda) y mochila 0/1 (`POST /botin`, PD frente al voraz por densidad), con comandos `npc-nav patrullaje|pasillo|botin`, vistas Patrullaje, Pasillo y Botín en el dashboard y 116 pruebas.
- Dashboard: D* Lite en Explorar y Comparar (busca desde el destino; `g` puede ser infinito) y vista **Simulación**: un NPC avanza, el usuario bloquea o libera celdas y se comparan las celdas que procesan A* y D* Lite en cada recálculo (`POST /simular`, cada planificación indica su `paso`).
- Pendiente: Arcadia con sesiones y los tres modos nuevos (Astra) e informe de resultados.

## Decisiones de alcance

1. **Comparación central:** A* y D* Lite para un agente que navega por vez. Varios agentes pueden mostrarse después, pero evitar choques entre ellos sería otro problema algorítmico.
2. **Mapa y costos comunes:** ocho direcciones; cardinal = 1 y diagonal = raíz de 2; sin atravesar esquinas. Un bloqueo también puede invalidar diagonales cercanas.
3. **Python calcula:** mapa, búsqueda, estado dinámico, rutas y métricas. Dashboard y Unity presentan el resultado y envían eventos por la API. El IDE (PyCharm, WebStorm, Rider) sirve para editar; no forma parte de la arquitectura en ejecución.
4. **Web primero:** el dashboard 2D será la demostración principal de la comparación. Unity consumirá la misma interfaz del motor y mostrará la simulación en 3D.
5. **HPA* y MAPF:** quedan como trabajo futuro hasta completar y validar la comparación central.

## Arquitectura y datos compartidos

```text
dataset (.map, .scen)
        ↓
motor Python: grafo + A* + D* Lite + simulación + medición
        ├── ejecución por lotes → CSV/JSON y figuras para el informe
        └── servicio local → dashboard web 2D / Unity 3D
```

Cada sesión debe tener: `mapa`, `algoritmo`, `origen`, `destino`, `posición_actual`, `celdas_bloqueadas`, `ruta`, `costo`, `estado` y `eventos`. Los eventos deberán incluir `busqueda_iniciada`, `nodo_procesado`, `ruta_encontrada`, `agente_movido`, `obstaculo_cambiado`, `ruta_actualizada` y `sin_ruta`. El dashboard puede reproducir eventos después del cálculo; el reloj de animación no forma parte del tiempo medido del algoritmo.

Para la primera versión, un servicio FastAPI puede exponer peticiones de mapa y simulación; WebSocket sirve para enviar eventos durante la demostración. El cliente web puede dibujar los mapas con Canvas. Unity puede consultar el mismo servicio desde C#.

## Secuencia de trabajo y criterios de aceptación

| Etapa y fecha objetivo | Trabajo | Evidencia para darla por terminada |
|---|---|---|
| 0. Base común, completada el 27 sep | Ordenar el código como paquete Python; fijar reglas de movimiento; validar dimensiones, coordenadas y entradas de los tres `.scen`; crear comandos reproducibles. | **Completada:** reglas comunes con costos y obstáculos por sesión; 17 pruebas pasan, y los tres mapas y 4 200 escenarios validan formato, transitabilidad, conectividad y cifras del informe. |
| 1. A*, completada el 27 sep | Implementar prioridad, heurística octil, reconstrucción de ruta, casos sin ruta, métricas y traza opcional. | **Completada:** 4 200/4 200 escenarios aprobados con tolerancia `1e-5`; rutas y costos revisados paso a paso, 27 pruebas pasan y hay CSV/JSON, hashes y ejemplo con traza. |
| 1b. Monorepo y algoritmos de comparación, completada el 29 sep | Reestructurar en capas, separar la medición de los algoritmos (observador), agregar BFS, Dijkstra y voraz, CI y convenciones. | **Completada:** pruebas en verde, A* reverificado 4 200/4 200 con el código nuevo, CLI `npc-nav`. |
| 2a. API, 30 sep–1 oct (`feature/engine-api`) | FastAPI: `/mapas`, `/mapas/{id}`, `/mapas/{id}/escenarios`, `/algoritmos`, `/buscar`, `/comparar`, `/health`. Despliegue en Render. | **Código completado el 30 sep** (66 pruebas; pseudocódigo y línea activa en la traza; endpoints de evidencia). Pendiente: desplegar en Render y comprobar una búsqueda A* con traza en los tres mapas. |
| 2b. Dashboard web, 2–4 oct (`feature/web-dashboard`) | Vue + Vite + Canvas: mapa, inicio, destino, exploración y ruta; selección de mapa/escenario/algoritmo, reproducción (play, pausa, paso, velocidad), zoom, comparación lado a lado, métricas y bloqueo de celdas con replanificación A*. Despliegue en Vercel. | **Entrega del 4 de octubre:** web pública donde se ejecutan y comparan los cuatro algoritmos en los tres mapas. Código completado el 30 sep (Inicio, Explorar, Comparar, Resultados y Acerca); pendiente el despliegue en Vercel. |
| 3. Cambios y D* Lite, 5–31 oct | Bloquear/liberar celdas, actualizar movimientos afectados, replanificar desde la posición actual e implementar D* Lite. | **Completada el 14 nov:** D* Lite coincide con Dijkstra en más de 300 secuencias aleatorias y con A* en 4 200/4 200 escenarios; las sesiones de la API son independientes entre sí. |
| 4. Comparación, 1–8 nov | Ejecutar casos repetibles con igual mapa, origen, destino, posición y secuencia de obstáculos; exportar resultados. | **Completada el 14 nov:** `npc-nav experimentar`, 540 planificaciones con costos coincidentes; resultados en la tabla de abajo. Faltan los gráficos para el informe. |
| 5. Dashboard comparativo y Unity, 9–18 nov | Vista A*/D* Lite lado a lado; eventos sincronizados, obstáculos interactivos y visualización del agente. Integración Unity con el mismo servicio Python. | **Unity adelantado al 22 oct:** Arcadia sigue rutas HTTP, cambia de ruta al bloquear, representa ausencia de ruta y permite explorar con teclado. Falta la comparación A*/D* Lite. |
| 6. Informe del segundo hito, hasta 22 nov | Documentar propuesta definitiva y diseño del aplicativo; incluir arquitectura, algoritmos, casos de prueba previstos e interfaz. | Entregable del hito 2 listo según el enunciado. |
| 7. Trabajo final, hasta 29 nov | Revisar pruebas, interpretar resultados, redactar conclusión, preparar video y ZIP. | Código fuente, dataset, informe `.docx` y archivo con enlace al video dentro del ZIP exigido; ejecución verificada desde instrucciones de instalación. |

Las fechas internas son objetivos de trabajo. El enunciado fija el segundo hito para el **22/11/2026** y el trabajo final para el **29/11/2026**.

## Resultados del experimento dinámico

`npc-nav experimentar` con semilla 2026: 30 escenarios por mapa (de la mitad con rutas más largas) y 5 eventos por escenario (bloqueo en la ruta, cierre de pasillo de 3×3, obstáculo lejano y desbloqueo). En total hay 150 replanificaciones por mapa y algoritmo. Tiempos del motor en Windows 11, sin red ni animación.

| Mapa | Búsqueda inicial, mediana A* / D* Lite | Replanificación, mediana de celdas A* / D* Lite | Replanificación, mediana ms A* / D* Lite | Tiempo total de replanificación A* / D* Lite |
|---|---|---|---|---|
| den011d | 4 095 / 3 597 celdas · 40.6 / 48.5 ms | 2 546.5 / 2.5 | 24.9 / 1.6 | 4.41 s / 0.32 s (13.7×) |
| brc201d | 14 963.5 / 14 223.5 celdas · 153.4 / 212.8 ms | 11 653.5 / 3 | 124.9 / 4.5 | 18.49 s / 0.72 s (25.8×) |
| brc100d | 13 708.5 / 13 982.5 celdas · 143.3 / 204.9 ms | 11 184.5 / 3 | 118.8 / 2.8 | 20.30 s / 0.49 s (41.1×) |

Lectura: la primera búsqueda de D* Lite cuesta lo mismo o algo más que la de A*, porque guarda g y rhs. Cada replanificación procesa solo las celdas afectadas, entre el 0.2 % y el 1 % de las de A* sumando todos los eventos. Detalle por tipo de evento en `resumen.json`.

## Protocolo de validación

1. **Mapa estático:** comparar A* con el costo óptimo de los `.scen`. Validar también inicio = destino, diagonales junto a muros y destinos en otra componente. El archivo `.scen` guarda coordenadas como `(x, y)`; el código utiliza `(fila, columna)`.
2. **Mapa modificado:** después de cada evento, comprobar que cada paso de la ruta siga siendo legal. El óptimo publicado en `.scen` ya no sirve para ese estado; usar A* sobre el mapa modificado como referencia de costo para D* Lite.
3. **Comparación justa:** entregar a ambos algoritmos los mismos estados y cambios. Separar planificación inicial de replanificación. Medir solo el motor, fuera del render, la red y la reproducción visual; repetir ejecuciones e informar distribución de tiempos y entorno de prueba.
4. **Definición de métricas:** documentar si «nodos procesados» cuenta extracciones de cola o vértices únicos, en especial para D* Lite; registrar costo de ruta y distancia total recorrida por el agente como magnitudes distintas.
5. **Casos dinámicos:** bloqueo de la ruta, bloqueo de un pasillo, obstáculo que no afecta la ruta, desbloqueo y cierre que deja el destino inaccesible. Conservar semillas y lista de eventos.

## Interfaz demostrativa

- Dos paneles con el mismo mapa y los mismos eventos: A* y D* Lite.
- Capas de terreno, obstáculos, origen, destino, nodos examinados, ruta vigente y posición del agente.
- Selección de escenario `.scen`, controles iniciar/pausar/avanzar, velocidad de reproducción, zoom y edición de obstáculos.
- Costo de ruta, tiempo de cómputo, nodos procesados y replanificaciones visibles, con un apartado de resultados por lotes.
- Mensajes claros para entrada inválida o destino inaccesible y leyenda de colores.
- Usar una ventana del mapa para mostrar la exploración detallada cuando la vista completa no permita distinguir cada celda.

## Organización del grupo de tres

| Frente | Responsable principal | Revisión cruzada |
|---|---|---|
| Motor Python, A*, D* Lite y pruebas | Integrante 1 | Integrante 2 valida rutas y costos. |
| API, dashboard y reproducción de eventos | Integrante 2 | Integrante 3 prueba usabilidad y casos límite. |
| Experimentos, Unity, informe y video | Integrante 3 | Integrante 1 revisa que las cifras del informe provengan de las ejecuciones. |

Hacer una integración corta al final de cada etapa. Cada integrante debe poder explicar el código y las decisiones de los tres frentes para la sustentación.

## Riesgos y decisiones pendientes

- Confirmar con el docente que D* Lite se acepta dentro de búsquedas en grafos o programación dinámica del curso. UFDS y recorridos de grafos también forman parte explícita de la solución.
- D* Lite requiere mantener estado entre cambios; reiniciarlo en cada petición destruiría la comparación. Diseñar sesiones aisladas desde el inicio.
- UFDS refleja la conectividad del mapa estático. Ante bloqueos o desbloqueos, actualizar o comprobar de nuevo la alcanzabilidad afectada.
- La demostración de varios NPC independientes no equivale a resolver colisiones entre agentes. Mantener el experimento central en un agente por consulta.
- La visualización de 167 componentes reutiliza colores; mejorar esa figura si vuelve a incorporarse al informe final.
- Reservar tiempo para instalar y probar el proyecto desde un entorno limpio antes de empaquetar el ZIP.

## Siguiente incremento

1. ✔ `feature/graph-algorithms`: Kruskal (red de patrullaje de costo mínimo entre puntos de interés, reutiliza UFDS), Edmonds-Karp (flujo máximo y corte mínimo en un pasillo, que indica qué celdas bloquear) y mochila 0/1 (programación dinámica para el botín del NPC). Cada uno tiene su caso de uso, endpoint, pruebas y vista; no entran en `/comparar` porque no buscan una ruta origen→destino.
2. ✔ Dashboard: D* Lite en Explorar y Comparar, y una vista dinámica A* vs D* Lite con `POST /simular`.
3. Arcadia con `/sesiones`, D* Lite y HUD comparativo (Astra).
4. Gráficos del experimento e informe del hito 2.

Arcadia utiliza el escenario 124 de `den011d`: inicio `(106,123)`, destino `(107,92)`. El mapa completo se conserva; el santuario destaca una zona para facilitar la demostración. A* produce costo `51.355339` al inicio y `57.941125` con la compuerta cerrada. El cliente conserva posición y obstáculos y envía una instantánea completa en cada `POST /buscar`. Estos resultados prueban la integración actual, no sustituyen la futura comparación incremental. Instrucciones en [Unity](../unity/README.md). La entrega TB1 permanece sin modificaciones.
