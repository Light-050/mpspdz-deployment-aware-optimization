# Raw MP-SPDZ run outputs

`mascot_lowgear_runs.txt` — the time, data sent and round count printed by MP-SPDZ (party 0) for all
102 MASCOT and LowGear runs (34 configurations x 3 runs), extracted from the individual output files whose
names are given in each header line (`<backend>_nomerge_<BL|BA>_n<parties>_M<multiplications>_run<k>.txt`).

`latency_runs.txt` — the same for the 8 emulated-latency runs (MASCOT, n = 2, M = 10,000; 0, 10, 50, 100 ms).

The same values are tabulated in `../runs_mascot_lowgear.csv` and `../runs_latency.csv`. The summary files
`../table5_mascot_results.csv` and `../table6_lowgear_results.csv` are computed from these runs (mean and sample
standard deviation over three runs; 95% confidence half-width = 4.303 x sd / sqrt(3)).

MP-SPDZ reports round counts as approximate ("~"). Two configurations show a difference of two rounds between runs
(MASCOT n = 5, M = 1,000 BA: 277-279; MASCOT n = 5, M = 10,000 BL: 80,675-80,677); the summary files give the range.
