% Pegar en Initialization al final de parametros_puente_P2.m si se edita a mano.
% Estos ajustes ya están incorporados en los modelos P1.
caso = 2; % 1,2,3 nominales; 4,5 cambios de consigna; 6 cambio R; 7 falla inyectada
t_fin = 0.4;
T_control = 1/fsw;
f_filtro = 3000;
w_filtro = 2*pi*f_filtro;
Kp = sqrt(R_tot^2 + (2*pi*600*L_carga)^2);
Kr = 150;
wc = 2*pi*5;
w0 = 2*pi*f0;
k_tustin = w0/tan(w0*T_control/2);
d0 = k_tustin^2+2*wc*k_tustin+w0^2;
b0_pr = 2*Kr*wc*k_tustin/d0;
a1_pr = 2*(w0^2-k_tustin^2)/d0;
a2_pr = (k_tustin^2-2*wc*k_tustin+w0^2)/d0;
m_lim = 0.90;
I_trip = 1.5;
R_ext_alt = 1.25*R_ext;
delta_R = R_ext_alt-R_ext;
amp_ini_lista = [0.2 0.5 1.0 0.2 0.5 0.5 0.5];
amp_fin_lista = [0.2 0.5 1.0 0.5 1.0 0.5 0.5];
t_amp_lista = [1 1 1 0.165 0.165 1 1];
t_R_lista = [1 1 1 1 1 0.165 1];
t_falla_lista = [1 1 1 1 1 1 0.200];
% Inyección temporal, exclusiva del camino del supervisor de la simulación.
inyeccion_A = 2.0;
duracion_inyeccion = 5*T_control;
PR_config = [f0, amp_ini_lista(caso), amp_fin_lista(caso), t_amp_lista(caso), ...
             t_R_lista(caso), Kp, Kr, b0_pr, -b0_pr, a1_pr, a2_pr, Vdc, ...
             m_lim, I_trip, t_falla_lista(caso), inyeccion_A, duracion_inyeccion];
