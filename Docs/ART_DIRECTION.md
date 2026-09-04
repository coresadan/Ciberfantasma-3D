# Direccion artistica

## Objetivo

Plataformas de accion 2.5D con modelado tridimensional detallado, lectura lateral inmediata y una identidad cyberpunk propia. La referencia no es un juego 2D extruido: personajes, materiales, luces, particulas y escenarios deben responder de forma coherente en tres dimensiones.

## Protagonista

- Altura visual canónica del asset procedural V9: 166 cm.
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

- Héroe procedural V11 de 53.323 vértices, con proporción chibi y silueta reconstruida contra `ciberfantasma-chibi-turnaround-v1`: capucha única tallada hacia una campana acolchada con frontal menos esférico, mandíbula gráfica más compacta, lentes ampliadas, doble órbita convexa, máscara-calavera estratificada, recorridos de energía abdominal continuos, biseles refinados, armadura curva, botas multicapa y manos completas. Paneles, costuras y circuitos siguen la cabeza y no pueden separarse durante las poses extremas. Su UV0 es un atlas de producción sin solapamientos y con margen uniforme.
- Rig segmentado de 26 huesos y catorce clips jugables a 60 FPS enlazados a locomoción, salto, combate, escudo y daño. `RunStart` construye anticipación, compresión y primer impulso hasta enlazar con el contacto inicial del bucle; `RunStop` planta el pie adelantado, contrapesa el torso y recupera la pose neutra. Los controles secundarios de capucha se conservan para una futura versión high-poly deformable, pero no rompen la carcasa actual. Además de la marcha agachada de 33 fotogramas, el disparo contralateral es una capa aditiva propia que mantiene la carrera hacia un lado mientras torso, cabeza y brazo emisor disparan al opuesto. Cada acción contiene 234/234 pistas escalares y sus 16.848 claves tienen tangentes auto-limitadas; V10 reduce el vuelo de carrera, estabiliza el agachado y mantiene el aterrizaje con precontacto, compresión sostenida y recuperación por fases.
- Control Rig de pies terminado con efectores y pole vectors bilaterales. En juego, la pasada final de pose proyecta cada apoyo contra el escenario, inclina las botas con la normal, compensa la pelvis y evita tanto el estiramiento como el efecto de “pegar” el pie de vuelo al suelo. Se reduce durante la carrera y se apaga en salto.
- Seis materiales de héroe V12 diferencian capucha, traje interior, blindaje negro metálico, hueso, circuitos verdes y visor. Ocho mapas fuente de 2K suministran macrovariación, normales de microdetalle y metallic/roughness/AO empaquetados a las cuatro familias físicas principales. Pulso y escudo conservan su revisión V9; los materiales de enemigo continúan desacoplados en V8.
- Orientación izquierda/derecha corregida mediante el eje frontal real del FBX y escala positiva, de modo que desplazamiento, mirada y carrera coincidan sin invertir la lateralidad de la animación.
- `Scripts/audit_hero_animation_bounds.py` audita en Blender geometría, rig, cobertura de pistas y cada fotograma entregado —no sólo claves— antes de importar a Unreal; `audit_hero_foot_contacts.py` exige alternancia, simetría de aterrizaje y cierre de loops.
- La V11 ha superado las auditorías de Blender y Unreal tras su importación. El build Windows V10 sigue siendo el último paquete distribuible hasta completar el cook V11.
- Cámara en perspectiva con anticipación lateral y amortiguación.
- World Art V3 no destructivo aplicado a los nueve actos: skyline estratificado, fachadas modulares profundas, ventanas individuales, coronaciones, cartelería, tráfico lejano, cornisas mecánicas, HVAC, barandillas, niebla y luz diferenciada por mundo.
- Pase de legibilidad y variedad jugable: pinchos, memoria, trituradoras y vallas láser poseen silueta/luz/movimiento propios; las plataformas de fase telegrafían su apagado y nueve plataformas móviles opcionales crean rutas aéreas alternativas en cuatro actos sin borrar el recorrido de Canvas.

La V11 completa la pasada reproducible de primer plano, silueta, superficies 2K y contactos, además de UV, materiales PBR, Control Rig bilateral, IK runtime y pulido cuadro a cuadro. El siguiente salto puramente artístico sigue siendo un high-poly esculpido, retopología de deformación, bake high-to-low de normales/AO/curvatura, texturas 4K de autor, animación enemiga específica y decorado único por acto.
