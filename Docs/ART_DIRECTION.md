# Direccion artistica

## Objetivo

Plataformas de accion 2.5D con modelado tridimensional detallado, lectura lateral inmediata y una identidad cyberpunk propia. La referencia no es un juego 2D extruido: personajes, materiales, luces, particulas y escenarios deben responder de forma coherente en tres dimensiones.

## Protagonista

- Altura visual canonica en el mundo: 150 cm.
- Proporcion chibi heroica de unas 2,6 cabezas: la cabeza con capucha ocupa aproximadamente el 38 % de la altura total.
- Torso compacto, extremidades cortas, guantes expresivos y botas anchas. No volver a proporciones adultas atleticas.
- Silueta reconocible en negro incluso sin iluminacion de color.
- Mascara-calavera grande y amable como foco principal; visor y emisor de pulso como focos secundarios.
- Separar visualmente tejido tecnico, placas pintadas, metal expuesto, goma y superficies emisivas.
- Los acentos verdes ocupan poca superficie y dirigen la mirada; no deben cubrir el traje entero.
- El arma forma parte del antebrazo o guante para mantener una silueta compacta al correr.

## Pipeline de personaje

1. Hoja de diseño frontal, lateral y trasera coherente.
2. Escultura de alta resolucion para formas y pliegues principales.
3. Retopologia para deformacion, no una reduccion automatica como resultado final.
4. UV sin solapamientos accidentales y densidad uniforme.
5. Bake de normales, ambient occlusion, curvatura e ID de materiales.
6. Texturas PBR y materiales maestros en Unreal.
7. Rig humanoide chibi compatible con retargeting; compensar brazos y piernas cortos sin estirar la silueta.
8. Pruebas de silueta y deformacion con carrera, salto, agachado y disparo.
9. LOD revisados manualmente en capucha, manos, mascara y arma.

La referencia canonica es `ReferenceArt/ciberfantasma-chibi-turnaround-v1.png`, apoyada por
`ReferenceArt/ciberfantasma-chibi-idle-final.png`. Las hojas atleticas anteriores solo sirven
para consultar detalles de las placas y nunca para determinar las proporciones.

El protagonista puede utilizar dos conjuntos de texturas de 4K durante produccion, con una variante de 2K para ajustes bajos. Los enemigos normales deben compartir materiales y esqueletos cuando no comprometa su identidad.

## Animacion

- Carrera con contacto de pies estable y centro de masa creible.
- Inicio, bucle y frenada separados para evitar deslizamiento.
- Saltos divididos en impulso, subida, apice, caida y aterrizaje.
- Disparo aditivo para permitir disparar en suelo y aire.
- Escudo con anticipacion breve, pose sostenida e impacto reactivo.
- Animation Blueprint con transiciones parametrizadas; no reproducir sprites como planos.

## Escenarios

- Tres planos funcionales: jugable, arquitectura media y skyline profundo.
- El plano jugable debe conservar contraste y bordes claros bajo cualquier luz.
- Kit modular por mundo: suelos, cornisas, fachadas, tuberias, barandillas, terminales y senaletica.
- Variacion mediante decals, vertex paint y props; evitar repetir el mismo modulo sin cambios visibles.
- Profundidad real con calles, pasarelas, trafico y actividad corporativa fuera del plano jugable.

## Iluminacion y color

- Mundo 1: negro, acero frio, cian y magenta; verde reservado para el jugador y objetivos liberados.
- Mundo 2: nubes blancas frias, cristal, dorado institucional y violeta de fase.
- Mundo 3: hormigon, vidrio oscuro, rojo de cumplimiento y laton corporativo.
- La luz debe describir volumen y material. El bloom nunca sustituye a una superficie bien modelada.

## Camara

- Perspectiva moderada, no ortografica, para mostrar profundidad.
- Movimiento principal sobre X y restriccion fisica en Y.
- Anticipacion horizontal segun velocidad y direccion.
- Encuadre estable durante saltos; desplazamiento vertical amortiguado.
- Variaciones de camara solo en entradas de jefe, terminales y final de acto.

## Criterio de aceptacion visual

Una captura sin HUD debe funcionar como una escena 3D terminada: materiales diferenciados, contactos con el suelo, sombras coherentes, siluetas claras y profundidad ambiental. Ningun asset provisional de `Blockout` se considera arte final.

## Estado del pase actual

- Proporción chibi, capucha, máscara-calavera, visor negro, placas compactas y acentos verdes integrados en un Skeletal Mesh propio.
- Rig segmentado de 23 huesos y diez clips jugables a 60 FPS enlazados a locomoción, salto, combate, escudo y daño.
- Paleta del héroe recalibrada para mantener capucha y blindaje negros bajo la iluminación real de juego.
- Cámara en perspectiva con anticipación lateral y amortiguación.
- Kit procedural de tres planos aplicado a los nueve actos, con identidad de color diferenciada por mundo.

Este pase supera el blockout funcional, pero no equivale todavía al arte final definido arriba: faltan escultura/retopología manual, UV y bakes, texturas de autor, Animation Blueprint con mezclas, animación enemiga específica y decorado único por acto.
