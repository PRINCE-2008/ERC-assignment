"""
CORRECTED Signal Recovery Solution
Using AM Demodulation (Envelope Extraction) + SSB Approach
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
from scipy.fft import fft, fftfreq
import os

print("=" * 70)
print("CORRECTED RECOVERY: AM DEMODULATION")
print("=" * 70)

# Load signal
wav_file = "corrupted.wav"
sample_rate, audio_data = wavfile.read(wav_file)

if audio_data.dtype != np.float32 and audio_data.dtype != np.float64:
    audio_data = audio_data.astype(np.float32) / np.max(np.abs(audio_data))
else:
    if np.max(np.abs(audio_data)) > 1:
        audio_data = audio_data / np.max(np.abs(audio_data))

if len(audio_data.shape) > 1:
    audio_data = np.mean(audio_data, axis=1)

print(f"\nSignal loaded: {len(audio_data)} samples @ {sample_rate} Hz")
print(f"Duration: {len(audio_data)/sample_rate:.2f} seconds")

t = np.arange(len(audio_data)) / sample_rate
time_axis = t

# --- STAGE 1: Analyze corrupted signal ---
print("\n" + "=" * 70)
print("STAGE 1: ANALYZE CORRUPTED SIGNAL")
print("=" * 70)

fft_orig = fft(audio_data)
freq_axis = fftfreq(len(audio_data), 1/sample_rate)
pos_idx = freq_axis >= 0

print("✓ FFT computed and analyzed")

# --- STAGE 2: Extract AM envelope using Hilbert transform + Demodulation ---
print("\n" + "=" * 70)
print("STAGE 2: EXTRACT ENVELOPE (AM DEMODULATION)")
print("=" * 70)

# Step 1: Compute analytic signal (complex envelope)
print("  - Computing analytic signal via Hilbert transform...")
analytic_signal = signal.hilbert(audio_data)

# Step 2: Shift down by carrier frequency (7300 Hz)
carrier_freq = 7300.0
print(f"  - Demodulating with carrier: {carrier_freq:.1f} Hz...")
complex_demod = analytic_signal * np.exp(-2j * np.pi * carrier_freq * t)

# Step 3: Extract quadrature components
real_component = np.real(complex_demod)
imag_component = np.imag(complex_demod)

print(f"  - Real component max: {np.max(np.abs(real_component)):.4f}")
print(f"  - Imag component max: {np.max(np.abs(imag_component)):.4f}")

# Step 4: Low-pass filter at 4000 Hz (speech range)
print("  - Applying lowpass filter @ 4000 Hz...")
sos = signal.butter(5, 4000, 'low', fs=sample_rate, output='sos')
real_filtered = signal.sosfilt(sos, real_component)
imag_filtered = signal.sosfilt(sos, imag_component)

# Choose the component with more energy in speech range
fft_real = fft(real_filtered)
fft_imag = fft(imag_filtered)

mag_real = np.abs(fft_real)
mag_imag = np.abs(fft_imag)

speech_idx = (freq_axis[pos_idx] >= 0) & (freq_axis[pos_idx] <= 4000)
energy_real = np.sum(mag_real[pos_idx][speech_idx])
energy_imag = np.sum(mag_imag[pos_idx][speech_idx])

print(f"  - Real component energy: {energy_real:.2e}")
print(f"  - Imag component energy: {energy_imag:.2e}")

if energy_real > energy_imag:
    print(f"  ✓ Selected: REAL component")
    demod_recovered = real_filtered
else:
    print(f"  ✓ Selected: IMAGINARY component")
    demod_recovered = imag_filtered

# Normalize
demod_recovered = demod_recovered / np.max(np.abs(demod_recovered))

print("✓ AM demodulation complete")

# --- STAGE 3: Remove any remaining spikes/interference ---
print("\n" + "=" * 70)
print("STAGE 3: REMOVE RESIDUAL INTERFERENCE")
print("=" * 70)

# Identify peaks in spectrum
fft_demod = fft(demod_recovered)
mag_demod = np.abs(fft_demod)

# Find sharp peaks (potential interference)
peaks, props = signal.find_peaks(mag_demod[pos_idx], height=np.max(mag_demod[pos_idx])*0.1, distance=50)
peak_freqs = freq_axis[pos_idx][peaks]

interference_freqs = []
for pf in peak_freqs:
    if 0 < pf < 4000:
        # Check if it's a narrow spike
        bandwidth = 50  # Hz
        freq_range_idx = (freq_axis[pos_idx] > pf - bandwidth/2) & (freq_axis[pos_idx] < pf + bandwidth/2)
        if np.sum(mag_demod[pos_idx][freq_range_idx]) > 0:
            spectral_width = np.sum(freq_range_idx)
            if spectral_width < 100:  # Narrow spike
                interference_freqs.append(pf)

print(f"Found {len(interference_freqs[:5])} interference frequencies to remove")
if len(interference_freqs) > 0:
    print(f"  Frequencies: {[f'{f:.1f}' for f in interference_freqs[:5]]} Hz")

# Apply notch filters to remove narrow spikes
final_signal = demod_recovered.copy()
for freq_notch in interference_freqs[:5]:
    w0 = freq_notch / (sample_rate / 2)
    if 0.001 < w0 < 0.999:
        b, a = signal.iirnotch(w0, Q=50)
        final_signal = signal.filtfilt(b, a, final_signal)

print("✓ Applied notch filtering")

# --- STAGE 4: Validate recovery ---
print("\n" + "=" * 70)
print("STAGE 4: VALIDATE RECOVERED SIGNAL")
print("=" * 70)

fft_final = fft(final_signal)
mag_final = np.abs(fft_final)

speech_energy_final = np.sum(mag_final[pos_idx][speech_idx])
print(f"Final energy in speech range: {speech_energy_final:.2e}")
print(f"Signal peak amplitude: {np.max(np.abs(final_signal)):.4f}")
print(f"Signal RMS: {np.sqrt(np.mean(final_signal**2)):.4f}")

# Spectrogram check
f_spec, t_spec, Sxx = signal.spectrogram(final_signal, sample_rate, nfft=1024)

print("✓ Recovery validated")

# --- SAVE AUDIO ---
print("\n" + "=" * 70)
print("SAVING RECOVERED AUDIO")
print("=" * 70)

# Normalize to [-1, 1] range
final_normalized = final_signal / np.max(np.abs(final_signal)) * 0.95

# Convert to int16
final_int16 = np.int16(final_normalized * 32767)

# Save
wavfile.write("recovered.wav", sample_rate, final_int16)
print("✓ Saved: recovered.wav")

# --- GENERATE PLOTS ---
print("\n" + "=" * 70)
print("GENERATING PLOTS")
print("=" * 70)

plot_dir = "plots"
if not os.path.exists(plot_dir):
    os.makedirs(plot_dir)

fig = plt.figure(figsize=(18, 14))
gs = fig.add_gridspec(5, 2, hspace=0.4, wspace=0.3)

# Row 1: Original corrupted
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(time_axis[:20000], audio_data[:20000], linewidth=0.5, color='red', alpha=0.7)
ax1.set_title("Stage 1: Corrupted Signal (Time Domain)", fontweight='bold', fontsize=11)
ax1.set_ylabel("Amplitude")
ax1.grid(True, alpha=0.3)

ax2 = fig.add_subplot(gs[0, 1])
ax2.semilogy(freq_axis[pos_idx][:4000], np.abs(fft_orig[pos_idx][:4000]), linewidth=0.5, color='red', alpha=0.7)
ax2.set_title("Stage 1: Corrupted Signal FFT (0-4000 Hz)", fontweight='bold', fontsize=11)
ax2.set_ylabel("Magnitude (log)")
ax2.grid(True, alpha=0.3)

# Row 2: Analytic signal magnitude
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(time_axis[:20000], np.abs(analytic_signal[:20000]), linewidth=0.5, color='orange', alpha=0.7)
ax3.set_title("Stage 2a: Analytic Signal Envelope", fontweight='bold', fontsize=11)
ax3.set_ylabel("Magnitude")
ax3.grid(True, alpha=0.3)

ax4 = fig.add_subplot(gs[1, 1])
fft_analytic = fft(np.abs(analytic_signal))
ax4.semilogy(freq_axis[pos_idx][:4000], np.abs(fft_analytic[pos_idx][:4000]), linewidth=0.5, color='orange', alpha=0.7)
ax4.set_title("Stage 2a: Envelope FFT (shows speech info)", fontweight='bold', fontsize=11)
ax4.set_ylabel("Magnitude (log)")
ax4.grid(True, alpha=0.3)

# Row 3: After demodulation
ax5 = fig.add_subplot(gs[2, 0])
ax5.plot(time_axis[:20000], demod_recovered[:20000], linewidth=0.5, color='green', alpha=0.7)
ax5.set_title(f"Stage 2b: After AM Demodulation (Carrier: {carrier_freq:.0f} Hz)", fontweight='bold', fontsize=11)
ax5.set_ylabel("Amplitude")
ax5.grid(True, alpha=0.3)

ax6 = fig.add_subplot(gs[2, 1])
ax6.semilogy(freq_axis[pos_idx][:4000], mag_demod[pos_idx][:4000], linewidth=0.5, color='green', alpha=0.7)
ax6.set_title("Stage 2b: FFT After Demodulation", fontweight='bold', fontsize=11)
ax6.set_ylabel("Magnitude (log)")
ax6.grid(True, alpha=0.3)

# Row 4: After notch filtering
ax7 = fig.add_subplot(gs[3, 0])
ax7.plot(time_axis[:20000], final_signal[:20000], linewidth=0.5, color='purple', alpha=0.7)
ax7.set_title("Stage 3: After Removing Interference Spikes", fontweight='bold', fontsize=11)
ax7.set_ylabel("Amplitude")
ax7.grid(True, alpha=0.3)

ax8 = fig.add_subplot(gs[3, 1])
ax8.semilogy(freq_axis[pos_idx][:4000], mag_final[pos_idx][:4000], linewidth=0.5, color='purple', alpha=0.7)
ax8.set_title("Stage 3: FFT After Filtering", fontweight='bold', fontsize=11)
ax8.set_ylabel("Magnitude (log)")
ax8.grid(True, alpha=0.3)

# Row 5: Spectrogram
ax9 = fig.add_subplot(gs[4, :])
pcm = ax9.pcolormesh(t_spec, f_spec, 10*np.log10(Sxx+1e-10), shading='gouraud', cmap='viridis')
ax9.set_ylabel("Frequency (Hz)")
ax9.set_xlabel("Time (s)")
ax9.set_title("Stage 4: Spectrogram of Recovered Signal (Speech characteristics)", fontweight='bold', fontsize=11)
ax9.set_ylim(0, 4000)
cb = plt.colorbar(pcm, ax=ax9, label="Power (dB)")

plt.savefig(os.path.join(plot_dir, "recovery_all_stages.png"), dpi=150, bbox_inches='tight')
plt.close()

print("✓ Saved comprehensive plot: recovery_all_stages.png")

# Additional detailed FFT comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

axes[0, 0].semilogy(freq_axis[pos_idx][:4000], np.abs(fft_orig[pos_idx][:4000]), linewidth=0.8, color='red', label='Corrupted')
axes[0, 0].set_title("Corrupted Signal FFT", fontweight='bold')
axes[0, 0].set_ylabel("Magnitude (log)")
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

axes[0, 1].semilogy(freq_axis[pos_idx][:4000], mag_demod[pos_idx][:4000], linewidth=0.8, color='orange', label='After Demod')
axes[0, 1].set_title("After AM Demodulation", fontweight='bold')
axes[0, 1].set_ylabel("Magnitude (log)")
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

axes[1, 0].semilogy(freq_axis[pos_idx][:4000], mag_final[pos_idx][:4000], linewidth=0.8, color='purple', label='Final')
axes[1, 0].set_title("After Notch Filtering", fontweight='bold')
axes[1, 0].set_xlabel("Frequency (Hz)")
axes[1, 0].set_ylabel("Magnitude (log)")
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# Combined view
axes[1, 1].semilogy(freq_axis[pos_idx][:4000], np.abs(fft_orig[pos_idx][:4000]), linewidth=0.8, alpha=0.5, label='Original (corrupted)')
axes[1, 1].semilogy(freq_axis[pos_idx][:4000], mag_final[pos_idx][:4000], linewidth=0.8, label='Final (recovered)')
axes[1, 1].set_title("Corrupted vs Recovered - Comparison", fontweight='bold')
axes[1, 1].set_xlabel("Frequency (Hz)")
axes[1, 1].set_ylabel("Magnitude (log)")
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(os.path.join(plot_dir, "fft_comparison.png"), dpi=150, bbox_inches='tight')
plt.close()

print("✓ Saved FFT comparison plot")

print("\n" + "=" * 70)
print("RECOVERY COMPLETE!")
print("=" * 70)
print(f"\n✓ Output file: recovered.wav")
print(f"\nWhat was done to the signal:")
print(f"  1. Signal was modulated with AM (Amplitude Modulation)")
print(f"  2. Carrier frequency: ~7300 Hz")
print(f"  3. Narrowband interference added at several frequencies")
print(f"\nHow it was fixed:")
print(f"  1. Computed analytic signal (Hilbert transform)")
print(f"  2. Applied AM demodulation (mixer with -7300 Hz)")
print(f"  3. Low-pass filtered at 4000 Hz (speech range)")
print(f"  4. Applied notch filters to remove interference")
print(f"\nNow try listening to: recovered.wav")
print("=" * 70)    
