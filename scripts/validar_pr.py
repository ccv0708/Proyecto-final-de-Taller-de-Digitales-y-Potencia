"""Referencia numérica del PR y de la carga RL con PWM unipolar ideal."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Parámetros de partida. Sustituir con los valores medidos del montaje.
VDC = 24.0
FSW = 20_000
F0 = 50
R_EXT = 8.0
R_EXT_ALT = 10.0
R_DEV = 2.0
L = 0.020
F_FILTRO = 3000.0
F_CRUCE_META = 600.0
F_RESONANTE = 5.0
KR = 150.0
M_LIM = 0.90
I_TRIP = 1.5
TS = 1 / FSW              # Propuesta: una actualización por período PWM.
PUNTOS_PWM = 100          # Malla de salida, no resolución del comparador.
T_CAMBIO = 0.165          # Cresta positiva de la referencia.
T_FIN = 0.400
SALIDA = Path(__file__).resolve().parent / "resultados"


def coeficientes():
    kp = np.hypot(R_EXT + R_DEV, 2 * np.pi * F_CRUCE_META * L)
    w0, wc = 2 * np.pi * np.array([F0, F_RESONANTE])
    k = w0 / np.tan(w0 * TS / 2)
    den = np.array([k*k + 2*wc*k + w0*w0,
                    2*(w0*w0 - k*k),
                    k*k - 2*wc*k + w0*w0])
    num = 2 * KR * wc * k * np.array([1., 0., -1.])
    return kp, num / den[0], den / den[0]


def estabilidad(r_total, fc, demora, kp, b, a):
    """Modelo ZOH de i e i_filtrada; demora entera adicional en la orden."""
    wf = 2 * np.pi * fc
    ac = [[-r_total / L, 0], [wf, -wf]]
    ad, bd, cd, dd, _ = signal.cont2discrete(
        tuple(map(np.array, (ac, [[1 / L], [0]], [[0, 1]], [[0]]))), TS)
    bp, ap = signal.ss2tf(ad, bd, cd, dd)
    bp = bp[0]
    bp[0] = 0.0
    lazo_b = np.r_[np.zeros(demora), np.convolve(kp*a + b, bp)]
    lazo_a = np.convolve(a, ap)
    # Los coeficientes están ordenados en potencias ascendentes de z^-1.
    # np.roots encuentra raíces en z al multiplicar todo por z^grado.
    caracteristico = np.polynomial.polynomial.polyadd(lazo_a, lazo_b)
    radio = np.max(np.abs(np.roots(caracteristico)))
    f = np.geomspace(1, 0.49999 / TS, 18000)
    q = np.exp(-2j * np.pi * f * TS)
    lazo = (np.polynomial.polynomial.polyval(q, lazo_b) /
            np.polynomial.polynomial.polyval(q, lazo_a))
    db = 20 * np.log10(np.abs(lazo))
    fase = np.unwrap(np.angle(lazo)) * 180 / np.pi
    cruces = np.flatnonzero(db[:-1] * db[1:] < 0)
    fc_out, mf_out = [], []
    for j in cruces:
        peso = db[j] / (db[j] - db[j+1])
        fc_out.append(float(f[j] * (f[j+1] / f[j])**peso))
        mf_out.append(float(180 + fase[j] + peso * (fase[j+1] - fase[j])))
    return float(radio), fc_out, mf_out, f, db, fase


def avanzar(i, y, v, duracion, r_total):
    """Solución exacta por tramos de tensión constante, con filtro continuo."""
    ai = r_total / L
    ay = 2 * np.pi * F_FILTRO
    ieq = v / r_total
    ei, ey = np.exp(-ai * duracion), np.exp(-ay * duracion)
    factor = (ay * duracion * ey if np.isclose(ai, ay, rtol=1e-10)
              else ay * (ei - ey) / (ay - ai))
    return ieq + (i - ieq) * ei, ieq + (y - ieq) * ey + (i - ieq) * factor


def segmentos_pwm(m):
    """Triangular común de -1 a +1 y vuelta; comparadores con +m y -m."""
    if m == 0:
        return [(TS, 0.0)]
    bajo = TS * (1 - abs(m)) / 4
    alto = TS * (1 + abs(m)) / 4
    pulso = np.copysign(VDC, m)
    return [(bajo, 0.0), (alto, pulso), (TS-alto, 0.0),
            (TS-bajo, pulso), (TS, 0.0)]


def simular(amp0, amp1, r_ext0, r_ext1, conmutado, kp, b, a):
    n = round(T_FIN / TS)
    local = TS * np.arange(PUNTOS_PWM) / PUNTOS_PWM
    t = TS * np.arange(n)
    tf = (t[:, None] + local).ravel()
    datos = np.empty((n, 7))
    alta = np.empty((n, PUNTOS_PWM, 2)) if conmutado else None
    i = y = x1 = x2 = m = 0.0
    for k, tk in enumerate(t):
        amp = amp0 if tk < T_CAMBIO else amp1
        r_total = (r_ext0 if tk < T_CAMBIO else r_ext1) + R_DEV
        ref = amp * np.sin(2 * np.pi * F0 * tk)
        error = ref - y
        u_libre = kp * error + b[0] * error + x1
        u_limit = np.clip(u_libre, -M_LIM * VDC, M_LIM * VDC)
        e_estado = error + (u_limit - u_libre) / (kp + KR)
        yr_estado = b[0] * e_estado + x1
        x1, x2 = b[1]*e_estado - a[1]*yr_estado + x2, b[2]*e_estado - a[2]*yr_estado
        datos[k] = ref, i, y, m, VDC*m, u_libre, u_limit
        segmentos = segmentos_pwm(m) if conmutado else [(TS, VDC*m)]
        inicio = 0.0
        for fin, voltaje in segmentos:
            if conmutado:
                indices = (local >= inicio) & (local < fin)
                alta[k, indices, 0], _ = avanzar(i, y, voltaje, local[indices]-inicio, r_total)
                alta[k, indices, 1] = voltaje
            i, y = avanzar(i, y, voltaje, fin-inicio, r_total)
            inicio = fin
        m = u_limit / VDC
    return t, datos, tf, alta.reshape(-1, 2) if conmutado else None


def fundamental(t, i):
    ang = 2 * np.pi * F0 * t
    mat = np.column_stack((np.sin(ang), np.cos(ang), np.ones_like(t)))
    coef = np.linalg.lstsq(mat, i, rcond=None)[0]
    return np.hypot(*coef[:2]), np.degrees(np.arctan2(coef[1], coef[0])), mat @ coef


def medir(t, i, amp, ventanas_rizado):
    ipk, fase, i_baja = fundamental(t, i)
    residuo = (i - i_baja).reshape(-1, ventanas_rizado)
    return ipk, 100 * abs(ipk / amp - 1), fase, np.max(np.ptp(residuo, axis=1))


def guardar_csv(nombre, cabecera, filas):
    with (SALIDA / nombre).open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)
        writer.writerow(cabecera)
        writer.writerows(filas)


def ejecutar():
    SALIDA.mkdir(exist_ok=True)
    kp, b, a = coeficientes()
    np.set_printoptions(precision=14)
    print(f"Kp={kp:.12g}; Kr={KR:.12g}; b={b}; a={a}")
    guardar_csv("coeficientes.csv", ["Kp_V_A", "Kr_V_A", "Ts_s", "b0", "b1", "b2", "a1", "a2"],
                [[kp, KR, TS, *b, *a[1:]]])
    filas_estabilidad = []
    fig, axs = plt.subplots(2, 1, sharex=True, figsize=(8, 5.1))
    for r_ext in (R_EXT, R_EXT_ALT):
        for fc in (1000., F_FILTRO, 6000.):
            for d in range(4):
                rho, fcr, mf, f, db, fase = estabilidad(r_ext+R_DEV, fc, d, kp, b, a)
                filas_estabilidad.append([r_ext, fc, d, rho,
                                          " / ".join(f"{x:.2f}" for x in fcr),
                                          " / ".join(f"{x:.2f}" for x in mf)])
                if fc == F_FILTRO and d == 1:
                    axs[0].semilogx(f, db, label=f"R ext = {r_ext:g} Ω")
                    axs[1].semilogx(f, fase)
    guardar_csv("estabilidad.csv", ["Rext_ohm", "fc_filtro_Hz", "retardo_Ts", "radio_espectral",
                                    "cruces_Hz", "margenes_fase_deg"], filas_estabilidad)
    axs[0].axhline(0, color="0.5", lw=0.8)
    axs[1].axhline(-180, color="0.5", lw=0.8)
    axs[0].legend()
    axs[0].set_ylabel("Magnitud (dB)")
    axs[1].set_ylabel("Fase (°)")
    axs[1].set_xlabel("Frecuencia (Hz)")
    for ax in axs:
        ax.grid(True, which="both", alpha=0.28)
    fig.tight_layout()
    fig.savefig(SALIDA / "lazo_abierto.png", dpi=170)
    plt.close(fig)

    casos = [
        ("nom_02", .2, .2, R_EXT, R_EXT),
        ("nom_05", .5, .5, R_EXT, R_EXT),
        ("nom_10", 1., 1., R_EXT, R_EXT),
        ("paso_02_05", .2, .5, R_EXT, R_EXT),
        ("paso_05_10", .5, 1., R_EXT, R_EXT),
        ("cambio_R_05", .5, .5, R_EXT, R_EXT_ALT),
    ]
    filas = []
    fig, axs = plt.subplots(3, 1, sharex=True, figsize=(8.5, 6.1))
    for nombre, amp0, amp1, r0, r1 in casos:
        for pwm in (False, True):
            t, datos, tf, alta = simular(amp0, amp1, r0, r1, pwm, kp, b, a)
            periodo = round(1 / (F0 * TS))
            n = 5 * periodo
            modelo = "PWM ideal" if pwm else "Promediado"
            if pwm:
                pts = n * PUNTOS_PWM
                corriente = alta[:, 0]
                ipk, err, fase, rip = medir(tf[-pts:], corriente[-pts:], amp1, PUNTOS_PWM)
            else:
                corriente = datos[:, 1]
                ipk, fase, _ = fundamental(t[-n:], corriente[-n:])
                err, rip = 100 * abs(ipk / amp1 - 1), ""
            mascara = (tf if pwm else t) >= T_CAMBIO
            pico = np.max(np.abs(corriente[mascara]))
            establecimiento_ms = ""
            if amp0 != amp1 or r0 != r1:
                i_lento = datos[:, 1]
                amp_final, fase_final, base_final = fundamental(t[-n:], i_lento[-n:])
                offset = np.mean(base_final)
                final = amp_final * np.sin(2*np.pi*F0*t + np.radians(fase_final)) + offset
                fuera = np.flatnonzero((t >= T_CAMBIO) &
                                       (np.abs(i_lento-final) > 0.10*amp_final))
                if len(fuera) == 0:
                    establecimiento_ms = 0.0
                elif fuera[-1]+1 < len(t):
                    establecimiento_ms = 1000 * (t[fuera[-1]+1] - T_CAMBIO)
            saturadas = np.count_nonzero(np.abs(datos[:, 5]-datos[:, 6]) > 1e-10)
            filas.append([nombre, modelo, ipk, err, fase, rip, pico,
                          np.max(np.abs(datos[:, 3])), saturadas, pico >= I_TRIP, establecimiento_ms])
            if pwm:
                guardar_csv(nombre+"_muestreo.csv", ["t_s", "i_ref_A", "i_A", "i_filtro_A", "m",
                            "v_prom_V", "v_libre_V", "v_limitada_V"], np.column_stack((t, datos)))
                if nombre in ("paso_02_05", "paso_05_10", "cambio_R_05"):
                    ax = axs[("paso_02_05", "paso_05_10", "cambio_R_05").index(nombre)]
                    ax.plot(t*1000, datos[:, 0], "--", label="Referencia", linewidth=1.2)
                    ax.plot(t*1000, datos[:, 1], label="Corriente en el valle", linewidth=1.2)
                    ax.axvline(T_CAMBIO*1000, color="0.4", linewidth=0.8)
                    ax.set_title({"paso_02_05": "0,2 a 0,5 A pico", "paso_05_10": "0,5 a 1,0 A pico",
                                  "cambio_R_05": "Cambio de resistencia externa a 0,5 A pico"}[nombre],
                                 loc="left", fontsize=10)
                    ax.set_ylabel("Corriente (A)")
                    ax.grid(True, alpha=0.25)
                if nombre == "nom_10":
                    mascara_rapida = (tf >= 0.325) & (tf < 0.32525)
                    guardar_csv("nom_10_ventana_pwm.csv", ["t_s", "i_A", "v_ab_V"],
                                np.column_stack((tf[mascara_rapida], alta[mascara_rapida])))
    guardar_csv("ensayos.csv", ["ensayo", "modelo", "I1_pico_A", "error_amplitud_pct",
                               "fase_deg", "rizado_max_A_pp", "I_max_desde_cambio_A", "m_max",
                               "muestras_saturadas", "cruce_umbral_en_ventana", "establecimiento_ms"], filas)
    axs[0].legend(loc="lower left", fontsize=8, ncols=2)
    axs[-1].set_xlim(135, 250)
    axs[-1].set_xlabel("Tiempo (ms)")
    fig.tight_layout()
    fig.savefig(SALIDA / "transitorios.png", dpi=170)
    plt.close(fig)
    print(f"{len(filas)} corridas. Resultados en {SALIDA}")


if __name__ == "__main__":
    ejecutar()
