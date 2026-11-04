"""
Análisis de la prueba P2 lazo abierto, referencia senoidal de 50 Hz
Entrada: CSV exportados del Scope_datos de PLECS con las columnas
  Time / s, m_ref, Am_carga, Vm_ab, Vm_bus
Corridas:
  A) t_dt = 500 ns, Rds_on = 0,05 ohm, Vf = 1,0 V  -> P2_<I>A.csv
  B) t_dt = 300 ns, Rds_on = 0,20 ohm, Vf = 1,3 V  -> P2_<I>A_dt300.csv (IRF520N + IR2101)
Uso:  python analisis_P2.py  (desde la carpeta scripts/)

Método (sección 5.3.5 del instructivo):
  - Ventana: últimos 5 períodos completos de 50 Hz (0,10 s a 0,20 s).
  - Fundamental: proyección a 50 Hz tras remuestreo uniforme (0,5 us).
  - Componente de baja frecuencia: armónicos hasta 2 kHz.
  - Rizado: corriente menos componente de baja frecuencia, pico a pico
    en ventanas locales de 1 ms; se reporta el máximo.
  - Pérdida de fundamental de tensión dV1 = m_a*Vdc - V1, separada en
    caída resistiva de los dos MOSFET en conducción (2*Rds*I1) y error
    de tiempo muerto (resto), que se compara con (4/pi)*2*Vdc*t_dt*fsw.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

Vdc, fsw, f0 = 24.0, 20e3, 50.0
R_tot, L = 10.0, 20e-3
w0 = 2 * np.pi * f0
Z = np.hypot(R_tot, w0 * L)
phi_teo = np.degrees(np.arctan2(w0 * L, R_tot))

CORRIDAS = {
    "dt500": dict(t_dt=500e-9, rds=0.05, sufijo="", nombre="500 ns, Rds 0,05"),
    "dt300": dict(t_dt=300e-9, rds=0.20, sufijo="_dt300", nombre="300 ns, IRF520N"),
}
CORRIENTES = [(0.2, "0p2"), (0.5, "0p5"), (1.0, "1")]

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(AQUI, "..", "datos")
FIGS = os.path.join(AQUI, "..", "figuras")
os.makedirs(FIGS, exist_ok=True)

T_INI, T_FIN = 0.10, 0.20
DT = 0.5e-6
F_LF = 2e3


def cargar(nombre):
    d = np.loadtxt(os.path.join(DATOS, nombre), delimiter=",", skiprows=1)
    t = d[:, 0]
    _, idx = np.unique(t[::-1], return_index=True)   # instantes repetidos: último valor
    d = d[np.sort(len(t) - 1 - idx)]
    return d.T


def fundamental(tu, x):
    a = 2 * np.mean(x * np.sin(w0 * tu))
    b = 2 * np.mean(x * np.cos(w0 * tu))
    return np.hypot(a, b), np.degrees(np.arctan2(b, a))


def baja_frecuencia(x):
    X = np.fft.rfft(x)
    X[np.fft.rfftfreq(len(x), DT) > F_LF] = 0
    return np.fft.irfft(X, len(x))


def analizar(archivo, cfg):
    t, m, i, vab, vbus = cargar(archivo)
    tu = np.arange(T_INI, T_FIN, DT)
    mu, iu, vu, bu = (np.interp(tu, t, x) for x in (m, i, vab, vbus))
    m_amp, m_fase = fundamental(tu, mu)
    I1, i_fase = fundamental(tu, iu)
    V1, _ = fundamental(tu, vu)
    i_lf = baja_frecuencia(iu)
    rip = iu - i_lf
    n = int(round(1e-3 / DT))
    pp = [np.ptp(rip[k:k + n]) for k in range(0, len(rip) - n + 1, n)]
    mm = min(m_amp, 0.5)
    dV1 = m_amp * Vdc - V1
    dV_rds = 2 * cfg["rds"] * I1
    return dict(m_a=m_amp, I1=I1, desfase=m_fase - i_fase, V1=V1, dV1=dV1,
                dV_rds=dV_rds, dV_dt=dV1 - dV_rds,
                dV_dt_teo=4 / np.pi * 2 * Vdc * cfg["t_dt"] * fsw,
                rip=max(pp), rip_teo=Vdc * mm * (1 - mm) / (2 * L * fsw),
                vbus_max=bu.max(), vbus_min=bu.min(),
                tu=tu, iu=iu, i_lf=i_lf, rip_s=rip, vu=vu, bu=bu, kmax=int(np.argmax(pp)), n=n)


def estilo(ax):
    ax.tick_params(labelsize=6)
    ax.grid(alpha=0.3, lw=0.4)


res = {}
for clave, cfg in CORRIDAS.items():
    for I_nom, et in CORRIENTES:
        archivo = f"P2_{et}A{cfg['sufijo']}.csv"
        if os.path.exists(os.path.join(DATOS, archivo)):
            r = analizar(archivo, cfg)
            # la referencia real se deduce del índice aplicado (no del nombre del archivo)
            I_ref = round(r["m_a"] * Vdc / Z, 1)
            if abs(I_ref - I_nom) > 1e-9:
                print(f"AVISO: {archivo} contiene la corrida de {I_ref} A (m_a = {r['m_a']:.3f})")
            r["err"] = 100 * (r["I1"] - I_ref) / I_ref
            res[(clave, I_ref)] = r
res = dict(sorted(res.items()))

#  figuras de la corrida original (500 ns) 
if ("dt500", 1.0) in res:
    for I_ref, et in CORRIENTES:
        r = res[("dt500", I_ref)]
        sel = (r["tu"] >= 0.16)
        fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)
        ax.plot(r["tu"][sel] * 1e3, r["iu"][sel], lw=0.6, color="#1f5f99", label="$i$ simulada")
        ax.plot(r["tu"][sel] * 1e3, I_ref * np.sin(w0 * r["tu"][sel] - np.radians(phi_teo)),
                lw=0.8, ls="--", color="#c0392b", label="$I_{ref}$ ideal desfasada")
        ax.set_xlabel("Tiempo [ms]", fontsize=7); ax.set_ylabel("Corriente [A]", fontsize=7)
        ax.legend(fontsize=6, loc="upper right", framealpha=0.9); estilo(ax)
        fig.tight_layout(); fig.savefig(os.path.join(FIGS, f"P2_corriente_{et.replace('1','1p0') if et=='1' else et}A.png")); plt.close(fig)

    r = res[("dt500", 1.0)]
    k0 = r["kmax"] * r["n"]; s2 = slice(k0, k0 + int(0.3e-3 / DT))
    fig, ax = plt.subplots(2, 1, figsize=(3.5, 3.0), dpi=300, sharex=True)
    tt = (r["tu"][s2] - r["tu"][s2][0]) * 1e6
    ax[0].plot(tt, r["iu"][s2], lw=0.7, color="#1f5f99", label="$i$")
    ax[0].plot(tt, r["i_lf"][s2], lw=0.8, ls="--", color="#c0392b", label="baja frecuencia")
    ax[0].set_ylabel("Corriente [A]", fontsize=7); ax[0].legend(fontsize=6)
    ax[1].plot(tt, r["rip_s"][s2] * 1e3, lw=0.7, color="#16825d")
    ax[1].set_ylabel("Rizado [mA]", fontsize=7); ax[1].set_xlabel(r"Tiempo relativo [$\mu$s]", fontsize=7)
    for a in ax: estilo(a)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "P2_rizado_1p0A.png")); plt.close(fig)

    sel = (r["tu"] >= 0.18)
    fig, ax = plt.subplots(2, 1, figsize=(3.5, 3.0), dpi=300, sharex=True)
    ax[0].plot(r["tu"][sel] * 1e3, r["vu"][sel], lw=0.3, color="#555555"); ax[0].set_ylabel("$v_{ab}$ [V]", fontsize=7)
    ax[1].plot(r["tu"][sel] * 1e3, r["bu"][sel], lw=0.6, color="#b9770e"); ax[1].set_ylabel("$V_{bus}$ [V]", fontsize=7)
    ax[1].set_xlabel("Tiempo [ms]", fontsize=7)
    for a in ax: estilo(a)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "P2_vab_bus_1p0A.png")); plt.close(fig)

# figuras de comparación entre corridas
if ("dt300", 0.2) in res:
    r5, r3 = res[("dt500", 0.2)], res[("dt300", 0.2)]
    sel = (r5["tu"] >= 0.16)
    fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)
    ax.plot(r5["tu"][sel] * 1e3, r5["iu"][sel], lw=0.6, color="#999999", label="$t_{dt}$ = 500 ns")
    ax.plot(r3["tu"][sel] * 1e3, r3["iu"][sel], lw=0.7, color="#1f5f99", label="$t_{dt}$ = 300 ns (IRF520N)")
    ax.plot(r5["tu"][sel] * 1e3, 0.2 * np.sin(w0 * r5["tu"][sel] - np.radians(phi_teo)),
            lw=0.8, ls="--", color="#c0392b", label="referencia ideal desfasada")
    ax.set_xlabel("Tiempo [ms]", fontsize=7); ax.set_ylabel("Corriente [A]", fontsize=7)
    ax.legend(fontsize=5.5, loc="upper right", framealpha=0.9); estilo(ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "P2_comparacion_0p2A.png")); plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.5, 2.2), dpi=300)
    x = np.arange(3); w = 0.36
    e5 = [abs(res[("dt500", I)]["err"]) for I, _ in CORRIENTES]
    e3 = [abs(res[("dt300", I)]["err"]) for I, _ in CORRIENTES]
    ax.bar(x - w / 2, e5, w, color="#999999", label="500 ns, $R_{DS}$ 0,05 Ω")
    ax.bar(x + w / 2, e3, w, color="#1f5f99", label="300 ns, IRF520N")
    ax.axhline(10, color="#c0392b", lw=0.8, ls="--", label="límite 10 %")
    ax.set_xticks(x); ax.set_xticklabels(["0,2 A", "0,5 A", "1,0 A"], fontsize=6.5)
    ax.set_ylabel("|Error de amplitud| [%]", fontsize=7)
    ax.legend(fontsize=5.5, framealpha=0.9); estilo(ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, "P2_comparacion_error.png")); plt.close(fig)

# resumen 
print(f"|Z| = {Z:.3f} ohm, desfase teórico = {phi_teo:.2f} grados")
cab = ("corrida", "I_ref", "m_a", "I1", "err%", "desf", "V1", "dV1", "dV_rds", "dV_dt", "dV_dt_teo",
       "rip mA", "rip_teo", "Vbus_min", "Vbus_max")
print(" | ".join(cab))
for (c, I), r in res.items():
    print(" | ".join([c, f"{I:.1f}", f"{r['m_a']:.4f}", f"{r['I1']:.4f}", f"{r['err']:+.2f}", f"{r['desfase']:.2f}",
                      f"{r['V1']:.3f}", f"{r['dV1']:.3f}", f"{r['dV_rds']:.3f}", f"{r['dV_dt']:.3f}",
                      f"{r['dV_dt_teo']:.3f}", f"{r['rip']*1e3:.2f}", f"{r['rip_teo']*1e3:.2f}",
                      f"{r['vbus_min']:.4f}", f"{r['vbus_max']:.4f}"]))
