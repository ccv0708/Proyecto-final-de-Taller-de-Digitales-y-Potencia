const double medida = InputSignal(0, 0);
const double inyeccion = (CurrentTime >= parametro(14) &&
                         CurrentTime < parametro(14) + parametro(16)) ? parametro(15) : 0.0;
const double medida_proteccion = medida + inyeccion;
const double kp = parametro(5);
const double kr = parametro(6);
const double b0 = parametro(7);
const double b2 = parametro(8);
const double a1 = parametro(9);
const double a2 = parametro(10);
const double vdc = parametro(11);
const double limite = parametro(12) * vdc;
const double umbral = parametro(13);

if (!isfinite(medida_proteccion)) {
    DiscState(4) = 1.0;
} else if (fabs(medida_proteccion) > umbral) {
    DiscState(3) += 1.0;
    if (DiscState(3) >= 3.0) {
        DiscState(4) = 1.0;
    }
} else {
    DiscState(3) = 0.0;
}
if (DiscState(4) != 0.0 || !isfinite(InputSignal(1, 0))) {
    DiscState(0) = DiscState(1) = DiscState(2) = 0.0;
    DiscState(4) = 1.0;
    return;
}

const double e = referencia(CurrentTime, parametro(0), parametro(1), parametro(2), parametro(3)) - InputSignal(1, 0);
const double u = (kp + b0) * e + DiscState(0);
const double u_sat = fmin(limite, fmax(-limite, u));
const double e_estado = e + (u_sat - u) / (kp + kr);
const double yr_estado = b0 * e_estado + DiscState(0);
DiscState(0) = -a1 * yr_estado + DiscState(1);
DiscState(1) = b2 * e_estado - a2 * yr_estado;
DiscState(2) = u_sat / vdc;
