# Scripts de Procesamiento y Análisis de Datos (MATLAB)

Este directorio contiene los scripts de MATLAB diseñados para procesar, calibrar y analizar las señales extraídas del entorno de simulación PLECS, pera el caso de la persona 3, este abarca los casos de entrada con (0.2 A, 0.5 A y demas).

---

## 1. Justificación Teórica del Factor de Escala $K{sensor} = 5.405$

En el script de análisis principal (analisis_multicaso.m), la señal exportada por PLECS correspondiente a la tensión acondicionada se escala según:

$$v{out} = \text{transfer fcn} \times K{sensor}$$

donde **$K{sensor} = 5.405\text{ A/V}$**.

### Origen del Factor $K_{sensor}$:
1. **Sensibilidad Nominal del Sensor ACS712-05B:** 
   El sensor integrado produce una variación analógica de $185\text{ mV/A}$ ($0.185\text{ V/A}$).
2. **Relación Inversa (Tensión a Corriente):** 
   Para reconstruir la corriente primaria $i(t)$ a partir de la tensión diferencial procesada por el amplificador operacional MCP6002 ($G=1$), se aplica el inverso matemático de la sensibilidad:

   $$K_{sensor} = \frac{1}{0.185\text{ V/A}} \approx 5.4054\text{ A/V}$$

### Demostración de Consistencia:
* Para un delta de tensión $\Delta V = 0.185\text{ V}$, el script calcula: 
  $$\Delta I = 0.185\text{ V} \times 5.4054\text{ A/V} = 1.000\text{ A}$$
* Este factor constante escala linealmente la señal en todos los casos de prueba ($0.2\text{ A}$, $0.5\text{ A}$ y $1.0\text{ A}$ pico), manteniendo una precisión relativa con error inferior al 1% respecto a las referencias ideales.

---

## 2. Descripción del Script (`analisis_multicaso.m`)

El script realiza de forma automatizada las siguientes tareas por cada archivo CSV:
1. **Calibración y Conversión:** Aplica $K_{sensor} = 5.405$ a la señal de tensión para convertirla a unidades directas de corriente ($A$).
2. **Filtrado Estacionario:** Aísla una ventana de 5 ciclos completos a $50\text{ Hz}$ ($t \in [0.5, 0.6]\text{ s}$).
3. **Cálculo de Parámetros RMS y Pico:** Evalúa la corriente eficaz $I_{rms}$ y el valor pico absoluto.
4. **Análisis de Rizado de Conmutación:** Separa la fundamental ($50\text{ Hz}$) mediante media móvil y evalúa si el rizado pico a pico cumple el criterio $\Delta i_{pp} \le 0.20\text{ A}$.
5. **Ajuste armónico (Mínimos Cuadrados):** Extrae amplitud fundamental, desfase en grados/radianes y offset de DC residual.
6. **Mapeo a Código Digital XADC (12-bit):** Calcula los códigos dinámicos del conversor analógico-digital de la FPGA Nexys 4 ($[0\text{ V}, 1\text{ V}] \rightarrow [0, 4096]$).
