"""
Cálculos del accionamiento del puente H 
Componentes: MOSFET IRF520N + driver IR2101 (bootstrap).
"""
import math

#  Datos de hoja de datos 
# IRF520N
VDSS, RDS_ON, RDS_ON_CAL = 100, 0.20, 0.30   # V, ohm (25 C), ohm (caliente, ~1,5x)
QG, QGD, CISS = 25e-9, 11e-9, 330e-12        # C, C, F (Qg y Qgd máximos a VGS=10 V)
VTH_MIN, VGS_MAX, VSD = 2.0, 20.0, 1.3       # V
RTH_JA, TJ_MAX = 62.0, 175.0                 # C/W, C
# IR2101
IO_SRC, IO_SNK = 0.130, 0.270                # A (mínimos)
T_ON_TYP, T_OFF_MAX = 160e-9, 220e-9         # s retardos de propagación
MT = 50e-9                                   # s desajuste máximo entre canales
IQBS, IQCC = 55e-6, 270e-6                   # A (máximos)
VBS_MIN = 10.0                               # V mínimo recomendado del canal alto
Q_LS = 5e-9                                  # C carga de desplazamiento de nivel (típica de drivers 600 V)

# Condiciones de operación (provisionales)
Vdc, fsw, I_pk = 24.0, 20e3, 1.0
VCC = 15.0              # V alimentación de drivers (regulador 7815)
VF_BOOT = 1.0           # V caída del diodo de bootstrap (UF4007)
C_BOOT = 1e-6           # F elegido
R_G = 10.0              # ohm resistencia de compuerta
T_AMB = 30.0            # C
F_CLK = 100e6           # Hz reloj del PWM (MicroBlaze / Taller)

def linea(nombre, valor, nota=""):
    print(f"  {nombre:<46s} {valor:<18s} {nota}")

print("\n1. Alimentación de los drivers")
i_drv = IQCC + IQBS + 2 * QG * fsw          # por driver: reposo + carga de 2 compuertas
i_tot = 2 * i_drv
linea("Corriente por driver", f"{i_drv*1e3:.2f} mA", "reposo + 2*Qg*fsw")
linea("Corriente total (2 drivers)", f"{i_tot*1e3:.2f} mA")
linea("Disipación del 7815 desde 24 V", f"{(Vdc-VCC)*i_tot*1e3:.1f} mW", "no requiere disipador")
linea("Tensión de compuerta", f"{VCC:.0f} V", f"< VGS máx {VGS_MAX:.0f} V")

print("\n2. Bootstrap (método de la nota AN-978 de IR)")
Q_ciclo = 2 * QG + IQBS / fsw + Q_LS
dV_perm = VCC - VF_BOOT - VBS_MIN
C_min = 2 * Q_ciclo / dV_perm
dV_real = (QG + IQBS / fsw + Q_LS) / C_BOOT
linea("Carga por ciclo Q", f"{Q_ciclo*1e9:.1f} nC", "2Qg + Iqbs/f + Qls")
linea("Caída permitida (VCC - Vf - VBSmin)", f"{dV_perm:.2f} V")
linea("C_boot mínimo (factor 2)", f"{C_min*1e9:.1f} nF")
linea("C_boot elegido", f"{C_BOOT*1e6:.1f} uF", f"caída real {dV_real*1e3:.0f} mV por ciclo")
d_max = (1 + 0.9) / 2
t_rec = (1 - d_max) / fsw
linea("Tiempo mínimo de recarga (m = 0,9)", f"{t_rec*1e6:.2f} us", "lado bajo encendido")

print("\n3. Tiempo muerto")
q_off = QG + CISS * (VCC - 10)              # carga a retirar desde VCC
t_off_mos = q_off / IO_SNK                  # apagado limitado por la corriente del driver
t_enc = T_OFF_MAX - T_ON_TYP                # el que se apaga tarda más que el que se enciende
t_dt_min = t_enc + MT + t_off_mos
t_dt = math.ceil(1.4 * t_dt_min / 10e-9) * 10e-9
linea("Apagado del MOSFET (Q/I_sink)", f"{t_off_mos*1e9:.0f} ns")
linea("Diferencia de retardos del driver", f"{t_enc*1e9:.0f} ns", "toff,max - ton,typ")
linea("Desajuste entre canales MT", f"{MT*1e9:.0f} ns")
linea("Tiempo muerto mínimo", f"{t_dt_min*1e9:.0f} ns")
linea("Tiempo muerto elegido (x1,4)", f"{t_dt*1e9:.0f} ns", f"= {round(t_dt*F_CLK)} ciclos de 10 ns")
err_old = 4 / math.pi * 2 * Vdc * 500e-9 * fsw
err_new = 4 / math.pi * 2 * Vdc * t_dt * fsw
linea("Error de tensión fundamental (500 ns)", f"{err_old:.3f} V")
linea("Error de tensión fundamental (nuevo)", f"{err_new:.3f} V", f"{100*(1-err_new/err_old):.0f} % menos")

print("\n4. Pérdidas y temperatura por MOSFET (1 A pico)")
I_rms_sw = I_pk / 2                          # cota típica por dispositivo
p_cond = I_rms_sw**2 * RDS_ON_CAL
t_r = QGD / IO_SRC
t_f = QGD / IO_SNK
I_conm = 2 / math.pi * I_pk                  # corriente media conmutada
p_sw = 0.5 * Vdc * I_conm * (t_r + t_f) * fsw / 2   # conmuta con corriente medio ciclo
p_dt = VSD * I_conm * t_dt * fsw / 2
p_tot = p_cond + p_sw + p_dt
tj = T_AMB + p_tot * RTH_JA
linea("Conducción", f"{p_cond*1e3:.1f} mW", f"I_rms={I_rms_sw:.2f} A, Rds caliente={RDS_ON_CAL} ohm")
linea("Conmutación", f"{p_sw*1e3:.1f} mW", f"tr~{t_r*1e9:.0f} ns, tf~{t_f*1e9:.0f} ns")
linea("Diodo en tiempo muerto", f"{p_dt*1e3:.1f} mW")
linea("Total por MOSFET", f"{p_tot*1e3:.0f} mW")
linea("Temperatura de unión sin disipador", f"{tj:.0f} C", f"límite {TJ_MAX:.0f} C")
for f in (10e3, 20e3, 40e3):
    ps = 0.5 * Vdc * I_conm * (t_r + t_f) * f / 2 + VSD * I_conm * t_dt * f / 2
    linea(f"  Total a {f/1e3:.0f} kHz", f"{(p_cond+ps)*1e3:.0f} mW")

print("\n5. Protecciones (versión mínima)")
I_SW, N_MUESTRAS = 1.5, 3          # A umbral de corte por software, muestras consecutivas
L_c = 20e-3
for Tc in (50e-6, 100e-6, 200e-6):  # períodos de control posibles
    di = Vdc / L_c * N_MUESTRAS * Tc
    linea(f"Subida máx. en {N_MUESTRAS} muestras (Tc={Tc*1e6:.0f} us)", f"{di:.2f} A",
          f"corta antes de {I_SW+di:.2f} A")
linea("Corriente media del bus a 1 A pico", f"{5.0/Vdc:.2f} A", "límite de fuente 1,5 A, fusible 2 A")
R_bl, C_b = 4.7e3, 470e-6
linea("Resistencia de descarga 4,7 kohm", f"{Vdc**2/R_bl:.3f} W", f"tau = {R_bl*C_b:.1f} s, 5 tau = {5*R_bl*C_b:.0f} s")
