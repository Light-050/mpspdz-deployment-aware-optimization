"""
deployment_decision.py — EPPC Deployment Scenario Analysis
===========================================================
Paper:   "Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection"
Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu

This file implements the EPPC (Enhanced Privacy-Preserving Computation)
framework's Deployment Feasibility layer (Figure 1) and
generates the analytical deployment scenario predictions in Table 8
(the manuscript).

The five deployment scenarios correspond to Table 8 of the manuscript:
  Healthcare:   n=5,  M=10,000, B=100, H=600,  log_p=128
  Finance:      n=10, M=5,000,  B=50,  H=400,  log_p=128
  Government:   n=7,  M=8,000,  B=100, H=800,  log_p=128
  ML Inference: n=5,  M=50,000, B=100, H=400,  log_p=128
  IoT:          n=20, M=1,000,  B=200, H=200,  log_p=128

All scenarios use log_p=128 (Overdrive LowGear 2.0 default prime size).
BW_red = H/(H+128) x (1-1/B) x 100.

USAGE:
  python deployment_decision.py    # prints full Table 8 analysis
"""

from dataclasses import dataclass
from typing import List, Dict
from complexity_models import (
    ProtocolParams, full_comparison, OverdriveLG2,
    offline_bandwidth_mb, offline_time_seconds, bw_red_formula
)


# =============================================================================
# Deployment Scenario Definitions
# =============================================================================

@dataclass
class DeploymentScenario:
    """A real-world MPC deployment scenario for EPPC evaluation."""
    name: str
    domain: str
    n: int              # party count
    M: int              # multiplication count
    B: int              # DAPS-recommended batch size
    H: int              # header size in bits
    log_p: int          # field element size in bits
    network: str        # LAN / WAN / Cloud
    latency_ms: float   # typical network latency
    bandwidth_mbps: float  # available bandwidth
    ram_gb: float       # available RAM (for EPPC feasibility layer)
    description: str
    regulation: str     # applicable regulations


# Five scenarios from Table 8
# B values are DAPS recommendations (Algorithm 5, Table 11)
# All use log_p=128 (Overdrive LG2.0 default)
SCENARIOS = [
    DeploymentScenario(
        name="Healthcare",
        domain="Healthcare",
        n=5, M=10000, B=100, H=600, log_p=128,
        network="WAN", latency_ms=35.0, bandwidth_mbps=320.0,
        ram_gb=11.0,
        description="5 hospitals jointly analyzing genomic data for rare disease research",
        regulation="HIPAA, GDPR, Data Protection Act (Ghana)",
    ),
    DeploymentScenario(
        name="Finance",
        domain="Finance",
        n=10, M=5000, B=50, H=400, log_p=128,
        network="Cloud", latency_ms=5.0, bandwidth_mbps=5000.0,
        ram_gb=8.0,
        description="10 financial institutions computing aggregate risk metrics",
        regulation="Basel III, SOX, PCI DSS",
    ),
    DeploymentScenario(
        name="Government",
        domain="Government",
        n=7, M=8000, B=100, H=800, log_p=128,
        network="WAN", latency_ms=25.0, bandwidth_mbps=100.0,
        ram_gb=10.0,
        description="7 government agencies sharing intelligence without exposing sources",
        regulation="National security regulations, classification requirements",
    ),
    DeploymentScenario(
        name="ML Inference",
        domain="Machine Learning",
        n=5, M=50000, B=100, H=400, log_p=128,
        network="WAN", latency_ms=15.0, bandwidth_mbps=5000.0,
        ram_gb=11.0,
        description="5 data owners jointly evaluating a neural network on private data",
        regulation="GDPR, EU AI Act",
    ),
    DeploymentScenario(
        name="IoT",
        domain="IoT",
        n=20, M=1000, B=200, H=200, log_p=128,
        network="WAN", latency_ms=75.0, bandwidth_mbps=50.0,
        ram_gb=4.0,
        description="20 IoT gateway nodes securely aggregating sensor readings",
        regulation="IoT security standards, data minimisation",
    ),
]


# =============================================================================
# Analysis Functions
# =============================================================================

def analyze_scenario(scenario: DeploymentScenario) -> Dict:
    """Perform full EPPC analysis for one deployment scenario."""
    params = ProtocolParams(
        n=scenario.n, M=scenario.M, B=scenario.B,
        H=scenario.H, log_p=scenario.log_p,
        label=scenario.name,
    )

    comp = full_comparison(params)

    # Round-latency model (Equation 1): t = t_compute + rounds * latency
    # t_compute estimated from protocol parameters; rounds from Table 2
    baseline_time_s = (
        comp['baseline']['rounds'] * (scenario.latency_ms / 1000) +
        comp['baseline']['total_bits'] / (scenario.bandwidth_mbps * 1e6)
    )
    enhanced_time_s = (
        comp['enhanced']['rounds'] * (scenario.latency_ms / 1000) +
        comp['enhanced']['total_bits'] / (scenario.bandwidth_mbps * 1e6)
    )

    # BW_red formula verification
    bw_red_check = bw_red_formula(scenario.H, scenario.log_p, scenario.B)

    return {
        'scenario': scenario,
        'comparison': comp,
        'latency_model': {
            'baseline_s': baseline_time_s,
            'enhanced_s': enhanced_time_s,
            'speedup': baseline_time_s / max(enhanced_time_s, 1e-9),
            'time_saved_s': baseline_time_s - enhanced_time_s,
        },
        'offline': {
            'bandwidth_MB': offline_bandwidth_mb(scenario.M),
            'time_s': offline_time_seconds(scenario.M),
        },
        'bw_red_formula_check': bw_red_check,
        'eppc_assessment': generate_eppc_assessment(comp, scenario),
    }


def generate_eppc_assessment(comp: Dict, scenario: DeploymentScenario) -> str:
    """Generate EPPC-guided deployment assessment (5-layer framework)."""
    reduction = comp['improvement']['total_reduction_pct']
    header_red = comp['improvement']['header_reduction_pct']

    if reduction > 70:
        verdict = "STRONGLY RECOMMENDED"
    elif reduction > 50:
        verdict = "RECOMMENDED"
    elif reduction > 20:
        verdict = "CONDITIONALLY RECOMMENDED"
    else:
        verdict = "MARGINAL BENEFIT"

    lines = [
        f"EPPC Assessment — {scenario.name}",
        f"  Layer 1 (Security):     Active security preserved (Claim 1)",
        f"  Layer 2 (Complexity):   {comp['improvement']['message_factor']:.0f}x message reduction; "
        f"{reduction:.1f}% total BW reduction",
        f"  Layer 3 (Efficiency):   Header: {comp['baseline']['header_pct']:.1f}% -> "
        f"{comp['enhanced']['header_pct']:.1f}% of total",
        f"  Layer 4 (Feasibility):  RAM={scenario.ram_gb}GB; "
        f"Network={scenario.network} ({scenario.latency_ms}ms)",
        f"  Layer 5 (Compliance):   {scenario.regulation}",
        f"  Verdict:                {verdict} ({reduction:.1f}% BW reduction)",
        f"  Header reduction:       {header_red:.1f}% "
        f"(from {comp['baseline']['header_pct']:.1f}% to {comp['enhanced']['header_pct']:.1f}%)",
    ]
    return "\n".join(lines)


# =============================================================================
# Table 8 Generator
# =============================================================================

def generate_table8(scenarios: List[DeploymentScenario] = None) -> str:
    """Generate Table 8: Deployment Scenarios with DAPS-Recommended Parameters."""
    if scenarios is None:
        scenarios = SCENARIOS

    lines = [
        "=" * 85,
        "TABLE 8: Deployment Scenarios with DAPS-Recommended Parameters",
        "All scenarios: log_p = 128 bits (Overdrive LG2.0 default prime size)",
        "BW Red = H/(H+128) x (1-1/B) x 100",
        "=" * 85,
        f"{'Scenario':<14} {'n':>3} {'M':>6} {'B(DAPS)':>8} {'H':>5} "
        f"{'BL(MB)':>8} {'Enh(MB)':>8} {'Msg Red':>8} {'BW Red':>8}",
        "-" * 85,
    ]

    for sc in scenarios:
        analysis = analyze_scenario(sc)
        comp = analysis['comparison']
        bl_mb = comp['baseline']['total_MB']
        en_mb = comp['enhanced']['total_MB']
        msg_red = f"{comp['improvement']['message_factor']:.0f}x"
        bw_red = f"{comp['improvement']['total_reduction_pct']:.1f}%"
        formula_check = analysis['bw_red_formula_check']

        lines.append(
            f"{sc.name:<14} {sc.n:>3} {sc.M:>6,} {sc.B:>8} {sc.H:>5} "
            f"{bl_mb:>8.2f} {en_mb:>8.2f} {msg_red:>8} {bw_red:>8}"
        )

    lines += [
        "-" * 85,
        "",
        "Formula verification (BW_red = H/(H+128) x (1-1/B) x 100):",
    ]
    for sc in scenarios:
        check = bw_red_formula(sc.H, sc.log_p, sc.B)
        lines.append(
            f"  {sc.name:<14}: {sc.H}/({sc.H}+128) x (1-1/{sc.B}) x 100 = {check:.1f}%"
        )

    return "\n".join(lines)


def print_full_analysis(scenarios: List[DeploymentScenario] = None):
    """Print detailed EPPC analysis for each scenario."""
    if scenarios is None:
        scenarios = SCENARIOS

    for sc in scenarios:
        analysis = analyze_scenario(sc)
        comp = analysis['comparison']
        lat = analysis['latency_model']

        print(f"\n{'='*70}")
        print(f"  SCENARIO: {sc.name}")
        print(f"  {sc.description}")
        print(f"  Network: {sc.network} ({sc.latency_ms}ms, {sc.bandwidth_mbps} Mbps)")
        print(f"{'='*70}")

        b, e = comp['baseline'], comp['enhanced']
        imp = comp['improvement']

        print(f"\n  Online Phase Comparison (Table 2 applied):")
        print(f"    {'Metric':<30} {'Baseline':>12} {'Enhanced':>12}")
        print(f"    {'-'*54}")
        print(f"    {'Messages':<30} {b['messages']:>12,} {e['messages']:>12,}")
        print(f"    {'Rounds':<30} {b['rounds']:>12,} {e['rounds']:>12,}")
        print(f"    {'Total (MB)':<30} {b['total_MB']:>12.4f} {e['total_MB']:>12.4f}")
        print(f"    {'Header fraction':<30} {b['header_pct']:>11.1f}% {e['header_pct']:>11.1f}%")

        print(f"\n  Improvements:")
        print(f"    Total BW reduction:         {imp['total_reduction_pct']:.1f}%")
        print(f"    Header reduction:           {imp['header_reduction_pct']:.1f}%")
        print(f"    Message reduction:          {imp['message_factor']:.0f}x")

        print(f"\n  Round-Latency Model (Equation 1):")
        print(f"    Baseline:  {lat['baseline_s']:.2f} s")
        print(f"    Enhanced:  {lat['enhanced_s']:.2f} s")
        print(f"    Speedup:   {lat['speedup']:.1f}x ({lat['time_saved_s']:.2f} s saved)")

        print(f"\n  Offline Phase (Overdrive LG2.0):")
        off = analysis['offline']
        print(f"    Triple generation: {off['bandwidth_MB']:.3f} MB, {off['time_s']:.2f} s")

        print(f"\n  {analysis['eppc_assessment']}")


if __name__ == "__main__":
    print("EPPC Deployment Scenario Analysis")
    print("Implements Table 8 of the manuscript")
    print("=" * 70)

    print(generate_table8())

    print("\n\n" + "=" * 70)
    print("DETAILED SCENARIO ANALYSES")
    print("=" * 70)
    print_full_analysis()
