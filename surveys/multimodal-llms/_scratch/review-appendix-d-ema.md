# Independent check — Appendix D.2, the EMA codebook update (2026-08-15)

Scope: the four numbered equations added to § D.2 in the residual-gaps closure, and the three
claims the prose makes about them. Per `[opt:MATH-REDERIVE]` (`.claude/rules/workflow.md`).

## What is quoted vs what is derived

This matters for how much re-derivation is owed, so it is stated first rather than assumed.

- **Eq. (3), (4), (5) are transcriptions**, not derivations. They are the closed-form centroid,
  the two-accumulator online update, and the ratio, printed in the source's Appendix A.1
  (`download/vandenoord-vqvae-2017.pdf`, "VQ-VAE dictionary updates with Exponential Moving
  Averages"), read directly from the PDF text rather than recalled. $\gamma = 0.99$ is the
  source's own reported value. The obligation on these is *fidelity*, discharged by reading.
- **Eq. (6) and the surrounding argument are mine.** They are what a re-derivation must test:
  the fixed-point claim, the evidence-weighting claim, and the exact-invariance claim.

## Claim 1 — the fixed point of Eq. (4) recovers Eq. (3)

Hold the assignment fixed at count $n$ and sum $S$. Then $N^\star = \gamma N^\star + (1-\gamma)n$
gives $N^\star(1-\gamma) = (1-\gamma)n$, so $N^\star = n$; identically $m^\star = S$; hence
$e = m/N \to S/n$, which is Eq. (3). Note the $(1-\gamma)$ cancels, so **the fixed point does not
depend on $\gamma$** — $\gamma$ sets the approach rate and the effective window
$1/(1-\gamma) = 100$, not the target. The survey says exactly this and no more.

Numerically ($d = 4$, $\gamma = 0.99$, 5000 steps): $\max|e - S/n| = 2.8\times10^{-15}$. Machine
precision, i.e. exact.

## Claim 2 — the ratio form weights minibatches by evidence; a single EMA on the centroid does not

The counter-construction is the sharp test, so it was run rather than asserted. Alternate two
batches: one assigning $500$ vectors with mean $\mu_a$, one assigning $1$ vector with mean
$\mu_b$. The correct count-weighted answer is $(500\mu_a + \mu_b)/501$.

| form | result |
|---|---|
| two-accumulator, $e = m/N$ | $[0.998,\ 0.002,\ 0,\ 0]$ |
| one-accumulator, $e \leftarrow \gamma e + (1-\gamma)\,\mathrm{mean}_j z$ | $[0.4975,\ 0.5025,\ 0,\ 0]$ |
| true count-weighted mean | $[0.998,\ 0.002,\ 0,\ 0]$ |

The two-accumulator form matches to three decimals; the one-accumulator form renders a $500\!:\!1$
evidence ratio as $\approx 1\!:\!1$. The claim holds and is not marginal.

## Claim 3 — an unused code is held exactly invariant (Eq. 6)

If $n_i^{(t)} = 0$ the assigned set is empty, so the sum term in Eq. (4) is the zero vector and
both accumulators are multiplied by $\gamma$. The ratio is therefore unchanged **exactly**, not
approximately — the $\gamma$ cancels rather than becoming small. Simulated over 1000 consecutive
idle steps: worst drift $9.4\times10^{-16}$, i.e. floating-point only.

Two things the survey is careful **not** to claim from this, both checked:

- It does *not* claim EMA prevents codebook collapse. Invariance means a starving code does not
  drift or destabilize **while it waits**; it does nothing to make the code win an assignment.
  The survey says "neither drifts nor destabilizes while it waits", which is what was proved.
- It does *not* attribute the collapse-mitigation reputation to the source. The source states
  EMA was "not used for the experiments in this work", so it reports no such result. The survey
  tags that sentence *[reported]* and names it a claim about practice.

## Findings against the drafted text

None requiring a change. One thing was tightened during the check: an earlier draft phrasing
implied $\gamma$ influenced *where* the codebook settles. It does not — it influences only how
fast and over what window — and the text now says "the codebook's adaptation rate is set by
$\gamma$", which is the correct scope.

## Reproduce

The three checks are 30 lines of numpy with `default_rng(0)`; they are simple enough to re-type
from the claims above, and are not worth a committed script. Constants: $d = 4$, $\gamma = 0.99$,
5000 steps (claim 1), 1000 idle steps (claim 3), 4000 alternating batches at $500\!:\!1$
(claim 2).
