# Deployment-aware optimization in MP-SPDZ

Code, MP-SPDZ programs, experimental data and figure scripts for the article:

> Kudzordzi L, Asante G, Asiedu W, Osei-Wusu F. *Deployment-aware optimization in MP-SPDZ: Compiler
> characterization, batching, and backend selection.* (Under review at PLOS ONE.)

The repository reproduces every analytical table and every figure in the article, and contains the MP-SPDZ
programs and measurements behind the empirical results.

## Contents

```
mp_spdz_programs/          MP-SPDZ programs: baseline (individual multiplications) and batched (dot products),
                           M = 100, 1,000 and 10,000, batch size B = 50
analysis/
  daps.py                   Algorithm 5 (DAPS); Tables 11-13 and the LowGear compute-basis sensitivity analysis
  complexity_models.py     Complexity and bandwidth models for Algorithms 2 and 3 (Table 2)
  deployment_decision.py   EPPC deployment scenarios (Table 8)
  crossover_analysis.py    Sensitivity and crossover analysis (data for Figs 8-11)
  run_analysis.py          Runs all analyses (and, optionally, all figure scripts)
figures/
  make_figs.py             Figs 4-11 (EPS and 300 dpi TIFF)
  diagrams.py              Figs 1-3 (vector diagrams; EPS and 300 dpi TIFF)
data/
  table4_compiler_merging.csv   Default versus no-merge (-n) compilation
  runs_mascot_lowgear.csv       Every individual MASCOT and LowGear run (102 runs: time, data sent, rounds)
  runs_latency.csv              The 8 emulated-latency runs
  table5_mascot_results.csv     MASCOT summary: mean, sample sd and 95% CI over 3 runs (Table 5)
  table6_lowgear_results.csv    LowGear summary: mean, sample sd and 95% CI over 3 runs (Table 6)
  table7_latency_results.csv    Emulated latency 0/10/50/100 ms, MASCOT, n = 2, M = 10,000
  table10_hardware.csv          Observed memory requirements
  raw_logs/                     Raw MP-SPDZ outputs (time, data sent, rounds) of all 110 measurements
```

## Requirements

Python 3.8 or later. The analysis scripts use only the standard library; the figure scripts need

```
pip install -r requirements.txt
```

## Reproducing the analyses and figures

```
cd analysis
python daps.py                  # Tables 11-13 and the LowGear compute-basis sensitivity (158.8 s / 258.8 s)
python deployment_decision.py  # Table 8
python crossover_analysis.py   # data behind Figs 8-11
python run_analysis.py         # everything above, plus all figures (use --no-figures to skip them)

cd ../figures
python make_figs.py            # Figs 4-11 -> figures/output/
python diagrams.py             # Figs 1-3  -> figures/output/
```

All DAPS comparison values are model-based predictions from the round-latency model (Equation 1 of the
article), combining measured round counts with measured or scaled compute times; see the note to Table 12.

## Reproducing the MP-SPDZ experiments

Environment used: MP-SPDZ commit `71631ce9`; Ubuntu 24.04 under WSL 2 on Windows 10; Intel i5-6200U (2 cores,
4 threads); 16 GB RAM with WSL 2 limited to 11 GB via `.wslconfig`.

1. Copy the programs into MP-SPDZ: `cp mp_spdz_programs/*.mpc ~/MP-SPDZ/Programs/Source/`
2. Compile **with the no-merge flag**, which disables MP-SPDZ's default instruction merging and exposes
   protocol-level round counts:
   ```
   ./compile.py -n baseline_10000
   ./compile.py -n batched_10000
   ```
   Compiling without `-n` merges the baseline into its batched equivalent (about 221 instead of about 20,219
   rounds for M = 10,000), which is the compiler-merging effect characterized in the article.
3. Run with MASCOT or LowGear, for example for three parties:
   ```
   PLAYERS=3 Scripts/mascot.sh baseline_10000
   PLAYERS=3 Scripts/lowgear.sh batched_10000
   ```
   Each configuration was run three times. The time, data sent and rounds reported by MP-SPDZ are the values in
   `data/`.
4. Latency emulation (n = 2, M = 10,000):
   ```
   sudo tc qdisc add dev lo root netem delay 50ms    # 10, 50 or 100 ms
   Scripts/mascot.sh baseline_10000
   sudo tc qdisc del dev lo root netem               # always remove afterwards
   ```

## Data

`data/raw_logs/` holds the MP-SPDZ output (time, data sent, rounds) of all 110 measurements, and
`runs_*.csv` tabulate every individual run. The summary files are computed from these runs and reproduce Tables 4-7
and 10 of the article.

## Licence

Code: MIT Licence (see `LICENSE`). Data in `data/`: Creative Commons Attribution 4.0 International (CC BY 4.0).

## Citation

If you use this repository, please cite the article above and the archived release (see `CITATION.cff`; the
Zenodo DOI is listed on the release page).
