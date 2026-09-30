# unity — demostración 3D

Segundo hito. Un proyecto Unity (editado con Rider) representa el mapa como escenario 3D, con un personaje que sigue la ruta calculada por el motor y la cambia cuando aparece un obstáculo, al estilo de los NPC de Minecraft.

- Unity no calcula rutas: consulta la misma API que el dashboard (HTTP/WebSocket) desde C#.
- Posiciones `(fila, columna)` → mundo Unity `(x = columna, z = fila)`.
- El proyecto se crea dentro de esta carpeta; `Library/`, `Temp/`, `Logs/` y los `.csproj` generados ya están en el `.gitignore` raíz.
- Si se agregan modelos o texturas pesadas, activar Git LFS para `*.fbx`, `*.png` de assets y audio.

Alcance: un agente por consulta. La coordinación de varios agentes con prevención de colisiones queda fuera de la comparación central.
