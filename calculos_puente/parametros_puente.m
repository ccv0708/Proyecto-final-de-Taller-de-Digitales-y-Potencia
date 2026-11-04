% =====================================================================
% Parámetros del puente H 
% Valores PROVISIONALES: actualizar cuando se cierren Vdc, f_sw, R y L.
% Mantener ESTOS MISMOS NOMBRES 
% =====================================================================

% --- Bus DC ---
Vdc      = 24;          % [V]   tensión del bus
C_bus    = 470e-6;      % [F]   capacitor electrolítico de bus
R_fuente = 0.1;         % [ohm] resistencia interna de la fuente

% --- Conmutación ---
fsw      = 20e3;        % [Hz]  frecuencia por transistor
t_dt     = 500e-9;      % [s]   tiempo muerto (provisional, se recalcula en punto 4)

% --- MOSFET (provisional, se actualiza con la hoja de datos elegida) ---
Rds_on   = 0.05;        % [ohm] resistencia de conducción
Vf_d     = 1.0;         % [V]   caída del diodo interno
Rd_on    = 0.01;        % [ohm] resistencia del diodo

% --- Carga RL (la define la Persona 3) ---
R_ext    = 8;           % [ohm] resistencia externa
R_dev    = 2;           % [ohm] resistencia del devanado
R_tot    = R_ext + R_dev;
L_carga  = 20e-3;       % [H]

% --- Referencia y modulación en lazo abierto ---
f0       = 50;          % [Hz]
I_ref    = 1.0;         % [A pico]  probar 0.2, 0.5 y 1.0
Z_carga  = sqrt(R_tot^2 + (2*pi*f0*L_carga)^2);
m_a      = I_ref * Z_carga / Vdc;   % índice de modulación necesario

% --- Simulación ---
t_fin    = 0.2;         % [s]  10 ciclos de 50 Hz
dt_max   = 1/(fsw*200); % [s]  paso máximo para formas de onda limpias
