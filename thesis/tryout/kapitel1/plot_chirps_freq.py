import numpy as np
import matplotlib.pyplot as plt

# --- Parameter Definitions ---
f_min = 1.0          # Minimum frequency: 1 Hz
f_max = 50.0         # Maximum frequency: 50 Hz
duration_per_period = 1.0  # Duration of one full period: 1 second
sample_rate = 2000   # Sampling rate in Hz
total_periods = 3

# Samples for a single 1-second period
total_samples_per_period = int(sample_rate * duration_per_period)

# --- Step 1: Create the Up-Chirp Profile (Sawtooth) ---
single_up_period = np.linspace(f_min, f_max, total_samples_per_period)
three_periods_up = np.tile(single_up_period, total_periods)

# --- Step 2: Create the Down-Chirp Profile (Inverted Sawtooth) ---
single_down_period = np.linspace(f_max, f_min, total_samples_per_period)
three_periods_down = np.tile(single_down_period, total_periods)

# Create a shared time vector for the complete 3-second duration
total_samples = len(three_periods_up)
t = np.linspace(0, duration_per_period * total_periods, total_samples)

# --- Plot Generation ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.5), sharey=True)

# Left Subplot: Up-Chirp Frequency Profile
ax1.plot(t, three_periods_up, color='crimson', linewidth=2.5, label='Up-Chirp $f(t)$')
ax1.set_title('Up-Chirp', fontsize=12, fontweight='bold')
ax1.set_xlabel('Time (s)', fontsize=11)
ax1.set_ylabel('Frequency (Hz)', fontsize=11)
ax1.set_xlim(0, duration_per_period * total_periods)
ax1.set_ylim(0, f_max + 5)
ax1.grid(True, linestyle=':', alpha=0.6)

# Add period boundary lines for the left plot
for i in range(total_periods + 1):
    ax1.axvline(x=i * duration_per_period, color='gray', linestyle='--', alpha=0.5)
ax1.legend(loc='upper left')

# Right Subplot: Down-Chirp Frequency Profile
ax2.plot(t, three_periods_down, color='royalblue', linewidth=2.5, label='Down-Chirp $f(t)$')
ax2.set_title('Down-Chirp', fontsize=12, fontweight='bold')
ax2.set_xlabel('Time $t$ (s)', fontsize=11)
ax2.set_xlim(0, duration_per_period * total_periods)
ax2.grid(True, linestyle=':', alpha=0.6)

# Add period boundary lines for the right plot
for i in range(total_periods + 1):
    ax2.axvline(x=i * duration_per_period, color='gray', linestyle='--', alpha=0.5)
ax2.legend(loc='upper right')

# Optimize spacing and render the plots
plt.tight_layout()
plt.show()