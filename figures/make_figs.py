import sys, os, math
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'analysis'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PIL import Image
from complexity_models import ProtocolParams, total_reduction_pct
from crossover_analysis import sensitivity_analysis

OUT = 'output'
os.makedirs(OUT, exist_ok=True)
PREV = 'output/png'; os.makedirs(PREV, exist_ok=True)

# Figs 4-11 of the manuscript. Run from this folder: python make_figs.py
plt.rcParams.update({
    'font.family': 'Liberation Sans', 'font.size': 9, 'axes.titlesize': 9.5, 'axes.labelsize': 9,
    'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
    'mathtext.fontset': 'custom', 'mathtext.rm': 'Liberation Sans', 'mathtext.it': 'Liberation Sans:italic',
    'mathtext.bf': 'Liberation Sans:bold',
    'ps.fonttype': 42, 'pdf.fonttype': 42, 'axes.linewidth': 0.8, 'lines.linewidth': 1.6,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.04,
})
W1, W2 = 5.2, 7.5   # PLOS single-column and full width (inches)

def save(fig, n):
    fig.savefig(f'{OUT}/Fig{n}.eps', format='eps')
    fig.savefig(f'{PREV}/Fig{n}.png', dpi=300)
    im = Image.open(f'{PREV}/Fig{n}.png').convert('RGB')
    im.save(f'{OUT}/Fig{n}.tif', compression='tiff_lzw', dpi=(300, 300))
    plt.close(fig)
    print('Fig', n, im.size)

thou = FuncFormatter(lambda x, _: f'{x:,.0f}')

# ---------------- Fig 4: MASCOT speedups (Table 5) ----------------
T5 = {  # (n, M): (BL mean, BL sample sd, BA mean, BA sample sd), from data/runs_mascot_lowgear.csv
 (2,100):(0.100,0.009,0.100,0.012),(2,1000):(0.718,0.068,0.494,0.058),(2,10000):(5.322,0.335,3.086,0.231),
 (3,100):(0.204,0.018,0.180,0.013),(3,1000):(1.408,0.108,1.127,0.036),(3,10000):(7.956,0.980,5.462,0.038),
 (5,100):(0.567,0.025,0.527,0.036),(5,1000):(6.068,0.756,4.873,0.258),(5,10000):(34.213,1.770,28.079,1.200),
 (10,100):(4.000,0.477,4.162,0.909),(10,1000):(16.701,5.119,14.984,0.933),(10,10000):(100.542,10.299,89.093,3.339)}
ns, Ms = [2,3,5,10], [100,1000,10000]
SPD = {(2,100):1.00,(2,1000):1.45,(2,10000):1.72,(3,100):1.14,(3,1000):1.25,(3,10000):1.46,(5,100):1.08,(5,1000):1.25,(5,10000):1.22,(10,100):0.96,(10,1000):1.11,(10,10000):1.13}
cols = ['#1f77b4', '#ff7f0e', '#2ca02c']
fig, ax = plt.subplots(figsize=(W1, 3.2))
w = 0.26
for k, M in enumerate(Ms):
    sp, er = [], []
    for n in ns:
        bl, sbl, ba, sba = T5[(n, M)]
        s = SPD[(n, M)]; sp.append(s); er.append((bl/ba)*math.sqrt((sbl/bl)**2 + (sba/ba)**2))
    x = np.arange(len(ns)) + (k-1)*w
    ax.bar(x, sp, w, yerr=er, capsize=2, color=cols[k], error_kw={'elinewidth': 0.8}, label=f'$M$ = {M:,}')
    for xi, s, e in zip(x, sp, er):
        ax.text(xi, s + e + 0.03, f'{s:.2f}×', ha='center', va='bottom', fontsize=6)
ax.axhline(1.0, color='k', ls='--', lw=0.8)
ax.set_xticks(range(len(ns))); ax.set_xticklabels([f'$n$ = {n}' for n in ns])
ax.set_ylabel('Speedup (BL time / BA time)'); ax.set_ylim(0, 2.35)
ax.legend(ncol=3, loc='upper right', frameon=False)
ax.set_title('MASCOT speedup by party count ($B$ = 50, -n compilation, 3-run means)')
save(fig, 4)

# ---------------- Fig 5: latency (Table 7) ----------------
lat = [0, 10, 50, 100]
BL = [5.831, 210.109, 1022.920, 2037.350]; BA = [3.491, 10.469, 36.509, 69.351]
spd = [b/a for b, a in zip(BL, BA)]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.0))
a1.plot(lat, BL, 'o-', color='#d62728', label='Baseline (BL), ~20,219 rounds')
a1.plot(lat, BA, 's-', color='#1f77b4', label='Batched (BA), ~619 rounds')
a1.set_yscale('log'); a1.set_xlabel('Emulated network latency (ms)'); a1.set_ylabel('Total execution time (s, log scale)')
for x, y, s in zip(lat, BA, spd):
    a1.annotate(f'{s:.2f}×', (x, y), textcoords='offset points', xytext=(9, -11), ha='left', fontsize=7)
a1.set_title('(a) Execution time versus latency'); a1.legend(frameon=False, loc='upper left'); a1.grid(color='#e3e3e3', lw=0.6)
a1.set_xticks(lat)
saved = [b - a for b, a in zip(BL, BA)]
bars = a2.bar([str(x) for x in lat], saved, color='#9467bd', width=0.6)
a2.set_yscale('log'); a2.set_ylim(1, 6000)
for b_, v in zip(bars, saved):
    a2.text(b_.get_x() + b_.get_width()/2, v*1.15, f'{v:,.1f} s', ha='center', fontsize=7)
a2.set_xlabel('Emulated network latency (ms)'); a2.set_ylabel('Time saved by batching (s, log scale)')
a2.set_title('(b) Absolute time saved by batching'); a2.grid(color='#e3e3e3', axis='y', lw=0.6)
fig.suptitle('MASCOT, $n$ = 2, $M$ = 10,000, $B$ = 50, -n compilation; data volume 195.15 MB in all runs', fontsize=8.5, y=1.02)
fig.tight_layout(); save(fig, 5)

# ---------------- Fig 6: communication breakdown (Table 8, log p = 128) ----------------
sc = [('Healthcare',5,10000,100,600),('Finance',10,5000,50,400),('Government',7,8000,100,800),
      ('ML Inference',5,50000,100,400),('IoT',20,1000,200,200)]
MB = 8*1024*1024
rows = []
for name, n, M, B, H in sc:
    d = 2*n*M*128/MB; hb = 2*n*M*H/MB; he = 2*n*math.ceil(M/B)*H/MB
    rows.append((name, d, hb, he, 100*(1-(d+he)/(d+hb))))
def breakdown(ax, rs, log):
    x = np.arange(len(rs)); w = 0.36
    for i, (name, d, hb, he, red) in enumerate(rs):
        ax.bar(i - w/2, d, w, color='#1f77b4', label='Baseline data' if i == 0 else None)
        ax.bar(i - w/2, hb, w, bottom=d, color='#ff7f0e', label='Baseline headers' if i == 0 else None)
        ax.bar(i + w/2, d, w, color='#2ca02c', label='Enhanced data' if i == 0 else None)
        ax.bar(i + w/2, he, w, bottom=d, color='#d62728', label='Enhanced headers' if i == 0 else None)
        ax.text(i - w/2, (d+hb)*(1.15 if log else 1.02), f'{red:.1f}%\nred.', ha='center', va='bottom', fontsize=6.5)
    ax.set_xticks(x); ax.set_xticklabels([r_[0] for r_ in rs], rotation=20)
    if log: ax.set_yscale('log'); ax.set_ylim(0.3, 120)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W2, 3.2), gridspec_kw={'width_ratios': [1.25, 1]})
breakdown(a1, rows, True); a1.set_ylabel('Communication (MB, log scale)'); a1.set_title('(a) All five scenarios')
breakdown(a2, [r_ for r_ in rows if r_[0] != 'ML Inference'], False); a2.set_ylabel('Communication (MB)')
a2.set_title('(b) Excluding ML Inference (linear scale)'); a2.set_ylim(0, 15)
a1.legend(frameon=False, loc='upper left', fontsize=7)
fig.suptitle(r'Baseline versus enhanced communication, $\log\,p$ = 128 bits, DAPS batch sizes', fontsize=8.5, y=1.02)
fig.tight_layout(); save(fig, 6)

# ---------------- Fig 7: Healthcare breakdown ----------------
KB = 8*1024; n, M, B, H = 5, 10000, 100, 600
d = 2*n*M*128/KB; hb = 2*n*M*H/KB; he = 2*n*math.ceil(M/B)*H/KB
fig, ax = plt.subplots(figsize=(W1, 3.4))
ax.bar(0, d, 0.5, color='#1a9e77', label='Data payload'); ax.bar(0, hb, 0.5, bottom=d, color='#e34a33', label='Header overhead')
ax.bar(1, d, 0.5, color='#1a9e77'); ax.bar(1, he, 0.5, bottom=d, color='#e34a33')
ax.text(0, d/2, f'{d:,.1f} KB\n({100*d/(d+hb):.1f}%)', ha='center', va='center', color='white', fontsize=8, fontweight='bold')
ax.text(0, d+hb/2, f'{hb:,.1f} KB\n({100*hb/(d+hb):.1f}%)', ha='center', va='center', color='white', fontsize=8, fontweight='bold')
ax.text(1, d/2, f'{d:,.1f} KB\n({100*d/(d+he):.1f}%)', ha='center', va='center', color='white', fontsize=8, fontweight='bold')
ax.text(1, d+he+150, f'Headers {he:,.1f} KB ({100*he/(d+he):.1f}%)\nTotal {d+he:,.1f} KB', ha='center', va='bottom', fontsize=7.5)
ax.text(0, d+hb+150, f'Total {d+hb:,.1f} KB', ha='center', va='bottom', fontsize=7.5)
ax.annotate(f'{100*(1-(d+he)/(d+hb)):.1f}% reduction', xy=(1, d+he+900), xytext=(0.5, 7000), ha='center', fontsize=9,
            fontweight='bold', arrowprops=dict(arrowstyle='->', lw=1))
ax.set_xticks([0, 1]); ax.set_xticklabels(['Baseline SPDZ', 'Enhanced SPDZ (batched)'])
ax.set_ylabel('Bandwidth (KB)'); ax.set_ylim(0, 10500); ax.yaxis.set_major_formatter(thou)
ax.set_title(r'Healthcare scenario ($n$ = 5, $M$ = 10,000, $B$ = 100, $H$ = 600, $\log\,p$ = 128)')
ax.legend(frameon=False, loc='upper right'); save(fig, 7)

# ---------------- Fig 8: sensitivity ----------------
sens = sensitivity_analysis(base_log_p=256)
fig, axs = plt.subplots(2, 2, figsize=(W2, 5.4))
spec = [('vary_n', 'n', 'Number of parties $n$', '(a) Party count', 'o-', '#1f77b4'),
        ('vary_B', 'B', 'Batch size $B$', '(b) Batch size', 's-', '#2ca02c'),
        ('vary_H', 'H', 'Header size $H$ (bits)', '(c) Header size', '^-', '#ff7f0e'),
        ('vary_log_p', 'log_p', r'Field element size $\log\,p$ (bits)', '(d) Field size', 'D-', '#9467bd')]
for ax, (key, fld, xl, tl, sty, c) in zip(axs.flat, spec):
    dd = sens[key]
    ax.plot([e[fld] for e in dd], [e['reduction_pct'] for e in dd], sty, color=c, ms=4)
    ax.set_xlabel(xl); ax.set_ylabel('Bandwidth reduction (%)'); ax.set_title(tl); ax.grid(color='#e3e3e3', lw=0.6)
axs[1, 1].axvline(128, color='r', ls='--', lw=0.9, label=r'Overdrive LowGear 2.0 ($\log\,p$ = 128)')
axs[1, 1].legend(frameon=False, fontsize=7)
fig.suptitle(r'Sensitivity analysis (base case: $n$ = 10, $M$ = 1,000, $B$ = 50, $H$ = 400, $\log\,p$ = 256)', fontsize=9, y=1.0)
fig.tight_layout(); save(fig, 8)

# ---------------- Fig 9: heatmap ----------------
n_vals = [2, 3, 5, 7, 10, 15, 20]; B_vals = [10, 20, 50, 75, 100, 150, 200]
grid = np.array([[total_reduction_pct(ProtocolParams(n=n_, M=1000, B=B_, H=400, log_p=128)) for B_ in B_vals] for n_ in n_vals])
fig, ax = plt.subplots(figsize=(W1, 3.6))
im = ax.imshow(grid, cmap='Greens', aspect='auto', vmin=50, vmax=80)
ax.set_xticks(range(len(B_vals))); ax.set_xticklabels(B_vals); ax.set_yticks(range(len(n_vals))); ax.set_yticklabels(n_vals)
ax.set_xlabel('Batch size $B$'); ax.set_ylabel('Number of parties $n$')
for i in range(len(n_vals)):
    for j in range(len(B_vals)):
        ax.text(j, i, f'{grid[i, j]:.1f}', ha='center', va='center', fontsize=7, color='white' if grid[i, j] > 70 else 'black')
fig.colorbar(im, ax=ax, label='Bandwidth reduction (%)')
ax.set_title(r'Bandwidth reduction (%) ($M$ = 1,000, $H$ = 400, $\log\,p$ = 128)')
save(fig, 9)

# ---------------- Fig 10: reduction vs B ----------------
fig, ax = plt.subplots(figsize=(W1, 3.2))
Br = np.arange(5, 201, 5)
for lp, c in zip([128, 256, 384], ['#1f77b4', '#ff7f0e', '#2ca02c']):
    ax.plot(Br, [total_reduction_pct(ProtocolParams(n=10, M=1000, B=int(b), H=400, log_p=lp)) for b in Br],
            color=c, label=rf'$\log\,p$ = {lp}')
y50 = total_reduction_pct(ProtocolParams(n=10, M=1000, B=50, H=400, log_p=128))
ax.plot([50], [y50], 'ko', ms=4)
ax.annotate(f'$B$ = 50: {y50:.1f}%\n(Overdrive LowGear 2.0,\n' + r'$\log\,p$ = 128)', xy=(50, y50), xytext=(95, 30),
            fontsize=7.5, arrowprops=dict(arrowstyle='->', color='gray'))
ax.axhline(0, color='k', lw=0.5, ls='--'); ax.set_ylim(-5, 85)
ax.set_xlabel('Batch size $B$'); ax.set_ylabel('Total bandwidth reduction (%)')
ax.set_title('Bandwidth reduction versus batch size ($n$ = 10, $M$ = 1,000, $H$ = 400)')
ax.legend(frameon=False, loc='lower left'); ax.grid(color='#e3e3e3', lw=0.6); save(fig, 10)

# ---------------- Fig 11: reduction vs n by scenario ----------------
sc11 = [('Healthcare', 100, 600, 5, '#1f77b4', 'o', '-'), ('Finance', 50, 400, 10, '#9467bd', 's', '-'),
        ('Government', 100, 800, 7, '#d62728', '^', '-'), ('ML Inference', 100, 400, 5, '#2ca02c', 'D', '-'),
        ('IoT (DAPS, $B$ = 200)', 200, 200, 20, '#ff7f0e', 'v', '-'), ('IoT (small batch, $B$ = 20)', 20, 200, 20, '#8c564b', 'X', '--')]
nr = list(range(2, 21))
fig, ax = plt.subplots(figsize=(W1, 3.4))
for name, B_, H_, tn, c, mk, ls in sc11:
    red = [total_reduction_pct(ProtocolParams(n=n_, M=1000, B=B_, H=H_, log_p=128)) for n_ in nr]
    ax.plot(nr, red, ls, color=c, label=f'{name}: {red[0]:.1f}%')
    ax.plot([tn], [red[nr.index(tn)]], mk, color=c, ms=6, mfc='white' if mk != 'X' else c, mew=1.2)
ax.axhline(0, color='k', lw=0.8); ax.axvline(2, color='gray', lw=0.8, ls=':')
ax.set_xlim(1.5, 20.5); ax.set_ylim(-5, 100); ax.set_xticks([2, 3, 5, 7, 10, 15, 20])
ax.set_xlabel('Number of parties $n$'); ax.set_ylabel('Bandwidth reduction (%)')
ax.set_title(r'Bandwidth reduction versus party count ($M$ = 1,000, $\log\,p$ = 128)')
ax.text(2.3, 5, 'Positive from $n$ = 2 in every scenario;\nmarkers show typical party counts', fontsize=7)
ax.legend(frameon=False, fontsize=7, loc='center right', bbox_to_anchor=(1.0, 0.33)); ax.grid(color='#e3e3e3', lw=0.6)
save(fig, 11)
