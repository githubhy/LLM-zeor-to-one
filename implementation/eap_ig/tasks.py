"""Self-generated (templated) circuit tasks: IOI, Greater-Than, SVA.

Each builder returns a TaskBatch of clean+corrupt token ids and the answer indices/masks
needed by the task metric. No external dataset is downloaded (offline host). Single-token
answers are enforced against the live tokenizer so logit-diff / prob-diff are well-defined.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from . import metrics as _m
from .config import TaskConfig

# ---- word banks (filtered to single GPT-2 tokens at build time) ----------------
_NAMES = [" John", " Mary", " Tom", " James", " Robert", " Michael", " William",
          " David", " Richard", " Joseph", " Charles", " Thomas", " Daniel", " Paul",
          " Mark", " George", " Steven", " Edward", " Brian", " Kevin", " Jason",
          " Gary", " Jose", " Larry", " Frank", " Scott", " Eric", " Adam", " Henry",
          " Peter", " Walter", " Harold", " Carl", " Arthur", " Ryan", " Roger"]
_PLACES = [" store", " park", " school", " office", " hospital", " garden", " station",
           " market", " church", " library"]
_OBJECTS = [" drink", " book", " ball", " ring", " snack", " gift", " note", " coin",
            " card", " key"]
_EVENTS = [" war", " reign", " journey", " famine", " siege", " voyage", " drought",
           " feud", " plague", " project", " trial", " revolt", " boom", " crisis"]
# SVA singular/plural noun pairs
_NOUNS = [(" key", " keys"), (" dog", " dogs"), (" book", " books"), (" car", " cars"),
          (" tree", " trees"), (" star", " stars"), (" road", " roads"), (" bird", " birds"),
          (" wall", " walls"), (" game", " games"), (" king", " kings"), (" light", " lights"),
          (" river", " rivers"), (" door", " doors"), (" song", " songs"), (" farm", " farms")]
_PPS = [" near the door", " by the tree", " in the house", " behind the wall",
        " under the bridge", " on the table", " beside the road", " past the gate"]


@dataclass
class TaskBatch:
    clean_ids: torch.Tensor        # (B, T)
    corrupt_ids: torch.Tensor      # (B, T)
    attn_mask: torch.Tensor        # (B, T)  (1 = real token)
    last_idx: torch.Tensor         # (B,)    answer-prediction position
    metric_kind: str               # "logit_diff" | "prob_diff"
    pos_ids: torch.Tensor | None = None    # (B,)  logit_diff
    neg_ids: torch.Tensor | None = None
    pos_mask: torch.Tensor | None = None   # (B, V) prob_diff
    neg_mask: torch.Tensor | None = None

    def metric(self, logits: torch.Tensor) -> torch.Tensor:
        if self.metric_kind == "logit_diff":
            return _m.logit_diff(logits, self.last_idx, self.pos_ids, self.neg_ids)
        return _m.prob_diff(logits, self.last_idx, self.pos_mask, self.neg_mask)

    def to(self, device: str) -> "TaskBatch":
        for f in ("clean_ids", "corrupt_ids", "attn_mask", "last_idx",
                  "pos_ids", "neg_ids", "pos_mask", "neg_mask"):
            v = getattr(self, f)
            if v is not None:
                setattr(self, f, v.to(device))
        return self


def _single_token_id(tok, s: str) -> int | None:
    ids = tok.encode(s)
    return ids[0] if len(ids) == 1 else None


def _filter_single(tok, words: list[str]) -> list[tuple[str, int]]:
    out = []
    for w in words:
        tid = _single_token_id(tok, w)
        if tid is not None:
            out.append((w, tid))
    return out


def _pad_batch(tok, seqs: list[list[int]]) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Right-pad with eos; return ids, attn_mask, last_idx (true last content position)."""
    T = max(len(s) for s in seqs)
    pad = tok.eos_token_id
    ids, mask, last = [], [], []
    for s in seqs:
        last.append(len(s) - 1)
        ids.append(s + [pad] * (T - len(s)))
        mask.append([1] * len(s) + [0] * (T - len(s)))
    return (torch.tensor(ids, dtype=torch.long),
            torch.tensor(mask, dtype=torch.long),
            torch.tensor(last, dtype=torch.long))


def build_ioi(tok, cfg: TaskConfig) -> TaskBatch:
    rng = np.random.default_rng(cfg.seed)
    names = _filter_single(tok, _NAMES)
    places = _filter_single(tok, _PLACES)
    objs = _filter_single(tok, _OBJECTS)
    clean_seqs, corrupt_seqs, pos_ids, neg_ids = [], [], [], []
    for _ in range(cfg.n_examples):
        (io, io_id), (s, s_id), (c, c_id) = (names[i] for i in rng.choice(len(names), 3, replace=False))
        place, _p = places[rng.integers(len(places))]
        obj, _o = objs[rng.integers(len(objs))]
        clean = f"When{io} and{s} went to the{place},{s} gave a{obj} to"
        corrupt = f"When{io} and{s} went to the{place},{c} gave a{obj} to"
        clean_seqs.append(tok.encode(clean))
        corrupt_seqs.append(tok.encode(corrupt))
        pos_ids.append(io_id)   # correct = indirect object (appears once)
        neg_ids.append(s_id)    # foil = subject (appears twice)
    cids, cmask, clast = _pad_batch(tok, clean_seqs)
    xids, _xm, _xl = _pad_batch(tok, corrupt_seqs)
    # clean & corrupt differ by one name token -> equal length; reuse clean mask/last
    return TaskBatch(cids, xids, cmask, clast, "logit_diff",
                     pos_ids=torch.tensor(pos_ids), neg_ids=torch.tensor(neg_ids))


def _year_token_map(tok) -> dict[int, int]:
    """Map two-digit year YY (0..99) -> single token id for the continuation after '17'."""
    m = {}
    for yy in range(100):
        s = f"{yy:02d}"
        tid = _single_token_id(tok, s)   # e.g. "42" as a standalone continuation token
        if tid is not None:
            m[yy] = tid
    return m


def build_greater_than(tok, cfg: TaskConfig) -> TaskBatch:
    rng = np.random.default_rng(cfg.seed)
    events = _filter_single(tok, _EVENTS)
    ymap = _year_token_map(tok)
    valid_yy = sorted(ymap)
    V = len(tok)
    clean_seqs, corrupt_seqs, pos_masks, neg_masks = [], [], [], []
    # restrict start years so both sides have tokens
    starts = [y for y in valid_yy if sum(1 for z in valid_yy if z > y) >= 5
              and sum(1 for z in valid_yy if z <= y) >= 5]
    for _ in range(cfg.n_examples):
        ev, _e = events[rng.integers(len(events))]
        start = int(starts[rng.integers(len(starts))])
        cent = "17"
        clean = f"The{ev} lasted from the year {cent}{start:02d} to the year {cent}"
        corrupt = f"The{ev} lasted from the year {cent}01 to the year {cent}"
        clean_seqs.append(tok.encode(clean))
        corrupt_seqs.append(tok.encode(corrupt))
        pos = torch.zeros(V, dtype=torch.bool); neg = torch.zeros(V, dtype=torch.bool)
        for yy, tid in ymap.items():
            (pos if yy > start else neg)[tid] = True
        pos_masks.append(pos); neg_masks.append(neg)
    cids, cmask, clast = _pad_batch(tok, clean_seqs)
    xids, _xm, _xl = _pad_batch(tok, corrupt_seqs)
    return TaskBatch(cids, xids, cmask, clast, "prob_diff",
                     pos_mask=torch.stack(pos_masks), neg_mask=torch.stack(neg_masks))


def build_sva(tok, cfg: TaskConfig) -> TaskBatch:
    rng = np.random.default_rng(cfg.seed)
    nouns = [(sg, pl) for sg, pl in _NOUNS
             if _single_token_id(tok, sg) is not None and _single_token_id(tok, pl) is not None]
    are_id = _single_token_id(tok, " are"); is_id = _single_token_id(tok, " is")
    were_id = _single_token_id(tok, " were"); was_id = _single_token_id(tok, " was")
    V = len(tok)
    plural_ids = [i for i in (are_id, were_id) if i is not None]
    singular_ids = [i for i in (is_id, was_id) if i is not None]
    clean_seqs, corrupt_seqs, pos_masks, neg_masks = [], [], [], []
    for _ in range(cfg.n_examples):
        sg, pl = nouns[rng.integers(len(nouns))]
        pp = _PPS[rng.integers(len(_PPS))]
        clean = f"The{pl}{pp}"      # plural subject -> agreeing verb is plural (are/were)
        corrupt = f"The{sg}{pp}"    # singular subject
        clean_seqs.append(tok.encode(clean))
        corrupt_seqs.append(tok.encode(corrupt))
        pos = torch.zeros(V, dtype=torch.bool); neg = torch.zeros(V, dtype=torch.bool)
        for i in plural_ids: pos[i] = True     # agreeing (clean=plural)
        for i in singular_ids: neg[i] = True   # disagreeing
        pos_masks.append(pos); neg_masks.append(neg)
    cids, cmask, clast = _pad_batch(tok, clean_seqs)
    xids, _xm, _xl = _pad_batch(tok, corrupt_seqs)
    return TaskBatch(cids, xids, cmask, clast, "prob_diff",
                     pos_mask=torch.stack(pos_masks), neg_mask=torch.stack(neg_masks))


_BUILDERS = {"ioi": build_ioi, "greater_than": build_greater_than, "sva": build_sva}


def build_task(tok, cfg: TaskConfig) -> TaskBatch:
    return _BUILDERS[cfg.task](tok, cfg)
