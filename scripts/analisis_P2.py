"""
Análisis de la prueba P2 (lazo abierto, referencia senoidal de 50 Hz)
Persona 2 - EL4201 Proyecto 4

Entrada: CSV exportados del Scope_datos de PLECS con las columnas
  Time / s, m_ref, Am_carga, Vm_ab, Vm_bus
Uso:  python analisis_P2.py  (desde la carpeta scripts/)

Método (sección 5.3.5 del instructivo):
  - Ventana de evaluación: los últimos 5 períodos completos de 50 Hz
    (0,10 s a 0,20 s), ya en régimen periódico.
  - Fundamental: proyección DFT a 50 Hz sobre la ventana, previo
    remuestreo uniforme (el solver de PLECS es de paso variable).
  - Componente de baja frecuencia: armónicos hasta 2 kHz (todo lo que
    está muy por debajo de la componente de conmutación de 2*fsw).
  - Rizado de conmutación: corriente menos su componente de baja
    frecuencia; pico a pico en ventanas locales de 1 ms.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---- parámetros usados en la simulación (parametros_puente.m) ----
Vdc, fsw, f0 = 24.0, 20e3, 50.0
R_tot, L = 10.0, 20e-3
t_dt = 500e-9
w0 = 2 * np.pi * f0
Z = np.hypot(R_tot, w0 * L)
phi_teo = np.degrees(np.arctan2(w0 * L, R_tot))

CASOS = [("P2_0p2A.csv", 0.2), ("P2_0p5A.csv", 0.5), ("P2_1A.csv", 1.0)]
AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "datos")
FIGS = os.path.join(AQUI, "..", "figuras")
os.makedirs(FIGS, exist_ok=True)

T0 = 1 / f0
T_INI, T_FIN = 0.10, 0.20          # 5 períodos completos
DT = 0.5e-6                        # remuestreo uniforme (50 puntos por período de conmutación)
F_LF = 2e3                          # corte de la componente de baja frecuencia


def cargar(nombre):
    d = np.loadtxt(os.path.join(DATOS, nombre), delimiter=",", skiprows=1)
    t = d[:, 0]
    # el solver repite instantes en los eventos de conmutación: dejar el último valor
    _, idx = np.unique(t[::-1], return_index=True)
    idx = len(t) - 1 - idx
    d = d[np.sort(idx)]
    return d[:, 0], d[:, 1], d[:, 2], d[:, 3], d[:, 4]


def remuestrear(t, x, tu):
    return np.interp(tu, t, x)


def fundamental(tu, x):
    """Amplitud y fase (grados, referida a seno) de la componente de 50 Hz."""
    s = np.sin(w0 * tu)
    c = np.cos(w0 * tu)
    a = 2 * np.mean(x * s)
    b = 2 * np.mean(x * c)
    return np.hypot(a, b), np.degrees(np.arctan2(b, a))


def baja_frecuencia(x):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), DT)
    X[f > F_LF] = 0
    return np.fft.irfft(X, len(x))


res = []
for nombre, I_ref in CASOS:
    t, m, i, vab, vbus = cargar(nombre)
    tu = np.arange(T_INI, T_FIN, DT)
    mu, iu, vu, bu = (remuestrear(t, x, tu) for x in (m, i, vab, vbus))

    m_amp, m_fase = fundamental(tu, mu)
    I1, i_fase = fundamental(tu, iu)
    V1, v_fase = fundamental(tu, vu)
    desfase = m_fase - i_fase        # positivo = corriente atrasada

    i_lf = baja_frecuencia(iu)
    rip = iu - i_lf
    n_win = int(round(1e-3 / DT))
    pp = [rip[k:k + n_win].max() - rip[k:k + n_win].min()
          for k in range(0, len(rip) - n_win + 1, n_win)]
    k_max = int(np.argmax(pp))
    m_eff = m_amp  # índice pico
    rip_teo = Vdc * min(m_eff, 0.5) * (1 - min(m_eff, 0.5)) / (2 * L * fsw)

    # bus: ventana completa (incluye los intervalos regenerativos)
    dVbus = bu.max() - bu.min()

    res.append(dict(I_ref=I_ref, m_a=m_amp, I1=I1, err=100 * (I1 - I_ref) / I_ref,
                    I_teo=m_amp * Vdc / Z, desfase=desfase, V1=V1, V1_teo=m_amp * Vdc,
                    rip_max=max(pp), rip_teo=rip_teo, vbus_max=bu.max(), vbus_min=bu.min(),
                    dVbus=dVbus, I_rms=np.sqrt(np.mean(iu**2))))

    # ---------- figuras ----------
    etiqueta = f"{I_ref:.1f}".replace(".", "p")
    # (a) dos ciclos: corriente, fundamental y referencia ideal
    sel = (tu >= 0.16) & (tu < 0.20)
    fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)
    ax.plot(tu[sel] * 1e3, iu[sel], lw=0.6, color="#1f5f99", label="$i$ simulada")
    ax.plot(tu[sel] * 1e3, I_ref * np.sin(w0 * tu[sel] - np.radians(phi_teo)),
            lw=0.8, ls="--", color="#c0392b", label="$I_{ref}$ ideal desfasada")
    ax.set_xlabel("Tiempo [ms]", fontsize=7)
    ax.set_ylabel("Corriente [A]", fontsize=7)
    ax.tick_params(labelsize=6)
    ax.grid(alpha=0.3, lw=0.4)
    ax.legend(fontsize=6, loc="upper right", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGS, f"P2_corriente_{etiqueta}A.png"))
    plt.close(fig)

    if I_ref == 1.0:
        # (b) rizado en la ventana local de máximo rizado
        k0 = k_max * n_win
        s2 = slice(k0, k0 + int(0.3e-3 / DT))
        fig, ax = plt.subplots(2, 1, figsize=(3.5, 3.0), dpi=300, sharex=True)
        tt = (tu[s2] - tu[s2][0]) * 1e6
        ax[0].plot(tt, iu[s2], lw=0.7, color="#1f5f99", label="$i$")
        ax[0].plot(tt, i_lf[s2], lw=0.8, ls="--", color="#c0392b", label="baja frecuencia")
        ax[0].set_ylabel("Corriente [A]", fontsize=7)
        ax[0].legend(fontsize=6, loc="best")
        ax[1].plot(tt, rip[s2] * 1e3, lw=0.7, color="#16825d")
        ax[1].set_ylabel("Rizado [mA]", fontsize=7)
        ax[1].set_xlabel(r"Tiempo relativo [$\mu$s]", fontsize=7)
        for a_ in ax:
            a_.tick_params(labelsize=6)
            a_.grid(alpha=0.3, lw=0.4)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGS, "P2_rizado_1p0A.png"))
        plt.close(fig)

        # (c) tensión de bus y corriente en un ciclo
        sel = (tu >= 0.18) & (tu < 0.20)
        fig, ax = plt.subplots(2, 1, figsize=(3.5, 3.0), dpi=300, sharex=True)
        ax[0].plot(tu[sel] * 1e3, vu[sel], lw=0.3, color="#555555")
        ax[0].set_ylabel("$v_{ab}$ [V]", fontsize=7)
        ax[1].plot(tu[sel] * 1e3, bu[sel], lw=0.6, color="#b9770e")
        ax[1].set_ylabel("$V_{bus}$ [V]", fontsize=7)
        ax[1].set_xlabel("Tiempo [ms]", fontsize=7)
        for a_ in ax:
            a_.tick_params(labelsize=6)
            a_.grid(alpha=0.3, lw=0.4)
        fig.tight_layout()
        fig.savefig(os.path.join(FIGS, "P2_vab_bus_1p0A.png"))
        plt.close(fig)

# ---------- resumen ----------
print(f"|Z| = {Z:.3f} ohm, desfase teórico = {phi_teo:.2f} grados")
cab = ("I_ref", "m_a", "I1 [A]", "err [%]", "I_teo sin perd [A]", "desfase [deg]",
       "V1 [V]", "m_a*Vdc [V]", "rizado max [mA]", "rizado teo [mA]",
       "Vbus min", "Vbus max", "dVbus [mV]", "I_rms [A]")
print(" | ".join(cab))
for r in res:
    print(" | ".join([f"{r['I_ref']:.1f}", f"{r['m_a']:.4f}", f"{r['I1']:.4f}", f"{r['err']:+.2f}",
                      f"{r['I_teo']:.4f}", f"{r['desfase']:.2f}", f"{r['V1']:.3f}",
                      f"{r['V1_teo']:.3f}", f"{r['rip_max']*1e3:.2f}", f"{r['rip_teo']*1e3:.2f}",
                      f"{r['vbus_min']:.4f}", f"{r['vbus_max']:.4f}", f"{r['dVbus']*1e3:.1f}",
                      f"{r['I_rms']:.4f}"]))
