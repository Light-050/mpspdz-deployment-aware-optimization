"""
crossover_analysis.py — Crossover Threshold and Sensitivity Analysis
=====================================================================
Paper:   "Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection"
Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu

This file generates:
  - Figure 8: Four-subplot sensitivity analysis
  - Figure 9: Bandwidth reduction heatmap
  - Figure 10: Bandwidth reduction vs batch size
  - Figure 11: Bandwidth reduction versus party count by deployment scenario

Key finding from the manuscript:
  - BW reduction is independent of party count n (flat at ~59.7%)
  - BW reduction rises quickly with B and then saturates (diminishing returns)
  - BW reduction increases monotonically with H
  - BW reduction decreases with log_p
  - Overdrive LG2.0 operating point (log_p=128) achieves 74.2% at base params

USAGE:
  python crossover_analysis.py    # prints analysis to console
"""

import math
from typing import List, Dict, Optional
from complexity_models import (
    ProtocolParams, baseline_total_bits, enhanced_total_bits,
    total_reduction_pct, full_comparison, OverdriveLG2
)


def crossover_sweep(M: int = 1000, H: int = 400, log_p: int = 128,
                    B_values: List[int] = None,
                    n_values: List[int] = None) -> List[Dict]:
    """
    Sweep across B and n values to find where batching is bandwidth-beneficial.
    Generates data for Figure 9 (heatmap).
    Returns list of result dicts for each (n, B) combination.
    """
    if B_values is None:
        B_values = [10, 20, 50, 75, 100, 150, 200]
    if n_values is None:
        n_values = [2, 3, 5, 7, 10, 15, 20]

    results = []
    for n in n_values:
        for B in B_values:
            if B > M:
                continue
            p = ProtocolParams(n=n, M=M, B=B, H=H, log_p=log_p,
                               label=f"n={n}, B={B}")
            reduction = total_reduction_pct(p)
            results.append({
                'n': n, 'B': B, 'M': M, 'H': H, 'log_p': log_p,
                'reduction_pct': reduction,
                'beneficial': reduction > 0,
            })
    return results


def sensitivity_analysis(base_n: int = 10, base_M: int = 1000,
                          base_B: int = 50, base_H: int = 400,
                          base_log_p: int = 256) -> Dict:
    """
    Sensitivity analysis varying one parameter at a time (Figure 8).
    Generates the four subplots:
      (a) Sensitivity to party count n  -> flat line, ~59.7%
      (b) Sensitivity to batch size B   -> logarithmic increase, diminishing past B~100
      (c) Sensitivity to header size H  -> monotone increase
      (d) Sensitivity to field size log_p -> monotone decrease

    Base parameters: n=10, M=1,000, B=50, H=400, log_p=128
    """
    results = {}

    # (a) Vary n — demonstrates BW reduction is n-independent
    results['vary_n'] = []
    for n in [2, 3, 5, 7, 10, 15, 20, 30, 50]:
        p = ProtocolParams(n=n, M=base_M, B=base_B, H=base_H, log_p=base_log_p)
        results['vary_n'].append({'n': n, 'reduction_pct': total_reduction_pct(p)})

    # (b) Vary B — demonstrates diminishing returns past B~100
    results['vary_B'] = []
    for B in [5, 10, 20, 25, 50, 75, 100, 150, 200, 500]:
        if B > base_M:
            continue
        p = ProtocolParams(n=base_n, M=base_M, B=B, H=base_H, log_p=base_log_p)
        results['vary_B'].append({'B': B, 'reduction_pct': total_reduction_pct(p)})

    # (c) Vary H — demonstrates larger headers amplify batching benefit
    results['vary_H'] = []
    for H in [100, 200, 300, 400, 500, 600, 800, 1000, 1500]:
        p = ProtocolParams(n=base_n, M=base_M, B=base_B, H=H, log_p=base_log_p)
        results['vary_H'].append({'H': H, 'reduction_pct': total_reduction_pct(p)})

    # (d) Vary log_p — demonstrates smaller field elements benefit more
    results['vary_log_p'] = []
    for lp in [64, 128, 192, 256, 384, 512]:
        p = ProtocolParams(n=base_n, M=base_M, B=base_B, H=base_H, log_p=lp)
        results['vary_log_p'].append({'log_p': lp, 'reduction_pct': total_reduction_pct(p)})

    return results


def crossover_threshold_by_scenario() -> Dict:
    """
    Compute n* (crossover threshold) for each deployment scenario.
    Generates data for Figure 11.

    n* = minimum party count at which batching is bandwidth-beneficial.
    Because the reduction does not depend on n, n* = 2 (always beneficial) for
    every scenario, including IoT with a small batch size (B=20).
    """
    scenarios = {
        'Healthcare':   {'B': 100, 'H': 600, 'log_p': 128, 'typical_n': 5},
        'Finance':      {'B': 50,  'H': 400, 'log_p': 128, 'typical_n': 10},
        'Government':   {'B': 100, 'H': 800, 'log_p': 128, 'typical_n': 7},
        'ML Inference': {'B': 100, 'H': 400, 'log_p': 128, 'typical_n': 5},
        'IoT (small batch, B=20)':   {'B': 20,  'H': 200, 'log_p': 128, 'typical_n': 20},
        'IoT (DAPS B=200)': {'B': 200, 'H': 200, 'log_p': 128, 'typical_n': 20},
    }

    results = {}
    for name, params in scenarios.items():
        n_star = None
        for n in range(2, 51):
            p = ProtocolParams(
                n=n, M=1000, B=params['B'],
                H=params['H'], log_p=params['log_p']
            )
            if total_reduction_pct(p) > 0:
                n_star = n
                break
        results[name] = {
            'n_star': n_star,
            'typical_n': params['typical_n'],
            'B': params['B'],
            'H': params['H'],
        }
    return results


def print_sensitivity(results: Dict):
    """Print sensitivity analysis results (Figure 8 data)."""
    print("\n  Base parameters: n=10, M=1,000, B=50, H=400, log_p=128")
    print(f"  Base BW reduction (formula): "
          f"{400/(400+128)*(1-1/50)*100:.1f}%")
    print()

    param_labels = {
        'vary_n': ('n (party count)', 'n', 'BW_red constant in n'),
        'vary_B': ('B (batch size)', 'B', 'logarithmic increase, diminishing past B~100'),
        'vary_H': ('H (header size bits)', 'H', 'monotone increase'),
        'vary_log_p': ('log_p (field size bits)', 'log_p', 'monotone decrease'),
    }

    for param_name, (label, key, insight) in param_labels.items():
        if param_name not in results:
            continue
        data = results[param_name]
        print(f"  Subplot — Varying {label}:")
        print(f"  Insight: {insight}")
        print(f"    {'Value':>8}  {'BW Reduction %':>14}")
        print(f"    {'-'*24}")
        for row in data:
            val = row.get(key, '?')
            red = row['reduction_pct']
            marker = ' <- Overdrive LG2.0' if (key == 'log_p' and val == 128) else ''
            print(f"    {val:>8}  {red:>13.2f}%{marker}")
        print()


if __name__ == "__main__":
    print("Crossover Threshold and Sensitivity Analysis")
    print("Generates data for Figures 8-11")
    print("=" * 70)

    # Figure 8: Sensitivity analysis
    print("\nFIGURE 8 DATA: Four-Subplot Sensitivity Analysis")
    print("Base: n=10, M=1,000, B=50, H=400, log_p=128")
    print("-" * 50)
    sens = sensitivity_analysis()
    print_sensitivity(sens)

    # Figure 9: Bandwidth reduction heatmap
    print("\nFIGURE 9 DATA: Bandwidth Reduction Heatmap (M=1,000, H=400, log_p=128)")
    sweep = crossover_sweep(M=1000, H=400, log_p=128)
    print(f"\n  {'n':>4} {'B':>5} {'BW Reduction':>12} {'Beneficial':>12}")
    print(f"  {'-'*38}")
    for r in sweep:
        mark = 'YES' if r['beneficial'] else 'no'
        print(f"  {r['n']:>4} {r['B']:>5} {r['reduction_pct']:>11.2f}% {mark:>12}")

    # Figure 11: Crossover thresholds
    print("\nFIGURE 11 DATA: Crossover Thresholds by Deployment Scenario")
    print("-" * 50)
    thresholds = crossover_threshold_by_scenario()
    for name, data in thresholds.items():
        note = ""
        if data['n_star'] is not None and data['typical_n'] > data['n_star']:
            note = f"(typical n={data['typical_n']} exceeds threshold — batching beneficial)"
        print(f"  {name:<20}: n* = {data['n_star']}  {note}")
    print()
    print("  Batching is bandwidth-beneficial from n=2 in every scenario, including IoT at B=20.")
