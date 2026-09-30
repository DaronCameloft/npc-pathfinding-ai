# Motor Python: contrato de navegación

La base utiliza únicamente la biblioteca estándar de Python. `Mapa` conserva el terreno original y `MotorNavegacion` mantiene los obstáculos de una sesión. A* recibe una instancia del motor para consultar movimientos y costos; D* Lite utilizará el mismo contrato cuando se implemente.

## Reglas

- Una posición se expresa como `(fila, columna)`, con origen `(0, 0)` en la esquina superior izquierda.
- Solo `.` y `G` son transitables. `@`, `O`, `T`, `S` y `W` se consideran obstáculos en este proyecto; no se modelan sus reglas especiales de terreno.
- Hay cuatro movimientos cardinales de costo `1.0` y cuatro diagonales de costo `sqrt(2)`.
- Para una diagonal, el destino y ambas celdas cardinales laterales deben estar libres.
- Una celda bloqueada no tiene movimientos entrantes ni salientes. Fuera del mapa tampoco se puede transitar.
- La distancia octil estima el costo sin obstáculos y es la heurística de A*.

## Uso

Después de instalar el paquete desde la raíz (`python -m pip install -e .`):

```python
from npc_pathfinding import MotorNavegacion, leer_mapa, leer_escenarios

mapa = leer_mapa('data/maps/den011d.map')
caso = leer_escenarios('data/scenarios/den011d.map.scen')[0]
motor = MotorNavegacion(mapa)
motor.validar_consulta(caso.inicio, caso.destino)

# Cada resultado incluye la posición y el costo del movimiento.
movimientos = motor.vecinos(caso.inicio)
```

`validar_consulta` comprueba que ambos extremos estén libres; no busca rutas ni demuestra alcanzabilidad. `costo_movimiento` devuelve infinito cuando un paso es ilegal. `costo_ruta` suma los costos de una ruta válida y rechaza rutas vacías, saltos, pasos bloqueados y posiciones repetidas consecutivas. Una ruta de una sola posición transitable cuesta cero.

## Obstáculos por sesión

```python
cambiadas = motor.actualizar_obstaculos(bloquear=[(39, 105)])
version = motor.version
motor.actualizar_obstaculos(liberar=[(39, 105)])
```

Los cambios se validan antes de aplicarse. No se puede alterar terreno originalmente intransitable ni bloquear y liberar la misma celda en un solo cambio. Se devuelve la lista de celdas que realmente cambiaron y se incrementa la versión solo si hubo un cambio efectivo. Las diagonales se comprueban en cada consulta, incluso cuando se bloquea una celda lateral que no es un extremo de la diagonal.

Cada motor tiene sus propios obstáculos; dos motores pueden compartir el mapa original sin afectar sus sesiones. A* puede ejecutarse de nuevo después de cada cambio. D* Lite deberá recibir la notificación para actualizar su estado de búsqueda. La conectividad estática de UFDS no debe tratarse como conectividad vigente después de modificar el mapa.

## Validación de datos

```powershell
python -m npc_pathfinding.validacion --output results/validacion_dataset.json
python -m unittest discover -s tests -v
```

El primer comando comprueba los pares `.map` / `.map.scen`, cabeceras, dimensiones, símbolos, coordenadas, terreno de los extremos, conectividad y costos de referencia finitos que respeten la cota octil. También registra hashes SHA-256 para identificar los archivos validados. Rechaza datos inválidos con un mensaje y código de salida 1.

La lectura de escenarios convierte las coordenadas `(x, y)` del archivo a `(fila, columna)` y admite las cabeceras `version 1` y `version 1.0`. La validación de integridad no calcula rutas. El comando `python -m npc_pathfinding.verificar_astar` realiza la comprobación experimental de las rutas de A* contra todos los costos de referencia; su contrato está en [astar.md](astar.md).

Los comandos antiguos de análisis y figuras conservan sus funciones de entrada, pero ahora reutilizan estas mismas reglas y lectores.
