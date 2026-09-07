#!/usr/bin/env python3
"""
entity_scorer.py — dedup-neutral ENTITY-LEVEL NER scorer, FROZEN v1.

WHY THIS EXISTS
───────────────
The per-mention scorer (bench_ner.score_doc) counts every gold *occurrence*
independently. A system that emits each unique entity once (an LLM with an
entity resolver — e.g. SOLE) is therefore structurally penalised on recall
whenever a name repeats inside a document: gold has "Paris" ×3, the resolver
emits it once → per-mention recall 1/3 even though the entity was found. A
token-tagger (hmBERT, GLiNER) emits every mention and is not penalised.

This module adds a SUPPLEMENTARY entity-level metric that collapses both gold
and predictions to unique (normalised-surface, type) entities BEFORE matching,
so resolution-style and tagging-style systems are compared on equal footing.

It NEVER replaces the per-mention metric. Every run emits BOTH side by side
(see score_run_dual). The per-mention number stays the harness's primary,
backwards-comparable metric; the entity-level number is the fair supplement.

FROZEN v1 DEFINITION (see ENTITY_SCORER_VERSION)
────────────────────────────────────────────────
1. Neutral equivalence — two mentions are the SAME entity iff they share a key
   (normalize_surface(text), type), where
       normalize_surface(s) = " ".join((s or "").casefold().split())
   i.e. Unicode case-fold + whitespace collapse. This is corpus/system-neutral:
   it is NOT SOLE's resolver (no Levenshtein, no LLM, no gazetteer); it is the
   same rule applied identically to EVERY system and BOTH sides (gold & pred).
2. Dedup — within one document, collapse mentions to unique keys, retaining all
   occurrence spans of each unique entity.
3. Matching — RELAXED only (overlap + type): two unique entities match iff same
   type AND any occurrence span of one overlaps any occurrence span of the other.
   Greedy 1-1 bipartite, identical iteration order to bench_ner.score_doc.
4. Aggregation — MICRO (sum tp/fp/fn across docs, then F1 from totals), matching
   the harness convention.

⚠️  ANY change to (a) normalize_surface, (b) the type set / type mapping, (c) the
overlap predicate, or (d) greedy-vs-optimal matching is a BREAKING CHANGE. Bump
ENTITY_SCORER_VERSION and RE-BASELINE every saved number. Numbers tagged "v1" are
NOT comparable to numbers from any other version.

CONTROL INVARIANT (assert_token_tagger_control)
─────────────────────────────────────────────────
A token-tagger emits every mention, so dedup mostly collapses *correct* repeats
on both sides → its entity-level lift over per-mention must be SMALL. If a
token-tagger shows a large lift the scorer (or the adapter) is misbehaving. The
baseline harness asserts lift < 0.02 for token-taggers and FAILS LOUDLY.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

ENTITY_SCORER_VERSION = "v1"

# Token-tagger control: max acceptable entity-level lift over per-mention F1.
TOKEN_TAGGER_MAX_LIFT = 0.02


# ─── frozen neutral equivalence ──────────────────────────────────────────────


def normalize_surface(s: str | None) -> str:
    """FROZEN v1 neutral equivalence: Unicode case-fold + whitespace collapse.

    Changing this is a BREAKING CHANGE (bump ENTITY_SCORER_VERSION)."""
    return " ".join((s or "").casefold().split())


def _overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Half-open span overlap — identical predicate to bench_ner.score_doc."""
    return max(a[0], b[0]) < min(a[1], b[1])


# ─── per-mention scorer (self-contained mirror of bench_ner.score_doc) ───────
#
# Re-implemented here so entity_scorer is a standalone, frozen unit with zero
# heavy dependencies. test_entity_scorer.py PROVES parity with the live
# bench_ner.score_doc (the harness source of truth) so the two cannot drift.


def score_doc_permention(predicted: list[dict[str, Any]],
                         gold: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-mention strict (start+end+type) and relaxed (overlap+type) F1.

    Greedy 1-1, prediction-first iteration (predictions outer, gold inner) —
    byte-for-byte the same algorithm as
    bench_ner.score_doc, restricted to the {strict, relaxed} tp/fp/fn it needs."""

    def matches_strict(p, g):
        return p["start"] == g["start"] and p["end"] == g["end"] and p["type"] == g["type"]

    def matches_relaxed(p, g):
        if p["type"] != g["type"]:
            return False
        return max(p["start"], g["start"]) < min(p["end"], g["end"])

    def f1_for(matcher):
        matched_gold: set[int] = set()
        tp = 0
        for p in predicted:
            for gi, g in enumerate(gold):
                if gi in matched_gold:
                    continue
                if matcher(p, g):
                    tp += 1
                    matched_gold.add(gi)
                    break
        fp = len(predicted) - tp
        fn = len(gold) - tp
        return tp, fp, fn

    ts, fps, fns = f1_for(matches_strict)
    tr, fpr, fnr = f1_for(matches_relaxed)
    return {
        "strict": {"tp": ts, "fp": fps, "fn": fns},
        "relaxed": {"tp": tr, "fp": fpr, "fn": fnr},
        "n_predicted": len(predicted),
        "n_gold": len(gold),
    }


# ─── entity-level (dedup-neutral) scorer ─────────────────────────────────────


def dedup_entities(entities: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse mentions to unique (normalize_surface(text), type) within a doc,
    retaining every occurrence span. Insertion-ordered (first-seen key first) so
    greedy matching is deterministic."""
    groups: dict[tuple[str, str], list[tuple[int, int]]] = {}
    for e in entities:
        key = (normalize_surface(e.get("text", "")), e.get("type"))
        groups.setdefault(key, []).append((e["start"], e["end"]))
    return [{"key": k, "type": k[1], "spans": v} for k, v in groups.items()]


def score_doc_entity(predicted: list[dict[str, Any]],
                     gold: list[dict[str, Any]]) -> dict[str, Any]:
    """Entity-level RELAXED (overlap+type) F1 on deduplicated entities.

    Mirrors the per-mention relaxed matcher (greedy 1-1, prediction-first) but on
    unique entities; two unique entities match iff same type AND any of their
    occurrence spans overlap."""
    P = dedup_entities(predicted)
    G = dedup_entities(gold)

    def match(p, g):
        if p["type"] != g["type"]:
            return False
        return any(_overlap(ps, gs) for ps in p["spans"] for gs in g["spans"])

    matched_gold: set[int] = set()
    tp = 0
    for p in P:
        for gi, g in enumerate(G):
            if gi in matched_gold:
                continue
            if match(p, g):
                tp += 1
                matched_gold.add(gi)
                break
    fp = len(P) - tp
    fn = len(G) - tp
    return {
        "relaxed": {"tp": tp, "fp": fp, "fn": fn},
        "n_pred_entities": len(P),
        "n_gold_entities": len(G),
    }


# ─── micro aggregation + dual emit ───────────────────────────────────────────


def _prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": p, "recall": r, "f1": f, "tp": tp, "fp": fp, "fn": fn}


def score_run_dual(docs: Iterable[tuple[list[dict[str, Any]], list[dict[str, Any]]]]
                   ) -> dict[str, Any]:
    """Score a whole run, emitting per-mention AND entity-level side by side.

    `docs` is an iterable of (predicted, gold) pairs, one per document, already
    normalised (offsets valid, types mapped, filtered to the eval type set).
    Returns micro-aggregated metrics plus the entity-level lift over per-mention.
    """
    acc = {
        "pm_strict": [0, 0, 0],   # tp, fp, fn
        "pm_relaxed": [0, 0, 0],
        "ent_relaxed": [0, 0, 0],
    }
    n_docs = 0
    for predicted, gold in docs:
        n_docs += 1
        pm = score_doc_permention(predicted, gold)
        en = score_doc_entity(predicted, gold)
        for k, src in (("pm_strict", pm["strict"]), ("pm_relaxed", pm["relaxed"]),
                       ("ent_relaxed", en["relaxed"])):
            acc[k][0] += src["tp"]
            acc[k][1] += src["fp"]
            acc[k][2] += src["fn"]

    per_mention = {
        "strict": _prf(*acc["pm_strict"]),
        "relaxed": _prf(*acc["pm_relaxed"]),
    }
    entity_level = {"relaxed": _prf(*acc["ent_relaxed"])}
    lift = entity_level["relaxed"]["f1"] - per_mention["relaxed"]["f1"]
    return {
        "scorer_version": ENTITY_SCORER_VERSION,
        "n_docs": n_docs,
        "per_mention": per_mention,
        "entity_level": entity_level,
        "entity_lift_relaxed_f1": lift,
    }


def assert_token_tagger_control(result: dict[str, Any], system_name: str,
                                max_lift: float = TOKEN_TAGGER_MAX_LIFT) -> None:
    """Control invariant: a token-tagger's entity-level lift must be < max_lift.

    Raise (FAIL LOUDLY) otherwise — a large lift on a system that emits every
    mention means the scorer or the adapter is misbehaving, not that the metric
    is fair. Call this for every token-tagger system in the baseline harness."""
    lift = result["entity_lift_relaxed_f1"]
    if lift >= max_lift:
        raise AssertionError(
            f"TOKEN-TAGGER CONTROL FAILED for {system_name!r}: entity-level lift "
            f"{lift:+.3f} >= {max_lift} (per-mention relaxed F1="
            f"{result['per_mention']['relaxed']['f1']:.3f}, entity-level="
            f"{result['entity_level']['relaxed']['f1']:.3f}). A token-tagger emits "
            f"every mention, so dedup should barely move its score. Investigate the "
            f"adapter or the scorer before trusting any entity-level number."
        )


__all__ = [
    "ENTITY_SCORER_VERSION",
    "TOKEN_TAGGER_MAX_LIFT",
    "normalize_surface",
    "dedup_entities",
    "score_doc_permention",
    "score_doc_entity",
    "score_run_dual",
    "assert_token_tagger_control",
]
