"""Figura ideal de PWM unipolar: portadora, +m y -m, compuertas y v_ab."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

m = 0.5
N = 4000
t = np.linspace(0, 2, N)               # dos períodos de portadora (unidades de Ts)
f = t % 1
c = np.where(f < 0.5, -1 + 4 * f, 3 - 4 * f)
gA = (m > c).astype(float)
gB = (-m > c).astype(float)
vab = gA - gB

fig, ax = plt.subplots(4, 1, figsize=(3.5, 3.6), dpi=300, sharex=True,
                       gridspec_kw=dict(height_ratios=[2, 1, 1, 1.4]))
ax[0].plot(t, c, lw=0.8, color="#444444", label="portadora")
ax[0].axhline(m, lw=0.9, color="#16825d", label="$+m$")
ax[0].axhline(-m, lw=0.9, ls="--", color="#6c4fb3", label="$-m$")
ax[0].legend(fontsize=5.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.32), frameon=False)
ax[1].step(t, gA, lw=0.8, color="#16825d", where="post")
ax[2].step(t, gB, lw=0.8, color="#6c4fb3", where="post")
ax[3].step(t, vab, lw=0.9, color="#c0392b", where="post")
ax[0].set_ylabel("señales", fontsize=6.5)
ax[1].set_ylabel("$S_1$", fontsize=6.5)
ax[2].set_ylabel("$S_3$", fontsize=6.5)
ax[3].set_ylabel("$v_{ab}/V_{dc}$", fontsize=6.5)
ax[3].set_xlabel("Tiempo [$T_{s}$ = 1/$f_{sw}$]", fontsize=6.5)
ax[3].set_yticks([-1, 0, 1])
for a in ax:
    a.tick_params(labelsize=5.5)
    a.grid(alpha=0.3, lw=0.4)
fig.tight_layout(h_pad=0.3)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figuras", "pwm_unipolar_ideal.png")
fig.savefig(out)
print("ok", out)
