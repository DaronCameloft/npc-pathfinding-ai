# Arte original de Arcadia

Estos modelos se generan con `build_arcadia_assets.py`, sin descargas, texturas externas ni complementos. El archivo conserva materiales, geometría y pivotes editables.

**Foca Watona** se genera por separado con `build_foca_watona.py`, a partir de geometría original inspirada en la referencia visual del usuario. Su piel utiliza una textura UV procedural propia. Conserva la silueta rechoncha, el hocico doble, los ojos pequeños, los bigotes, las aletas y la cola dividida.

```powershell
& 'D:/Blender/blender.exe' --background --factory-startup --python 'D:/complejidad-npc-ai/unity/art-source/build_foca_watona.py'
```

Genera `FocaWatona.blend`, `FocaWatona-preview.png` (render real de Blender), `../Arcadia/Assets/Arcadia/Art/FocaWatona.fbx` y `FocaWatona_Albedo.png`. Los pivotes `LeftFlipperPivot`, `RightFlipperPivot` y `TailPivot` dependen de `SealBodyPivot`; Unity conserva sus transformaciones importadas y añade respiración, balanceo y movimiento de aletas mediante `SealMotion`. La escala de presentación en Unity es 0,85. Los materiales `FocaWatona_Skin`, `Cream`, `Eyes`, `Nose`, `Whiskers` y `Eyelids` se asignan a materiales URP por nombre, conservando el mapa de color de la piel.

## Regeneración

```powershell
& 'D:/Blender/blender.exe' --background --factory-startup --python 'D:/complejidad-npc-ai/unity/art-source/build_arcadia_assets.py'
```

Validado con Blender **5.2.2 LTS**. La ejecución genera los FBX en `../Arcadia/Assets/Arcadia/Art/`, guarda `Auri.blend` y `Arcadia-assets.blend` aquí y renderiza `Auri-preview.png` con Cycles.

Para regenerar modelos sin repetir el render, añade `-- --skip-render` al final del comando. La exportación usa `bake_space_transform=False`: la conversión de ejes se conserva en las transformaciones FBX, manteniendo alineados los pivotes vacíos y sus mallas. No restablezcas las rotaciones importadas del modelo; coloca el FBX bajo un objeto contenedor para orientar al personaje en Unity.

## Modelos

| Archivo | Uso | Dimensiones aproximadas |
|---|---|---|
| `Auri.fbx` | Autómata explorador articulado | Altura 0,964 m, pies en el suelo |
| `RuinColumn.fbx` | Columna de piedra con remates y musgo | Altura 1,98 m; base 0,72 m |
| `RuinArch.fbx` | Arco de ruinas modular | Ancho 3,4 m; altura 2,94 m |
| `RuinRockCluster.fbx` | Grupo de piedras de borde | Ancho cercano a 1 m |
| `GardenFern.fbx` | Helecho de hojas geométricas | Diámetro cercano a 0,88 m |

Los modelos usan metros. El archivo Blender tiene Z vertical y frente hacia −Y. El FBX se exporta con Y vertical. Los pivotes de los módulos se sitúan en el centro del suelo. Los props son decorativos: la transitabilidad pertenece al mapa del motor.

## Articulaciones de Auri

El nodo raíz `Auri` contiene los pivotes `BodyPivot`, `HeadPivot`, `LeftArmPivot`, `RightArmPivot`, `LeftLegPivot` y `RightLegPivot`. Cada pivote contiene piezas rígidas, listas para animación mecánica por transformaciones. No se necesita un rig humanoide ni un Animator Controller. Al animar se debe componer la rotación relativa con la rotación de reposo importada.

## Materiales

| Nombre FBX | Tratamiento |
|---|---|
| `Auri_Ceramic` | Cerámica marfil |
| `Auri_Brass` | Bronce metálico |
| `Auri_Joint` | Articulaciones verde oscuro |
| `Auri_Light` | Turquesa emisivo: ojos, pecho, antena |
| `Auri_Visor` | Visor negro azulado |
| `Ruin_Limestone` | Piedra de tono oliva claro |
| `Ruin_Edge` | Piedra clara en remates |
| `Ruin_Moss` | Musgo oscuro |
| `Garden_Leaf`, `Garden_LeafLight` | Dos verdes para el follaje |

Unity remapea estos nombres a materiales URP. El FBX conserva la asignación por pieza; Cycles y URP requieren materiales propios de cada renderizador para iluminación y emisión equivalentes.

`Auri-preview.png` es un render real de Blender del modelo entregado, sin retoque ni generación de imagen.
