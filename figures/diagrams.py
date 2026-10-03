"""Figs 1-3 of the manuscript (vector diagrams). Run from this folder: python diagrams.py"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, FancyArrowPatch
from PIL import Image

plt.rcParams.update({
    'font.family': 'Liberation Sans', 'font.size': 8,
    'mathtext.fontset': 'stixsans', 'ps.fonttype': 42, 'pdf.fonttype': 42,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03,
})
import os
OUT = 'output'; os.makedirs(OUT, exist_ok=True)
PREV = 'output/png'; os.makedirs(PREV, exist_ok=True)

def canvas(w_in, h_in, W=100, H=100):
    fig = plt.figure(figsize=(w_in * 7.44 / 7.5, h_in * 7.44 / 7.5))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis('off')
    return fig, ax

def box(ax, x, y, w, h, fc='white', ec='black', lw=0.8, r=0.8, ls='-', z=1):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f'round,pad=0,rounding_size={r}', fc=fc, ec=ec, lw=lw, ls=ls, zorder=z)
    ax.add_patch(p); return p

def rect(ax, x, y, w, h, fc, ec=None, lw=0, z=1):
    p = FancyBboxPatch((x, y), w, h, boxstyle='square,pad=0', fc=fc, ec=ec or fc, lw=lw, zorder=z)
    ax.add_patch(p); return p

def text(ax, x, y, s, size=8, ha='center', va='center', color='black', weight='normal', style='normal', z=5, **kw):
    return ax.text(x, y, s, fontsize=size, ha=ha, va=va, color=color, fontweight=weight, fontstyle=style, zorder=z,
                   linespacing=1.15, **kw)

def arrow(ax, x1, y1, x2, y2, color='#333333', lw=1.0, ms=8, z=3, style='-|>'):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms, color=color, lw=lw, zorder=z,
                        shrinkA=0, shrinkB=0)
    ax.add_patch(a); return a

def line(ax, xs, ys, color='#333333', lw=1.0, z=3, ls='-'):
    ax.plot(xs, ys, color=color, lw=lw, zorder=z, ls=ls, solid_capstyle='butt')

def diamond(ax, cx, cy, w, h, fc, ec, lw=0.8, z=2):
    p = Polygon([(cx - w/2, cy), (cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2)], closed=True, fc=fc, ec=ec, lw=lw, zorder=z)
    ax.add_patch(p); return p

def save(fig, n):
    fig.savefig(f'{OUT}/Fig{n}.eps', format='eps')
    fig.savefig(f'{PREV}/Fig{n}.png', dpi=300)
    im = Image.open(f'{PREV}/Fig{n}.png').convert('RGB')
    im.save(f'{OUT}/Fig{n}.tif', compression='tiff_lzw', dpi=(300, 300))
    plt.close(fig); print('Fig', n, im.size)


def fig1():
    fig, ax = canvas(7.5, 7.5, 100, 100)

    layers = [
     ('L1', 'Security\nanalysis', 'Layer 1: Security analysis', '#1f4e9c', '#eef3fb',
      [('Confidentiality', 'Parties learn nothing\nbeyond the output'), ('Integrity', 'Result correctness'),
       ('Authenticity', 'Message origin\nverification'), ('Adversary models', 'Semi-honest, malicious,\ncovert')]),
     ('L2', 'Complexity\nanalysis', 'Layer 2: Complexity analysis', '#5b3fb5', '#f3f0fc',
      [('Offline complexity', 'Preprocessing cost'), ('Online complexity', 'Secure computation\ncost'),
       ('Communication rounds', 'Sequential steps'), ('Storage requirements', 'Memory for\npreprocessed data')]),
     ('L3', 'Efficiency\nevaluation', 'Layer 3: Efficiency evaluation', '#2e7d4f', '#ecf6f0',
      [('Latency', 'End-to-end time'), ('Throughput', 'Operations per\nunit time'), ('Scalability', 'Party count and\ncomputation size'),
       ('Resource utilization', 'CPU, memory,\nnetwork, storage'), ('Analytical and\nempirical', 'MP-SPDZ\nmeasurements')]),
     ('L4', 'Deployment\nfeasibility', 'Layer 4: Deployment feasibility', '#b03a2e', '#fdf0ee',
      [('Network assumptions', 'LAN versus WAN,\nbandwidth'), ('Hardware requirements', 'CPU, GPU, FPGA,\nmemory'),
       ('Implementation complexity', 'Development effort,\nmaintainability'), ('Operational constraints', 'Fault tolerance,\nmonitoring')]),
     ('L5', 'Regulatory\ncompliance', 'Layer 5: Regulatory compliance', '#b36b00', '#fdf5e6',
      [('Data protection', 'GDPR, CCPA'), ('Industry-specific', 'HIPAA, finance\nregulations'),
       ('Jurisdictional issues', 'Cross-border\ndata transfer'), ('Audit and accountability', 'Logging, monitoring,\nverification')]),
    ]
    top, rowh, gap = 99.0, 12.0, 1.6
    for i, (lab, name, title, col, fill, subs) in enumerate(layers):
        y0 = top - i * (rowh + gap) - rowh
        box(ax, 1, y0 + rowh - 6.2, 7.4, 5.4, fc=col, ec=col, r=0.7)
        text(ax, 4.7, y0 + rowh - 3.5, lab, size=10, color='white', weight='bold')
        text(ax, 4.7, y0 + rowh - 9.3, name, size=7, color=col)
        box(ax, 10.5, y0, 88.5, rowh, fc=fill, ec=col, lw=0.9, r=0.8)
        text(ax, 54.75, y0 + rowh - 1.7, title, size=8.5, color=col, weight='bold')
        k = len(subs); x_start, x_end, g = 12.0, 97.5, 1.4
        w = (x_end - x_start - (k - 1) * g) / k
        for j, (h, d) in enumerate(subs):
            x = x_start + j * (w + g)
            box(ax, x, y0 + 0.9, w, rowh - 4.4, fc='white', ec=col, lw=0.6, r=0.6)
            text(ax, x + w/2, y0 + rowh - (5.4 if '\n' in h else 5.4), h, size=7.5, weight='bold', color='#1a1a1a')
            text(ax, x + w/2, y0 + 2.75, d, size=7, style='italic', color='#333333')
        if i < 4:
            arrow(ax, 54.75, y0, 54.75, y0 - gap, ms=7, lw=0.9)

    ylast = top - 4 * (rowh + gap) - rowh   # bottom of layer 5
    # selection matrix
    sm_y, sm_h = ylast - 2.2 - 9.6, 9.6
    arrow(ax, 54.75, ylast, 54.75, sm_y + sm_h, ms=7, lw=0.9)
    box(ax, 32, sm_y, 45.5, sm_h, fc='#eef7e9', ec='#4b8b2b', lw=1.0)
    text(ax, 54.75, sm_y + sm_h - 2.0, 'SELECTION MATRIX', size=8.5, weight='bold', color='#2f6b17')
    text(ax, 54.75, sm_y + sm_h - 4.6, 'Integrated multi-dimensional decision framework', size=7.5)
    text(ax, 54.75, sm_y + 2.0, 'Guiding protocol selection based on application requirements', size=7, style='italic', color='#444444')
    box(ax, 2, sm_y + 1.4, 18, sm_h - 2.8, fc='white', ec='#1f4e9c', lw=0.8, ls='--')
    text(ax, 11, sm_y + sm_h/2, 'All layers feed into\nthe selection matrix', size=7.5, color='#1f4e9c', weight='bold')
    arrow(ax, 20, sm_y + sm_h/2, 32, sm_y + sm_h/2, color='#1f4e9c', ms=8, lw=1.1)
    # guided selection
    gs_y, gs_h = sm_y - 2.2 - 5.4, 5.4
    arrow(ax, 54.75, sm_y, 54.75, gs_y + gs_h, ms=7, lw=0.9)
    box(ax, 32, gs_y, 45.5, gs_h, fc='#f0f0fb', ec='#4a3fa8', lw=1.0)
    text(ax, 54.75, gs_y + 3.6, 'GUIDED PROTOCOL SELECTION', size=8.5, weight='bold', color='#3a2f98')
    text(ax, 54.75, gs_y + 1.4, 'for specific applications', size=7.5, color='#3a2f98')
    # domains
    doms = [('Healthcare', 5, '#2e7d4f', '#ecf6f0'), ('Finance', 10, '#1f4e9c', '#eef3fb'),
            ('Government', 7, '#b03a2e', '#fdf0ee'), ('Machine learning', 5, '#5b3fb5', '#f3f0fc'),
            ('IoT', 20, '#b36b00', '#fdf5e6')]
    d_h = 6.0; d_y = gs_y - 4.0 - d_h; dw, dg = 17.4, 2.2; x0 = 1.5
    for j, (nm, n, col, fill) in enumerate(doms):
        x = x0 + j * (dw + dg)
        arrow(ax, 54.75, gs_y, x + dw/2, d_y + d_h, ms=6, lw=0.7, color='#555555')
        box(ax, x, d_y, dw, d_h, fc=fill, ec=col, lw=0.9)
        text(ax, x + dw/2, d_y + 3.9, nm, size=8, weight='bold', color=col)
        text(ax, x + dw/2, d_y + 1.6, f'($n$ = {n})', size=7.5, color=col)
    # legend
    lg_y = d_y - 4.6
    box(ax, 1.5, lg_y, 97, 3.4, fc='#fafafa', ec='#7a7a7a', lw=0.6, ls='--')
    text(ax, 3, lg_y + 1.7, 'Legend:', size=7.5, weight='bold', ha='left')
    text(ax, 12, lg_y + 1.7, 'L1–L5 = analytical layers     |     All layers → selection matrix → guided selection → domain applications',
         size=7.5, ha='left')
    ax.set_ylim(lg_y - 0.5, 99.5)
    fig.set_size_inches(7.44, 7.44 * (99.5 - (lg_y - 0.5)) / 100)
    save(fig, 1)



def fig2():
    import textwrap
    def wrap(s, n): return '\n'.join(textwrap.wrap(s, n))
    PS = r'$\Pi_{\mathrm{SPDZ}}$'
    PB = r'$\Pi_{\mathrm{batch}}$'
    PSB = r'$\Pi_{\mathrm{SPDZ' + '\u2010' + r'batch}}$'
    A = r'$\mathcal{A}$'
    RED, BLUE, GREEN, PURP, NAVY = '#c62828', '#3b7dd8', '#3c9a4b', '#7b3fa0', '#0d2b6b'
    H = 82
    fig, ax = canvas(7.5, 7.5 * H / 100, 100, H)

    # ---------------- panel (a) ----------------
    box(ax, 0.6, 16.0, 45.4, 65.4, fc='white', ec='#9aa7bd', lw=0.8, r=0.6)
    rect(ax, 0.6, 77.6, 45.4, 3.8, fc=NAVY)
    text(ax, 23.3, 79.5, '(a) Communication structure: baseline versus batched', size=8, color='white', weight='bold')
    text(ax, 11.0, 74.6, 'Baseline (Algorithm 2)', size=8, color=RED, weight='bold')
    text(ax, 11.0, 72.2, '$B$ individual multiplications', size=7.5)
    text(ax, 33.5, 74.6, 'Enhanced (Algorithm 3)', size=8, color=GREEN, weight='bold')
    text(ax, 33.5, 72.2, '$B$ multiplications in one batch', size=7.5)
    vals = [r'$\varepsilon_1$', r'$\varepsilon_2$', r'$\varepsilon_3$', r'$\vdots$', r'$\varepsilon_B$']
    for k, vv in enumerate(vals):
        y = 66.0 - k * 4.0
        box(ax, 3.0, y, 5.0, 3.0, fc=RED, ec=RED, r=0.3); text(ax, 5.5, y + 1.5, '$H$', size=7.5, color='white', weight='bold')
        box(ax, 8.2, y, 7.5, 3.0, fc=BLUE, ec=BLUE, r=0.3); text(ax, 11.95, y + 1.5, vv, size=8, color='white')
    line(ax, [16.4, 17.4, 17.4, 16.4], [69.0, 69.0, 50.0, 50.0], lw=1.0); line(ax, [17.4, 18.2], [59.5, 59.5], lw=1.0)
    text(ax, 21.6, 59.5, '$B$\nmessages', size=7.5)
    for k, (vv, col) in enumerate([(r'$\varepsilon_1, \varepsilon_2, \ldots, \varepsilon_B$', BLUE),
                                   (r'$\delta_1, \delta_2, \ldots, \delta_B$', GREEN)]):
        y = 64.0 - k * 4.4
        box(ax, 25.0, y, 4.6, 3.0, fc=RED, ec=RED, r=0.3); text(ax, 27.3, y + 1.5, '$H$', size=7.5, color='white', weight='bold')
        box(ax, 29.8, y, 10.2, 3.0, fc=col, ec=col, r=0.3); text(ax, 34.9, y + 1.5, vv, size=7.5, color='white')
    line(ax, [40.4, 41.2, 41.2, 40.4], [67.0, 67.0, 59.6, 59.6], lw=1.0); line(ax, [41.2, 41.9], [63.3, 63.3], lw=1.0)
    text(ax, 43.8, 63.3, '2\nmsgs', size=7)
    arrow(ax, 9.5, 49.4, 9.5, 43.6, color=RED, lw=2.2, ms=12)
    arrow(ax, 34.9, 58.6, 34.9, 43.6, color=GREEN, lw=2.2, ms=12)
    box(ax, 2.0, 30.0, 16.2, 13.2, fc='#fff5f5', ec=RED, lw=0.9, ls='--')
    text(ax, 10.1, 41.4, 'Baseline\ncommunication', size=7.5, color=RED, weight='bold')
    text(ax, 10.1, 36.3, '$2B$ messages\n$2B$ headers\n$2B$ rounds', size=7.5)
    line(ax, [3.0, 17.2], [33.2, 33.2], color=RED, lw=0.5)
    text(ax, 10.1, 31.5, r'Header cost: $2nBH$ bits', size=7.2, color=RED, weight='bold')
    arrow(ax, 18.8, 37.0, 24.4, 37.0, color='#e8710a', lw=2.4, ms=14)
    text(ax, 21.6, 33.6, 'Factor $B$\nreduction', size=7, color='#e8710a', weight='bold')
    box(ax, 25.2, 30.0, 19.4, 13.2, fc='#f3fbf4', ec=GREEN, lw=0.9, ls='--')
    text(ax, 34.9, 41.4, 'Batched\ncommunication', size=7.5, color=GREEN, weight='bold')
    text(ax, 34.9, 36.3, r'2 messages ($= 2\lceil B/B \rceil$)' + '\n2 headers\n2 rounds', size=7.5)
    line(ax, [26.2, 43.6], [33.2, 33.2], color=GREEN, lw=0.5)
    text(ax, 34.9, 31.5, r'Header cost: $2nH$ bits', size=7.2, color=GREEN, weight='bold')
    box(ax, 2.0, 22.4, 42.6, 5.6, fc='#eef3fb', ec='#1f4e9c', lw=0.9)
    text(ax, 23.3, 25.2, 'Same data payload transmitted in both cases:\n' + r'$O(nM \cdot \log\,p)$ bits per party', size=7.5,
         color='#1f4e9c', weight='bold')
    box(ax, 2.0, 16.8, 42.6, 4.6, fc='#fafafa', ec='#bbbbbb', lw=0.6)
    text(ax, 3.0, 19.1, r'• $H$: header size (bits); $\log\,p$: field element size (bits); $n$: number of parties' + '\n'
         '• Only the transport structure (messages, rounds, headers) changes', size=6.9, ha='left')

    # ---------------- panel (b) ----------------
    box(ax, 47.0, 16.0, 52.4, 65.4, fc='white', ec='#9aa7bd', lw=0.8, r=0.6)
    rect(ax, 47.0, 77.6, 52.4, 3.8, fc=NAVY)
    text(ax, 73.2, 79.5, '(b) Active-security preservation: three structural arguments', size=8, color='white', weight='bold')
    box(ax, 49.0, 63.0, 48.4, 13.4, fc=NAVY, ec=NAVY, r=0.6)
    text(ax, 73.2, 74.4, 'Claim 1 (Active-Security Preservation Under Batching)', size=8, color='white', weight='bold')
    text(ax, 73.2, 68.4, 'If standard SPDZ ' + PS + ' is secure against malicious adversaries corrupting\n'
         'up to $n - 1$ parties in the UC framework, then the batched variant ' + PSB + '\n'
         r'(with identical offline preprocessing and batch size $B \geq 1$) preserves this' + '\n'
         'security guarantee. (Reduction to ' + PS + '; contradiction if broken.)', size=7.0, color='white')
    args = [('Argument 1', 'MAC verification\nis batch-independent', '#e8710a', '#fff6ee',
             ['MACs are verified at\noutput reconstruction,\nnot per multiplication.',
              r'The same $\varepsilon_k$, $\delta_k$ values' + '\ngive the same MAC\nrelations.',
              'Detection probability\nremains ' + r'$1 - 1/p$.']),
            ('Argument 2', 'Offline phase\ncompletely unmodified', GREEN, '#f3fbf4',
             ['Overdrive LowGear 2.0\nzero-knowledge proofs,\nBGV encryption and\nMAC key generation\nare unchanged.',
              'Active security of the\noffline phase carries\nover directly.']),
            ('Argument 3', 'Message content\nis preserved', '#1f4e9c', '#eef3fb',
             ['Both protocols transmit\nthe same ' + r'$\varepsilon_k$, $\delta_k$' + '\nfor each ' + r'$k$.',
              'The batched protocol\nsends ' + r'$B$' + ' values per\nmessage; any\ndeviation causes the\nsame MAC failure.'])]
    xs = [49.0, 65.6, 82.2]; aw = 15.2
    for (t1, t2, col, fill, bullets), x in zip(args, xs):
        arrow(ax, x + aw/2, 63.0, x + aw/2, 60.6, color=NAVY, lw=1.0, ms=8)
        box(ax, x, 36.4, aw, 24.2, fc=fill, ec=col, lw=0.9)
        text(ax, x + aw/2, 58.6, t1, size=7.5, weight='bold', color='#222222')
        text(ax, x + aw/2, 55.4, t2, size=7.2, weight='bold', color=col)
        yy = 52.4
        for b in bullets:
            wrapped = b
            nl = wrapped.count('\n') + 1
            text(ax, x + 0.7, yy, '• ' + wrapped.replace('\n', '\n   '), size=6.8, ha='left', va='top')
            yy -= nl * 1.5 + 0.9
        line(ax, [x + aw/2, x + aw/2, 73.2], [36.4, 34.6, 34.6], color='#333333', lw=0.9)
    arrow(ax, 73.2, 34.6, 73.2, 33.2, color='#333333', lw=0.9, ms=8)
    box(ax, 49.6, 24.4, 47.2, 9.0, fc='#f6effa', ec=PURP, lw=0.9)
    text(ax, 73.2, 31.8, 'Reduction argument', size=7.8, weight='bold', color=PURP)
    text(ax, 73.2, 27.6, 'Any attack on ' + PB + ' can be transformed into an attack on ' + PS + '\n'
         'by decomposing batched messages into individual messages, preserving all\n'
         'values and MAC relations. This contradicts the assumed security of ' + PS + '.', size=6.9, color=PURP)
    arrow(ax, 73.2, 24.4, 73.2, 23.4, color=NAVY, lw=1.0, ms=6)
    box(ax, 49.6, 16.8, 47.2, 6.6, fc='#eef7e9', ec=GREEN, lw=1.0)
    text(ax, 73.2, 21.7, 'No additional attack surface', size=7.8, weight='bold', color='#2f6b17')
    text(ax, 73.2, 18.7, 'Under the assumed UC security of ' + PS + ', active security\nis preserved under batching.', size=6.9,
         color='#2f6b17')

    # ---------------- bottom row ----------------
    box(ax, 0.6, 0.6, 45.4, 13.8, fc='#eef3fb', ec='#1f4e9c', lw=0.9, ls='--')
    text(ax, 23.3, 12.4, 'Theorem 1 (Semi-Honest Security)', size=8, weight='bold', color='#1f4e9c')
    text(ax, 23.3, 6.6, 'For any semi-honest adversary ' + A + ' corrupting up to $n - 1$ parties,\n'
         r'there exists a simulator $S$ such that' + '\n'
         r'$\mathrm{VIEW}_{\mathcal{A}}(\Pi_{\mathrm{batch}}) \approx_{c} \mathrm{VIEW}_{\mathcal{A}}(B$'
         r' executions of $\Pi_{\mathrm{baseline}})$.' + '\n'
         'Batching changes the transport structure but not\nthe information available to ' + A + '.',
         size=7.0, color='#1f2f5a')
    box(ax, 47.0, 0.6, 37.6, 13.8, fc='#fafafa', ec='#9a9a9a', lw=0.7)
    text(ax, 48.2, 12.4, 'Scope and notes', size=7.8, weight='bold', ha='left')
    text(ax, 48.2, 6.2, '• Theorem 1 is a complete formal proof (semi-honest setting).\n'
         '• Claim 1 is a security-preservation argument, conditional on\n   the UC security of standard SPDZ.\n'
         '• A complete UC proof with an explicit simulator construction\n   is left for future work.', size=6.9, ha='left')
    box(ax, 85.8, 0.6, 13.6, 13.8, fc='white', ec='#555555', lw=0.7)
    text(ax, 92.6, 12.4, 'Legend', size=7.8, weight='bold')
    for k, (col, lab) in enumerate([(RED, 'Header ($H$)'), (BLUE, r'Values $\varepsilon_k$'), (GREEN, r'Values $\delta_k$')]):
        y = 8.9 - k * 3.2
        rect(ax, 87.0, y - 1.0, 2.6, 2.0, fc=col); text(ax, 90.4, y, lab, size=7, ha='left')
    save(fig, 2)



def fig3():
    HH = 82
    fig, ax = canvas(7.5, 7.5 * HH / 100, 100, HH)
    NAVY, GRN, PUR, ORG = '#173a7a', '#2e7d32', '#6a1b9a', '#d35400'
    F_IO, F_DEC, F_ACT, F_CFG, F_CMP = '#e8eef8', '#dbe6f6', '#e8f5e9', '#f3e5f5', '#fff3e0'
    BW = r'$\mathrm{BW}_{\mathrm{red}}$'
    RAMMIN = r'$\mathrm{RAM}_{\mathrm{min}}$'

    def act(x, y, w, h, s, fc, ec, size=7):
        box(ax, x, y, w, h, fc=fc, ec=ec, lw=0.8, r=0.5); text(ax, x + w/2, y + h/2, s, size=size)
    def dec(cx, cy, w, h, s, fc=F_DEC, ec=NAVY, size=7):
        diamond(ax, cx, cy, w, h, fc, ec); text(ax, cx, cy, s, size=size)
    def yes(x, y): text(ax, x, y, 'Yes', size=6.8, color=GRN, weight='bold')
    def no(x, y): text(ax, x, y, 'No', size=6.8, weight='bold')

    # input
    box(ax, 20, 77.2, 60, 3.6, fc=F_IO, ec=NAVY, lw=0.9)
    text(ax, 50, 79.0, r'INPUT: $n$, $M$, lat (ms), ram (GB), $H$ = 400 bits, $\log\,p$ = 128 bits, mode', size=8)
    panels = [(0.6, 28.6, 'STAGE 1: Backend selection', NAVY), (30.0, 24.4, 'STAGE 2: Batch size selection', GRN),
              (55.2, 18.4, 'STAGE 3: Compiler flag', PUR), (74.4, 25.0, 'STAGE 4: Predicted performance', ORG)]
    for x, w, t, c in panels:
        box(ax, x, 19.6, w, 55.6, fc='white', ec=c, lw=0.8, ls='--', r=0.6)
        box(ax, x + 1.0, 72.6, w - 2.0, 3.6, fc=c, ec=c, r=0.6)
        text(ax, x + w/2, 74.4, t, size=7.3, color='white', weight='bold')
        arrow(ax, x + w/2, 77.2, x + w/2, 76.2, color=c, ms=5, lw=0.8)

    # ---- stage 1 ----
    cx = 7.4; AX, AW = 15.0, 13.6
    dec(cx, 66.5, 11.2, 6.0, r'$n \geq 10$?')
    arrow(ax, cx + 5.6, 66.5, AX, 66.5, ms=6); yes(14.0, 68.1)
    act(AX, 63.2, AW, 6.6, 'backend ← MASCOT\nwarn: LowGear infeasible\nat ' + r'$n \geq 10$' + '\n(OOM at 11 GB)', F_IO, NAVY, 6.4)
    arrow(ax, cx, 63.5, cx, 60.1, ms=6); no(cx + 1.5, 61.7)
    dec(cx, 56.4, 13.8, 7.4, 'ram <\n' + RAMMIN + '(LowGear,\n$n$)?', size=6.4)
    arrow(ax, cx + 6.9, 56.4, AX, 56.4, ms=6); yes(14.0, 58.0)
    act(AX, 53.4, AW, 6.0, 'backend ← MASCOT\nwarn: insufficient RAM\nfor LowGear at this $n$', F_IO, NAVY, 6.4)
    arrow(ax, cx, 52.7, cx, 49.6, ms=6); no(cx + 1.5, 51.1)
    dec(cx, 46.9, 10.4, 5.4, r'$n \leq 3$?')
    arrow(ax, cx + 5.2, 46.9, AX, 46.9, ms=6); yes(13.6, 48.4)
    act(AX, 45.0, AW, 3.8, 'backend ← LowGear', F_ACT, GRN, 6.6)
    arrow(ax, cx, 44.2, cx, 41.6, ms=6); no(cx + 1.5, 42.9)
    dec(cx, 37.9, 13.8, 7.2, '$n$ = 5 and\nram ≥ 11 GB?', size=6.6)
    arrow(ax, cx + 6.9, 37.9, AX, 37.9, ms=6); yes(14.0, 39.5)
    act(AX, 34.2, AW, 7.4, 'backend ← LowGear\nwarn: LowGear $n$ = 5:\n~75 min key generation;\ncache keys', F_ACT, GRN, 6.4)
    arrow(ax, cx, 34.3, cx, 32.4, ms=6); no(cx + 1.5, 33.3)
    act(1.4, 28.6, 12.6, 3.8, 'backend ← MASCOT\n(safe default)', F_IO, NAVY, 6.4)
    box(ax, 1.4, 20.4, 27.0, 7.6, fc='white', ec='#555555', lw=0.6)
    text(ax, 2.0, 24.2, 'Observed in the evaluated environment (11 GB):\n'
         r'• LowGear $n$ = 10: OOM at binomial key generation' + '\n'
         r'• LowGear $n$ = 5: ≥ 11 GB RAM; ~75 min key gen.' + '\n'
         r'• MASCOT $n$ = 10: runs within 8 GB RAM', size=6.1, ha='left')

    # ---- stage 2 ----
    cx = 36.4
    dec(cx, 65.0, 11.6, 6.0, 'lat ≥ 50 ms?', fc='#e3f0e4', ec=GRN)
    arrow(ax, cx + 5.8, 65.0, 42.6, 65.0, ms=6); yes(41.0, 66.6)
    act(42.6, 62.6, 11.0, 4.8, '$B$ ← 200\n(high-latency WAN)', F_ACT, GRN, 6.4)
    arrow(ax, cx, 62.0, cx, 58.0, ms=6); no(cx + 1.5, 60.0)
    dec(cx, 55.0, 11.6, 6.0, 'lat ≥ 10 ms?', fc='#e3f0e4', ec=GRN)
    arrow(ax, cx + 5.8, 55.0, 42.6, 55.0, ms=6); yes(41.0, 56.6)
    act(42.6, 52.6, 11.0, 4.8, '$B$ ← 100\n(WAN)', F_ACT, GRN, 6.6)
    arrow(ax, cx, 52.0, cx, 48.6, ms=6); no(cx + 1.5, 50.3)
    act(31.0, 44.2, 10.8, 4.4, '$B$ ← 50\n(below 10 ms)', F_ACT, GRN, 6.8)
    line(ax, [cx, cx], [44.2, 41.4]); arrow(ax, cx, 41.4, 41.0, 40.0, ms=6)
    act(32.0, 34.6, 21.0, 5.4, r'$B \leftarrow \min(B, M)$' + '\n(batch size ≤ computation size)', F_ACT, GRN, 6.8)
    box(ax, 31.0, 20.6, 22.4, 11.4, fc='white', ec='#555555', lw=0.6)
    text(ax, 42.2, 26.3, 'Observed ($n$ = 2, $M$ = 10,000):\n0 ms → 1.67×\n10 ms → 20.07×\n50 ms → 28.02×\n100 ms → 29.38×',
         size=6.8)

    # ---- stage 3 ----
    cx = 64.4
    dec(cx, 62.0, 16.8, 10.0, 'mode =\n“benchmark” or\n“compare”?', fc='#efe1f5', ec=PUR, size=6.6)
    line(ax, [cx - 4.2, 59.6], [59.5, 56.0]); arrow(ax, 59.6, 56.0, 59.6, 54.6, ms=6); yes(57.6, 57.6)
    line(ax, [cx + 4.2, 69.2], [59.5, 56.0]); arrow(ax, 69.2, 56.0, 69.2, 54.6, ms=6); no(71.2, 57.6)
    act(55.8, 44.0, 8.6, 10.6, 'flag ← “-n”\n(no-merge)\n\nexposes\nprotocol-level\nbehavior', F_CFG, PUR, 6.5)
    act(65.0, 44.0, 8.4, 10.6, 'flag ← “”\n(default CISC)\n\nproduction:\nfastest wall-\nclock time', F_CFG, PUR, 6.5)
    box(ax, 56.0, 20.6, 17.4, 11.4, fc='white', ec='#555555', lw=0.6)
    text(ax, 64.7, 26.3, 'Observed:\ndefault CISC ≈ 221\nrounds vs ≈ 20,219\nunmerged rounds\n(91× distortion)', size=6.8)

    # ---- stage 4 ----
    cx = 86.9
    box(ax, 75.6, 59.0, 22.6, 11.6, fc=F_CMP, ec=ORG, lw=0.9)
    text(ax, cx, 68.4, 'Bandwidth reduction (%)', size=7, weight='bold')
    text(ax, cx, 63.0, BW + r'$ = \frac{H}{H + \log\,p} \times \left(1 - \frac{1}{B}\right) \times 100$', size=7.4)
    arrow(ax, cx, 59.0, cx, 56.8, ms=6)
    box(ax, 75.6, 46.8, 22.6, 10.0, fc=F_CMP, ec=ORG, lw=0.9)
    text(ax, cx, 51.8, r'Nominal batching factor $\rho = B$' + '\n(measured round reduction\nat $B$ = 50: 5.6×–36.0×)', size=6.8)
    arrow(ax, cx, 46.8, cx, 44.6, ms=6)
    box(ax, 75.6, 36.6, 22.6, 8.0, fc=F_CMP, ec=ORG, lw=0.9)
    text(ax, cx, 40.6, 'Return output:\nbackend, $B$, flag, ' + BW + r', $\rho$, warnings', size=6.8)
    box(ax, 75.6, 20.6, 22.6, 11.4, fc='white', ec='#555555', lw=0.6)
    text(ax, 76.6, 26.3, 'Where:\n$H$ = 400 bits (header size)\n' + r'$\log\,p$ = 128 bits (field size)' + '\n$B$ = batch size',
         size=6.8, ha='left')

    # ---- output ----
    for x, w, _, c in panels:
        line(ax, [x + w/2, x + w/2], [19.6, 18.0], lw=0.8)
    line(ax, [panels[0][0] + panels[0][1]/2, panels[3][0] + panels[3][1]/2], [18.0, 18.0], lw=0.8)
    arrow(ax, 50, 18.0, 50, 16.6, ms=6)
    box(ax, 22, 13.2, 56, 3.4, fc='#fff4d6', ec='#b8860b', lw=0.9)
    text(ax, 50, 14.9, 'OUTPUT: backend, $B$, flag, ' + BW + r', $\rho$, warnings', size=8)

    # ---- bottom key ----
    box(ax, 0.6, 0.6, 98.8, 11.4, fc='white', ec='#333333', lw=0.8)
    text(ax, 1.8, 10.4, 'Legend:', size=7, weight='bold', ha='left')
    items = [('dec', F_DEC, NAVY, 'Decision'), ('box', F_ACT, GRN, 'Action / selection'), ('box', F_CFG, PUR, 'Configuration'),
             ('box', F_CMP, ORG, 'Computation'), ('box', F_IO, NAVY, 'Input / output')]
    for k, (kind, fc, ec, lab) in enumerate(items):
        x = 2.4 + (k % 2) * 15.0; y = 7.6 - (k // 2) * 2.8
        if kind == 'dec': diamond(ax, x + 1.2, y, 2.4, 2.0, fc, ec)
        else: box(ax, x, y - 0.9, 2.4, 1.8, fc=fc, ec=ec, r=0.2)
        text(ax, x + 3.2, y, lab, size=6.8, ha='left')
    line(ax, [33.4, 33.4], [1.4, 11.2], color='#999999', lw=0.6)
    text(ax, 34.4, 10.4, 'Key empirical findings incorporated:', size=7, weight='bold', ha='left')
    text(ax, 34.4, 5.6, '• Compiler merging distorts round counts by 91×\n• Round complexity dominates under WAN latency\n'
         r'• LowGear hardware limit: $n \geq 10$ infeasible within' + '\n   the 11 GB allocation', size=6.8, ha='left')
    line(ax, [66.8, 66.8], [1.4, 11.2], color='#999999', lw=0.6)
    text(ax, 67.8, 10.4, 'Complexity and calibration:', size=7, weight='bold', ha='left')
    text(ax, 67.8, 5.6, r'• Time complexity: $O(1)$ for a fixed threshold table' + '\n'
         '• Thresholds calibrated to the evaluated\n   environment; recalibrate for other environments', size=6.8, ha='left')
    save(fig, 3)



if __name__ == "__main__":
    fig1(); fig2(); fig3()
