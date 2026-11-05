# Regulador PR y simulación PLECS

El modelo conmutado del puente H integra un regulador proporcional resonante (PR) para seguir una referencia de corriente de 50 Hz. Los resultados de los siete ensayos están en [resultados_plecs_persona_1.md](resultados_plecs_persona_1.md).

## Archivos del repositorio

| Ruta | Contenido |
|---|---|
| [`calculos_puente/P2_puente_H.plecs`](calculos_puente/P2_puente_H.plecs) | Puente H original de la Persona 2, en lazo abierto. |
| [`calculos_puente/01_Promediado_PR.plecs`](calculos_puente/01_Promediado_PR.plecs) | Modelo promediado con fuente controlada y PR. |
| [`calculos_puente/02_Puente_H_PR.plecs`](calculos_puente/02_Puente_H_PR.plecs) | Modelo conmutado con PR, cambio de carga y supervisor de falla. |
| [`calculos_puente/Scopes_Plex.zip`](calculos_puente/Scopes_Plex.zip) | Once CSV de PLECS dentro de la carpeta `Scopes_Plex/`. |
| [`scripts/control_pr/`](scripts/control_pr/) | Código C del regulador y del supervisor, y ajustes del modelo en `ajustes_P1.m`. |
| [`scripts/`](scripts/) | Scripts de simulación de referencia y análisis de CSV. |
| [`scripts/resultados/`](scripts/resultados/) | CSV y gráficas generados por Python. |
| [`resultados_plecs_persona_1.md`](resultados_plecs_persona_1.md) | Mediciones extraídas de los Scopes de PLECS y método de análisis. |

Los parámetros del puente original están en [`calculos_puente/parametros_puente.m`](calculos_puente/parametros_puente.m). Los modelos 01 y 02 ya traen su inicialización y el código C incorporados.

## Ejecutar los casos en PLECS

1. Abrí el modelo 01 en **PLECS Standalone 5.0**. Para una primera comprobación, configurá `caso = 2;`. La referencia numérica del promediado para ese caso es **0,479 A pico** en la fundamental.
2. Abrí el modelo 02 y configurá el mismo caso. En la corrida documentada en el informe, la fundamental de corriente fue de **0,47658 A pico**.
3. Para cambiar de ensayo, abrí **Simulation → Simulation Parameters → Initialization** y editá `caso` en el bloque de ajustes P1, cerca del final. Aplicá el cambio y corré el modelo de nuevo. En el puente original en lazo abierto se ajusta `I_ref` en lugar de `caso`.

| `caso` | Referencia de corriente | Evento |
|---:|---|---|
| 1 | 0,2 A pico | Carga nominal de 10 Ω totales |
| 2 | 0,5 A pico | Carga nominal de 10 Ω totales |
| 3 | 1,0 A pico | Carga nominal de 10 Ω totales |
| 4 | 0,2 → 0,5 A pico | Cambio de consigna a los 165 ms |
| 5 | 0,5 → 1,0 A pico | Cambio de consigna a los 165 ms |
| 6 | 0,5 A pico | A los 165 ms el bypass abre. La resistencia externa cambia de 8 a 10 Ω y la total de 10 a 12 Ω. |
| 7 | 0,5 A pico | A los 200 ms se inyectan 2 A en la entrada del supervisor para probar el corte. |

Las corridas duran **0,4 s**. El modelo usa un bus nominal de **24 V**, PWM de **20 kHz**, muestreo del PR cada **50 µs**, una inductancia de **20 mH** y un filtro de corriente de **3 kHz**. En el puente conmutado, el tiempo muerto configurado es de **300 ns** y el índice de modulación se limita a **±0,90**.

| Scope | Canales en orden |
|---|---|
| `Scope_datos`, modelo 01 | Referencia, corriente de carga, tensión aplicada y permiso PWM. |
| `Scope_datos`, modelo 02 | Referencia, corriente de carga, tensión diferencial y tensión del bus. |
| `Scope_control`, ambos modelos | Índice de modulación, corriente filtrada, permiso PWM y orden del bypass. |
| `Scope_puente`, modelo 02 | Señales del modulador, cuatro órdenes de compuerta, tensión diferencial, corriente y tensión del bus. |

En el caso 6, el CSV de control confirma que el bypass pasa de `1` a `0` a los **165 ms** y que el permiso permanece en `1` durante la captura. En el caso 7, el supervisor enclava la falla al detectar tres muestras consecutivas con corriente en magnitud superior a **1,5 A**. Las cuatro órdenes de compuerta quedaron en cero **150 µs** después de la inyección simulada.

## Reproducir el análisis en Windows

Ejecutá estos comandos de PowerShell desde la **raíz del repositorio**. El ZIP de datos debe contener la carpeta `Scopes_Plex/` con los CSV dentro. El ejemplo la extrae en una carpeta vecina para que los CSV queden fuera del árbol de trabajo.

```powershell
Expand-Archive -LiteralPath .\calculos_puente\Scopes_Plex.zip -DestinationPath ..\Potencia_PR_Scopes
py -3.11 -m pip install numpy scipy matplotlib
py -3.11 .\scripts\validar_pr.py
py -3.11 .\scripts\referencia_puente.py
py -3.11 .\scripts\analizar_csv_plecs.py ..\Potencia_PR_Scopes\Scopes_Plex\02_caso3_datos.csv --caso 3 --conmutado
```

`validar_pr.py` y `referencia_puente.py` guardan sus resultados en `scripts/resultados/`. Esas corridas sirven como referencia numérica. Las mediciones de PLECS provienen de `Scopes_Plex.zip`. Para analizar una exportación propia, usá un CSV de `Scope_datos` con encabezado y con **tiempo en segundos, referencia y corriente de carga** como primeras tres columnas. Usá `--conmutado` para calcular el rizado y omitilo para el modelo promediado. Para el caso 7, revisá el permiso y las compuertas en sus respectivos Scopes.

## Código del PR

El C-Script recibe la corriente cruda para el supervisor y la corriente filtrada para el PR. Sus salidas son el índice de modulación, el permiso PWM, la referencia y la orden del bypass, en ese orden. El promediado multiplica el índice por la tensión del bus. En el puente H, el índice entra directamente al PWM.

| Sección del C-Script | Archivo |
|---|---|
| Code Declarations | [`scripts/control_pr/Declaraciones.c`](scripts/control_pr/Declaraciones.c) |
| Start Function | [`scripts/control_pr/Inicio.c`](scripts/control_pr/Inicio.c) |
| Output Function | [`scripts/control_pr/Salida.c`](scripts/control_pr/Salida.c) |
| Update Function | [`scripts/control_pr/Actualizacion.c`](scripts/control_pr/Actualizacion.c) |
| Inicialización del modelo | [`scripts/control_pr/ajustes_P1.m`](scripts/control_pr/ajustes_P1.m) |

La simulación documenta el seguimiento de corriente, los transitorios y el corte del supervisor. Para llevar el control al montaje físico quedan por confirmar la carga y la respuesta del sensor, el retardo de actuación y el tiempo muerto de la cadena de compuertas.
