"""Referencia por eventos del puente H con bus fijo, Rds, diodos y tiempo muerto."""
import csv
import math

import numpy as np

from analizar_csv_plecs import medir
from validar_pr import (F0, F_FILTRO, I_TRIP, KR, L, M_LIM, R_DEV, R_EXT, R_EXT_ALT,
                        SALIDA, T_CAMBIO, T_FIN, TS, VDC, coeficientes)

T_MUERTO = 300e-9
RDS = 0.20
VF = 1.30
RD = 0.01
PASO = 0.5e-6
POLO_FILTRO = 2 * math.pi * F_FILTRO
CASOS = ((.2, .2), (.5, .5), (1., 1.), (.2, .5), (.5, 1.), (.5, .5))


def flancos(m):
    """Mando simétrico por valle. Estado de cada rama: alto 1, bajo -1, abierto 0."""
    eventos = [(0., 0, 1), (0., 1, 1)]
    for rama, d in enumerate((m, -m)):
        t_baja = TS * (1+d) / 4
        t_alta = TS - t_baja
        eventos.extend(((t_baja, rama, 0), (t_baja+T_MUERTO, rama, -1),
                        (t_alta, rama, 0), (t_alta+T_MUERTO, rama, 1)))
    eventos.sort()
    estado = [1, 1]
    anterior = 0.
    for tiempo, rama, nuevo in eventos:
        if tiempo > anterior:
            yield anterior, tiempo, *estado
        estado[rama] = nuevo
        anterior = tiempo
    yield anterior, TS, *estado


def equivalente(a, b, signo, r_carga):
    v_a = {-1: 0., 1: VDC, 0: -VF if signo > 0 else VDC+VF}[a]
    v_b = {-1: 0., 1: VDC, 0: VDC+VF if signo > 0 else -VF}[b]
    r = r_carga + (RDS if a else RD) + (RDS if b else RD)
    return v_a-v_b, r


def tramos(i, a, b, r, h):
    """Divide en el cruce de i=0 para actualizar la trayectoria de los diodos."""
    signo = 1 if i > 0 else -1 if i < 0 else 0
    if not signo:
        if equivalente(a,b,1,r)[0] > 0:
            signo = 1
        elif equivalente(a,b,-1,r)[0] < 0:
            signo = -1
        else:
            yield h, 0., r
            return
    v, r_eq = equivalente(a,b,signo,r)
    if i and signo*v < 0:
        t0 = L/r_eq * math.log1p(abs(i*r_eq/v))
        if 0 < t0 < h:
            yield t0, v, r_eq
            yield from tramos(0., a, b, r, h-t0)
            return
    yield h, v, r_eq


def avanzar(i, y, v, r, h):
    a = r / L
    w = POLO_FILTRO
    e_i, e_y = math.exp(-a*h), math.exp(-w*h)
    i_eq = v/r
    d = i-i_eq
    mezcla = w*h*e_y if abs(w-a)<1e-10 else w*(e_i-e_y)/(w-a)
    return i_eq + d*e_i, i_eq + (y-i_eq)*e_y + d*mezcla


def simular(caso, abierto=False):
    amp0, amp1 = CASOS[caso-1]
    kp, b, a = coeficientes()
    n = round(T_FIN/TS)
    sub = round(TS/PASO)
    t = np.arange(n*sub+1)*PASO
    corriente = np.full_like(t,np.nan)
    referencia = np.empty_like(t)
    local = np.arange(sub)*PASO
    i = y = x1 = x2 = m = 0.
    pico_m = 0.
    for k in range(n):
        tk = k*TS
        amp = amp0 if tk < T_CAMBIO else amp1
        r = R_DEV + (R_EXT_ALT if caso == 6 and tk >= T_CAMBIO else R_EXT)
        e = amp*math.sin(2*math.pi*F0*tk)-y
        u = (kp+b[0])*e+x1
        u_sat = min(VDC*M_LIM,max(-VDC*M_LIM,u))
        ec = e+(u_sat-u)/(kp+KR)
        yr = b[0]*ec+x1
        x1, x2 = -a[1]*yr+x2, b[2]*ec-a[2]*yr
        if abierto:
            m = amp * math.hypot(r,2*math.pi*F0*L)/VDC * math.sin(2*math.pi*F0*tk)
        pico_m = max(pico_m,abs(m))
        desde = 0
        for t0, t1, sa, sb in flancos(m):
            inicio = t0
            for h,v,r_eq in tramos(i,sa,sb,r,t1-t0):
                fin = inicio+h
                hasta = np.searchsorted(local,fin)
                eq = v/r_eq
                corriente[k*sub+desde:k*sub+hasta] = eq+(i-eq)*np.exp(
                    -r_eq*(local[desde:hasta]-inicio)/L)
                i, y = avanzar(i,y,v,r_eq,h)
                if abs(i)<1e-13:
                    i = 0.
                desde = hasta
                inicio = fin
        assert desde == sub
        referencia[k*sub:(k+1)*sub] = amp*np.sin(2*np.pi*F0*t[k*sub:(k+1)*sub])
        m = u_sat/VDC
    referencia[-1] = amp1*math.sin(2*math.pi*F0*t[-1])
    corriente[-1] = i
    return t, referencia, corriente, pico_m


def main():
    SALIDA.mkdir(exist_ok=True)
    filas = []
    for abierto, casos in ((True, range(1,4)),(False, range(1,7))):
        for caso in casos:
            t, ref, i, m = simular(caso, abierto)
            assert np.all(np.isfinite(i))
            datos = medir(t,ref,i,caso,True)
            filas.append((caso,"abierto" if abierto else "PR",datos["I1_pico_A"],
                          datos["error_amplitud_pct"],datos["fase_i_menos_ref_deg"],
                          datos["rizado_max_A_pp"],m,np.max(np.abs(i))))
    with (SALIDA/"puente_no_ideal_referencia.csv").open("w",newline="",encoding="utf-8") as f:
        out = csv.writer(f)
        out.writerow(("caso","lazo","I1_pico_A","error_amplitud_pct","fase_deg",
                      "rizado_max_A_pp","m_pico","i_abs_max_A"))
        out.writerows(filas)
    assert max(row[-1] for row in filas if row[1]=="PR") < I_TRIP
    print(f"{len(filas)} ensayos de referencia del puente en {SALIDA}")


if __name__ == "__main__":
    main()
