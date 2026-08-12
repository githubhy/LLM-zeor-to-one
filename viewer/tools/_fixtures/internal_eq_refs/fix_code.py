"""Fixture source for check-internal-eq-refs.py.

Two survey-ref comments: one CONSISTENT, one INCONSISTENT. The gate must flag exactly
the inconsistent one and pass the consistent one.
"""


# survey-ref: fix.md#sec-1.2 (Eq. 2)   -- CONSISTENT: eq-2 lives in section 1.2
def apply_reconstruct_quantize(y):
    return round(y * 2)


# survey-ref: fix.md#sec-1.1 (Eq. 2)   -- INCONSISTENT: eq-2 lives in 1.2, not 1.1
def wrong_but_resolving(y):
    return round(y * 2)
