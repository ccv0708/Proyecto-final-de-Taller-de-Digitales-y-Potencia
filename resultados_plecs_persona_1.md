# Resultados PLECS de la Persona 1 de Potencia

Se analizaron once CSV de `Scopes_Plex` correspondientes al modelo `02_Puente_H_PR.plecs`. Son resultados de la simulación PLECS compartida, con bus nominal de 24 V, PWM a 20 kHz, control cada 50 µs, referencia de 50 Hz, inductancia de 20 mH y tiempo muerto de 300 ns. Las resistencias nominales son 8 Ω externos y 2 Ω de devanado.

## Seguimiento en régimen

| Caso | Referencia (A pico) | Fundamental de corriente (A pico) | Error de amplitud | Fase de corriente respecto de referencia | Corriente RMS (A) | Rizado (mA pico a pico) | Fundamental de vAB (V pico) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0,2 | 0,18960 | 5,20 % | −0,246° | 0,13408 | 2,63 | 2,251 |
| 2 | 0,5 | 0,47658 | 4,68 % | −0,236° | 0,33700 | 5,44 | 5,642 |
| 3 | 1,0 | 0,95486 | 4,51 % | −0,232° | 0,67520 | 7,53 | 11,263 |

Los tres casos cumplen los límites del instructivo en simulación, con un error de amplitud de hasta 10 % y un rizado de hasta 0,20 A pico a pico. El signo de fase negativo indica atraso respecto a la referencia exportada. La amplitud medida fue menor que la consigna en los tres puntos.

## Cambios de consigna y carga

| Caso | Cambio a los 165 ms | Fundamental antes → después (A pico) | Máximo absoluto después del cambio (A) | Tiempo de establecimiento con banda del 5 % |
|---|---|---:|---:|---:|
| 4 | Referencia de 0,2 a 0,5 A pico | 0,18959 → 0,47658 | 0,48007 | 0,40 ms |
| 5 | Referencia de 0,5 a 1,0 A pico | 0,47655 → 0,95486 | 0,95950 | 0,70 ms |
| 6 | Carga total de 10 a 12 Ω con referencia de 0,5 A pico | 0,47655 → 0,47256 | 0,47934 | Dentro de la banda desde el cambio |

En el caso 6, la fundamental de tensión diferencial subió de **5,642 a 6,435 V pico**, mientras que la fundamental de corriente bajó unos **4,00 mA** respecto de su valor anterior. La resistencia externa subió de 8 a 10 Ω, un 25 %. El cociente fasorial tensión/corriente da una parte real aproximada de **10,02 Ω antes y 12,07 Ω después**, coherente con las resistencias totales configuradas. Después del cambio, la corriente fue **0,33416 A RMS** y el rizado fue **5,90 mA pico a pico**.

El tiempo de establecimiento se midió en muestras de corriente cada 50 µs, comparadas con el último ciclo periódico a la misma fase. El criterio fue quedar dentro de ±5 % de la amplitud final de la fundamental y permanecer en la banda hasta el final de la corrida. La estimación tiene una resolución de 50 µs.

## Datos para la Persona 2

- En el caso 3, el bus varió entre **23,95075 y 24,08024 V** en la corrida completa, con una excursión total de **129,49 mV**. La tensión diferencial vAB tuvo extremos de **−26,61047 y +26,61057 V**. Son extremos de la tensión de carga del modelo.
- Los **262 relevos entre compuertas complementarias** con ambos flancos disponibles en la ventana exportada del caso 3 dieron **300 ns**, en ambas direcciones de cada rama. En esa ventana no hubo solapamiento de S1/S2 ni de S3/S4.
- En el caso 7 se inyectó la señal de falla a los **200,000 ms**. El permiso cayó y las cuatro órdenes de compuerta quedaron en cero a los **200,150 ms**, es decir, **150 µs** después. Las compuertas siguieron en cero hasta el final de su captura, a **205,575 ms**. La prueba verifica el corte ante una inyección simulada en el supervisor.

## Datos para la Persona 3

- Para la mayor consigna nominal, el caso 3 entrega **0,67520 A RMS**, **0,95950 A de pico absoluto** y **7,53 mA pico a pico de rizado**.
- Con 8 Ω externos, la disipación estimada a partir de la corriente RMS de esa corrida es **3,65 W** en la resistencia externa. A la consigna nominal ideal de 1 A pico, el dimensionamiento sigue siendo **4,00 W** antes de aplicar el margen térmico del componente.
- La comparación del caso 6 indica cuánto debe variar la tensión para sostener la corriente cuando cambia la resistencia. Las mediciones de resistencia, inductancia y calibración del sensor se obtienen del montaje físico.

## Método y cobertura

- Para los resultados estacionarios se usaron cinco períodos de 50 Hz, de **300 a 400 ms**, remuestreados a **0,5 µs**. La fundamental se ajustó con seno, coseno y componente continua. Se comparó la fase de la corriente con la referencia exportada y se calculó el RMS de la corriente completa.
- El rizado se calculó quitando las componentes de hasta 2 kHz y tomando el máximo pico a pico del residuo en ventanas de 1 ms. Los picos absolutos y extremos de bus se tomaron de las muestras originales. Para compuertas se conservaron los tiempos originales de los flancos.
- Están los datos de los casos 1–6 y los dos Scopes de falla del caso 7. El CSV corregido `02_caso6_control.csv` confirma que el bypass pasa de **1 a 0 a los 165,000 ms** y que el permiso PWM se mantiene en **1** durante toda la captura, de 150,90 a 202,55 ms. Se conserva la captura de PWM del envío anterior como `02_caso6_compuertas.csv`. Los seis CSV principales de corriente y tensión coinciden con los ya analizados, por lo que se mantienen las métricas de las tablas.
- Las capturas de PWM disponibles corresponden a los casos 3, 6 y 7. Si el informe se arma con evidencia PWM individual de cada ensayo, faltaría exportar `Scope_puente` de los casos 1, 2, 4 y 5. El CSV del modelo promediado 01 sería complementario para comparar modelos.

## Ubicación propuesta en el repositorio de Potencia

Creá una carpeta `persona_1/` en la raíz del repositorio y copiá dentro el contenido de la carpeta `Avances locales/` del ZIP.

| Contenido del ZIP | Destino en el repositorio |
|---|---|
| `resultados_plecs_persona_1.md` | `persona_1/resultados_plecs_persona_1.md` |
| `LEEME.md` | `persona_1/LEEME.md` |
| `Control/` | `persona_1/Control/` |
| `PLECS/` | `persona_1/PLECS/` |
| `Python/` | `persona_1/Python/`, con `resultados/` dentro |
| `Scopes_Plex/` | `persona_1/Scopes_Plex/` si el grupo usa Git LFS para los CSV grandes. También puede conservarse como carpeta de datos compartida fuera del repositorio. |

El archivo `00_Puente_H_P2_original.plecs` es una copia de referencia del puente de la Persona 2. El archivo del equipo ya está en `calculos_puente/P2_puente_H.plecs`. Podés omitir la copia 00 al subir tu parte. Conservá los modelos 01 y 02.
