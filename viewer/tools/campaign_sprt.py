#!/usr/bin/env python3
"""Sequential stopping for DEFECT-SEARCH closure. OPT-IN, default OFF.

P10 of `plans/2026-08-15-campaign-driver-v2.md` (inherited verbatim from v1.1 Phase 4).
Registered `[opt:CAMPAIGN-SPRT · default OFF · toggle .claude/skill-options.json]`.

THIS ANSWERS ONE OF THE TWO CLOSURE QUESTIONS, NOT BOTH. Coverage closure -- every unit
dispositioned and every in-scope unit done -- is a deterministic set difference over an
ENUMERATED population and must acquire no statistics. This module is for the other
question: have the defects in a wave been found, over a population whose size is UNKNOWN.
Applying it to coverage would be the category error `check-campaign._check_closure`
rejects; applying a consecutive-clean-rounds count here is the naive instrument it
supersedes, and this repo's own five-pass review record shows that count does not converge.

WALD'S SPRT. Test H0: p <= p0 ("defect rate is acceptably low, stop") against H1: p >= p1
("keep looking"), accumulating the log-likelihood ratio after each observation:

    per defect      log(p1/p0)
    per clean       log((1-p1)/(1-p0))
    stop for H0     LLR <= log(beta / (1 - alpha))
    stop for H1     LLR >= log((1 - beta) / alpha)
    otherwise       continue

The property that makes it worth having: expected sample size is smaller than any
fixed-n test with the same error rates, and -- unlike a clean-rounds count -- alpha and
beta are the ACTUAL error probabilities, declared up front rather than hoped for.

WHY DEFAULT OFF. It carries two parameters (p0, p1) that are honest only if they come from
a real prior about the defect rate, and this campaign has no such prior yet: 6 defects in
32 units is the entire observational base. Shipping it enabled would put unfounded numbers
on the critical path. It is built, tested and switchable; it is not on.

Usage:
    from campaign_sprt import Sprt
    s = Sprt(p0=0.01, p1=0.10, alpha=0.05, beta=0.20)
    for observation in wave:  s.observe(defect=bool(...))
    s.verdict()   # 'accept-h0' (stop) | 'accept-h1' (keep looking) | 'continue'
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CONTINUE, ACCEPT_H0, ACCEPT_H1 = "continue", "accept-h0", "accept-h1"


@dataclass
class Sprt:
    """Wald's sequential probability ratio test over a stream of clean/defect observations."""
    p0: float = 0.01          # defect rate at which we are willing to stop
    p1: float = 0.10          # defect rate at which we must keep looking
    alpha: float = 0.05       # P(stop | the rate is really p1) -- the costly error
    beta: float = 0.20        # P(keep looking | the rate is really p0)
    llr: float = 0.0
    n: int = 0
    defects: int = 0
    history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (0.0 < self.p0 < self.p1 < 1.0):
            raise ValueError(f"require 0 < p0 < p1 < 1; got p0={self.p0}, p1={self.p1}")
        if not (0.0 < self.alpha < 1.0) or not (0.0 < self.beta < 1.0):
            raise ValueError("alpha and beta must be in (0, 1)")

    # ------------------------------------------------------------------ bounds

    @property
    def lower(self) -> float:
        return math.log(self.beta / (1.0 - self.alpha))

    @property
    def upper(self) -> float:
        return math.log((1.0 - self.beta) / self.alpha)

    # ------------------------------------------------------------- observation

    def observe(self, defect: bool) -> str:
        self.n += 1
        if defect:
            self.defects += 1
            self.llr += math.log(self.p1 / self.p0)
        else:
            self.llr += math.log((1.0 - self.p1) / (1.0 - self.p0))
        v = self.verdict()
        self.history.append(v)
        return v

    def verdict(self) -> str:
        if self.llr <= self.lower:
            return ACCEPT_H0
        if self.llr >= self.upper:
            return ACCEPT_H1
        return CONTINUE

    # ------------------------------------------------------------------ report

    def report(self) -> dict:
        return {
            "rule": "sprt",
            "p0": self.p0, "p1": self.p1, "alpha": self.alpha, "beta": self.beta,
            "n": self.n, "defects": self.defects,
            "llr": round(self.llr, 6),
            "bounds": [round(self.lower, 6), round(self.upper, 6)],
            "verdict": self.verdict(),
            "_note": ("alpha and beta are the ACTUAL error probabilities of this rule, "
                      "declared before the run -- which is what a consecutive-clean-rounds "
                      "count cannot offer. Applies to DEFECT-SEARCH closure only; coverage "
                      "closure is a set difference and takes no statistics."),
        }


def enabled(options: dict | None = None) -> bool:
    """`[opt:CAMPAIGN-SPRT]`, default OFF. Read from the toggle registry, never assumed."""
    if options is None:
        return False
    opt = (options.get("CAMPAIGN-SPRT") or {})
    return bool(opt.get("default") is True or opt.get("default") == "on")
