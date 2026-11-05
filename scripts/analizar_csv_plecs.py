"""Analiza un CSV de Scope_datos (tiempo, referencia, corriente, tensión, auxiliar)."""
import argparse
import json

import numpy as np

F0 = 50
FINAL_PICO = (0.2, 0.5, 1.0, 0.5, 1.0, 0.5)
T_CAMBIO = 0.165


def ajuste(t, señal):
    w = 2 * np.pi * F0
    base = np.column_stack((np.sin(w*t), np.cos(w*t), np.ones_like(t)))
    a, b, c = np.linalg.lstsq(base, señal, rcond=None)[0]
    return np.hypot(a, b), np.degrees(np.arctan2(b, a)), c


def cargar(path, delimitador):
    datos = np.loadtxt(path, delimiter=delimitador, skiprows=1, usecols=(0,1,2),
                       encoding="utf-8-sig", ndmin=2)
    if len(datos) < 2 or not np.all(np.isfinite(datos)):
        raise ValueError("El CSV debe tener al menos dos filas válidas.")
    if np.any(np.diff(datos[:,0]) < 0):
        raise ValueError("La primera columna debe ser el tiempo creciente en segundos.")
    # Los eventos pueden producir varias filas al mismo tiempo: conservar la última.
    ultimo = np.r_[np.diff(datos[:,0]) > 0, True]
    unicos = datos[ultimo]
    if len(unicos) < 2:
        raise ValueError("El CSV debe cubrir al menos dos instantes distintos.")
    return unicos.T


def medir(t, ref, i, caso, conmutado):
    if caso == 7:
        raise ValueError("Para el caso 7, revisar permiso y compuertas en los scopes.")
    periodos = 5
    dt = 0.5e-6
    ventana = periodos / F0
    # La ventana termina en un múltiplo de 50 Hz cubierto por la exportación.
    fin = np.floor((t[-1]+1e-11)*F0) / F0
    inicio = fin - ventana
    if inicio < t[0]-1e-11 or (caso in (4,5,6) and inicio < T_CAMBIO):
        raise ValueError("El CSV no cubre cinco ciclos completos después del cambio.")
    tu = inicio + np.arange(round(ventana/dt)) * dt
    iu, ru = np.interp(tu,t,i), np.interp(tu,t,ref)
    amp, fase, _ = ajuste(tu,iu)
    amp_ref, fase_ref, _ = ajuste(tu,ru)
    consigna = FINAL_PICO[caso-1]
    if abs(amp_ref-consigna) > 0.02*consigna:
        raise ValueError("La referencia del CSV no concuerda con el caso indicado.")
    salida = {
        "ventana_s": [inicio, fin], "consigna_pico_A": consigna,
        "I1_pico_A": float(amp), "referencia_fundamental_pico_A": float(amp_ref),
        "corriente_abs_pico_A": float(np.max(np.abs(iu))),
        "error_amplitud_pct": float(100*abs(amp/consigna-1)),
        "fase_i_menos_ref_deg": float((fase-fase_ref+180)%360-180),
        "I_rms_A": float(np.sqrt(np.mean(iu*iu))),
    }
    if conmutado:
        indices = t[(t>=inicio)&(t<=fin)]
        if len(indices)<2 or np.max(np.diff(indices)) > 2e-6:
            raise ValueError("Exportación demasiado espaciada para calcular rizado. Usá un paso máximo de 1 µs.")
        espectro = np.fft.rfft(iu)
        espectro[np.fft.rfftfreq(len(iu), dt) > 2000] = 0
        rizado = iu - np.fft.irfft(espectro, len(iu))
        n = round(1e-3/dt)
        pp = np.ptp(rizado.reshape(-1,n),axis=1)
        k = int(np.argmax(pp))
        salida["rizado_max_A_pp"] = float(pp[k])
        salida["inicio_ventana_rizado_s"] = float(tu[k*n])
    if caso in (4,5,6):
        salida["pico_despues_del_cambio_A"] = float(np.max(np.abs(i[t>=T_CAMBIO])))
    if caso in (1,2,3):
        salida["cumple_amplitud"] = salida["error_amplitud_pct"] <= 10
        if conmutado:
            salida["cumple_rizado"] = salida["rizado_max_A_pp"] <= 0.20
    return salida


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv")
    p.add_argument("--caso", type=int, required=True, choices=range(1,7))
    p.add_argument("--conmutado", action="store_true")
    p.add_argument("--delimitador", default=",")
    args = p.parse_args()
    try:
        salida = medir(*cargar(args.csv,args.delimitador),args.caso,args.conmutado)
    except (ValueError, OSError) as e:
        p.error(str(e))
    print(json.dumps(salida, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
