# Dataset utilizado

Se conservaron los siguientes pares de mapas y escenarios del conjunto *Dragon Age: Origins* de Moving AI Lab:

| Mapa | Escenarios | Celdas transitables | Consultas `.scen` |
|---|---|---:|---:|
| `maps/den011d.map` | `scenarios/den011d.map.scen` | 14 506 | 750 |
| `maps/brc201d.map` | `scenarios/brc201d.map.scen` | 25 645 | 2 090 |
| `maps/brc100d.map` | `scenarios/brc100d.map.scen` | 31 023 | 1 360 |

**Origen:** [Moving AI Lab — Dragon Age: Origins](https://www.movingai.com/benchmarks/dao/index.html). El proyecto reconoce a Moving AI Lab y a BioWare como fuentes de estos datos. La [página general de benchmarks](https://www.movingai.com/benchmarks/) indica la licencia Open Data Commons Attribution para los datos.

Los mapas contienen celdas transitables y obstáculos. Cada escenario define una consulta con coordenadas `(x, y)` y longitud óptima para el mapa original. El código convierte esas coordenadas a `(fila, columna)`. El [formato oficial](https://www.movingai.com/benchmarks/formats.html) especifica diagonales de costo raíz de 2 y prohíbe atravesar esquinas entre paredes.

Se retiraron los otros 153 archivos `.scen` de la descarga porque sus mapas no forman parte del estudio. Los ZIP originales pueden volver a descargarse desde la fuente indicada si se amplía el conjunto.
