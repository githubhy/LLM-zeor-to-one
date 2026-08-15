# Independent re-derivation — Appendix F (audio/video tokenization)

`[opt:MATH-REDERIVE]` per `.claude/rules/workflow.md`. **Part 1 was written before
the target file was opened.** Only the stated source constants in the brief were
used; no survey prose was read.

Arithmetic verified with `python3` (see § Arithmetic log at the bottom).

---

## Part 1 — Derivation from first principles (target UNREAD)

### (a) Mel frame rate — window or hop?

Constants: 16 kHz sample rate, 25 ms analysis window, 10 ms stride.

A short-time analysis produces one feature vector per *placement* of the window.
The window length fixes **how much signal each vector sees** (its time support,
hence its frequency resolution — a 25 ms Hann window has main-lobe width
$\approx 4/0.025 = 160$ Hz); the stride/hop fixes **how often a new vector is
emitted**. These are independent knobs. The output rate is therefore

$$ f_{\text{mel}} = 1/\text{hop} = 1/0.010\ \text{s} = 100\ \text{Hz}. $$

**The HOP determines the frame rate. The window does not.** Using the window
would give the wrong 40 Hz. The window is 2.5x the hop, so consecutive frames
overlap by 15 ms (60% of each window) — the frames are *not* an orthogonal
decomposition and the sequence is deliberately oversampled relative to its
own bandwidth. This is the ordinary STFT/overlap-add setting from signal
processing: hop = decimation factor of the analysis filterbank.

In samples: hop $= 0.010 \times 16000 = 160$ samples; window $= 400$ samples.

For a fixed 30 s segment: $30 \times 100 = 3000$ mel frames.
Cross-check on samples: $30 \times 16000 = 480{,}000$ samples, $/160 = 3000$. ✓

### (b) Encoder frame rate after the conv stem

Stem = two convolutions, filter width 3. Conv 1 has stride 1 (rate-preserving);
conv 2 has stride 2 (decimation by 2). Filter *width* does not change the rate —
only the stride does (with 'same' padding, width only sets the receptive field).

$$ f_{\text{enc}} = 100/2 = 50\ \text{Hz}, \qquad T_{30\text{s}} = 3000/2 = 1500 \ \text{positions}. $$

So one Whisper 30 s chunk = **1500 encoder positions**, i.e. 20 ms per position.

### (c) SALMONN Q-Former output for 30 s

Whisper (50 Hz) and BEATs (50 Hz) are concatenated **frame-by-frame**. That is a
concatenation along the *feature* axis, not the time axis, so the rate stays
50 Hz and the sequence length stays $T = 1500$ for 30 s. (If it were a time-axis
concat the rate claim "both output at 50 Hz, concatenated frame-by-frame" would
be self-contradictory.)

Stated formula: output length $= \lceil T/L \rceil \times N$ with $N=1$, $L=17$.

$$ T/L = 1500/17 = 88.2353\ldots $$

- $\lceil 1500/17 \rceil \times 1 = \mathbf{89}$
- $\lfloor 1500/17 \rfloor \times 1 = \mathbf{88}$

**The paper's reported 88 does NOT equal what the paper's own stated formula
gives.** 88 is the *floor*.

Which does the padding language imply? "The last window is padded with zeros"
means the trailing partial window is **retained and completed**, so it still
emits its $N=1$ query output. Retaining it is exactly what the ceiling counts.
88 full windows cover $88 \times 17 = 1496$ frames, leaving a remainder of
$1500 - 1496 = 4$ frames (0.08 s). Zero-padding those 4 frames to a full 17-frame
window yields an 89th token. **So the padding language implies 89, and the
reported 88 is what you get by *discarding* the remainder — the opposite
operation.** The paper is internally inconsistent: formula + padding ⇒ 89;
reported value ⇒ 88.

Range of $T$ for which the ceiling gives exactly 88:

$$ \lceil T/17 \rceil = 88 \iff 87 < T/17 \le 88 \iff 1480 \le T \le 1496 $$

i.e. **$T \in [1480, 1496]$ frames = 29.60 s to 29.92 s** of audio at 50 Hz.
Verified: $\lceil 1480/17 \rceil = 88$, $\lceil 1496/17 \rceil = 88$,
$\lceil 1497/17 \rceil = 89$. A full 30 s chunk (1500) is *outside* that range.

Window duration: $L/50 = 17/50 = 0.34$ s. The brief's "~0.33 s/window" is a
rounding of 0.34 s, off by 3%; 0.34 s is exact.

Token rate: $88/30 = 2.933$ tokens per second of audio (or $89/30 = 2.967$).

### (d) Qwen2-VL: verify the stated 66 tokens

$$ N_{\text{patch}} = \frac{HW}{P^2} = \frac{224 \times 224}{14^2} = \frac{50176}{196} = 256 $$

i.e. a $16 \times 16$ patch grid. A $2\times2$ MLP merge divides by 4:

$$ 256/4 = \mathbf{64}. $$

The stated value is 66. **Delta = +2, and the patch arithmetic alone cannot
produce it.** The only consistent reading is that the two extra tokens are the
`<|vision_start|>` / `<|vision_end|>` sentinel markers wrapping the visual block
— they are text-vocabulary tokens, not patches. So 66 = 64 visual + 2 markers.
Verified, **conditional on that hypothesis being stated**; if a document quotes
66 as "the patch count" without naming the +2, that is an unstated hypothesis
and the arithmetic does not close.

### (e) Video tokens at 2 fps, 576 tokens/frame

| Clip | Frames ($2 \times$ s) | Tokens |
|---|---|---|
| 30 s | 60 | **34,560** |
| 5 min (300 s) | 600 | **345,600** |
| 2 h (7200 s) | 14,400 | **8,294,400** |

The 2 h figure is ~8.3 M tokens — roughly 500x a 16 k context and ~8x even a
1 M-token context. This is the number that makes the cap non-optional.

### (f) Tokens per frame available under the 16,384-token cap at 2 fps

| Clip | Frames | Budget/frame $=16384/F$ | Implied square grid side |
|---|---|---|---|
| 30 s | 60 | **273.07** | 16.5 |
| 300 s | 600 | **27.31** | 5.2 |

So a 30 s clip can afford ~273 tokens/frame — under half of 576, i.e. the frame
must be downscaled to roughly a $16\times16$ post-merge grid. A 5-minute clip
gets ~27 tokens/frame, i.e. about a $5\times5$ grid — well below any useful
spatial resolution. The cap does not degrade gracefully; it collapses spatial
detail linearly in clip duration.

### Prose claims — my independent positions (written before reading the target)

**P1 — "half a minute of speech costs about what three images cost" (1500 vs 576).**
$1500/576 = 2.604$. That is "about 2.6 images", not three; stating three
overstates by 15% (three images = 1728 tokens, 13% more than 1500). Separately,
**the two sides are on different bases**: 1500 is the *Whisper encoder position*
count, whereas 576 is the *LLM-visible token* count of a LLaVA-1.5-style
$336/14 = 24\times24$ grid. In SALMONN the LLM never sees 1500 — it sees 88.
On the LLM-token basis the ratio is $88/576 = 0.15$, i.e. **30 s of speech costs
about one sixth of one image**, a 17x difference from the encoder-side reading.
The comparison is only defensible if the document says explicitly that both
numbers are encoder-side pre-resampler counts.

**P2 — "about 2.9 tokens per second of audio" and "cheaper per second than
transcribed text at a normal speaking rate".**
First half: $88/30 = 2.933$ ✓.
Second half: I do not think this survives. Transcribed English at $r$ words per
minute costs $\approx (r/60) \times \tau$ tokens/s with $\tau \approx 1.3$–$1.4$
BPE tokens per word (subword splits + leading space + punctuation).
Break-even against 2.933 tokens/s is at **135 wpm** ($\tau=1.3$) or **126 wpm**
($\tau=1.4$). Normal conversational English is commonly quoted at ~120–150 wpm
(spontaneous speech at the low end, read/presentation speech higher). So the
claim is **true at 150 wpm (3.25 tok/s), false at 120 wpm (2.60 tok/s), and
break-even sits inside the normal range.** The direction of the inequality is
decided by which end of "normal" you pick — that is not a finding, it is a
coin-flip dressed as one. It should be stated as *comparable to*, with the
assumed wpm and tokens-per-word disclosed, or dropped.

**P3 — "eight fixed frames is 0.8 fps on a ten-second clip and 0.001 fps on a
two-hour film".** $8/10 = 0.8$ ✓. $8/7200 = 0.001111$, which rounds to 0.001 ✓.
Both correct; the second is to 1 s.f. and is the honest rounding.

**P4 — 1-D RoPE 60-frame clip "consumes 34,560 consecutive position indices"
while M-RoPE uses "60 temporal indices and 24 each of height and width".**
$60 \times 576 = 34{,}560$ ✓. And $\sqrt{576} = 24$ exactly, so a 576-token
frame is a $24\times24$ grid and the height/width extents of 24 are consistent ✓.
Both halves check.

**P5 — halving patch size raises attention cost "roughly sixteenfold".**
$N \propto 1/P^2$, so halving $P$ quadruples $N$. Self-attention is
$O(N^2)$, so $4^2 = 16$x ✓ — **provided the claim is scoped to the attention
(score-matrix) term**. The per-token linear terms (QKV/out projections, MLP) are
$O(N)$ and rise only 4x, so *total* encoder FLOPs rise by less than 16x, and at
small $N$ (256 patches) the linear terms typically dominate — so end-to-end wall
time would rise well under 16x. Correct as a statement about the quadratic term;
an overstatement if written as "cost" unqualified.

---

## Part 2 — Comparison against the target

*(appended after reading `surveys/multimodal-llms/appendix-f-audio-video.md`)*

