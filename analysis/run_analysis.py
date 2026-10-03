"""
run_analysis.py — Main Orchestration Script
============================================
Paper:   "Deployment-aware optimization in MP-SPDZ: Compiler characterization, batching, and backend selection"
Authors: Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu

This script runs the complete EPPC analytical framework in sequence:
  Step 1: Complexity comparison (Table 2)
  Step 2: Deployment scenario analysis (Table 8)
  Step 3: DAPS validation (Tables 11-13)
  Step 4: Sensitivity and crossover analysis (Figures 8-11)
  Step 5: Generate figures (if matplotlib available)
  Step 6: Write full analysis report to file

USAGE:
  python run_analysis.py              # full pipeline
  python run_analysis.py --no-figures # skip figure generation

DEPENDENCIES:
  - complexity_models.py
  - crossover_analysis.py
  - deployment_decision.py
  - daps.py
  - ../figures/make_figs.py and ../figures/diagrams.py (optional, for figures)
"""

import os
import sys
from datetime import datetime

from complexity_models import (
    ProtocolParams, print_comparison, full_comparison, OverdriveLG2
)
from crossover_analysis import (
    crossover_sweep, sensitivity_analysis, print_sensitivity,
    crossover_threshold_by_scenario
)
from deployment_decision import (
    SCENARIOS, generate_table8, print_full_analysis
)
from daps import (
    MANUSCRIPT_SCENARIOS, run_daps, generate_daps_report,
    generate_validation_table, compiler_merging_impact,
    DeploymentScenario
)


PAPER_TITLE = (
    "Deployment-Aware Optimization of SPDZ Protocols: Compiler Characterization,\n"
    "Online Batching, and Backend Selection with Empirical Validation in MP-SPDZ"
)
AUTHOR = "Light Kudzordzi, George Asante, William Asiedu, Franco Osei-Wusu"
TARGET = "PLOS ONE"


def write_report(filepath: str = "analysis_report.txt"):
    """Write complete analysis report to file."""
    original_stdout = sys.stdout

    with open(filepath, 'w', encoding='utf-8') as f:
        sys.stdout = f

        print("=" * 80)
        print("  EPPC ANALYTICAL FRAMEWORK — COMPLETE ANALYSIS REPORT")
        print("=" * 80)
        print(f"  Paper:     {PAPER_TITLE}")
        print(f"  Author:    {AUTHOR}")
        print(f"  Target:    {TARGET}")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Base:      Overdrive LowGear 2.0 (Reisert et al., AsiaCCS 2023)")
        print(f"             DOI: 10.1145/3579856.3582809")
        print("=" * 80)

        # the manuscript: Compiler merging finding (Table 4)
        print("\n\n" + "=" * 80)
        print("  COMPILER MERGING IMPACT (Table 4)")
        print("=" * 80)
        print(compiler_merging_impact())

        # the manuscript: Overdrive LG2.0 parameters
        print("\n\n" + "=" * 80)
        print("  OVERDRIVE LOWGEAR 2.0 BASE PARAMETERS")
        print("=" * 80)
        print(f"\n  Triple bandwidth (sec=40):  {OverdriveLG2.TRIPLE_KBIT_SEC40} kbit/triple")
        print(f"  Triple bandwidth (sec=128): {OverdriveLG2.TRIPLE_KBIT_SEC128} kbit/triple")
        print(f"  Throughput (sec=40):        {OverdriveLG2.THROUGHPUT_SEC40:,} triples/s")
        print(f"  Rounds per triple batch:    {OverdriveLG2.ROUNDS_PI_TRIPLE}")
        print(f"  Prime size:                 {OverdriveLG2.PRIME_BITS} bits")
        print(f"  Ciphertext modulus:         {OverdriveLG2.CIPHERTEXT_MOD_BITS} bits")
        print(f"  Plaintext slots:            {OverdriveLG2.PLAINTEXT_SLOTS:,}")
        print(f"  Offline BW reduction:       {OverdriveLG2.OFFLINE_BW_REDUCTION*100:.0f}% vs Overdrive LG")

        # the manuscript: Table 2 complexity comparison
        print("\n\n" + "=" * 80)
        print("  TABLE 2 COMPLEXITY COMPARISON")
        print("=" * 80)
        for config in [
            ProtocolParams(n=2, M=10000, B=50, H=400, log_p=128,
                           label="n=2, M=10,000, B=50 (Table 5 key config)"),
            ProtocolParams(n=2, M=1000, B=50, H=400, log_p=128,
                           label="n=2, M=1,000, B=50 (Listing 1)"),
        ]:
            print_comparison(config)

        # the manuscript: Table 8 deployment scenarios
        print("\n\n" + "=" * 80)
        print("  TABLE 8 DEPLOYMENT SCENARIOS")
        print("=" * 80)
        print(generate_table8())
        print()
        print_full_analysis()

        # the manuscript: DAPS validation (Tables 11-13)
        print("\n\n" + "=" * 80)
        print("  DAPS EVALUATION (Tables 11-13)")
        print("=" * 80)
        print("\nIndividual DAPS Scenario Reports (Table 11 rationale):")
        for scenario in MANUSCRIPT_SCENARIOS:
            print(generate_daps_report(scenario))
        print("\n\n")
        print(generate_validation_table(MANUSCRIPT_SCENARIOS))

        # the manuscript: Sensitivity analysis (Figure 8)
        print("\n\n" + "=" * 80)
        print("  SENSITIVITY ANALYSIS (Figure 8)")
        print("=" * 80)
        sens = sensitivity_analysis()
        print_sensitivity(sens)

        # the manuscript: Heatmap (Figure 9)
        print("\n\n" + "=" * 80)
        print("  BANDWIDTH REDUCTION HEATMAP (Figure 9)")
        print("=" * 80)
        sweep = crossover_sweep(M=1000, H=400, log_p=128)
        print(f"\n  {'n':>4} {'B':>5} {'BW Reduction':>12} {'Beneficial':>12}")
        print(f"  {'-'*38}")
        for r in sweep:
            mark = 'YES' if r['beneficial'] else 'no'
            print(f"  {r['n']:>4} {r['B']:>5} {r['reduction_pct']:>11.2f}% {mark:>12}")

        # the manuscript: Crossover thresholds (Figure 11)
        print("\n\n" + "=" * 80)
        print("  CROSSOVER THRESHOLDS (Figure 11)")
        print("=" * 80)
        thresholds = crossover_threshold_by_scenario()
        for name, data in thresholds.items():
            print(f"  {name:<22}: n* = {data['n_star']}")

        print("\n\n" + "=" * 80)
        print("  END OF REPORT")
        print("=" * 80)

    sys.stdout = original_stdout
    print(f"  Report written to: {filepath}")


def main():
    """Run the complete EPPC analysis pipeline."""
    skip_figures = '--no-figures' in sys.argv

    print("=" * 70)
    print("EPPC Analytical Framework")
    print(f"Paper: {PAPER_TITLE}")
    print(f"Author: {AUTHOR}")
    print("=" * 70)
    print()

    print("STEP 1: Compiler Merging Discovery (Table 4)")
    print("-" * 50)
    print(compiler_merging_impact())

    print("\n\nSTEP 2: Complexity Comparison (Table 2)")
    print("-" * 50)
    print_comparison(ProtocolParams(
        n=2, M=10000, B=50, H=400, log_p=128,
        label="n=2, M=10,000, B=50 (Overdrive LG2.0 params)"))

    print("\n\nSTEP 3: Deployment Scenarios (Table 8)")
    print("-" * 50)
    print(generate_table8())

    print("\n\nSTEP 4: DAPS Validation (Tables 11-13)")
    print("-" * 50)
    for scenario in MANUSCRIPT_SCENARIOS:
        print(generate_daps_report(scenario))
    print("\n")
    print(generate_validation_table(MANUSCRIPT_SCENARIOS))

    print("\n\nSTEP 5: Sensitivity Analysis (Figures 8-11)")
    print("-" * 50)
    sens = sensitivity_analysis()
    print_sensitivity(sens)

    print("\n\nSTEP 6: Writing Full Report")
    print("-" * 50)
    write_report("analysis_report.txt")

    if not skip_figures:
        print("\n\nSTEP 7: Generating Figures")
        print("-" * 50)
        try:
            import subprocess, pathlib
            figdir = pathlib.Path(__file__).resolve().parent.parent / "figures"
            subprocess.run([sys.executable, "make_figs.py"], cwd=figdir, check=True)
            subprocess.run([sys.executable, "diagrams.py"], cwd=figdir, check=True)
            print("  Figures generated in figures/output/.")
        except ImportError:
            print("  Skipping figures: matplotlib not available.")
            print("  Install with: pip install matplotlib numpy")
        except Exception as e:
            print(f"  Figure generation error: {e}")
    else:
        print("\n\nSTEP 7: Skipping figure generation (--no-figures)")

    print("\n" + "=" * 70)
    print("Analysis complete.")
    print(f"  Report:   analysis_report.txt")
    print(f"  Figures:  figures/ (if generated)")
    print("=" * 70)


if __name__ == "__main__":
    main()
