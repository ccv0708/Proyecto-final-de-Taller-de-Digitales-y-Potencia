% ANÁLISIS MULTI-CASO PROYECTO 4 POT
clear; clc; close all;

% Definir los archivos y sus respectivas referencias de amplitud (en Amperios)
% Ajusta los nombres de los archivos o referencias si difieren en tu carpeta
archivos = {'Caso1_POT.csv', 'Caso2_POT.csv', 'Caso3_POT.csv', 'Caso4_POT.csv'};
referencias = [0.2, 0.5, 1.0, 0.5]; % Ejemplo: Caso 1 (0.2A), Caso 2 (0.5A), Caso 3 (1.0A), Caso 4 (0.5A)

for i = 1:length(archivos)
    nombre_archivo = archivos{i};
    amp_referencia = referencias(i);
    
    fprintf('=========================================================\n');
    fprintf('--- ANÁLISIS DETALLADO PARA: %s ---\n', nombre_archivo);
    fprintf('=========================================================\n');
    
    % 1. Cargar el archivo CSV
    datos = readtable(nombre_archivo);
    
    % Renombrar columnas para facilitar el manejo
    datos.Properties.VariableNames = {'tiempo', 'transfer_fcn'};
    t = datos.tiempo;
    % Aplicar el factor de escala del sensor para calibrar la señal a Amperios
    K_sensor = 5.405; 
    v_out = datos.transfer_fcn * K_sensor;
    
    % Obtener la frecuencia de muestreo de forma automática
    dt = t(2) - t(1);
    fs = 1 / dt;
    fprintf('Frecuencia de muestreo estimada: %.2f Hz\n\n', fs);
    
    % =====================================================================
    % 2. SELECCIÓN DE RÉGIMEN ESTACIONARIO Y VENTANA DE 5 CICLOS (50 Hz)
    % =====================================================================
    f_red = 50;                     % Frecuencia fundamental (Hz)
    T_ciclo = 1 / f_red;            % Duración de 1 ciclo (0.02 s)
    N_ciclos = 5;                   % Número de ciclos requeridos
    t_ventana = N_ciclos * T_ciclo; % 0.1 segundos
    
    % Tomamos una ventana en régimen estacionario (a partir de t = 0.5 s)
    t_inicio = 0.5;
    idx_est = (t >= t_inicio) & (t <= (t_inicio + t_ventana));
    t_est = t(idx_est);
    v_est = v_out(idx_est);
    
    % =====================================================================
    % 3. CÁLCULO DE VALORES RMS Y PICO ABSOLUTO
    % =====================================================================
    v_rms = rms(v_est);
    v_pico_abs = max(abs(v_est));
    
    fprintf('--- 1. Valores Eficaces y Pico ---\n');
    fprintf('Valor RMS: %.4f V\n', v_rms);
    fprintf('Pico absoluto: %.4f V\n\n', v_pico_abs);
    
    % =====================================================================
    % 4. SEPARACIÓN DEL RIZADO DE CONMUTACIÓN (Alta Frecuencia)
    % =====================================================================
    ventana_filtro = round(fs / (10 * f_red)); 
    v_fundamental_aprox = movmean(v_est, ventana_filtro);
    rizado = v_est - v_fundamental_aprox;
    rizado_pp = max(rizado) - min(rizado);
    
    fprintf('--- 2. Rizado de Conmutación ---\n');
    fprintf('Rizado Pico a Pico (Delta i_pp): %.4f A (o V equivalentes)\n', rizado_pp);
    if rizado_pp <= 0.20
        fprintf('[OK] El rizado cumple con el límite exigido (<= 0.20 A).\n\n');
    else
        fprintf('[ALERTA] El rizado supera el límite de 0.20 A.\n\n');
    end
    
    % =====================================================================
    % 5. EXTRACCIÓN DE LA COMPONENTE FUNDAMENTAL (Amplitud, Error y Desfase)
    % =====================================================================
    omega = 2 * pi * f_red;
    X = [sin(omega * t_est), cos(omega * t_est), ones(size(t_est))];
    coeffs = X \ v_est;
    A_sin = coeffs(1);
    B_cos = coeffs(2);
    offset_fund = coeffs(3);
    
    amp_fundamental = sqrt(A_sin^2 + B_cos^2);
    fase_rad = atan2(B_cos, A_sin); 
    fase_deg = rad2deg(fase_rad);
    
    error_relativo = abs(amp_fundamental - amp_referencia) / amp_referencia * 100;
    
    fprintf('--- 3. Componente Fundamental (50 Hz) ---\n');
    fprintf('Amplitud medida: %.4f\n', amp_fundamental);
    fprintf('Amplitud de referencia: %.4f\n', amp_referencia);
    fprintf('Error relativo de amplitud: %.2f%%\n', error_relativo);
    if error_relativo <= 10
        fprintf('[OK] El error de amplitud es menor al 10%%.\n');
    else
        fprintf('[ALERTA] El error de amplitud supera el 10%%.\n');
    end
    fprintf('Ángulo de desfase: %.2f grados (%.4f rad)\n\n', fase_deg, fase_rad);
    
    % =====================================================================
    % 6. CALIBRACIÓN FÍSICA DEL XADC (Mapeo de 12 bits)
    % =====================================================================
    v_min = min(v_est);
    v_max = max(v_est);
    code_min = round((v_min / 1.0) * 4096);
    code_max = round((v_max / 1.0) * 4096);
    code_offset = round((offset_fund / 1.0) * 4096);
    
    fprintf('--- 4. Calibración y XADC (12 bits) ---\n');
    fprintf('Offset de reposo medido: %.4f V (Código ADC: %d)\n', offset_fund, code_offset);
    fprintf('Rango de códigos XADC: [%d, %d]\n\n', code_min, code_max);
    
    % =====================================================================
    % 7. GRÁFICAS DE VALIDACIÓN (Se generará una figura independiente por caso)
    % =====================================================================
    figure('Name', ['Analisis - ', nombre_archivo], 'Position', [100 + i*30, 100 + i*30, 900, 500]);
    
    subplot(2,1,1);
    plot(t_est, v_est, 'b', 'LineWidth', 1.2); hold on;
    plot(t_est, v_fundamental_aprox, 'r--', 'LineWidth', 1.5);
    grid on;
    xlabel('Tiempo (s)');
    ylabel('Tensión / Corriente');
    title(sprintf('Régimen Estacionario y Fundamental (%s)', nombre_archivo));
    legend('Señal Original', 'Fundamental (50 Hz)', 'Location', 'best');
    
    subplot(2,1,2);
    plot(t_est, rizado, 'k', 'LineWidth', 1);
    grid on;
    xlabel('Tiempo (s)');
    ylabel('Rizado (Alta Freq)');
    title(sprintf('Rizado Pico a Pico: %.4f A', rizado_pp));
end