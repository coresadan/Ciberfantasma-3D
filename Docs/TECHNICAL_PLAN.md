# Plan técnico

## Plataforma y render

- Windows 10/11 de 64 bits.
- Objetivo de 1920x1080 a 60 FPS.
- Perfil bajo funcional en GTX 1060 de 6 GB.
- DX11/SM5, iluminación dinámica, Lumen y ray tracing desactivados.
- Colisiones jugables separadas de la representación visual para permitir sustituir el escenario modular sin alterar el recorrido.

## Arquitectura implementada

- `CFGameInstance`: conserva nivel, puntos y bajas durante los cambios de mapa.
- `CFGameMode` y `CFHUD`: crean el jugador y dibujan el estado completo de la partida.
- `CFGameState`: controla fragmentos, terminales, enemigos, jefes, puntuación, transición, victoria y derrota.
- `CFPlayerCharacter`: locomoción 2.5D, doble salto, agachado, disparo, escudo, salud, checkpoints, pausa y reinicio.
- `CFPulseProjectile` y `CFEnemyProjectile`: combate de jugador y enemigos, incluido bloqueo con escudo.
- `CFPatrolEnemy`: perfiles para los nueve tipos de enemigo y los tres jefes de Canvas. Catálogo de referencias duras cocinables y selección de `StaticMesh` por `EnemyKind`.
- `CFShard`, `CFTerminal`, `CFHazard`, `CFMovingPlatform` y `CFExitPortal`: objetivos y elementos de nivel.

## Personaje y animación implementados

- `SK_Ciberfantasma_Chibi_Pro`: héroe procedural V11 de 53.323 vértices, reconstruido contra el turnaround canónico. La pasada de primer plano conserva la corona alta, talla el volumen único de capucha hacia una silueta acolchada y acampanada, aplana el plano facial, compacta la mandíbula gráfica, amplía lentes y órbitas convexas, y suaviza los reflejos de biseles y circuitos. La capucha utiliza una sola carcasa rígida continua: paneles, costuras y circuitos siguen el hueso de cabeza y no pueden abrirse como una falsa segunda capucha durante impactos o aterrizajes. UV0 usa un atlas sin solapamientos y margen de isla constante. Su esqueleto chibi tiene 26 huesos —incluidos controles `hood_l`, `hood_r` y `hood_back`, reservados para una futura capucha high-poly realmente deformable— y la piel no contiene vértices huérfanos.
- Catorce secuencias a 60 FPS: idle, run start, run, run stop, jump start, jump rise, jump fall, land, crouch, crouch walk, fire, contralateral fire, shield y hit. Cada acción contiene las 234/234 pistas escalares previstas —posición, rotación y escala de los 26 huesos— para impedir que una pose herede canales de otra. Las 16.848 claves emplean tangentes Bezier auto-limitadas para eliminar overshoot entre poses y el FBX hornea el resultado cuadro a cuadro a 60 Hz. El aterrizaje incorpora precontacto, dos fotogramas de compresión y recuperación escalonada. La carrera V10 reduce vuelo, extensión trasera y oscilación vertical; sus contactos enlazan con `RunStart`/`RunStop`. La marcha agachada de 33 fotogramas estabiliza pelvis y alterna apoyos sin desplazamiento congelado. El disparo contralateral conserva la orientación y ciclo de carrera mientras torso, cabeza y brazo emisor apuntan al sentido opuesto; fogonazo, luz y proyectil usan la dirección real del tiro.
- Máquina de presentación en C++ gobernada por intención de movimiento, velocidad, estado de suelo, velocidad vertical, agachado, disparo, daño y escudo. La locomoción terrestre dispone de estados explícitos `Idle → Starting → Running → Stopping`, con interrupciones seguras para salto, aterrizaje y acciones.
- `CR_Ciberfantasma_FootIK`: Control Rig artístico con la jerarquía completa de 27 huesos importados, efectores `CTRL_FootIK_L/R`, pole vectors `CTRL_KneePole_L/R` y dos cadenas Two Bone IK encadenadas en `Forward Solve`. La ejecución usa una pasada final equivalente en `UCFHeroAnimInstance`: dos trazas de suelo, adaptación de pendiente limitada a 32°, compensación de pelvis, solve sin estiramiento y suavizado independiente. Su peso baja durante la carrera para preservar la zancada y se desvanece en el aire.
- Carrera con anticipación y primer impulso propios, bucle a velocidad de reproducción variable y frenada con apoyo adelantado, contrapeso de torso y recuperación a neutro. Los enlaces de pose coinciden entre clips para eliminar cortes y reducir el deslizamiento visual al iniciar o soltar la dirección. La orientación usa el eje frontal real del FBX y escala siempre positiva: pulsar derecha o izquierda alinea movimiento, mirada y animación en el mismo sentido, sin invertir la lateralidad del rig ni sus tangentes.
- Seis materiales de héroe V12 (`Hood`, `Undersuit`, `Armor`, `Bone`, `Green` y `Visor`) separan tejido, goma, blindaje metálico, hueso, pantalla y emisión. Ocho mapas fuente de 2K aportan macrovariación, normal de microdetalle y canales PBR empaquetados —metallic, roughness y ambient occlusion— a capucha, traje, armadura y máscara; el verificador impide degradarlos accidentalmente a 512 px. Pulso y escudo permanecen en V9; los materiales de enemigo continúan desacoplados en V8 para evitar migraciones destructivas.
- Escudo frontal translúcido de dos capas, núcleo redondeado, marco emisivo pulsante, barrido vertical y luz localizada; fogonazo ligado al personaje y cola ligada al proyectil para que ningún efecto quede rezagado al correr.
- Cámara lateral calibrada contra el Canvas: brazo base de 1.400 cm, FOV 44°, apertura adicional al correr/saltar, 240 cm de anticipación horizontal, anticipación vertical y respuesta amortiguada al aterrizaje.

## VFX de combate implementados

- Cinco sistemas Niagara con emisores reales y assets cocinables: impacto de pulso, fogonazo, absorción de escudo, muerte de enemigo y explosión de jefe.
- Enlace nativo mediante `UNiagaraFunctionLibrary` para impactos y estallidos breves en espacio mundial. El fogonazo jugable usa un cono emisivo V9 adjunto al personaje —en vez de una instancia mundial— y la cola viaja con el proyectil, eliminando el retraso visual al correr.
- Generación idempotente desde plantillas authored de Unreal; sustituye automáticamente los antiguos sistemas vacíos y conserva sistemas válidos.
- Auditoría dedicada que rechaza assets Niagara ausentes, obsoletos o creados como stubs sin emisor.

## Enemigos — modelos chibi implementados (9 tipos)

| EnemyKind | Tipo       | Mesh FBX                | Color distintivo    |
|-----------|------------|-------------------------|---------------------|
| 0         | Bot        | SM_LicenseWarden_Chibi  | Rojo                |
| 1         | Drone      | SM_PanopticonDrone_Chibi | Magenta / cian     |
| 2         | Boss CEO   | SM_CEO9000_Chibi        | Dorado / rojo       |
| 3         | Crawler    | SM_Crawler_Chibi        | Naranja hazard      |
| 4         | Harvester  | SM_Harvester_Chibi      | Teal / dorado       |
| 5         | Boss CEO II| SM_CEO9000_Chibi (×1.8) | Dorado / rojo       |
| 6         | Enforcer   | SM_Enforcer_Chibi       | Azul policial       |
| 7         | Auditor    | SM_Auditor_Chibi        | Amarillo burocrático |
| 8         | Director   | SM_Director_Chibi       | Blanco / ojo rojo   |

`ApplyProfile()` selecciona el mesh, escala, salud, velocidad, rango de patrulla, color de luz e intensidad correctos para cada tipo en `BeginPlay`.

## Datos y generación de campaña

`Scripts/export_canvas_levels.mjs` extrae los datos literales de los nueve niveles desde `D:\Trabajo\Ciberfantasma Bros\game.js` y escribe `Design/campaign_levels.json`.

`Content/Python/build_campaign.py` convierte las coordenadas Canvas a centímetros Unreal y genera los nueve mapas con tres planos de profundidad, decorado procedural y luces dinámicas por acto. El trazado original se mantiene como ruta principal y los actos 1, 3, 7 y 9 reciben nueve plataformas móviles opcionales que convierten huecos de peligro en rutas aéreas de riesgo/recompensa.

`Content/Python/upgrade_world_art.py` sustituye únicamente los actores de entorno etiquetados, sin reconstruir ni modificar el gameplay. El pase World Art V3 añade a los nueve mapas materiales por mundo, fachadas con bahías y columnas, ventanas individuales, coronaciones, antenas, cartelería, tráfico lejano, paneles de cornisa, HVAC compuesto, barandillas, niebla y una iluminación recalibrada. Los peligros tienen siluetas, color y movimiento propios para pinchos, memoria, trituradora y valla láser; las plataformas de fase avisan mediante parpadeo y cambio de intensidad antes de desaparecer. `audit_world_art.py` impide aceptar mapas sin la densidad mínima de arte o sin sus luces y niebla.

## Pruebas actuales

- Compilación `Ciberfantasma3DEditor Win64 Development` superada.
- Verificación de estructura, datos y recursos: cero errores.
- Auditoría Blender `Scripts/audit_hero_animation_bounds.py` superada cuadro a cuadro: 53.323 vértices, 26 huesos, catorce acciones completas, 234/234 pistas escalares por acción y todos los fotogramas entregados dentro de límites espaciales y temporales.
- Auditoría de contactos `Scripts/audit_hero_foot_contacts.py` superada: cierre exacto de los loops, alternancia izquierda/derecha en carrera y marcha agachada, y apoyo bilateral simétrico durante la compresión del aterrizaje.
- Test runtime `CFAutomatedFootIKTest` superado también desde el ejecutable empaquetado: instancia de animación final activa, dos contactos válidos, alpha estable, pelvis acotada y ausencia de NaN en offsets y rotaciones.
- El smoke test de presentación recorre ambos sentidos y valida que entrada, velocidad y eje visual coinciden. Una prueba de locomoción separada exige la cadena completa `RunStart → Run → RunStop → Idle` y comprueba que el personaje termina físicamente detenido. Un test contralateral independiente corre hacia la derecha y dispara hacia la izquierda, repite después el caso espejo —carrera hacia la izquierda y disparo hacia la derecha— y exige conservar orientación/velocidad, seleccionar `FireBack`, avanzar su capa aditiva y mantener fogonazo/proyectil en la dirección de disparo; cualquier regresión devuelve código de proceso distinto de cero.
- Auditoría de los cinco sistemas Niagara runtime: superada.
- Auditoría World Art V3 de los nueve mapas: superada; geometría jugable preservada.
- Los nueve mapas generados con 148 plataformas base, nueve rutas aéreas opcionales, 68 enemigos, 27 fragmentos y 14 terminales. La auditoría valida además el tipo de cada peligro y el inventario exacto de plataformas móviles/fase.
- La V11 está importada y auditada en Unreal con cero errores y cero avisos. El último cook completo empaquetado corresponde a V10: 708 paquetes cocinados, 640 paquetes runtime (707 entradas importadas), materiales de héroe V12, catorce animaciones, Control Rig y los ocho meshes únicos de enemigo.
- El empaquetado Windows Development V10 permanece funcional en `Builds/Windows-Development`; la V11 debe sustituirlo en el siguiente cook antes de considerarla build distribuible.

## Trabajo artístico restante

- Rigs y animaciones propios para enemigos y jefes (actualmente Static Mesh con movimiento procedural).
- Escultura de alta resolución independiente, retopología manual orientada a deformación y bake high-to-low de normales, AO y curvatura; la V11 ya dispone de silueta corregida, UV0, biseles refinados y microdetalle PBR 2K, pero no sustituye ese trabajo artístico manual.
- Texturas de autor 4K con desgaste localizado, costuras, variación material y decals narrativos; mantener las actuales como base reproducible y variante de rendimiento.
- Audio: música ambiental por mundo, SFX de disparo, salto, daño, recogida, victoria y derrota.
- Escenarios únicos por acto: geometría a mano, props 3D y VFX de entorno.
