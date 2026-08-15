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

Target: `surveys/multimodal-llms/appendix-f-audio-video.md` (plus
`appendix-a-vit-and-encoders.md` L8, which is where the "sixteenfold" claim
actually lives — it is not in Appendix F).

**Headline:** every displayed equation checks out — (1), (2), (3), (4), (5), (6),
(7), (8), (9) are all correct, and the §F.4 ceiling-vs-floor analysis is not
merely correct but reaches exactly the conclusion I reached independently. The
defects are all in prose: **6 findings, 3 of them load-bearing.**

### Equation ledger (all CONFIRMED)

| Eq | Target | My value | Verdict |
|---|---|---|---|
| (1) | $r_{\text{mel}} = 1/0.010 = 100$ frames/s, hop not window | 100 Hz, hop | ✓ identical, and the hop-vs-window justification is right |
| (2) | $r_{\text{enc}} = 100/(1\cdot2) = 50$ | 50 Hz | ✓ |
| (3) | $30 \times 50 = 1500$ encoder positions | 1500 | ✓ |
| (4) | $\mathbf{E}' \in \mathbb{R}^{(t+a)\times m}$ | — | ✓ well-formed |
| (5) | $\mathbf{Z}\in\mathbb{R}^{T\times(d_w+d_b)}$, feature-axis concat | feature-axis, $T$ preserved | ✓ |
| (6) | $\lvert\mathbf{H}\rvert = \lceil T/L\rceil \times N$ | same | ✓ |
| (7) | $\lceil 1500/17\rceil = \lceil 88.24\rceil = 89 \ne 88 = \lfloor\cdot\rfloor$ | 88.2353 → 89 / 88 | ✓ incl. the 88.24 rounding |
| (8) | Bayes decomposition | $P(Y \mid X,I)=P(Y \mid X)P(I \mid Y,X)/P(I \mid X)$ | ✓ |
| (9) | $N_{\text{video}} = F\cdot HW/P^2$ | same | ✓ |

Other spot-checks that pass: $W/H = 2.5$ windows per sample (§F.1); 400-sample
window → ~201 real-FFT bins ("on the order of 200") and 257 at $n_{\text{fft}}=512$
(§F.1); $1500/88 = 17.045$, "a factor of 17" (§F.4); LoRA $4.0 \to 2.0$ is a
halving (§F.4); $(224/14)^2 = 256 \to 64 + 2 = 66$ (§F.5 lever 2);
$16384/60 = 273.07$ and $16384/600 = 27.31$ (§F.5 lever 3); the whole §F.5
token table (4608 / 34,560 / 345,600 / 8,294,400);
$8/10 = 0.8$ and $8/7200 = 0.00111 \to 0.001$ (§F.5 lever 1);
$\sqrt{576} = 24$ (§F.6).

---

### [OVERSTATEMENT] §F.2 — "half a minute of speech costs about what three images cost"

**Claim (L45):** "$1500$ tokens is *comparable to an image*: a $336$-px frame at
patch size $14$ costs $(336/14)^2 = 576$ tokens, so half a minute of speech costs
about what three images cost."

**My result:** $1500/576 = 2.604$. Three images cost $1728$ tokens — 15% more than
1500. The honest phrasing is "about two and a half images", or the exact "2.6".
"About three" rounds 2.60 up past 2.75 and is the flattering direction.

**Delta:** +15% (2.604 stated as ~3).

Small on its own; it matters because the sentence is the appendix's one
cross-modal cost intuition, and §F.5 later re-uses 576 as its per-frame unit, so
a reader carries the 3:1 ratio forward.

### [UNSTATED HYPOTHESIS] §F.2/§F.4 — the 1500-vs-88 basis is never declared

**Claim:** §F.2 L45 calls 1500 "**tokens**" and compares it to an image's 576
tokens. Equation (3) itself correctly says "1500 **encoder positions**".

**My result:** these are two different bases and the appendix contains both
numbers for the *same* 30 s of audio. On the encoder-position basis, 30 s ≈ 2.6
images. On the **LLM-token** basis — which is the basis 576 is on, and the basis
"cost" means to a reader — SALMONN's 30 s is **88** tokens, i.e. $88/576 = 0.15$
images. **The two readings differ by a factor of 17.05.** §F.4 L86 states the 88
seventy-odd lines later and never reconciles it against §F.2's "three images".

**Delta:** 17.05x, depending on which basis the reader assumes.

This is precisely `[opt:MATH-BASIS]` (`.claude/rules/workflow.md`): a quantity
measurable on two bases declares which, at the point of use. §F.2 does not.
Minimum fix: keep the word "positions" in the prose as Eq. (3) does, and add
"before any connector — §F.4 compresses the same 30 s to 88 LLM tokens".

### [ERROR] §F.4 — "cheaper per second than transcribed text at a normal speaking rate"

**Claim (L86):** "...the token rate falls to about $2.9$ tokens per second of
audio — cheaper per second than transcribed text at a normal speaking rate."

**First half is right:** $88/30 = 2.933$ ✓.

**Second half does not survive.** Transcribed English at $r$ wpm costs
$(r/60)\cdot\tau$ tokens/s, $\tau \approx 1.3$–$1.4$ BPE tokens per word.
Break-even against 2.933 tok/s:

| $\tau$ | break-even |
|---|---|
| 1.3 tok/word | **135 wpm** |
| 1.4 tok/word | **126 wpm** |

and across the range usually called normal conversational English:

| wpm | tok/s ($\tau{=}1.3$) | vs 2.93 audio |
|---|---|---|
| 120 | 2.60 | audio is **more expensive** |
| 130 | 2.82 | audio is **more expensive** |
| 140 | 3.03 | audio cheaper by 3% |
| 150 | 3.25 | audio cheaper by 10% |

**The claim's truth value flips inside the normal range, and break-even sits in
the middle of it.** Even at the favourable end the margin (10%) is smaller than
the uncertainty in $\tau$. This is not a finding; it is a coin-flip stated as
one.

Worse, it is a **memory citation** in the sense of
`.claude/rules/citation-integrity.md`: the sentence silently supplies two
uncited constants (words/minute and tokens/word) to license a comparative claim
— in an appendix whose own opening paragraph (L6) promises "where a paper does
**not** state a number the survey needs, that is recorded as a gap in §F.7
rather than filled in from memory", and whose §F.7 congratulates itself on
exactly that discipline. The appendix breaks its own stated contract here.

**Fix:** either delete the clause, or state it as "*comparable to* transcribed
text at a normal speaking rate (break-even near 130 wpm at ~1.3 tokens/word)"
with the two constants disclosed and sourced, or file the speaking-rate constant
as a §F.7 gap.

### [UNSTATED HYPOTHESIS] §F.4 — BEATs' 50 Hz "is in fact a shared convention inherited from the 10 ms hop"

**Claim (L77):** "two independently trained encoders agreeing on a frame rate
looks like a coincidence, and **is in fact** a shared convention inherited from
the $10$ ms hop that Equation (1) started from."

**My result:** nothing the appendix cites supports this. The only cited fact is
SALMONN's "both encoders have the same output frame rate of 50Hz". A 10 ms hop
gives **100 Hz**, not 50 — Equation (2) is what supplies the extra factor of 2,
and that factor is Whisper's *conv-stem stride*, an architectural feature the
appendix never claims BEATs shares. So the asserted mechanism requires BEATs to
independently implement its own 2x time decimation on top of a 10 ms hop, which
is a substantive claim about a third paper's internals that is neither cited nor
derived.

"Is in fact" asserts knowledge the appendix does not have. This is the exact
failure class this re-derivation is looking for: a correct equation (5) with an
un-sourced causal story wrapped around it.

**Fix:** downgrade to "plausibly a shared convention descending from the standard
10 ms hop, though SALMONN states only the rate and not BEATs' decimation
factor" — or list BEATs' downsampling factor in the §F.7 gap table, where it
belongs.

### [ERROR] §F.5 — the table's "8 frames (Video-LLaVA) → 4,608" is not Video-LLaVA's cost

**Claim (L128):** table row `| 8 frames (Video-LLaVA) | 8 | 4,608 | fits any modern context |`.

**My result:** $8 \times 576 = 4608$ ✓ *arithmetically*, but Video-LLaVA encodes
$224\times224$ frames, and the appendix's own §F.7 says so: "The encoder name
(OpenCLIP-L/14) and the $224$ resize target **imply 256**". Video-LLaVA's own
implied cost is $8 \times 256 = \mathbf{2{,}048}$.

**Delta: 4,608 vs 2,048 = 2.25x**, with a model's name attached to a number that
is not that model's.

The table preamble does declare $N_v^{\text{frame}} = 576$ for all rows, so a
careful reader can reconstruct it. But this is the one row carrying a model
name, it sits eight lines after §F.5 lever 2 says "the Video-LLaVA per-frame
count below is **not** [quoted]", and it is quoted-adjacent in a way that
contradicts that sentence. Relabel the row `8 frames (Video-LLaVA's $F$, at this
table's 576 tok/frame)`, or drop the model name from the row.

### [ERROR] §F.5 — "infeasible by three orders of magnitude" / "a $10^3$ gap"

**Claim (L131, L133):** the 2 h row (8,294,400 tokens) is "infeasible by three
orders of magnitude", and "no single lever closes a $10^3$ gap".

**My result:** the multiplier is entirely a function of the assumed context, and
the claim never names one. Against:

| context | ratio | orders |
|---|---|---|
| 8,192 | 1012x | 3.01 |
| 16,384 (Qwen2-VL's own cap) | 506x | **2.70** |
| 32,768 | 253x | 2.40 |
| 131,072 | 63x | **1.80** |
| 1,000,000 | 8.3x | 0.92 |

Only an **8k** context yields three orders. But the table's own verdict column
pins the assumed context far higher: 34,560 tokens "fits, but dominates the
context" requires a context well above 34,560, and 345,600 "exceeds *most*
deployed contexts" requires most deployed contexts to be below ~345k — together
implying ~64k–128k. At 128k the gap is **63x, i.e. 1.8 orders, not 3**.

**Delta: ~16x** (1000x claimed vs ~63x on the table's own implied baseline).

**The prose contradicts the table it is summarizing**, three lines below it. Fix:
name the baseline. "8.3 M tokens is 500x Qwen2-VL's own 16,384-token cap and
still 63x a 128k context" is both true and stronger than the unanchored "three
orders of magnitude", because it survives the next context-length increase.

### [INCOMPLETE BOUND — and it weakens the survey's own argument] §F.4 — "only for $T \le 1496$"

**Claim (L95):** "a shorter effective $T$ would also explain it, but only for
$T \le 1496$, which contradicts the paper's own $50$ Hz."

**My result:** $\lceil T/17\rceil = 88$ holds iff $87 < T/17 \le 88$, i.e. iff
$1480 \le T \le 1496$ — audio of **29.60 s to 29.92 s**. Verified:
$\lceil 1480/17\rceil = 88$, $\lceil 1496/17\rceil = 88$, $\lceil 1497/17\rceil = 89$.

$T \le 1496$ is a *necessary* condition, not the characterization: $T = 100$ also
satisfies it and gives 6, not 88. Stating only the upper bound leaves the
alternative hypothesis looking like an open half-line.

This is the one finding where the correction **helps** the author: the true
interval is only **0.32 s wide**, so the "shorter effective $T$" hypothesis
requires the audio to be within 0.4 s of 30 s *without being* 30 s — far more
contrived than "$T \le 1496$" makes it sound, and therefore a stronger argument
for the floor-vs-ceiling implementation explanation the paragraph actually
favours. Recommend: "only for $1480 \le T \le 1496$, i.e. 29.60–29.92 s of
audio".

### [OVERSTATEMENT] §F.4 — "about $0.33$ s per window"

**Claim (L86):** "$L = 17$ frames, about $0.33$ s per window".

**My result:** $17/50 = \mathbf{0.34}$ s exactly. 0.33 s at $L=17$ would need
51.5 Hz; 0.33 s at 50 Hz would need $L = 16.5$.

This is quoted from the source, and "about" covers it — but it is a **second**
internal cross-check on the same paper that the appendix had in hand and did not
run, in the very paragraph that precedes a long methodological note about how
the 88 is "the *only* token count in Appendix F that can be checked against a
second independent statement by the same paper". That "only" claim survives
literally (0.33 s is a duration, not a token count), but the appendix should say
its own constants give 0.34 s.

### [CONFIRMED] §F.5 lever 1 — 8 frames = 0.8 fps / 0.001 fps

$8/10 = 0.8$ ✓. $8/7200 = 0.001111$, correctly given to 1 s.f. as 0.001 ✓.
Both halves correct; the framing ("a fixed frame count is not a sampling *rate*
at all") is right and well made.

### [CONFIRMED] §F.5 lever 2 — the 66 tokens

$(224/14)^2 = 256 \to 64$ after the $2\times2$ merge, $+2$ boundary tokens $= 66$
✓. The appendix **names the $+2$**, which is the disclosure the arithmetic
requires — 64 alone does not reach 66 and any document quoting 66 without naming
the sentinels has an unstated hypothesis. This one does it right.

### [CONFIRMED, with an undeclared basis] §F.6 — 34,560 vs "24 each of height and width"

$60 \times 576 = 34{,}560$ ✓, and $\sqrt{576} = 24$, so 576 tokens/frame is a
$24\times24$ grid and the height/width extents of 24 are exactly consistent ✓.
Both halves check.

One note: the paragraph attaches Qwen2-VL's M-RoPE to a **LLaVA-basis** frame
(336 px / patch 14 / no merge = 576 tokens). Qwen2-VL's own 30 s clip is capped
at 16,384 tokens, i.e. ~273 tokens/frame (§F.5 lever 3), which is a ~16x16 grid,
not 24x24 — so the 34,560 figure is what 1-D RoPE *would* cost on this
appendix's illustrative frame, not what Qwen2-VL faces. That is a legitimate
counterfactual, but the frame's provenance should be stated, since §F.5 supplies
the contradicting 273 three subsections earlier.

### [OVERSTATEMENT] `appendix-a-vit-and-encoders.md` L8 — "compute is quartic in the inverse patch size"

The "sixteenfold" claim is **not in Appendix F**; it is in
`appendix-a-vit-and-encoders.md` L8: "Because attention is quadratic in sequence
length, and $N$ is quadratic in $1/P$, **compute is quartic in the inverse patch
size** ... Halving $P$ quadruples the tokens and so raises **attention cost**
roughly sixteenfold."

**"Attention cost ... sixteenfold" is CORRECT** and correctly scoped:
$N \propto P^{-2}$, so halving $P$ gives $N \times 4$, and the $O(N^2)$
score+AV term gives $4^2 = 16$ ✓.

**"Compute is quartic in the inverse patch size" is wrong at the operating point
the same sentence quotes.** Per ViT-L layer ($d = 1024$), the linear terms
(QKVO $4d^2$ + MLP $8d^2$ per token) are $O(N)$ and dominate:

| $N$ | config | linear MACs | attention MACs | attention share |
|---|---|---|---|---|
| 196 | 224 px / P16 | 2.47e9 | 7.87e7 | **3.1%** |
| 256 | 224 px / P14 | 3.22e9 | 1.34e8 | **4.0%** |
| 576 | 336 px / P14 | 7.25e9 | 6.80e8 | 8.6% |
| 1024 | 224 px / P7 | 1.29e10 | 2.15e9 | 14.3% |

Halving $P$ from 14 to 7 at 224 px: attention x16.0, linear x4.0,
**total encoder x4.48**.

**Delta: 16x vs 4.5x — 3.6x overstated** for the quantity a reader cares about
(what the encoder actually costs). Attention is 4% of a ViT-L/14 layer at 224 px;
it is not the cost driver at any resolution this survey discusses, and only
reaches 14% even after the patch size is halved. "Compute is quartic" is an
asymptotic statement ($N \gg 6d$, i.e. $N \gg 6144$) presented as an operating
fact at $N = 196$–$576$.

**Fix:** keep "attention cost x16"; replace "compute is quartic in the inverse
patch size" with "the *attention term* is quartic in the inverse patch size,
though at ViT-L scale that term is only ~4% of encoder FLOPs, so total cost rises
~4.5x rather than 16x". Same caveat applies to `fundamentals.md` L35's "the
encoder cost grows with the *fourth power* of the image side" — its own
$(576/256)^2 \approx 5.1$x is correctly scoped to "the attention term", so only
the "encoder cost" sentence needs the same qualification.

---

## Summary

**Load-bearing (fix before sign-off):**
1. §F.4 "cheaper per second than transcribed text" — unsupported, flips inside the
   normal speaking range, and supplies two uncited constants in an appendix that
   promises not to.
2. §F.5 "three orders of magnitude" — contradicts the adjacent table's own verdict
   column; the real figure is ~63x (1.8 orders) at 128k, ~506x at Qwen2-VL's cap.
3. `appendix-a` "compute is quartic in the inverse patch size" — 16x vs a measured
   4.5x total; attention is 4% of ViT-L/14 encoder FLOPs at 224 px.

**Should fix (cheap, and two of them strengthen the argument):**
4. §F.2 "three images" (2.60, not ~3) and the undeclared 1500-positions /
   88-tokens basis split (17.05x).
5. §F.4 BEATs' 50 Hz "is in fact ... inherited from the 10 ms hop" — unsourced
   mechanism; a 10 ms hop gives 100 Hz, and the missing 2x is Whisper's stride.
6. §F.5 table row attributing 4,608 tokens to Video-LLaVA (its own implied cost
   is 2,048).

**Nits:** §F.4 "$T \le 1496$" → "$1480 \le T \le 1496$" (strengthens the
argument); §F.4 "about 0.33 s" → 0.34 s exact; §F.6 declare the 576/frame frame
as LLaVA-basis, not Qwen2-VL's.

**Nothing found wrong in:** all nine displayed equations; the hop-vs-window
derivation; the conv-stride decimation; the 1500 composition; the entire
ceiling-vs-floor analysis of the SALMONN 88 (which I reached independently and
identically, including the padding-implies-ceiling reading); the 66-token
Qwen2-VL closure incl. the +2 sentinels; the 273/27 cap arithmetic; the full
§F.5 token table; the 0.8/0.001 fps figures; and the 24x24 M-RoPE consistency.

## Arithmetic log

All values above computed with `python3` (exact integer / IEEE-754 double
arithmetic), in four batches: (i) mel/conv/Q-Former rates and the
$\lceil\cdot\rceil = 88$ interval, (ii) Qwen2-VL patch arithmetic, video token
totals and cap budgets, (iii) speaking-rate break-even sweep and the five prose
claims, (iv) ViT-L per-layer MAC split (linear vs attention) across
$N \in \{196, 256, 576, 1024\}$ and the context-ratio table.

