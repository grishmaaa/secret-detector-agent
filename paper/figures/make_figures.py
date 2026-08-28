"""Figures for the preprint. Vector PDF, Times-metric serif, greyscale-safe."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif"],
    "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "pdf.fonttype": 42, "figure.dpi": 200,
})
ACCENT, INK, MID, LIGHT = "#2a5d9f", "#1a1a1a", "#8a8f96", "#dcdcdc"
W = 3.3   # single column width, inches

# ---------------------------------------------------------------- Figure 2
# The regime line: where the derived boundary sits, and where 0.5 sits.
fig, ax = plt.subplots(figsize=(W, 1.35))
lo, hi = 3e-4, 1.0
b1, b2 = 0.00145, 0.06588
BAND_D, BAND_V, BAND_R = "#e9e9e9", "#b6c7db", "#6f97c4"

ax.add_patch(Rectangle((lo, 0), b1-lo, 1, color=BAND_D, lw=0))
ax.add_patch(Rectangle((b1, 0), b2-b1, 1, color=BAND_V, lw=0))
ax.add_patch(Rectangle((b2, 0), hi-b2, 1, color=BAND_R, lw=0))

for x, lab in [(b1, "0.00145"), (b2, "0.06588")]:
    ax.axvline(x, color=INK, lw=1.0, zorder=5)
    ax.text(x, 1.07, lab, ha="center", va="bottom", fontsize=6.6, color=INK)
ax.axvline(0.5, color=INK, lw=1.0, ls=(0, (3, 2)), zorder=5)
ax.text(0.5, 1.07, "0.5", ha="center", va="bottom", fontsize=6.6, color=INK)
ax.text(0.985, 1.30, "where instinct puts it", ha="right", va="bottom",
        fontsize=6.6, color="#555", transform=ax.transAxes)

ax.text(np.sqrt(lo*b1), .52, "dismiss", ha="center", va="center",
        fontsize=6.8, color="#666")
ax.text(np.sqrt(b1*b2), .52, "revoke now", ha="center", va="center",
        fontsize=7.2, color=INK)
ax.text(np.sqrt(b2*hi), .52, "rotate safely", ha="center", va="center",
        fontsize=7.2, color="white")

reach = [0.0045, 0.0362, 0.2400, 0.3294, 0.5754, 0.6329]
ax.plot(reach, [0.19]*6, "o", ms=4.0, color="#12305a",
        markeredgecolor="white", markeredgewidth=0.8, zorder=6)

ax.set_xscale("log"); ax.set_xlim(lo, hi); ax.set_ylim(0, 1)
ax.set_yticks([]); ax.set_xlabel(r"$P(\mathrm{live})$", labelpad=2)
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
ax.spines["bottom"].set_position(("outward", 4))
fig.savefig("regimes.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---------------------------------------------------------------- Figure 3
# Escalation as a function of one guessed number.
fig, ax = plt.subplots(figsize=(W, 1.75))
h  = [1, 2, 3, 5, 8, 10, 12, 15, 20, 25, 30, 45, 60]
esc= [100, 100, 100, 89.42, 89.42, 89.42, 15.62, 1.20, 0, 0, 0, 0, 0]
ax.plot(h, esc, "-", lw=1.6, color=ACCENT, zorder=3)
ax.plot(h, esc, "o", ms=3.4, color=ACCENT, markeredgecolor="white",
        markeredgewidth=0.6, zorder=4)

ax.axvline(15.03, color=MID, lw=0.8, ls=(0, (2, 2)), zorder=2)
ax.text(15.03, 104, " VPI bound\n 15.03", fontsize=6.6, color="#555", va="bottom", ha="left")
ax.axvline(30, color=INK, lw=0.8, ls=(0, (1, 2)), zorder=2)
ax.text(30, 55, " our assumed\n cost, 30 min", fontsize=6.6, color=INK, va="center", ha="left")

ax.set_xlim(0, 62); ax.set_ylim(-4, 108)
ax.set_xlabel("cost of one human interruption (minutes)")
ax.set_ylabel("findings escalated (%)")
ax.set_yticks([0, 25, 50, 75, 100])
ax.grid(axis="y", lw=0.4, color=LIGHT, zorder=0)
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
fig.savefig("escalation.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)

# ---------------------------------------------------------------- Figure 4
# Point estimates against their sampled distributions. Small multiples --
# the quantities have different units, so they get different axes.
rows = [
    ("P2 saving vs baseline (%)", 0.53, 19.23, 51.27, 23.2, (0, 55)),
    ("value of belief model (min)",  0.00,  0.87,  6.31,  1.75, (0, 7)),
    ("revoke/rotate boundary",     -0.136, 0.059, 0.600, 0.0659, (-0.2, 0.65)),
    ("max VPI, reachable (min)",     1.37, 12.12, 32.12, 15.03, (0, 35)),
]
fig, axes = plt.subplots(len(rows), 1, figsize=(W, 2.20))
for ax, (lab, p5, med, p95, pt, xlim) in zip(axes, rows):
    ax.hlines(0, p5, p95, color=MID, lw=2.4, zorder=2)
    ax.plot([med], [0], "o", ms=4.6, color=MID, markeredgecolor="white",
            markeredgewidth=0.8, zorder=3)
    ax.plot([pt], [0], "D", ms=4.6, color=ACCENT, markeredgecolor="white",
            markeredgewidth=0.8, zorder=4)
    ax.set_xlim(*xlim); ax.set_ylim(-1, 1); ax.set_yticks([])
    ax.text(0.0, 0.92, lab, transform=ax.transAxes, fontsize=6.8,
            va="bottom", ha="left", color=INK)
    for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
    ax.tick_params(axis="x", pad=1.5)
axes[0].plot([], [], "o", ms=4.6, color=MID, label="median of 40,000 draws")
axes[0].plot([], [], "D", ms=4.6, color=ACCENT, label="value used in the paper")
h_, l_ = axes[0].get_legend_handles_labels()
fig.legend(h_, l_, loc="upper center", bbox_to_anchor=(0.5, 1.06), ncol=2,
           frameon=False, fontsize=6.6, handletextpad=0.4, columnspacing=1.6)
fig.subplots_adjust(hspace=1.6, top=0.88)
fig.savefig("intervals.pdf", bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print("wrote regimes.pdf escalation.pdf intervals.pdf")
