"""
Cálculos del puente H (Persona 2) - EL4201 Proyecto 4
Todos los valores marcados como PROVISIONAL se reemplazan cuando la
Persona 3 entregue R y L medidos y el grupo cierre Vdc y f_sw.
Ejecutar:  python calculos_puente.py
"""
import math

# ---------------- Parámetros (PROVISIONALES) ----------------
Vdc    = 24.0      # V   tensión de bus (rango permitido 12-24 V)
fsw    = 20e3      # Hz  frecuencia de conmutación por transistor
f0     = 50.0      # Hz  frecuencia de la referencia
R_ext  = 8.0       # ohm resistencia externa      (Persona 3)
R_dev  = 2.0       # ohm resistencia del devanado (Persona 3)
L      = 20e-3     # H   inductancia              (Persona 3)
R_ext2 = 1.25 * R_ext   # cambio de carga de +25 % sobre R externa
I_pk   = [0.2, 0.5, 1.0]  # A pico
m_max  = 0.90      # índice máximo que se deja usar (margen para el PR)
C_opts = [220e-6, 470e-6, 1000e-6]  # F  opciones de capacitor de bus

w  = 2 * math.pi * f0
X  = w * L

def ripple_pp(m):
    """Rizado pico a pico en PWM unipolar para índice instantáneo |m|."""
    m = abs(m)
    return Vdc * m * (1 - m) / (2 * L * fsw)

def ripple_max_hasta(ma):
    """Máximo rizado a lo largo del ciclo de 50 Hz (|m| recorre 0..ma)."""
    return ripple_pp(min(ma, 0.5))

def energia_regenerada(R, Ipk, n=20000):
    """Energía devuelta al bus en UN intervalo regenerativo (hay 2 por ciclo).
    p(t) = v*i con i = Ipk sin(wt) y v = R i + L di/dt (valores promedio)."""
    T = 1 / f0
    dt = T / n
    e_neg = 0.0
    for k in range(n):
        t = k * dt
        i = Ipk * math.sin(w * t)
        v = R * i + L * Ipk * w * math.cos(w * t)
        p = v * i
        if p < 0:
            e_neg += -p * dt
    return e_neg / 2

def tabla(titulo, cab, filas):
    print(f"\n{titulo}")
    print(" | ".join(cab))
    for f in filas:
        print(" | ".join(f))

# ---------------- 1. Margen de tensión y rizado ----------------
filas = []
casos = [(R_ext + R_dev, I) for I in I_pk] + [(R_ext2 + R_dev, 0.5), (R_ext2 + R_dev, 1.0)]
for R, I in casos:
    Z = math.hypot(R, X)
    phi = math.degrees(math.atan2(X, R))
    Vpk = I * Z
    ma = Vpk / Vdc
    filas.append([f"{R:.1f}", f"{I:.1f}", f"{Z:.2f}", f"{phi:.1f}", f"{Vpk:.2f}",
                  f"{ma:.3f}", "OK" if ma <= m_max else "NO",
                  f"{ripple_max_hasta(ma)*1e3:.2f}"])
tabla("Tabla A - Margen de tensión y rizado (PWM unipolar)",
      ["R_tot [ohm]", "I_pk [A]", "|Z| [ohm]", "phi [deg]", "V_pk req [V]",
       "m_a", f"m_a<={m_max}", "di_pp max [mA]"], filas)
print(f"Rizado máximo absoluto (m=0.5): {ripple_pp(0.5)*1e3:.2f} mA  "
      f"(límite 200 mA)")

# ---------------- 2. Esfuerzos sobre los MOSFET ----------------
I = max(I_pk)
di = ripple_max_hasta((I * math.hypot(R_ext + R_dev, X)) / Vdc)
I_rms_carga = I / math.sqrt(2)
filas = [
    ["Tensión de bloqueo V_DS", f"{Vdc:.1f} V", f">= {2.5*Vdc:.0f} V (factor 2,5 por sobretensiones)"],
    ["Corriente pico I_D", f"{I + di/2:.3f} A", "1 A pico + mitad del rizado"],
    ["Corriente pico de diseño", "2.0 A", "transitorios de consigna/carga, umbral de protección"],
    ["I_rms carga", f"{I_rms_carga:.3f} A", "a 1,0 A pico"],
    ["I_rms por MOSFET (cota)", f"{I_rms_carga:.3f} A", "conservador: toda la corriente por un solo dispositivo"],
    ["I_rms por MOSFET (típico)", f"{I_rms_carga/math.sqrt(2):.3f} A", "la corriente se reparte entre alto y bajo de la pierna"],
]
tabla("Tabla B - Esfuerzos eléctricos en cada MOSFET",
      ["Magnitud", "Valor", "Criterio"], filas)

# ---------------- 3. Bus DC y capacitor ----------------
R = R_ext + R_dev
P_carga = R * I**2 / 2
I_bus = P_carga / Vdc
E_reg = energia_regenerada(R, I)
E_reg_peor = energia_regenerada(R_ext2 + R_dev, I)
print("\nTabla C - Bus DC")
print(f"Potencia en la carga a 1 A pico: {P_carga:.2f} W "
      f"(R_ext disipa {R_ext*I**2/2:.2f} W, devanado {R_dev*I**2/2:.2f} W)")
print(f"Corriente media del bus: {I_bus:.3f} A")
print(f"Energía devuelta por intervalo regenerativo: {E_reg*1e3:.3f} mJ "
      f"(con R_ext +25 %: {E_reg_peor*1e3:.3f} mJ)")
print("Si la fuente no absorbe corriente, toda va al capacitor:")
for C in C_opts:
    dV = E_reg / (C * Vdc)
    print(f"  C_bus = {C*1e6:6.0f} uF  ->  dV_bus ~ {dV*1e3:6.1f} mV")
print("Tensión nominal del capacitor: >= 1,5*Vdc ->", f"{1.5*Vdc:.0f} V  (usar 50 V)")
