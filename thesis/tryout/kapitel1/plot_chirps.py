import numpy as np
import matplotlib.pyplot as plt

# --- Parameter Definitions ---
duration = 1.0       # Duration of the chirp in seconds (Ts)
sample_rate = 2000   # Sampling rate in Hz (high enough for smooth curves)
t = np.linspace(0, duration, int(sample_rate * duration))

# Frequency limits for the plot (exactly 3 full periods within the integral)
f_start_up = 1
f_end_up = 50

f_start_down = 50
f_end_down = 1

# --- Mathematical Phase Calculation ---
# The phase of a linear chirp is the integral of the instantaneous frequency:
# phi(t) = 2 * pi * (f_start * t + 0.5 * (f_end - f_start) / duration * t^2)

# 1. Up-Chirp (frequency linearly increasing)
phase_up = 2 * np.pi * (f_start_up * t + 0.5 * (f_end_up - f_start_up) / duration * t**2)
signal_up = np.sin(phase_up)

# 2. Down-Chirp (frequency linearly decreasing)
phase_down = 2 * np.pi * (f_start_down * t + 0.5 * (f_end_down - f_start_down) / duration * t**2)
signal_down = np.sin(phase_down)

# --- Plot Generation ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)

# Left Subplot: Up-Chirp
ax1.plot(t, signal_up, color='red', linewidth=2)
ax1.set_title(f'Up-Chirp ({f_start_up} Hz $\\to$ {f_end_up} Hz)', fontsize=12, fontweight='bold')
ax1.set_xlabel('Time $t$ (s)', fontsize=11)
ax1.set_ylabel('Amplitude', fontsize=11)
ax1.grid(True, linestyle='--', alpha=0.6)
ax1.set_xlim(0, duration)

# Right Subplot: Down-Chirp
ax2.plot(t, signal_down, color='blue', linewidth=2)
ax2.set_title(f'Down-Chirp ({f_start_down} Hz $\\to$ {f_end_down} Hz)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Time $t$ (s)', fontsize=11)
ax2.grid(True, linestyle='--', alpha=0.6)
ax2.set_xlim(0, duration)

# Optimize layout and display the window
plt.tight_layout()
plt.show()