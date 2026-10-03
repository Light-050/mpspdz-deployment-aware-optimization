"""
complexity_models.py — Communication Complexity Models for Enhanced SPDZ Protocol
==================================================================================
Paper:   "Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection"
Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu

This file implements:
  - Algorithm 2 (Baseline SPDZ Multiplication)
  - Algorithm 3 (Enhanced SPDZ Batched Multiplication)

It provides the complexity model underlying Table 2 (Complexity Comparison)
and the bandwidth reduction formula from the manuscript:
  BW_red = H/(H + log_p) x (1 - 1/B) x 100%

Base paper (offline phase parameters):
  Reisert et al. (2023). Overdrive LowGear 2.0: Reduced-Bandwidth MPC
  without Sacrifice. ACM AsiaCCS 2023. DOI: 10.1145/3579856.3582809

USAGE:
  python complexity_models.py               # runs built-in examples
  from complexity_models import full_comparison, ProtocolParams
"""

import math
from dataclasses import dataclass
from typing import Dict


# =============================================================================
# Overdrive LowGear 2.0 Empirical Parameters
# Source: Reisert et al. (2023), Tables 1, 8 and the manuscript
# =============================================================================

class OverdriveLG2:
    """Concrete parameters from Reisert et al. (2023)."""

    # Triple generation bandwidth (Table 8)
    TRIPLE_KBIT_SEC40  = 6.875    # kbit per triple, statistical security 40
    TRIPLE_KBIT_SEC64  = 7.783    # kbit per triple, statistical security 64
    TRIPLE_KBIT_SEC128 = 8.691    # kbit per triple, statistical security 128

    # Triple throughput — single core (Table 8)
    THROUGHPUT_SEC40  = 25778     # triples/second
    THROUGHPUT_SEC64  = 21382
    THROUGHPUT_SEC128 = 17012

    # Protocol structure (Table 1)
    ROUNDS_PI_TRIPLE = 2          # communication rounds per batch in Pi_Triple
    CIPHERTEXTS_PER_PAIR = 6      # 5 data + 1 ZKP amortized

    # Cryptographic setup
    PRIME_BITS = 128              # |p| = 128 bits
    CIPHERTEXT_MOD_BITS = 383     # |q| = 383 bits
    PLAINTEXT_SLOTS = 8192        # N = phi(m) = 8192
    STAT_SECURITY = 40            # default statistical security parameter

    # Improvements vs original Overdrive LowGear
    OFFLINE_BW_REDUCTION = 0.33   # 33% offline bandwidth reduction
    OFFLINE_RUNTIME_SPEEDUP = 3.80  # ~3.8x faster offline phase


# =============================================================================
# Protocol Parameters
# =============================================================================

@dataclass
class ProtocolParams:
    """Parameters for a specific SPDZ deployment configuration."""
    n: int       # number of parties
    M: int       # number of multiplication gates
    B: int       # batch size (Algorithm 3)
    H: int       # protocol header size per message (bits)
    log_p: int   # field element size = log2(p) (bits)
    label: str = ""  # descriptive label for output


# =============================================================================
# Algorithm 2: Baseline SPDZ Multiplication
# Two messages and two rounds per multiplication gate.
# =============================================================================

def baseline_messages(p: ProtocolParams) -> int:
    """2M messages total (2 per multiplication)."""
    return 2 * p.M

def baseline_total_bits(p: ProtocolParams) -> int:
    """Total: 2M * n * (H + log_p) bits."""
    return 2 * p.M * p.n * (p.H + p.log_p)

def baseline_header_bits(p: ProtocolParams) -> int:
    """Header component: 2M * n * H bits."""
    return 2 * p.M * p.n * p.H

def baseline_data_bits(p: ProtocolParams) -> int:
    """Data component (information-theoretically optimal): 2M * n * log_p bits."""
    return 2 * p.M * p.n * p.log_p

def baseline_rounds(p: ProtocolParams) -> int:
    """2M communication rounds."""
    return 2 * p.M


# =============================================================================
# Algorithm 3: Enhanced SPDZ Batched Multiplication
# Two messages and two rounds per BATCH of B multiplications.
# Data payload unchanged from baseline (information-theoretically optimal).
# =============================================================================

def num_batches(p: ProtocolParams) -> int:
    """ceil(M / B)."""
    return math.ceil(p.M / p.B)

def enhanced_messages(p: ProtocolParams) -> int:
    """2 * ceil(M/B) messages total. Factor-B reduction from baseline."""
    return 2 * num_batches(p)

def enhanced_total_bits(p: ProtocolParams) -> int:
    """Total: 2*ceil(M/B) * n * (H + B*log_p) bits."""
    return 2 * num_batches(p) * p.n * (p.H + p.B * p.log_p)

def enhanced_header_bits(p: ProtocolParams) -> int:
    """Header component: 2*ceil(M/B) * n * H bits. Factor-B reduction."""
    return 2 * num_batches(p) * p.n * p.H

def enhanced_data_bits(p: ProtocolParams) -> int:
    """Data component: 2*ceil(M/B) * B * n * log_p bits. IDENTICAL to baseline."""
    return 2 * num_batches(p) * p.B * p.n * p.log_p

def enhanced_rounds(p: ProtocolParams) -> int:
    """2 * ceil(M/B) communication rounds. Factor-B reduction from baseline."""
    return 2 * num_batches(p)


# =============================================================================
# Improvement Metrics (Table 2)
# =============================================================================

def header_reduction_pct(p: ProtocolParams) -> float:
    """Percentage reduction in header overhead (Factor B)."""
    bh = baseline_header_bits(p)
    return (1.0 - enhanced_header_bits(p) / bh) * 100.0 if bh else 0.0

def total_reduction_pct(p: ProtocolParams) -> float:
    """Percentage reduction in total bandwidth (BW_red formula)."""
    bt = baseline_total_bits(p)
    return (1.0 - enhanced_total_bits(p) / bt) * 100.0 if bt else 0.0

def bw_red_formula(H: int, log_p: int, B: int) -> float:
    """
    Direct application of BW_red formula from the manuscript:
    BW_red = H/(H + log_p) x (1 - 1/B) x 100%
    """
    return (H / (H + log_p)) * (1 - 1.0 / B) * 100.0


# =============================================================================
# Offline Phase Cost (Overdrive LowGear 2.0)
# =============================================================================

def offline_bandwidth_mb(M: int, sec: int = 40) -> float:
    """Offline bandwidth to generate M triples via Overdrive LG2.0 (MB)."""
    kbit = {40: OverdriveLG2.TRIPLE_KBIT_SEC40,
            64: OverdriveLG2.TRIPLE_KBIT_SEC64,
            128: OverdriveLG2.TRIPLE_KBIT_SEC128}.get(sec, OverdriveLG2.TRIPLE_KBIT_SEC40)
    return (M * kbit * 1000) / 8 / 1024 / 1024

def offline_time_seconds(M: int, sec: int = 40) -> float:
    """Time to generate M triples via Overdrive LG2.0 (seconds, single core)."""
    tput = {40: OverdriveLG2.THROUGHPUT_SEC40,
            64: OverdriveLG2.THROUGHPUT_SEC64,
            128: OverdriveLG2.THROUGHPUT_SEC128}.get(sec, OverdriveLG2.THROUGHPUT_SEC40)
    return M / tput


# =============================================================================
# Full Comparison (Table 2 generator)
# =============================================================================

def full_comparison(p: ProtocolParams) -> Dict:
    """Generate complete comparison dictionary for one parameter set."""
    b_total = baseline_total_bits(p)
    b_header = baseline_header_bits(p)
    b_data = baseline_data_bits(p)
    e_total = enhanced_total_bits(p)
    e_header = enhanced_header_bits(p)
    e_data = enhanced_data_bits(p)

    return {
        'label': p.label,
        'n': p.n, 'M': p.M, 'B': p.B, 'H': p.H, 'log_p': p.log_p,
        'baseline': {
            'messages': baseline_messages(p),
            'rounds': baseline_rounds(p),
            'total_bits': b_total,
            'header_bits': b_header,
            'data_bits': b_data,
            'header_pct': (b_header / b_total * 100) if b_total else 0,
            'total_MB': b_total / 8 / 1024 / 1024,
        },
        'enhanced': {
            'messages': enhanced_messages(p),
            'rounds': enhanced_rounds(p),
            'batches': num_batches(p),
            'total_bits': e_total,
            'header_bits': e_header,
            'data_bits': e_data,
            'header_pct': (e_header / e_total * 100) if e_total else 0,
            'total_MB': e_total / 8 / 1024 / 1024,
        },
        'improvement': {
            'message_factor': baseline_messages(p) / max(enhanced_messages(p), 1),
            'round_factor': baseline_rounds(p) / max(enhanced_rounds(p), 1),
            'header_reduction_pct': header_reduction_pct(p),
            'total_reduction_pct': total_reduction_pct(p),
        },
        'offline': {
            'triples_needed': p.M,
            'bandwidth_MB': offline_bandwidth_mb(p.M),
            'generation_time_s': offline_time_seconds(p.M),
        },
    }


def print_comparison(p: ProtocolParams):
    """Print formatted Table 2 comparison for one parameter set."""
    r = full_comparison(p)
    b, e, imp = r['baseline'], r['enhanced'], r['improvement']

    print(f"\n{'='*70}")
    print(f"  {r['label']}")
    print(f"  n={p.n}, M={p.M:,}, B={p.B}, H={p.H}, log_p={p.log_p}")
    print(f"{'='*70}")

    fmt = "  {:<35} {:>15} {:>15}"
    print(fmt.format('Metric', 'Baseline (Alg.2)', 'Enhanced (Alg.3)'))
    print(f"  {'-'*65}")
    print(fmt.format('Messages', f"{b['messages']:,}", f"{e['messages']:,}"))
    print(fmt.format('Rounds', f"{b['rounds']:,}", f"{e['rounds']:,}"))
    print(fmt.format('Total bits', f"{b['total_bits']:,}", f"{e['total_bits']:,}"))
    print(fmt.format('Header bits', f"{b['header_bits']:,}", f"{e['header_bits']:,}"))
    print(fmt.format('Data bits', f"{b['data_bits']:,}", f"{e['data_bits']:,}"))
    print(fmt.format('Header fraction', f"{b['header_pct']:.1f}%", f"{e['header_pct']:.1f}%"))
    print(fmt.format('Total (MB)', f"{b['total_MB']:.4f}", f"{e['total_MB']:.4f}"))

    print(f"\n  Table 2 Improvements (Factor-B reduction):")
    print(f"    Message reduction:         {imp['message_factor']:.1f}x (= B = {p.B})")
    print(f"    Round reduction:           {imp['round_factor']:.1f}x (= B = {p.B})")
    print(f"    Header reduction:          {imp['header_reduction_pct']:.1f}%")
    print(f"    Total bandwidth reduction: {imp['total_reduction_pct']:.1f}%")
    print(f"    Data payload:              UNCHANGED (information-theoretically optimal)")

    bw_formula = bw_red_formula(p.H, p.log_p, p.B)
    print(f"\n  BW_red formula check: H/(H+log_p)*(1-1/B)*100 = "
          f"{p.H}/({p.H}+{p.log_p})*(1-1/{p.B})*100 = {bw_formula:.1f}%")

    off = r['offline']
    print(f"\n  Overdrive LG2.0 Offline Phase (complementary):")
    print(f"    Triples needed:            {off['triples_needed']:,}")
    print(f"    Offline bandwidth:         {off['bandwidth_MB']:.4f} MB")
    print(f"    Generation time (1 core):  {off['generation_time_s']:.2f} s")


if __name__ == "__main__":
    print("SPDZ Communication Complexity Models")
    print("Implements Algorithms 2 and 3 from the manuscript")
    print("Grounded in Overdrive LowGear 2.0 (Reisert et al., AsiaCCS 2023)")
    print("=" * 70)

    # Reproduce Table 2 for key configurations
    print_comparison(ProtocolParams(
        n=2, M=10000, B=50, H=400, log_p=128,
        label="Table 2: n=2, M=10,000, B=50 (Overdrive LG2.0 default prime)"))

    print_comparison(ProtocolParams(
        n=2, M=1000, B=50, H=400, log_p=128,
        label="n=2, M=1,000, B=50 (Listing 1 configuration)"))

    # Healthcare scenario (Table 8)
    print_comparison(ProtocolParams(
        n=5, M=10000, B=100, H=600, log_p=128,
        label="Healthcare (Table 8): n=5, M=10,000, B=100, H=600"))
