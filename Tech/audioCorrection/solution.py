import numpy as np
from scipy.io import wavfile
from scipy import signal
import matplotlib.pyplot as plt
import os


plot = "plots"

if not os.path.exists(plot):
    os.makedirs(plot)


#//////////////////////////STEP 1: LOAD AND ANALYZE///////////////////////

sr , crrSig = wavfile.read("corrupted.wav")
if crrSig.dtype != np.float32 and crrSig.dtype != np.float64:
    crrSig = crrSig.astype(np.float32)
if np.max(np.abs(crrSig)) > 0:
    crrSig = crrSig / np.max(np.abs(crrSig))  # Normalize to [-1, 1]
time = np.arange(len(crrSig)) / sr

# plot : 1 plot of corrupted time domain signal
plt.figure(figsize=(14,5))
plt.plot(time, crrSig, linewidth=0.5)
plt.title("Stage 1: Corrupted Signal - Time Domain")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.tight_layout()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(plot, "stage1_time_domain.png"), dpi=150)
plt.close()

# plot : 2  fft of corrupted signal

fft = np.fft.fft(crrSig)
freq = np.fft.fftfreq(len(crrSig),1/sr)
mag = np.abs(fft)

plt.figure(figsize=(14,5))
plt.semilogy(freq[:len(freq)//2], mag[:len(mag)//2], linewidth=0.7)
plt.title("Stage 1: Corrupted Signal - FFT (Magnitude Spectrum)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (log scale)")
plt.tight_layout()
plt.grid(True, alpha=0.3, which='both')
plt.xlim([0, sr/2])
plt.savefig(os.path.join(plot, "stage1_fft.png"), dpi=150)
plt.close()

#//////////////////////////STEP 2: FREQUENCY SHIFTING///////////////////////
peakIdx = np.argmax(mag[:len(mag)//2])
peakFreq = freq[peakIdx]

shiftFreq = 0
shiftedSig = crrSig.copy()
if peakFreq > 5000:
    thresholdShift = np.max(mag[:len(mag)//2]) * 0.1
    shiftPeaks, _ = signal.find_peaks(mag[:len(mag)//2], height=thresholdShift)
    if len(shiftPeaks) > 1:
        peakDiffs = np.diff(freq[shiftPeaks])
        if len(peakDiffs) > 0:
            shiftFreq = peakFreq - 2000
            shiftedSig = crrSig * np.exp(-2j * np.pi * shiftFreq * time)
            shiftedSig = np.real(shiftedSig)

# plot : 3 fft after frequency shift
fftShifted = np.fft.fft(shiftedSig)
magShifted = np.abs(fftShifted)


plt.figure(figsize=(14,5))
plt.semilogy(freq[:len(freq)//2], magShifted[:len(magShifted)//2], linewidth=0.7)
plt.title("Stage 2/3: FFT Before Filtering")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (log scale)")
plt.tight_layout()
plt.grid(True, alpha=0.3, which='both')
plt.xlim([0, sr/2])
plt.savefig(os.path.join(plot, "stage2_fft_before_filter.png"), dpi=150)
plt.close()

# plot : 4 time domain after frequency shift
if shiftFreq != 0:
    plt.figure(figsize=(14,5))
    plt.plot(time, shiftedSig, linewidth=0.5)
    plt.title(f"Stage 2: After Frequency Shift Correction ({shiftFreq:.2f} Hz shift applied)")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.tight_layout()
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(plot, "stage2_after_frequency_shift.png"), dpi=150)
    plt.close()

#//////////////////////////STEP 3: SPIKE REMOVAL///////////////////////

threshold = np.max(magShifted) * 0.02
peaks, _ = signal.find_peaks(magShifted[:len(magShifted)//2], height=threshold, distance=50)
for peak in peaks:
    spikeFreq = freq[peak]
    w0 = spikeFreq / (sr/2)  
    if 0 < w0 < 1:
        b, a = signal.iirnotch(w0, 30)
        shiftedSig = signal.filtfilt(b, a, shiftedSig)

# plot : 5 fft comparision after spike removal

fftFiltered = np.fft.fft(shiftedSig)
magFiltered = np.abs(fftFiltered)
plt.figure(figsize=(14,5))
plt.semilogy(freq[:len(freq)//2], magFiltered[:len(magFiltered)//2], linewidth=0.7, label='After Filtering')
plt.semilogy(freq[:len(freq)//2], magShifted[:len(magShifted)//2], linewidth=0.7, alpha=0.5, label='Before Filtering')
plt.title("Stage 3: FFT After Filtering")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude (log scale)")
plt.legend()
plt.tight_layout()
plt.grid(True, alpha=0.3, which='both')
plt.xlim([0, sr/2])
plt.savefig(os.path.join(plot, "stage3_fft_after_filter.png"), dpi=150)
plt.close()

#/////////////////////////STAGE 4: PHASE ANALYSIS & CORRECTION///////////////////////
half = len(freq) // 2
freqPos = freq[:half]
fftPhaseAfter = np.angle(fftFiltered[:half])

phaseUnwrapped = np.unwrap(fftPhaseAfter)

# plot for phase before and after correction
plt.figure(figsize=(14,5))
plt.plot(freqPos[:1000], fftPhaseAfter[:1000], linewidth=0.7, label='Wrapped Phase')
plt.plot(freqPos[:1000], phaseUnwrapped[:1000], linewidth=0.7, alpha=0.7, label='Unwrapped Phase')
plt.title("Stage 4: Phase Analysis")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Phase (radians)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.xlim([0, 1000])
plt.tight_layout()
plt.savefig(os.path.join(plot, "stage4_phase_analysis.png"), dpi=150)
plt.close()

#detecting linear phase slope
magPos = magFiltered[:half]
validIdx = np.where(magPos > np.max(magPos) * 0.01)[0]
delay = 0.0
shiftSamples = 0
if len(validIdx) > 10:
    slope, intercept = np.polyfit(freqPos[validIdx], phaseUnwrapped[validIdx], 1)
    delay = -slope / (2 * np.pi)
    shiftSamples = int(np.round(delay * sr))

if abs(delay) > 1e-5 :
    correctedSig = np.roll(shiftedSig, -shiftSamples)
    if shiftSamples > 0:
        correctedSig[-shiftSamples:] = 0
    elif shiftSamples < 0:
        correctedSig[:(-shiftSamples)] = 0
else:
    correctedSig = shiftedSig
# plot : 7 time domain after phase correction
plt.figure(figsize=(14,5))
plt.plot(time, correctedSig, linewidth=0.5)
plt.title("Stage 4: Final Recovered Signal")
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.tight_layout()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(plot, "stage4_recovered_signal.png"), dpi=150)
plt.close()

#/////////////////////////SAVE RECOVERED SIGNAL///////////////////////
correctedSig = np.clip(correctedSig, -1, 1)
wavfile.write("recovered.wav", sr, (correctedSig * 32767).astype(np.int16))
print(f"✓ Recovered | Shift: {shiftFreq:.0f}Hz | Delay: {delay*1000:.1f}ms | Spikes Removed: {len(peaks)}")    
