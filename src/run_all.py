"""Run the full analysis and write results/*.csv and results/results.json.
Usage:  python -m src.run_all"""
import csv, json, os
import numpy as np
from .config import *
from .economics import Model, capex, crf
from .netmeter import net_metering, monthly_sum
from .weather import month_index

ROOT = os.path.join(os.path.dirname(__file__), "..")
CSV = os.path.join(ROOT, "data", "nasa_power_cox_bazar_2025_hourly.csv")
OUT = os.path.join(ROOT, "results")


def L(a):
    return np.asarray(a).tolist()


def main():
    os.makedirs(OUT, exist_ok=True)
    M = Model(CSV)
    R = {}
    mi = month_index()
    w = M.w
    # ---- weather
    R["ghi_mean"] = w["ghi"].sum() / 1000 / 365
    R["poa_mean"] = M.poa.sum() / 1000 / 365
    R["ghi_monthly"] = [w["ghi"][mi == m].sum() / 1000 / (mi == m).sum() for m in range(12)]
    R["t_mean"] = float(w["t2m"].mean())
    o = M.year(1)
    tf = 1 + PVC.gamma * (M.tcell - 25)
    R["temp_loss_pct"] = float((1 - (tf * M.poa).sum() / M.poa.sum()) * 100)
    R["tcell_day_mean"] = float(M.tcell[M.poa > 50].mean())
    # ---- annual flows (MWh)
    mwh = lambda k: float(o[k].sum() / 1e3)
    day = np.zeros(24, bool); day[LOAD.day_hours[0]:LOAD.day_hours[1]] = True
    direct = sum(min(o["ev"][d, h], max(o["pv"][d, h] - o["aux"][d, h], 0)) for d in range(365) for h in range(24) if day[h]) / 1e3
    billed_c, bank = net_metering(o["imp"], o["exp"], "carry")
    billed_m, _ = net_metering(o["imp"], o["exp"], "month")
    billed_n, _ = net_metering(o["imp"], o["exp"], "none")
    R["flows"] = {k: mwh(k) for k in ("pv", "ev", "imp", "exp", "bin", "bout", "aux")}
    R["flows"]["direct"] = float(direct)
    R["flows"].update(billed_carry=float(billed_c.sum() / 1e3), billed_month=float(billed_m.sum() / 1e3), billed_none=float(billed_n.sum() / 1e3))
    f = R["flows"]
    R["share_time"] = (f["direct"] + f["bout"]) / f["ev"]
    R["share_annual"] = 1 - f["billed_carry"] / f["ev"]
    R["cap_factor"] = f["pv"] * 1e3 / (PVC.kwp * 8760)
    R["specific_yield"] = f["pv"] * 1e3 / PVC.kwp
    R["pr"] = f["pv"] * 1e3 / (M.poa.sum() / 1000 * PVC.kwp)       # AC energy / POA energy at STC
    R["co2_t"] = f["pv"] * ECON.ef_t_per_mwh
    R["monthly"] = dict(ghi=R["ghi_monthly"], pv=L(monthly_sum(o["pv"]) / 1e3), imp=L(monthly_sum(o["imp"]) / 1e3),
                        exp=L(monthly_sum(o["exp"]) / 1e3), billed=L(billed_c / 1e3), bank=L(bank / 1e3), ev=L(monthly_sum(o["ev"]) / 1e3))
    dpv, dimp = o["pv"].sum(1), o["imp"].sum(1)
    R["daily"] = dict(pv_min=float(dpv.min()), pv_max=float(dpv.max()), pv_mean=float(dpv.mean()), imp_min=float(dimp.min()), imp_max=float(dimp.max()),
                      pv_sorted=L(np.sort(dpv)[::-1][::5]), imp_sorted=L(np.sort(dimp)[::-1][::5]))
    # sample days
    dry = int(np.argmax(dpv[0:90]))
    st = min(range(150, 270), key=lambda s: dpv[s:s + 3].sum())
    wet = [st, st + 1, st + 2]
    R["dry"] = dict(day=dry + 1, **{k: L(o[k][dry]) for k in ("pv", "ev", "imp", "exp", "bin", "bout", "soc")}, pv_total=float(dpv[dry]))
    R["wet"] = dict(days=[d + 1 for d in wet], pv=L(np.concatenate([o["pv"][d] for d in wet])), soc=L(np.concatenate([o["soc"][d] for d in wet])),
                    imp=L(np.concatenate([o["imp"][d] for d in wet])), pv_mean=float(np.mean([dpv[d] for d in wet])),
                    soc_max=float(max(o["soc"][d].max() for d in wet)))
    # ---- capex
    def cap_dict(scn, bess=True):
        rows, sub, eng, cont, tot = capex(scn, bess)
        return dict(rows={k: list(v) for k, v in rows.items()}, sub=sub, eng=eng, cont=cont, total=tot,
                    tax=sum(v[2] for v in rows.values()), freight=sum(v[1] for v in rows.values()), fob=sum(v[0] for v in rows.values()))
    cA, cB, cN = cap_dict("A"), cap_dict("B"), cap_dict("A", False)
    R["capex"] = dict(A=cA, B=cB, noBESS=cN)
    # ---- base case
    base = M.cashflow(cA["total"])
    d1 = base["detail"][0]
    R["base"] = dict(irr=base["irr"], irr_pre=base["irr_pre"], npv=base["npv"], payback=base["payback"], cum=L(base["cum"]), y1=d1)
    omy = ECON.om_frac_pv_bos * (ECON.fob["pv"] + ECON.fob["inv"] + ECON.fob["bos"]) * ECON.fx
    R["y1_items"] = dict(om=omy, insurance=ECON.insurance_frac * cA["total"], staff=ECON.staff_tk, land=ECON.land_tk,
                         demand=TAR.demand_kw * TAR.demand_tk_kw_month * 12, fee=ECON.fee_frac_revenue * d1["revenue"],
                         gross=d1["sold_kwh"] * ECON.price_tk_kwh, depreciation=cA["total"] / ECON.dep_years)
    sold = d1["sold_kwh"]
    ann = cA["total"] * crf(ECON.discount, ECON.life_years)
    repl = (0.5 * ECON.fob["bess"] + 0.6 * ECON.fob["inv"]) * ECON.fx / (1 + ECON.discount) ** BAT.replacement_year * crf(ECON.discount, ECON.life_years)
    fixed = R["y1_items"]["om"] + R["y1_items"]["insurance"] + ECON.staff_tk + ECON.land_tk + R["y1_items"]["demand"]
    u = dict(capital=ann / sold, fixed=fixed / sold, fees=R["y1_items"]["fee"] / sold, replacement=repl / sold, grid=d1["grid_bill"] / sold)
    R["unit"] = dict(u, total=sum(u.values()), net_price=ECON.price_tk_kwh / (1 + TAR.sale_vat))
    R["unit"]["margin"] = R["unit"]["net_price"] - R["unit"]["total"]
    R["breakeven"] = M.breakeven_price(cA["total"])
    R["npv_price"] = {s: [[p, M.cashflow(c["total"], price=p)["npv"]] for p in range(16, 33, 2)] for s, c in (("A", cA), ("B", cB))}
    # ---- sensitivities
    cases = [("Base (Scn. A, Tk 24/kWh)", cA["total"], {}),
             ("Capex -20%", cA["total"] * .8, {}), ("Capex +20%", cA["total"] * 1.2, {}),
             ("Price Tk 22/kWh", cA["total"], dict(price=22)), ("Price Tk 26/kWh", cA["total"], dict(price=26)),
             ("Pre-budget duties (Scn. B)", cB["total"], {}), ("Income-tax exemption", cA["total"], dict(tax=0.0)),
             ("Irradiation -10%", cA["total"], dict(pv_scale=0.9)), ("Irradiation +10%", cA["total"], dict(pv_scale=1.1)),
             ("Grid tariff +10%", cA["total"], dict(tariff=TAR.energy_tk_kwh * 1.1)),
             ("Throughput -20%", cA["total"], dict(ev_scale=0.8)), ("Throughput +20%", cA["total"], dict(ev_scale=1.2)),
             ("Monthly netting, no carry-forward", cA["total"], dict(mode="month")),
             ("PV + grid only (no BESS)", cN["total"], dict(bess=False)),
             ("No net-metering credit", cA["total"], dict(mode="none"))]
    R["sens"] = []
    for name, c, kw in cases:
        r = M.cashflow(c, **kw)
        R["sens"].append(dict(case=name, capex=c, irr=r["irr"], npv=r["npv"], payback=r["payback"], cum=L(r["cum"])))
    R["npc"] = cA["total"] + sum(d["opex"] / (1 + ECON.discount) ** d["year"] for d in base["detail"]) + (0.5 * ECON.fob["bess"] + 0.6 * ECON.fob["inv"]) * ECON.fx / (1 + ECON.discount) ** BAT.replacement_year
    R["lcoe_npc"] = R["npc"] * crf(ECON.discount, ECON.life_years) / sold
    R["fleet"] = dict(mwh_day=23000 * LOAD.kwh_per_vehicle / 1000, mw_avg=23000 * LOAD.kwh_per_vehicle / 24 / 1000,
                      stations=23000 * LOAD.kwh_per_vehicle / (sold / 365))
    R["fleet"]["capex_tk"] = R["fleet"]["stations"] * cA["total"]
    json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1)
    # ---- CSV outputs
    with open(os.path.join(OUT, "hourly_dispatch_year1.csv"), "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["month", "day_of_year", "hour", "ghi_Wm2", "poa_Wm2", "t_cell_C", "pv_kWh", "ev_kWh", "grid_import_kWh", "grid_export_kWh", "bess_charge_kWh", "bess_discharge_kWh", "bess_soc_kWh"])
        for d in range(365):
            for h in range(24):
                wr.writerow([int(mi[d]) + 1, d + 1, h, round(w["ghi"][d, h], 2), round(M.poa[d, h], 2), round(M.tcell[d, h], 2)] + [round(o[k][d, h], 3) for k in ("pv", "ev", "imp", "exp", "bin", "bout", "soc")])
    with open(os.path.join(OUT, "monthly_summary.csv"), "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["month", "ghi_kWh_m2_day", "pv_MWh", "import_MWh", "export_MWh", "billed_MWh", "credit_bank_MWh"])
        for m in range(12):
            wr.writerow([MONTHS[m]] + [round(R["monthly"][k][m], 3) for k in ("ghi", "pv", "imp", "exp", "billed", "bank")])
    with open(os.path.join(OUT, "sensitivity.csv"), "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["case", "capex_Tk_M", "post_tax_IRR_pct", "NPV_Tk_M", "payback_yr"])
        for s in R["sens"]:
            wr.writerow([s["case"], round(s["capex"] / 1e6, 2), round(s["irr"] * 100, 2), round(s["npv"] / 1e6, 2), s["payback"]])
    with open(os.path.join(OUT, "capex_breakdown.csv"), "w", newline="") as fh:
        wr = csv.writer(fh); wr.writerow(["item", "scenario", "fob_Tk_M", "freight_Tk_M", "duty_vat_Tk_M", "total_Tk_M"])
        for scn, c in (("A", cA), ("B", cB)):
            for k, v in c["rows"].items():
                wr.writerow([k, scn, *(round(x / 1e6, 3) for x in v), round(sum(v) / 1e6, 3)])
    print("Wrote results to", os.path.abspath(OUT))
    print(f"PV {f['pv']:.1f} MWh | import {f['imp']:.1f} | export {f['exp']:.1f} | billed {f['billed_carry']:.1f}")
    print(f"Capex A {cA['total']/1e6:.2f} M, B {cB['total']/1e6:.2f} M | IRR {base['irr']*100:.1f}% NPV {base['npv']/1e6:.1f} M payback {base['payback']} | unit {R['unit']['total']:.2f}")
    return R


if __name__ == "__main__":
    main()
