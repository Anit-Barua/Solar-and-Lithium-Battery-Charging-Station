"""Create the paper's figures as vector PDFs in paper/figures/ from results/results.json.
Usage: python -m src.make_figures   (run `python -m src.run_all` first)"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from .config import MONTHS

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "paper", "figures")
W = 3.45  # IEEE single-column width (in)
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 7, "axes.labelsize": 7.5,
                     "legend.fontsize": 6.2, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.4,
                     "lines.linewidth": 1.1, "savefig.bbox": "tight", "savefig.pad_inches": 0.02})
C = dict(pv="#e08a00", ev="#1f4e9c", bat="#2a8a3e", grid="#c0392b", a="#3a6fb5", b="#c0392b", g="#2a8a3e", k="#222222")


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    plt.close(fig)


def step(ax, y, x0=0, **kw):
    ax.step(list(range(x0, x0 + len(y) + 1)), list(y) + [y[-1]], where="post", **kw)


def architecture():
    fig, ax = plt.subplots(figsize=(W, 2.15)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6.2); ax.grid(False)
    def box(x, y, w, h, txt, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.1", fc=fc, ec="#333", lw=0.7))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=5.9, linespacing=1.15)
    box(0.1, 4.5, 2.3, 1.3, "500 kWp\nPV array", "#fff2c6"); box(3.0, 4.5, 2.6, 1.3, "5 x 100 kW\ninverters", "#e6eefb")
    box(3.0, 2.5, 2.6, 1.3, "500 kWh LFP BESS\n250 kW PCS", "#e6eefb"); box(3.0, 0.5, 2.6, 1.3, "400 kVA, 11/0.4 kV\n+ net meter", "#e6eefb")
    box(0.1, 0.5, 2.3, 1.3, "Utility grid\n(11 kV)", "#dff3df"); box(6.7, 3.2, 3.2, 1.6, "EV charging\n280 bays x 1.5 kW\n(managed to 250 kW)", "#ffe3c4")
    box(6.7, 0.7, 3.2, 1.3, "EMS: dispatch,\nbilling, SCADA", "#e8e8e8")
    ax.plot([6.15, 6.15], [0.3, 5.9], lw=3, color="#222", solid_capstyle="butt"); ax.text(6.15, 6.0, "0.4 kV AC bus", ha="center", va="bottom", fontsize=5.9)
    one = dict(arrowprops=dict(arrowstyle="->", lw=0.8, color="#222")); two = dict(arrowprops=dict(arrowstyle="<->", lw=0.8, color="#222"))
    ax.annotate("", xy=(3.0, 5.15), xytext=(2.4, 5.15), **one); ax.annotate("", xy=(6.1, 5.15), xytext=(5.6, 5.15), **one)
    ax.annotate("", xy=(6.1, 3.15), xytext=(5.6, 3.15), **two); ax.annotate("", xy=(6.1, 1.15), xytext=(5.6, 1.15), **two)
    ax.annotate("", xy=(3.0, 1.15), xytext=(2.4, 1.15), **two); ax.annotate("", xy=(6.7, 4.0), xytext=(6.2, 4.0), **one)
    ax.annotate("", xy=(6.2, 1.35), xytext=(6.7, 1.35), arrowprops=dict(arrowstyle="<->", lw=0.8, color="#222", ls="--"))
    save(fig, "fig_architecture")


def dry_day(R):
    d = R["dry"]; fig, ax = plt.subplots(figsize=(W, 2.0)); h = range(24)
    step(ax, d["pv"], color=C["pv"], label="PV"); step(ax, d["ev"], color=C["ev"], label="EV load")
    step(ax, [i - o for i, o in zip(d["bin"], d["bout"])], color=C["bat"], label="BESS (+charge / $-$discharge)")
    step(ax, [i - e for i, e in zip(d["imp"], d["exp"])], color=C["grid"], ls="--", label="Grid (+import / $-$export)")
    ax.axhline(0, color="k", lw=0.5); ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3)); ax.set_xlabel("Hour of day"); ax.set_ylabel("Power (kW)")
    ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.28), frameon=False); save(fig, "fig_dry_day")


def monsoon(R):
    w = R["wet"]; fig, ax = plt.subplots(figsize=(W, 2.0)); n = len(w["pv"])
    step(ax, w["pv"], color=C["pv"], label="PV (kW)"); step(ax, w["soc"], color=C["bat"], label="Battery charge (kWh)")
    step(ax, w["imp"], color=C["grid"], ls="--", label="Grid import (kW)")
    ax.set_xlim(0, n); ax.set_xticks(range(0, n + 1, 12)); ax.set_xlabel("Hour (three lowest-yield consecutive monsoon days)"); ax.set_ylabel("kW or kWh")
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.2), frameon=False); save(fig, "fig_monsoon")


def monthly(R):
    m = R["monthly"]; fig, ax = plt.subplots(figsize=(W, 2.1)); x = range(12); bw = 0.2
    for i, (k, lab, col) in enumerate((("pv", "PV", C["pv"]), ("imp", "Import", C["grid"]), ("exp", "Export", C["bat"]), ("billed", "Billed", C["a"]))):
        ax.bar([j + (i - 1.5) * bw for j in x], m[k], bw, label=lab, color=col)
    ax.set_xticks(list(x)); ax.set_xticklabels(MONTHS); ax.set_ylabel("MWh per month"); ax.grid(axis="x", visible=False)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.17), frameon=False); save(fig, "fig_monthly")


def capex(R):
    names = ["PV modules", "Inverters", "BESS, PCS, EMS", "Mounting, BOS, install.", "Charging bays", "Transformer, meter", "Civil works"]
    keys = ["pv", "inv", "bess", "bos", "ev", "grid", "civil"]; fig, ax = plt.subplots(figsize=(W, 2.1)); y = range(len(keys))
    a = [sum(R["capex"]["A"]["rows"][k]) / 1e6 for k in keys]; b = [sum(R["capex"]["B"]["rows"][k]) / 1e6 for k in keys]
    ax.barh([i - 0.18 for i in y], a, 0.36, color=C["a"], label="Scenario A"); ax.barh([i + 0.18 for i in y], b, 0.36, color=C["b"], label="Scenario B")
    ax.set_yticks(list(y)); ax.set_yticklabels(names); ax.invert_yaxis(); ax.set_xlabel("Tk million (incl. freight, duties, VAT)"); ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", frameon=False); save(fig, "fig_capex")


def cumulative(R):
    S = {s["case"]: s for s in R["sens"]}; fig, ax = plt.subplots(figsize=(W, 2.0))
    for name, lab, col, ls in (("Base (Scn. A, Tk 24/kWh)", "Base (Scn. A)", C["a"], "-"), ("Pre-budget duties (Scn. B)", "Scn. B", C["b"], "--"),
                               ("PV + grid only (no BESS)", "No BESS", C["g"], ":"), ("No net-metering credit", "No export credit", C["k"], "-.")):
        ax.plot(range(21), [v / 1e6 for v in S[name]["cum"]], color=col, ls=ls, label=lab)
    ax.axhline(0, color="k", lw=0.5); ax.set_xlim(0, 20); ax.set_xticks(range(0, 21, 2)); ax.set_xlabel("Year"); ax.set_ylabel("Cumulative post-tax cash (Tk M)")
    ax.legend(loc="upper left", frameon=False); save(fig, "fig_cumulative")


def npv_price(R):
    fig, ax = plt.subplots(figsize=(W, 2.0))
    for s, col, ls, lab in (("A", C["a"], "-", "Scenario A"), ("B", C["b"], "--", "Scenario B")):
        p, v = zip(*R["npv_price"][s]); ax.plot(p, [x / 1e6 for x in v], color=col, ls=ls, marker="o", ms=2.5, label=lab)
    ax.axhline(0, color="k", lw=0.5); ax.set_xlabel("Selling price incl. VAT (Tk/kWh)"); ax.set_ylabel("NPV at 10% (Tk M)"); ax.legend(loc="upper left", frameon=False)
    save(fig, "fig_npv_price")


def tornado(R):
    S = {s["case"]: s["irr"] * 100 for s in R["sens"]}; base = S["Base (Scn. A, Tk 24/kWh)"]
    rows = [("Capex $\\pm$20%", "Capex -20%", "Capex +20%"), ("Throughput $\\pm$20%", "Throughput +20%", "Throughput -20%"),
            ("Price $\\pm$Tk 2", "Price Tk 26/kWh", "Price Tk 22/kWh"), ("Irradiation $\\pm$10%", "Irradiation +10%", "Irradiation -10%"),
            ("Grid tariff +10%", None, "Grid tariff +10%")]
    fig, ax = plt.subplots(figsize=(W, 1.9))
    for i, (lab, hi, lo) in enumerate(rows):
        if hi: ax.barh(i, S[hi] - base, 0.5, color=C["g"], label="Favourable" if i == 0 else None)
        ax.barh(i, S[lo] - base, 0.5, color=C["b"], label="Unfavourable" if i == 0 else None)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis(); ax.axvline(0, color="k", lw=0.6)
    ax.set_xlabel("Change in post-tax IRR (percentage points)"); ax.grid(axis="y", visible=False); ax.legend(loc="lower right", frameon=False); save(fig, "fig_tornado")


def main():
    R = json.load(open(os.path.join(ROOT, "results", "results.json")))
    architecture(); dry_day(R); monsoon(R); monthly(R); capex(R); cumulative(R); npv_price(R); tornado(R)
    print("Wrote PDF figures to", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
