# El Ciberfantasma 3D

Recreación independiente en Unreal Engine de `El Ciberfantasma: Código Libre` como juego de acción y plataformas 2.5D. Los datos de la campaña proceden del juego Canvas original situado en `D:\Trabajo\Ciberfantasma Bros`; el original no se modifica ni es necesario para ejecutar la build.

## Estado jugable

- Campaña completa de nueve actos y tres mundos, con transición automática entre mapas y pantalla de victoria final.
- Disposición original de plataformas, plataformas móviles y de fase, peligros, fragmentos, terminales, enemigos, jefes y portales.
- Movimiento lateral, doble salto, agachado, disparo bidireccional, escudo temporal, daño, reaparición en checkpoints y derrota.
- Tres fragmentos obligatorios por acto; los portales de jefe también exigen derrotar al jefe.
- Puntuación persistente entre actos por fragmentos, terminales, enemigos, jefes y bloqueos con escudo.
- HUD con salud, fragmentos, puntos, carga de escudo, objetivo, mensajes de nivel, victoria y derrota.
- Protagonista chibi como Skeletal Mesh profesional de 26 huesos, con catorce clips de juego: reposo, arranque/ciclo/frenada de carrera, inicio/subida/caída de salto, aterrizaje, agachado, marcha agachada, disparo normal/contralateral, escudo e impacto.
- Presentación reactiva enlazada a la física: velocidad de carrera variable, lectura separada de salto y caída, aterrizaje, inclinación de avance, anticipación de cámara, retroceso de disparo y escudo 3D emisivo.
- **9 perfiles chibi de enemigo** sobre 8 meshes únicos: bot, drone, crawler, harvester, enforcer, auditor, CEO-9000 y Director. Cada tipo tiene forma, paleta y luz de acento propias. `ApplyProfile()` selecciona mesh, escala, salud, velocidad y color desde un catálogo de referencias duras compatible con el cooker.
- Escenarios con tres planos de profundidad, fachadas, skyline, ventanas, cornisas, antenas, climatización, barandillas y neón temático en los nueve actos.
- Iluminación dinámica calibrada para conservar el traje negro, sin lightmaps pendientes, DX11 y ajustes compatibles con una GTX 1060 de 6 GB.
- **VFX Niagara runtime**: cinco sistemas con emisores reales conectados a impacto de pulso, fogonazo, absorción de escudo, muerte de enemigo y explosión de jefe.

## Controles

- `A` / `D` o flechas izquierda/derecha: mover.
- `Espacio`, `W` o flecha arriba: salto y doble salto.
- `S` o flecha abajo: agacharse.
- `J`: disparar a la izquierda.
- `K`: disparar a la derecha.
- `X` o clic izquierdo: disparar hacia donde mira el personaje.
- `L`: escudo temporal.
- `P` o `Esc`: pausa.
- `R`: reiniciar el acto.
- `Enter`: reiniciar la campaña tras victoria o derrota.

## Preparar el proyecto

Con Unreal Engine 5.8, Visual Studio 2022 Build Tools, Node.js y Blender instalados:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\setup_unreal_project.ps1 -OpenEditor
```

El proceso vuelve a extraer los nueve actos desde Canvas, genera e importa los 9 modelos chibi de enemigo y el protagonista, compila C++ y reconstruye todos los mapas. El mapa inicial es `/Game/Maps/Act01_Rooftops`.

## Generación de VFX

```powershell
F:\Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe .\Ciberfantasma3D.uproject -run=pythonscript "-script=Content\Python\create_vfx_assets.py" -unattended -nop4 -nosplash
```

Crea sistemas Niagara runtime a partir de plantillas authored de Unreal en `/Game/Art/VFX`; también reemplaza automáticamente los antiguos assets vacíos.

## Verificación

Comprobación rápida de estructura, datos, mapas, controles y recursos:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\verify_project.ps1
```

La auditoría profunda carga los nueve mapas dentro de Unreal y compara sus actores jugables con los datos Canvas:

```powershell
F:\Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe .\Ciberfantasma3D.uproject -run=pythonscript "-script=Content\Python\audit_campaign.py" -unattended -nop4 -nosplash
```

La auditoría del héroe comprueba el esqueleto, los seis materiales, las catorce secuencias y el Control Rig bilateral de pies:

```powershell
F:\Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe .\Ciberfantasma3D.uproject -run=pythonscript "-script=Content\Python\audit_hero_assets.py" -unattended -nop4 -nosplash
```

Antes de importar, Blender valida cada fotograma y los contactos principales de locomoción:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" .\SourceAssets\Blender\CF_Character_Workfile.blend --background --python .\Scripts\audit_hero_animation_bounds.py
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" .\SourceAssets\Blender\CF_Character_Workfile.blend --background --python .\Scripts\audit_hero_foot_contacts.py
```

El generador produce además ocho mapas PBR/normal de 2048×2048 para capucha, traje, armadura y máscara; `verify_project.ps1` valida sus cabeceras PNG para evitar reducciones accidentales de resolución.

El solve final de IK se valida dentro del juego con dos trazas, compensación de pelvis y límites numéricos:

```powershell
F:\Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe .\Ciberfantasma3D.uproject -game -CFAutomatedFootIKTest -unattended -nullrhi -nosound
```

La auditoría VFX rechaza sistemas vacíos y comprueba la versión de los cinco efectos runtime:

```powershell
F:\Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe .\Ciberfantasma3D.uproject -run=pythonscript "-script=Content\Python\audit_vfx_assets.py" -unattended -nop4 -nosplash
```

## Build de Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\package_windows.ps1
```

El ejecutable se genera dentro de `Builds/Windows-Development`. El empaquetado cocina expresamente los nueve mapas de la campaña; el verificador también impide volver a usar cargas dinámicas de meshes que Unreal no pueda descubrir durante el cook.
