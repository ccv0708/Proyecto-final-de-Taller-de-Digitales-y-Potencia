#include <math.h>

#define parametro(indice) ParamRealData(0, (indice))

static double referencia(double t, double f, double amp_ini, double amp_fin, double cambio)
{
    const double amplitud = t < cambio ? amp_ini : amp_fin;
    return amplitud * sin(6.283185307179586 * f * t);
}
