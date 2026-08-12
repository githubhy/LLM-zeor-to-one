# Fixture survey — internal-eq-refs gate

A tiny two-section survey used only to test `check-internal-eq-refs.py`. It carries a
non-ASCII math glyph on purpose (α, ×, −) so a bare `open()` on a Windows/GBK box would
crash — the gate must read it as UTF-8.

<!-- sec:1.1 -->
### <a id="sec-1.1"></a>1.1 First section — the α operator

<a id="eq-1"></a><!-- eq:1.1-1 -->
$$
y = α · x − 1 \tag{1}
$$

Equation (1) lives in section 1.1.

<!-- sec:1.2 -->
### <a id="sec-1.2"></a>1.2 Second section — the reconstruct × quantize apply

<a id="eq-2"></a><!-- eq:1.2-1 -->
$$
z = \operatorname{round}(y × 2) \tag{2}
$$

Equation (2) lives in section 1.2, NOT 1.1.
