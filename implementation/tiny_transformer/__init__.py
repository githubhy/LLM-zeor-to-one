"""Tiny-transformer induction study — reference implementation.

Drives `plans/2026-06-30-tiny-transformer-induction-study.md`: train a small
transformer from scratch, watch an induction head emerge, reproduce its head dump,
and verify Appendix-A's QK/OV-circuit math empirically — plus the full
mechanistic-interpretability observable suite (H1–H19).

Convention: the survey (appendix-A §A.1) uses the column convention x' = W x;
this code uses the equivalent row/data-matrix convention h' = h W (h a row
vector), so the QK bilinear form on embeddings is W_Q W_Kᵀ and the OV map is
W_V W_O. Circuits are extracted in this code convention and documented as such.
"""
__all__ = ["config", "data", "utils"]
