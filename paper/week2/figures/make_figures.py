"""Week 2 figures. Vector PDF, Times-metric serif, greyscale-safe.

Style deliberately matches the Week 1 figures: same width, same serif, same
neutral ramp, one accent. The second hue exists only where two series have to be
told apart, and the pair was checked for colour-vision separation rather than
chosen by eye (worst adjacent dE 20.6 protan, 26.0 normal vision).

Every number below is copied from results/*.json. Nothing here is computed.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif"],
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "pdf.fonttype": 42, "figure.dpi": 200,
})
ACCENT, SECOND = "#2a5d9f", "#b1662a"
INK, MID, LIGHT = "#1a1a1a", "#8a8f96", "#dcdcdc"
W = 3.3

# ------------------------------------------------------------------ Figure 1
# The inversion. Same three evidence sources, ranked by bits and by minutes.
# A slope chart, because the claim is entirely about the order changing.
names = ["admin probe", "well-formedness", "repository context"]
bits = [0.6051, 0.3250, 0.2909]
mins = [0.0000, 1.2696, 0.0000]

def ranks(vals):
    """Competition ranks with ties averaged, so that two sources worth exactly
    the same are drawn at the same height rather than in an arbitrary order.
    The probe and repository context are both worth exactly 0.0000 minutes and
    showing one above the other would invent a distinction."""
    order = sorted(range(len(vals)), key=lambda i: -vals[i])
    out = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


rank_bits = ranks(bits)
rank_mins = ranks(mins)

fig, ax = plt.subplots(figsize=(W, 1.85))
for i, nm in enumerate(names):
    y0 = rank_bits[i]
    y1 = rank_mins[i]
    moved = y0 != y1
    ax.plot([0, 1], [y0, y1], "-", lw=1.8 if moved else 0.9,
            color=ACCENT if moved else MID, zorder=3 if moved else 2,
            solid_capstyle="round")
    ax.plot([0, 1], [y0, y1], "o", ms=4.4,
            color=ACCENT if moved else MID,
            markeredgecolor="white", markeredgewidth=0.8, zorder=4)

# Tied sources share a y, so their labels are drawn once, joined -- two labels
# stacked on one point would read as a collision rather than as a tie.
for side, rk, xx, ha in ((0, rank_bits, -0.045, "right"),
                         (1, rank_mins, 1.045, "left")):
    groups = {}
    for i, nm in enumerate(names):
        groups.setdefault(rk[i], []).append(nm)
    for yv, nms in groups.items():
        lab = " / ".join(nms)
        ax.text(xx, yv, f"{lab}  " if ha == "right" else f"  {lab}",
                ha=ha, va="center", fontsize=7 if len(nms) == 1 else 6.4,
                color=INK)

ax.text(0, -0.75, "ranked by bits", ha="center", va="center", fontsize=7.2,
        color=INK)
ax.text(1, -0.75, "ranked by minutes saved", ha="center", va="center",
        fontsize=7.2, color=INK)
ax.set_xlim(-0.78, 1.86); ax.set_ylim(2.35, -1.25)
ax.set_xticks([]); ax.set_yticks([])
for sp in ("top", "right", "left", "bottom"):
    ax.spines[sp].set_visible(False)
fig.savefig("w2-inversion.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ------------------------------------------------------------------ Figure 2
# What the unstated p_exploit = 1.0 was costing, per class. The whole point is
# that the overall cost barely moves while three of five classes go from
# unreachable to reachable, so cost is plotted beside recall rather than instead.
states = ["live", "revoked", "fake", "zero_scope", "other"]
before = [1.000, 0.000, 0.000, 0.000, 0.500]
after = [0.9859, 0.1085, 0.9542, 0.2857, 0.000]

fig, ax = plt.subplots(figsize=(W, 2.05))
y = np.arange(len(states))[::-1]
h = 0.34
ax.barh(y + h / 2 + 0.02, before, height=h, color=MID, zorder=3,
        label="before (P2, $p_{\\mathrm{exploit}}$ = 1.0 unstated)")
ax.barh(y - h / 2 - 0.02, after, height=h, color=ACCENT, zorder=3,
        label="after (P6, $p_{\\mathrm{exploit}}$ = 0.10 explicit)")
for yy, v in zip(y + h / 2 + 0.02, before):
    ax.text(v + 0.018, yy, f"{v:.3f}", va="center", fontsize=6.3, color="#555")
for yy, v in zip(y - h / 2 - 0.02, after):
    ax.text(v + 0.018, yy, f"{v:.3f}", va="center", fontsize=6.3, color=INK)

ax.set_yticks(y); ax.set_yticklabels(states)
ax.set_xlim(0, 1.19); ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
ax.set_xlabel("per-class recall")
ax.grid(axis="x", lw=0.4, color=LIGHT, zorder=0)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=1,
          frameon=False, fontsize=6.4, handlelength=1.1,
          handletextpad=0.5, borderpad=0.2)
ax.text(0.0, 1.055, "balanced accuracy 0.300 $\\rightarrow$ 0.467   ·   "
        "total cost 60.45 $\\rightarrow$ 59.11 min",
        transform=ax.transAxes, fontsize=6.5, color="#555", va="bottom")
fig.savefig("w2-pexploit.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ------------------------------------------------------------------ Figure 3
# The invariance relocating. Free evidence in each world, in bits, on the three
# state pairs that matter. The two exact zeros are labelled rather than left as
# absent bars, because they are the finding.
axes_lab = ["live vs\nrevoked", "live vs\nzero_scope", "live vs\nfake"]
free_text = [0.0000, 0.0000, 0.3637]      # best of the two text features
ident = [0.8400, 0.0000, 0.8981]

fig, ax = plt.subplots(figsize=(W, 1.95))
x = np.arange(3)
w_ = 0.36
b1 = ax.bar(x - w_ / 2 - 0.015, free_text, width=w_, color=MID, zorder=3,
            label="OpenAI: best free text feature")
b2 = ax.bar(x + w_ / 2 + 0.015, ident, width=w_, color=SECOND, zorder=3,
            label="AWS: free identifier lookup")
for bars, vals in ((b1, free_text), (b2, ident)):
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                v + 0.028, f"{v:.4f}", ha="center", fontsize=6.3,
                color=INK if v > 0 else "#a33", weight="bold" if v == 0 else "normal")

ax.set_xticks(x); ax.set_xticklabels(axes_lab, fontsize=7)
ax.set_ylim(0, 1.02); ax.set_ylabel("mutual information (bits)")
ax.grid(axis="y", lw=0.4, color=LIGHT, zorder=0)
ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1,
          frameon=False, fontsize=6.4, handlelength=1.1,
          handletextpad=0.5, borderpad=0.2)
fig.savefig("w2-invariance.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

print("wrote w2-inversion.pdf w2-pexploit.pdf w2-invariance.pdf")
