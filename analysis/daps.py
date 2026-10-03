"""
DAPS: Deployment-Aware Parameter Selection for SPDZ Protocols
=============================================================
Paper:   "Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection"
Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu

This file implements Algorithm 5 (DAPS) from the manuscript.
It is the primary DAPS implementation used for the evaluation results in the manuscript (Tables 11-13).


EVALUATION STRATEGY DESIGN:
  All three comparison strategies use the -n (no-merge) compiler flag,
  ensuring honest comparison on true protocol-level round counts.
  The compiler-merging artefact (~221 rounds vs ~20,219 true rounds) is
  documented separately as the motivating finding (Table 4).

  Strategy 1 — Unoptimized (-n):
    MASCOT backend, no batching (B=1), -n flag.
    Represents a practitioner who has disabled compiler merging to expose
    true protocol behavior but has not applied batching.
    Uses empirical BL round counts from Table 5 directly.

  Strategy 2 — Fixed-Batched (-n):
    MASCOT backend, fixed B=50, -n flag, regardless of scenario.
    Represents uniform batching without deployment-aware parameter selection.

  Strategy 3 — DAPS:
    Algorithm-selected backend (MASCOT or LowGear), B, and -n flag
    for each scenario. Represents deployment-aware optimization.

EMPIRICAL GROUNDING (April 2026 experiments, MP-SPDZ, WSL2 Ubuntu 24.04):
  - MASCOT: 12 configurations, 72 files, n=2,3,5,10 x M=100,1,000,10,000
  - LowGear: 5 configurations, 30 files, n=2,3,5 x M=1,000,10,000
  - Latency: 4 levels (0/10/50/100ms), n=2, M=10,000, -n flag
  - LowGear n=10: attempted, OOM at binomial key generation (empirically
    confirmed, 11 GB WSL2 allocation exhausted at binomial secret key gen)

KEY FINDING (Table 4):
  Default CISC compilation: ~221 rounds for M=10,000 at n=2
  No-merge (-n) compilation: ~20,219 rounds for M=10,000 at n=2
  Distortion ratio: ~91x
  This finding motivates mandatory use of the -n flag in all comparisons.

USAGE:
  python daps.py                    # runs all five deployment scenarios
  python daps.py --scenario custom  # prompts for custom parameters

DEPENDENCIES: Python 3.8+, no external libraries required.
"""

import sys
import math
from dataclasses import dataclass
from typing import List, Tuple

sys.stdout.reconfigure(encoding='utf-8')


# ==============================================================
# EMPIRICAL REFERENCE DATA
# All values from actual MP-SPDZ experiments (April 2026)
# Hardware: Intel i5-6200U, 16GB RAM, WSL2 Ubuntu 24.04
# All compiled with -n (no-merge) flag
# ==============================================================

# MASCOT empirical speedups (BL time / BA time): (n, M) -> speedup
# Source: Table 5 of manuscript
MASCOT_EMPIRICAL_SPEEDUP = {
    (2,  100):    1.00,
    (2,  1000):   1.45,
    (2,  10000):  1.72,
    (3,  100):    1.14,
    (3,  1000):   1.25,
    (3,  10000):  1.46,
    (5,  100):    1.08,
    (5,  1000):   1.25,
    (5,  10000):  1.22,
    (10, 100):    0.96,
    (10, 1000):   1.11,
    (10, 10000):  1.13,
}

# LowGear empirical speedups: (n, M) -> speedup
# Source: Table 6 of manuscript
LOWGEAR_EMPIRICAL_SPEEDUP = {
    (2,  1000):   1.02,
    (2,  10000):  1.14,
    (3,  10000):  1.15,
    (5,  1000):   1.10,
    (5,  10000):  1.24,
}

# Latency speedups (MASCOT, n=2, M=10,000, B=50, -n flag)
# Source: Table 7 of manuscript
LATENCY_EMPIRICAL_SPEEDUP = {
    0:   1.67,
    10:  20.07,
    50:  28.02,
    100: 29.38,
}

# Empirical round counts: ('backend', n, M) -> (BL_rounds, BA_rounds_at_B50)
# Source: Tables 5 and 6 of manuscript
EMPIRICAL_ROUNDS = {
    ('MASCOT', 2,  100):    (239,     43),
    ('MASCOT', 2,  1000):   (2039,    79),
    ('MASCOT', 2,  10000):  (20219,   619),
    ('MASCOT', 3,  100):    (465,     73),
    ('MASCOT', 3,  1000):   (4065,    145),
    ('MASCOT', 3,  10000):  (40371,   1171),
    ('MASCOT', 5,  100):    (917,     133),
    ('MASCOT', 5,  1000):   (8117,    277),
    ('MASCOT', 5,  10000):  (80676,   2275),
    ('MASCOT', 10, 100):    (2047,    283),
    ('MASCOT', 10, 1000):   (18247,   607),
    ('MASCOT', 10, 10000):  (181435,  5035),
    ('LowGear', 2,  1000):  (2775,    815),
    ('LowGear', 2,  10000): (20775,   1175),
    ('LowGear', 3,  10000): (41499,   2299),
    ('LowGear', 5,  1000):  (10947,   3107),
    ('LowGear', 5,  10000): (82947,   4547),
}

# Empirical execution times (3-run mean, seconds): ('backend', n, M, mode)
# Source: Tables 5 and 6 of manuscript. mode: 'BL'=baseline, 'BA'=batched
EMPIRICAL_TIMES = {
    ('MASCOT', 2,  100,   'BL'): 0.100,
    ('MASCOT', 2,  100,   'BA'): 0.100,
    ('MASCOT', 2,  1000,  'BL'): 0.718,
    ('MASCOT', 2,  1000,  'BA'): 0.494,
    ('MASCOT', 2,  10000, 'BL'): 5.322,
    ('MASCOT', 2,  10000, 'BA'): 3.086,
    ('MASCOT', 3,  100,   'BL'): 0.204,
    ('MASCOT', 3,  100,   'BA'): 0.180,
    ('MASCOT', 3,  1000,  'BL'): 1.408,
    ('MASCOT', 3,  1000,  'BA'): 1.127,
    ('MASCOT', 3,  10000, 'BL'): 7.956,
    ('MASCOT', 3,  10000, 'BA'): 5.462,
    ('MASCOT', 5,  100,   'BL'): 0.567,
    ('MASCOT', 5,  100,   'BA'): 0.527,
    ('MASCOT', 5,  1000,  'BL'): 6.068,
    ('MASCOT', 5,  1000,  'BA'): 4.873,
    ('MASCOT', 5,  10000, 'BL'): 34.213,
    ('MASCOT', 5,  10000, 'BA'): 28.079,
    ('MASCOT', 10, 100,   'BL'): 4.000,
    ('MASCOT', 10, 100,   'BA'): 4.162,
    ('MASCOT', 10, 1000,  'BL'): 16.701,
    ('MASCOT', 10, 1000,  'BA'): 14.984,
    ('MASCOT', 10, 10000, 'BL'): 100.542,
    ('MASCOT', 10, 10000, 'BA'): 89.093,
}

# Hardware RAM requirements (GB): ('backend', n) -> minimum RAM
# Source: Table 10 of manuscript. LowGear RAM scales with C(n,2) party pairs.
# LowGear n>=10: OOM confirmed empirically (binomial key generation).
HW_RAM_REQUIREMENTS = {
    ('MASCOT', 2):   1,
    ('MASCOT', 3):   2,
    ('MASCOT', 5):   4,
    ('MASCOT', 7):   6,    # interpolated between n=5 (4GB) and n=10 (8GB)
    ('MASCOT', 10):  8,
    ('MASCOT', 20):  16,   # extrapolated
    ('LowGear', 2):  2,
    ('LowGear', 3):  5,
    ('LowGear', 5):  11,
    ('LowGear', 7):  23,   # extrapolated: C(7,2)/C(5,2) * 11GB = 21/10 * 11 ≈ 23GB
    ('LowGear', 10): 999,  # infeasible: OOM at binomial key generation
    ('LowGear', 20): 999,  # infeasible
}

# Compiler merging discovery (Table 4)
# NOT used as a comparison baseline — documented as a motivating finding.
COMPILER_MERGED_ROUNDS_n2_M10k = 221   # default CISC compilation
TRUE_UNOPTIMIZED_ROUNDS_n2_M10k = 20219  # -n flag
COMPILER_DISTORTION_FACTOR = 91  # ~91x round difference


# ==============================================================
# DATA STRUCTURES
# ==============================================================

@dataclass
class DeploymentScenario:
    """A deployment scenario input to the DAPS algorithm (Definition 1)."""
    name: str
    n: int           # number of parties
    M: int           # number of multiplications
    latency_ms: float  # network latency in ms
    ram_gb: float    # available RAM in GB
    H: int = 400     # protocol header size in bits (default from Overdrive LG2.0)
    log_p: int = 128  # field element size in bits (Overdrive LG2.0 default)
    mode: str = 'compare'  # 'benchmark' | 'compare' | 'production'


@dataclass
class DAPSResult:
    """Output of the DAPS algorithm for one deployment scenario."""
    scenario: DeploymentScenario
    backend: str
    B: int
    compiler_flag: str
    bw_reduction_pct: float
    round_reduction: float
    predicted_speedup_LAN: float
    predicted_speedup_WAN: float
    warnings: List[str]
    rationale: List[str]
    stage_decisions: List[Tuple[str, str]]


# ==============================================================
# HELPER FUNCTIONS: ROUND COUNT ESTIMATION
# Scale empirical round counts to untested (n, M) combinations
# using the C(n,2) party-pair relationship.
# ==============================================================

def estimate_bl_rounds(backend: str, n: int, M: int) -> int:
    """
    Estimate BL (unoptimized, -n flag) round count for given backend, n, M.
    Uses exact empirical value if available; otherwise scales from
    nearest empirical point using M ratio and C(n,2) party-pair ratio.
    """
    key = (backend, n, M)
    if key in EMPIRICAL_ROUNDS:
        return EMPIRICAL_ROUNDS[key][0]

    available = [k for k in EMPIRICAL_ROUNDS if k[0] == backend]
    if not available:
        # Fallback: scale from MASCOT n=2, M=10000
        return max(1, int(20219 * (M / 10000) * (n * (n-1) / 2)))

    avail_n = sorted(set(k[1] for k in available))
    closest_n = min(avail_n, key=lambda x: abs(x - n))
    avail_M = sorted(set(k[2] for k in available if k[1] == closest_n))
    closest_M = min(avail_M, key=lambda x: abs(x - M))

    base_rounds = EMPIRICAL_ROUNDS[(backend, closest_n, closest_M)][0]
    m_scale = M / closest_M
    n_pairs_base = closest_n * (closest_n - 1) / 2
    n_pairs_target = n * (n - 1) / 2
    n_scale = n_pairs_target / n_pairs_base if n_pairs_base > 0 else 1.0

    return max(1, int(base_rounds * m_scale * n_scale))


def estimate_ba_rounds(backend: str, n: int, M: int, B: int) -> int:
    """
    Estimate BA (batched, -n flag) round count for given backend, n, M, B.
    Derives the round reduction ratio at B=50 from empirical data, then
    scales proportionally for the requested B.
    """
    bl = estimate_bl_rounds(backend, n, M)

    key = (backend, n, M)
    if key in EMPIRICAL_ROUNDS:
        bl_emp, ba_emp = EMPIRICAL_ROUNDS[key]
        rr_at_b50 = bl_emp / ba_emp if ba_emp > 0 else 32.7
    else:
        available = [k for k in EMPIRICAL_ROUNDS if k[0] == backend]
        if available:
            avail_n = sorted(set(k[1] for k in available))
            closest_n = min(avail_n, key=lambda x: abs(x - n))
            avail_M = sorted(set(k[2] for k in available if k[1] == closest_n))
            closest_M = min(avail_M, key=lambda x: abs(x - M))
            bl_e, ba_e = EMPIRICAL_ROUNDS[(backend, closest_n, closest_M)]
            rr_at_b50 = bl_e / ba_e if ba_e > 0 else 32.7
        else:
            rr_at_b50 = 32.7  # empirical default from n=2, M=10,000

    rr_at_B = rr_at_b50 * (B / 50)
    return max(2, int(bl / rr_at_B))


def estimate_time(backend: str, n: int, M: int,
                  mode: str, B: int, latency_ms: float) -> float:
    """
    Estimate total execution time: t_compute + rounds * latency_per_round.
    Uses exact empirical t_compute values where available; scales otherwise.
    Note: EMPIRICAL_TIMES holds MASCOT measurements only. For LowGear
    configurations the compute component is therefore scaled from the
    MASCOT n=2 measurement and excludes LowGear HE preprocessing (Table 12
    note). lowgear_sensitivity() reports the alternative using measured
    LowGear total times (Table 6).
    t_compute values are at 0ms latency (pure compute component).
    """
    if mode == 'BL':
        rounds = estimate_bl_rounds(backend, n, M)
        key = (backend, n, M, 'BL')
    else:
        rounds = estimate_ba_rounds(backend, n, M, B)
        key = (backend, n, M, 'BA')

    if key in EMPIRICAL_TIMES:
        t_compute = EMPIRICAL_TIMES[key]
    else:
        base_key = ('MASCOT', 2, 10000, mode)
        base_time = EMPIRICAL_TIMES.get(base_key, 5.322 if mode == 'BL' else 3.086)
        t_compute = base_time * (M / 10000) * ((n / 2) ** 0.6)

    return round(t_compute + (rounds * latency_ms) / 1000.0, 2)


# ==============================================================
# DAPS CORE ALGORITHM (Algorithm 5)
# Four sequential decision stages with empirically calibrated thresholds
# (Definition 1 is the guiding objective; DAPS does not solve it exactly).
# Time complexity: O(1)
# ==============================================================

def run_daps(scenario: DeploymentScenario) -> DAPSResult:
    """
    Deployment-Aware Parameter Selection — four stages.

    Stage 1: Backend selection (MASCOT vs LowGear)
             Grounded in empirical hardware feasibility (Table 10).
    Stage 2: Batch size selection
             Calibrated to empirical latency-speedup curve (Table 7).
    Stage 3: Compiler flag selection
             Mandatory -n for benchmark/compare; CISC for production.
    Stage 4: Predicted performance computation
             BW reduction formula from the manuscript Equation 1.
    """
    warnings = []
    rationale = []
    stage_decisions = []

    n, M, lat = scenario.n, scenario.M, scenario.latency_ms
    ram, H, log_p, mode = scenario.ram_gb, scenario.H, scenario.log_p, scenario.mode

    # ----------------------------------------------------------
    # STAGE 1: Backend Selection
    # Implements Definition 1 constraint C1: ram >= RAM_min(backend, n)
    # LowGear n>=10: infeasible regardless of RAM (OOM at binomial key gen)
    # ----------------------------------------------------------
    lg_ram = HW_RAM_REQUIREMENTS.get(('LowGear', n), 999)

    if n >= 10:
        backend = 'MASCOT'
        reason = (f"LowGear n={n} infeasible: OOM at binomial key generation "
                  f"(empirically confirmed, 11 GB WSL2 exhausted at n=10). "
                  f"MASCOT n=10 operates within 8 GB RAM.")
        warnings.append(f"LowGear unavailable at n>=10 on consumer hardware.")
    elif ram < lg_ram:
        backend = 'MASCOT'
        reason = (f"Insufficient RAM ({ram} GB) for LowGear at n={n} "
                  f"(requires ~{lg_ram} GB, Table 10). MASCOT selected.")
        warnings.append(f"LowGear requires ~{lg_ram} GB RAM at n={n}.")
    elif n == 5 and ram >= 11:
        backend = 'LowGear'
        reason = (f"LowGear feasible at n=5 ({ram} GB >= 11 GB). "
                  f"HE-based preprocessing; lower per-triple cost than MASCOT.")
        warnings.append("LowGear n=5: ~75 min key generation on consumer HW. "
                        "Cache keys; amortize across multiple computations.")
    elif n <= 3 and ram >= lg_ram:
        backend = 'LowGear'
        reason = (f"LowGear preferred: n={n} <= 3, RAM sufficient "
                  f"({ram} GB >= {lg_ram} GB). Lower per-triple HE cost.")
    else:
        backend = 'MASCOT'
        reason = "MASCOT: safe default. OT-based preprocessing; light RAM; fast key generation."

    rationale.append(f"Stage 1 — Backend: {backend}. {reason}")
    stage_decisions.append(("Backend", f"{backend} — {reason[:80]}..."))

    # ----------------------------------------------------------
    # STAGE 2: Batch Size Selection
    # Definition 1 guides this stage; under Equation 1 T is non-increasing in B,
    # so the practical operating points below are empirical calibration choices.
    # Thresholds calibrated to Table 7 empirical latency-speedup curve.
    # ----------------------------------------------------------
    if lat >= 50:
        B_ideal = 200
        b_reason = (f"High-latency WAN ({lat} ms): maximise round reduction. "
                    f"Empirical basis: 28.02x at 50 ms, 29.38x at 100 ms (Table 7).")
    elif lat >= 10:
        B_ideal = 100
        b_reason = (f"Medium-latency WAN ({lat} ms): strong round reduction. "
                    f"Empirical basis: 20.07x speedup at 10 ms (Table 7).")
    elif lat >= 1:
        B_ideal = 50
        b_reason = (f"Low-latency ({lat} ms): B=50 LAN default. "
                    f"Empirical basis: 1.67x speedup at 0 ms (Table 7). "
                    f"Achieves 74.2% BW reduction at H=400, log_p=128.")
    else:
        B_ideal = 50
        b_reason = "LAN/localhost: B=50 achieves 74.2% BW reduction."

    B = min(B_ideal, M)  # Constraint C2: B <= M
    if B < B_ideal:
        b_reason += f" (B capped at M={M} per constraint C2)"

    rationale.append(f"Stage 2 — Batch size: B={B}. {b_reason}")
    stage_decisions.append(("Batch Size", f"B={B} — {b_reason[:80]}..."))

    # ----------------------------------------------------------
    # STAGE 3: Compiler Flag Selection
    # Default CISC: ~221 rounds vs -n: ~20,219 rounds (91x distortion).
    # Any protocol-level comparison requires -n to expose true rounds.
    # ----------------------------------------------------------
    if mode in ('benchmark', 'compare'):
        flag = '-n'
        f_reason = (f"No-merge flag required: default CISC compilation produces "
                    f"~{COMPILER_MERGED_ROUNDS_n2_M10k} rounds vs "
                    f"~{TRUE_UNOPTIMIZED_ROUNDS_n2_M10k} true rounds at n=2, "
                    f"M=10,000 (~{COMPILER_DISTORTION_FACTOR}x distortion, Table 4). "
                    f"Masks all protocol-level differences between BL and BA.")
    else:
        flag = ''
        f_reason = ("Production mode: CISC default for fastest wall-clock time. "
                    "Use -n flag if benchmarking or comparing protocols.")

    rationale.append(f"Stage 3 — Compiler flag: '{flag}'. {f_reason}")
    stage_decisions.append(("Compiler Flag", f"'{flag}' — {f_reason[:80]}..."))

    # ----------------------------------------------------------
    # STAGE 4: Predicted Performance
    # BW_red formula from the manuscript; speedup from Table 7 interpolation.
    # ----------------------------------------------------------
    bw_reduction = (H / (H + log_p)) * (1 - 1.0 / B) * 100 if B > 0 else 0.0
    theoretical_round_red = B

    # Speedup interpolated from Table 7 empirical values
    if lat <= 0:
        pred_speedup = 1.67
    elif lat <= 10:
        pred_speedup = 1.67 + (lat / 10.0) * (20.07 - 1.67)
    elif lat <= 50:
        pred_speedup = 20.07 + ((lat - 10) / 40.0) * (28.02 - 20.07)
    elif lat <= 100:
        pred_speedup = 28.02 + ((lat - 50) / 50.0) * (29.38 - 28.02)
    else:
        pred_speedup = min(29.38 + (lat - 100) * 0.01, theoretical_round_red)

    b_scale = math.log(B + 1) / math.log(51)  # log scale: B=50 -> 1.0
    pred_speedup_WAN = min(pred_speedup * b_scale, theoretical_round_red)
    pred_speedup_LAN = min(1.67 * b_scale, theoretical_round_red)

    rationale.append(
        f"Stage 4 — BW reduction: {bw_reduction:.1f}%. "
        f"Nominal batching factor (rho = B): {theoretical_round_red}x. "
        f"Predicted speedup at {lat} ms: ~{pred_speedup_WAN:.1f}x."
    )
    stage_decisions.append(("Performance",
                             f"BW-{bw_reduction:.1f}%, "
                             f"rho={theoretical_round_red}, "
                             f"Speedup~{pred_speedup_WAN:.1f}x at {lat} ms"))

    return DAPSResult(
        scenario=scenario,
        backend=backend,
        B=B,
        compiler_flag=flag,
        bw_reduction_pct=round(bw_reduction, 1),
        round_reduction=theoretical_round_red,
        predicted_speedup_LAN=round(pred_speedup_LAN, 2),
        predicted_speedup_WAN=round(pred_speedup_WAN, 2),
        warnings=warnings,
        rationale=rationale,
        stage_decisions=stage_decisions,
    )


# ==============================================================
# STRATEGY BASELINES FOR VALIDATION
# All strategies use -n flag for honest comparison on true rounds.
# ==============================================================

def unoptimized_performance(scenario: DeploymentScenario) -> dict:
    """
    Strategy 1 — Unoptimized (-n):
    MASCOT, B=1, -n flag. Practitioner who exposes true protocol
    rounds but has not applied batching. Honest baseline.
    """
    n, M, lat = scenario.n, scenario.M, scenario.latency_ms
    rounds = estimate_bl_rounds('MASCOT', n, M)
    t_total = estimate_time('MASCOT', n, M, 'BL', 1, lat)
    return {
        'strategy': 'Unoptimized (-n)',
        'backend': 'MASCOT',
        'B': 1,
        'flag': '-n',
        'rounds': rounds,
        'predicted_time_s': t_total,
        'bw_reduction_pct': 0.0,
        'notes': 'True protocol rounds exposed; no batching applied'
    }


def fixed_batched_performance(scenario: DeploymentScenario) -> dict:
    """
    Strategy 2 — Fixed-Batched (-n):
    MASCOT, B=50 always, -n flag. Uniform batching without
    deployment-aware selection.
    """
    n, M, lat = scenario.n, scenario.M, scenario.latency_ms
    H, log_p = scenario.H, scenario.log_p
    B_fixed = 50
    rounds = estimate_ba_rounds('MASCOT', n, M, B_fixed)
    t_total = estimate_time('MASCOT', n, M, 'BA', B_fixed, lat)
    bw_reduction = (H / (H + log_p)) * (1 - 1.0 / B_fixed) * 100
    return {
        'strategy': 'Fixed-Batched (-n)',
        'backend': 'MASCOT',
        'B': B_fixed,
        'flag': '-n',
        'rounds': rounds,
        'predicted_time_s': t_total,
        'bw_reduction_pct': round(bw_reduction, 1),
        'notes': 'Uniform B=50; ignores latency, party count, and RAM context'
    }


def daps_performance(scenario: DeploymentScenario,
                     result: DAPSResult) -> dict:
    """
    Strategy 3 — DAPS:
    Algorithm-selected backend, B, -n flag. Deployment-aware parameter selection.
    """
    n, M, lat = scenario.n, scenario.M, scenario.latency_ms
    H, log_p = scenario.H, scenario.log_p
    B, backend = result.B, result.backend
    rounds = estimate_ba_rounds(backend, n, M, B)
    t_total = estimate_time(backend, n, M, 'BA', B, lat)
    bw_reduction = (H / (H + log_p)) * (1 - 1.0 / B) * 100
    return {
        'strategy': 'DAPS',
        'backend': backend,
        'B': B,
        'flag': result.compiler_flag,
        'rounds': rounds,
        'predicted_time_s': t_total,
        'bw_reduction_pct': round(bw_reduction, 1),
        'notes': f'Deployment-aware: {backend}, B={B}, flag={result.compiler_flag}'
    }


# ==============================================================
# COMPILER MERGING DOCUMENTATION (Table 4)
# Motivating finding — NOT a validation baseline.
# ==============================================================

def compiler_merging_impact() -> str:
    """Documents the compiler merging discovery (Table 4)."""
    lines = [
        "=" * 70,
        "COMPILER MERGING IMPACT (Table 4)",
        "=" * 70,
        "MP-SPDZ default CISC compilation merges open instructions,",
        "producing ~221 rounds instead of ~20,219 true rounds for",
        "M=10,000 at n=2. This ~91x distortion makes any comparison",
        "of baseline vs batched under default compilation invalid.",
        "All DAPS strategies therefore use the -n compiler flag.",
        "",
        f"  Config: MASCOT, n=2, M=10,000, B=50, 128-bit prime",
        f"  {'Compile Mode':<28} {'Rounds':>9}  {'Time (s)':>9}  Note",
        f"  {'-'*65}",
        f"  {'Default CISC (baseline)':<28} {'~221':>9}  {'3.19':>9}  "
        f"Compiler silently merges BL->BA",
        f"  {'No-merge (-n), Baseline':<28} {'~20,219':>9}  {'5.32':>9}  "
        f"True unoptimized protocol",
        f"  {'No-merge (-n), Batched':<28} {'~619':>9}  {'3.09':>9}  "
        f"True optimized protocol",
        f"  {'-'*65}",
        f"  Round difference (default vs -n BL): ~{COMPILER_DISTORTION_FACTOR}x",
        f"  Round reduction (-n BL vs BA):        ~32.7x",
        f"  Speedup (-n BL vs BA):                1.72x",
        "",
        "  Implication: experiments comparing default-compiled BL vs",
        "  batched BA compare functionally identical bytecode.",
        "  The -n flag is mandatory for all protocol-level comparisons.",
    ]
    return "\n".join(lines)


# ==============================================================
# REPORT GENERATORS
# ==============================================================

def generate_daps_report(scenario: DeploymentScenario) -> str:
    """Human-readable DAPS decision report for one scenario."""
    result = run_daps(scenario)
    lines = [
        f"\n{'='*70}",
        f"DAPS REPORT: {scenario.name}",
        f"{'='*70}",
        f"Input Parameters:",
        f"  Parties (n):          {scenario.n}",
        f"  Multiplications (M):  {scenario.M:,}",
        f"  Network latency:      {scenario.latency_ms} ms",
        f"  Available RAM:        {scenario.ram_gb} GB",
        f"  Header size (H):      {scenario.H} bits",
        f"  Field element (logp): {scenario.log_p} bits",
        f"  Mode:                 {scenario.mode}",
        f"",
        f"DAPS Recommendation (Algorithm 5):",
        f"  Backend:              {result.backend}",
        f"  Batch size (B):       {result.B}",
        f"  Compiler flag:        '{result.compiler_flag}'",
        f"",
        f"Predicted Performance:",
        f"  BW reduction:         {result.bw_reduction_pct}%",
        f"  Nominal batching factor (rho = B): {result.round_reduction}x",
        f"  Speedup (LAN 0 ms):   {result.predicted_speedup_LAN}x",
        f"  Speedup ({scenario.latency_ms} ms WAN): {result.predicted_speedup_WAN}x",
        f"",
        f"Stage-by-Stage Decision Rationale:",
    ]
    for stage, decision in result.stage_decisions:
        lines.append(f"  [{stage}] {decision}")
    if result.warnings:
        lines.append("")
        lines.append("Deployment Warnings:")
        for w in result.warnings:
            lines.append(f"  [!] {w}")
    return "\n".join(lines)


def generate_validation_table(scenarios: List[DeploymentScenario]) -> str:
    """
    Generates Table 12 (DAPS Validation) from the manuscript.
    All strategies use -n flag. Speedup ratios relative to Unoptimized.
    """
    lines = [
        "=" * 108,
        "TABLE 12: DAPS EVALUATION — Three-Strategy Performance Comparison",
        "All strategies use the -n compiler flag (true protocol-level round counts).",
        "Unoptimized: MASCOT, B=1, -n  |  Fixed-Batched: MASCOT, B=50, -n  |  DAPS: Algorithm 5",
        "=" * 108,
        f"{'Scenario':<14} {'n':>3} {'M':>6} {'Lat':>6} "
        f"{'Strategy':<20} {'Backend':<8} {'B':>4} "
        f"{'Rounds':>9} {'Time(s)':>9} {'BW%':>6} {'vs Unopt':>10}",
        "-" * 108,
    ]

    for scenario in scenarios:
        result = run_daps(scenario)
        un = unoptimized_performance(scenario)
        fb = fixed_batched_performance(scenario)
        dp = daps_performance(scenario, result)

        fb_vs_un = un['predicted_time_s'] / fb['predicted_time_s'] if fb['predicted_time_s'] > 0 else 1.0
        dp_vs_un = un['predicted_time_s'] / dp['predicted_time_s'] if dp['predicted_time_s'] > 0 else 1.0
        daps_vs_fb = fb['predicted_time_s'] / dp['predicted_time_s'] if dp['predicted_time_s'] > 0 else 1.0
        marker = ' †' if daps_vs_fb > 1.05 else ''

        rows = [
            (scenario.name, scenario.n, scenario.M, f"{scenario.latency_ms:.0f}ms",
             'Unoptimized (-n)', un['backend'], un['B'],
             un['rounds'], un['predicted_time_s'], un['bw_reduction_pct'], '1.00x (ref)'),
            ('', '', '', '',
             'Fixed-Batched (-n)', fb['backend'], fb['B'],
             fb['rounds'], fb['predicted_time_s'], fb['bw_reduction_pct'],
             f'{fb_vs_un:.2f}x'),
            ('', '', '', '',
             f'DAPS{marker}', dp['backend'], dp['B'],
             dp['rounds'], dp['predicted_time_s'], dp['bw_reduction_pct'],
             f'{dp_vs_un:.2f}x'),
        ]

        for i, row in enumerate(rows):
            nm, n, M, lat_s, strat, be, b, rnd, t, bw, vs = row
            lines.append(
                f"{nm:<14} {str(n):>3} {str(M):>6} {lat_s:>6} "
                f"{strat:<20} {be:<8} {b:>4} "
                f"{rnd:>9,} {t:>9.1f} {bw:>6.1f} {vs:>10}"
            )
        lines.append("-" * 108)

    lines += [
        "",
        "† DAPS is predicted to outperform Fixed-Batched by more than 5%.",
        "  In Finance, DAPS selects the same configuration as Fixed-Batched; in ML Inference,",
        "  its predicted time is within 0.1% of Fixed-Batched.",
        "  All values are model-based estimates from Equation 1 (see the Table 12 note).",
        "",
        "TABLE 13: DAPS PERFORMANCE SUMMARY",
        f"{'Scenario':<14} {'Unoptimized(s)':>15} {'Fixed-Batched(s)':>17} "
        f"{'DAPS(s)':>9} {'DAPS vs FB':>11} {'Advantage'}",
        "-" * 80,
    ]

    for scenario in scenarios:
        result = run_daps(scenario)
        un = unoptimized_performance(scenario)
        fb = fixed_batched_performance(scenario)
        dp = daps_performance(scenario, result)
        daps_vs_fb = fb['predicted_time_s'] / dp['predicted_time_s'] if dp['predicted_time_s'] > 0 else 1.0
        marker = ' †' if daps_vs_fb > 1.05 else ''
        adv = "Backend + B selection" if result.backend == 'LowGear' else \
              f"B selection ({result.B} vs 50)" if result.B != 50 else "Same configuration as Fixed-Batched"
        lines.append(
            f"{scenario.name:<14} {un['predicted_time_s']:>15.1f} "
            f"{fb['predicted_time_s']:>17.1f} "
            f"{dp['predicted_time_s']:>9.1f} {daps_vs_fb:>9.2f}x{marker}  {adv}"
        )

    return "\n".join(lines)


# ==============================================================
# FIVE DEPLOYMENT SCENARIOS (Table 11)
# ==============================================================

MANUSCRIPT_SCENARIOS = [
    DeploymentScenario(
        name="Healthcare", n=5, M=10000,
        latency_ms=35.0, ram_gb=11.0,
        H=600, log_p=128, mode='compare'
    ),
    DeploymentScenario(
        name="Finance", n=10, M=5000,
        latency_ms=5.0, ram_gb=8.0,
        H=400, log_p=128, mode='compare'
    ),
    DeploymentScenario(
        name="Government", n=7, M=8000,
        latency_ms=25.0, ram_gb=10.0,
        H=800, log_p=128, mode='compare'
    ),
    DeploymentScenario(
        name="ML Inference", n=5, M=50000,
        latency_ms=15.0, ram_gb=11.0,
        H=400, log_p=128, mode='compare'
    ),
    DeploymentScenario(
        name="IoT", n=20, M=1000,
        latency_ms=75.0, ram_gb=4.0,
        H=200, log_p=128, mode='compare'
    ),
]



# ==============================================================
# SENSITIVITY: LowGear compute basis (reported with Table 13)
# ==============================================================

def lowgear_sensitivity() -> str:
    """
    Re-evaluates the two LowGear scenarios using the measured LowGear total
    time including HE preprocessing (Table 6: n=5, M=10,000, BA = 79.217 s),
    extrapolated linearly to M=50,000 from the measured M=1,000 (77.174 s)
    and M=10,000 points. Reproduces the 158.8 s and 258.8 s values in the text.
    """
    saved = dict(EMPIRICAL_TIMES)
    try:
        EMPIRICAL_TIMES[('LowGear', 5, 10000, 'BA')] = 79.217
        EMPIRICAL_TIMES[('LowGear', 5, 50000, 'BA')] = round(79.217 + 40000 * (79.217 - 77.174) / 9000, 3)
        lines = ["LOWGEAR COMPUTE-BASIS SENSITIVITY (measured LowGear totals incl. HE preprocessing)",
                 "-" * 80]
        for sc in MANUSCRIPT_SCENARIOS:
            res = run_daps(sc)
            if res.backend != 'LowGear':
                continue
            fb = fixed_batched_performance(sc)['predicted_time_s']
            dp = daps_performance(sc, res)['predicted_time_s']
            lines.append(f"  {sc.name:<14} DAPS {dp:8.1f} s   Fixed-Batched {fb:8.1f} s   ratio {fb/dp:5.2f}x")
        lines.append("  Government and IoT use MASCOT and are unaffected by this assumption.")
        return "\n".join(lines)
    finally:
        EMPIRICAL_TIMES.clear(); EMPIRICAL_TIMES.update(saved)

# ==============================================================
# MAIN
# ==============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("DAPS: Deployment-Aware Parameter Selection for SPDZ Protocols")
    print("Paper: Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection")
    print("Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu")
    print("All strategies use -n flag (true protocol-level round counts)")
    print("=" * 70)

    # the manuscript: Compiler merging discovery
    print("\n")
    print(compiler_merging_impact())

    # Individual DAPS reports (Table 11)
    print("\n\nINDIVIDUAL DAPS SCENARIO REPORTS (Table 11 rationale):")
    for scenario in MANUSCRIPT_SCENARIOS:
        print(generate_daps_report(scenario))

    # Evaluation tables (Tables 12 and 13)
    print("\n\n")
    print(generate_validation_table(MANUSCRIPT_SCENARIOS))
    print("\n")
    print(lowgear_sensitivity())

    # Custom scenario demo
    print("\n\n" + "=" * 70)
    print("CUSTOM SCENARIO DEMO: Cross-Border Financial Settlement")
    print("=" * 70)
    custom = DeploymentScenario(
        name="Cross-Border", n=3, M=20000,
        latency_ms=80.0, ram_gb=8.0,
        H=400, log_p=128, mode='compare'
    )
    print(generate_daps_report(custom))
