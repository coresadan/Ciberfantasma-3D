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

- `SK_Ciberfantasma_Chibi_Pro`: esqueleto chibi de 23 huesos con pelvis, dos tramos de columna, cuello, cabeza, clavículas, brazos segmentados, manos, arma, piernas, pies y puntas.
- Diez secuencias a 60 FPS: idle, run, jump start, jump rise, jump fall, land, crouch, fire, shield y hit.
- Máquina de presentación en C++ gobernada por velocidad, estado de suelo, velocidad vertical, agachado, disparo, daño y escudo.
- Carrera con velocidad de reproducción variable, clips de acción con bloqueo temporal, giro visual de tres cuartos e inclinación de movimiento.
- Escudo esférico translúcido, pulso emisivo, luz de escudo, fogonazo de disparo y material propio para el proyectil.
- Cámara lateral con perspectiva, seguimiento amortiguado, anticipación horizontal y respuesta breve al aterrizaje.

## VFX de combate implementados

- Cinco sistemas Niagara con emisores reales y assets cocinables: impacto de pulso, fogonazo, absorción de escudo, muerte de enemigo y explosión de jefe.
- Enlace nativo en los puntos de gameplay correspondientes mediante `UNiagaraFunctionLibrary`, con escala y orientación específicas por evento.
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

`Content/Python/build_campaign.py` convierte las coordenadas Canvas a centímetros Unreal y genera los nueve mapas con tres planos de profundidad, decorado procedural y luces dinámicas por acto.

## Pruebas actuales

- Compilación `Ciberfantasma3DEditor Win64 Development` superada.
- Verificación de estructura, datos y recursos: cero errores.
- Auditoría de los cinco sistemas Niagara runtime: superada.
- Los nueve mapas generados con 148 plataformas, 68 enemigos, 27 fragmentos, 14 terminales.
- Cook completo validado con 631 paquetes, sin referencias Niagara heredadas y con los ocho meshes únicos de enemigo presentes en el manifiesto.
- Empaquetado Windows Development funcional en `Builds/Windows-Development`; smoke tests de animación/VFX y ataque enemigo superados desde el ejecutable.

## Trabajo artístico restante

- Animation Blueprint con máquina de estados y mezclas aditivas para el protagonista (actualmente usa máquina C++ directa).
- Rigs y animaciones propios para enemigos y jefes (actualmente Static Mesh con movimiento procedural).
- Desgaste, roughness maps y detalles de superficie en texturas.
- Audio: música ambiental por mundo, SFX de disparo, salto, daño, recogida, victoria y derrota.
- Escenarios únicos por acto: geometría a mano, props 3D y VFX de entorno.
