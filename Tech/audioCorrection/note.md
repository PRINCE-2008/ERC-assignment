# Electronics & Robotics Club — Technical Assignment
## Signal Processing Task: The Corrupted Transmission

---

### Background

A clean audio signal was prepared for transmission. During the transmission process, several things went wrong — in sequence. You are receiving the signal at the other end. Your job is to figure out what happened and undo it, step by step.

You are given one file: **`corrupted.wav`**

That is all.

---

### Objective

Recover the original audio signal from the corrupted WAV file using signal processing techniques. You are **not told** what was done to the signal. Part of the task is figuring that out yourself — from the data.

---

### What You Need to Do

Use FFT, filtering, and frequency domain analysis as your tools to investigate the signal at each stage. Every step you take should reveal the next problem. There is no single correct path — we are evaluating your reasoning, not your recipe-following.

**Stage 1 — Understand what you have received**
- Load and plot the signal in the time domain. Does it look like audio?
- Compute and plot its FFT. Where is the energy sitting?

**Stage 2 — The signal is not where you expect it**
- Normal speech lives in the 0–4000 Hz range.
- If the energy is somewhere else entirely, ask yourself: how does a signal end up shifted in frequency?
- Once you figure out how it got there, bring it back.

**Stage 3 — Clean up what remains**
- After Stage 2, compute the FFT again on your recovered signal.
- Are there any sharp, narrow spikes that do not belong in natural audio?
- Identify them. Remove them. Design your filter based on what you observe — not what you are told.

**Stage 4 — Something still feels off**
- The FFT may look fine after Stage 3.
- But the audio might still sound kindaa wrong.
- Think beyond amplitude. What else does a signal have?

---



### Deliverables

Submit the following:

1. **All plots**, clearly labelled, in order:
   - Time domain of the corrupted signal
   - FFT of the corrupted signal
   - Any intermediate signals during Stage 2
   - FFT after Stage 2 (pre and post Stage 3 filtering)
   - The plot that reveals the Stage 4 problem, and after correction

2. **The recovered audio file** — a clean `.wav` file of your final output.

3. **A README / report** explaining:
   - What you found at each stage
   - What you concluded was done to the signal
   - What technique you used to undo it and why
   - Tools and libraries used

---

### Allowed Tools

- **Python** — NumPy, SciPy, Matplotlib 
- **MATLAB**
- **Scilab**

AI tools are permitted for syntax and debugging help. However, you will be asked to explain every decision in your interview — so understand what you did, not just that it worked.

---

### Submission Structure

```
your_name/
├── corrupted.wav             ← the given file (unchanged)
├── recovered.wav             ← your output
├── solution.py / .m / .sce
├── plots/
│   ├── stage1_time_domain.png
│   ├── stage1_fft.png
│   ├── stage2_*.png
│   ├── stage3_*.png
│   └── stage4_*.png
└── README.md
```


*Trust the FFT. Plot everything. The signal will tell you what happened.*
