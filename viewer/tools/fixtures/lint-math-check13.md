# Fixture — lint-math check #13 (duplicate `\triangleq` definitions)

Expected result: **exactly one** warning, naming `` `\gamma` `` and citing the
two lines below. Anything else is a regression. Run via
`python viewer/tools/test-lint-math-checks.py`.

## MUST fire — one symbol, two different definitions

Let $\gamma \triangleq \sigma_H^2/\sigma_w^2$ be the pilot SNR.

Far away, redefined: $\gamma \triangleq E_s/N_0$ for the link budget.

## MUST NOT fire — identical restatement

Let $g \triangleq 1 - \text{NMSE}$ here, and $g \triangleq 1 - \text{NMSE}$ again later.

## MUST NOT fire — fenced code is not math

```
$\beta \triangleq a/b$
$\beta \triangleq c/d$
```

## MUST NOT fire — `aligned` alignment markers are not symbol names

This is `bugs/2026-08-10-lint-math-check13-aligned-ampersand`: the LHS sits on
the previous line, so the only thing before `\triangleq` on the matched line is
`&`. Two unrelated definitions must not collide on it.

$$
\begin{aligned}
\text{NMSE}(k)
  &\triangleq \frac{\text{MMSE}(k)}{\sigma_H^2}
\end{aligned}
$$

$$
\begin{aligned}
\tilde{y}_j
  &\triangleq \hat{H}_p(k_j) - \mathcal{L}_{\mathcal{M}}\bigl[\hat{H}_p(k_j)\bigr]
\end{aligned}
$$
