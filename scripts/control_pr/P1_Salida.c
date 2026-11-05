const int permiso = DiscState(4) == 0.0;
OutputSignal(0, 0) = permiso ? DiscState(2) : 0.0;
OutputSignal(1, 0) = permiso ? 1.0 : 0.0;
OutputSignal(2, 0) = referencia(CurrentTime, parametro(0), parametro(1), parametro(2), parametro(3));
OutputSignal(3, 0) = CurrentTime < parametro(4) ? 1.0 : 0.0;
