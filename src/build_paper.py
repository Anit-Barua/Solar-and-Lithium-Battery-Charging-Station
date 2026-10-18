"""Fill paper/template.tex with numbers from results/results.json -> paper/main.tex.
Usage: python -m src.build_paper   (run `python -m src.run_all` first)"""
import json, os, re
from .config import *
from .weather import month_index  # noqa

ROOT = os.path.join(os.path.dirname(__file__), "..")
M = lambda x, d=2: f"{x / 1e6:.{d}f}"


def tex_case(s):
    return s.replace("%", "\\%").replace(" -", " $-$").replace(" +", " $+$").replace("Scn.", "Scn.\\")


def main():
    R = json.load(open(os.path.join(ROOT, "results", "results.json")))
    f, u, b, mo = R["flows"], R["unit"], R["base"], R["monthly"]
    P = {}
    cA, cB, cN = R["capex"]["A"], R["capex"]["B"], R["capex"]["noBESS"]
    S = {s["case"]: s for s in R["sens"]}
    irr = lambda n: S[n]["irr"] * 100
    base_irr = b["irr"] * 100
    # headline
    P.update(capA=M(cA["total"]), capB=M(cB["total"]), capNB=M(cN["total"]), pv=f"{f['pv']:.1f}", spec=f"{R['specific_yield']:.0f}",
             ev=f"{f['ev']:.0f}", u_total=f"{u['total']:.2f}", price=f"{ECON.price_tk_kwh:.0f}", irr=f"{base_irr:.1f}", irr_pre=f"{b['irr_pre']*100:.1f}",
             pb=str(b["payback"]), npv=M(b["npv"], 1), sh_t=f"{R['share_time']*100:.0f}", sh_a=f"{R['share_annual']*100:.0f}")
    oth = 1.0
    for v in PVC.losses.values():
        oth *= (1 - v)
    P.update(oth_loss=f"{(1-oth)*100:.1f}", ghi=f"{R['ghi_mean']:.2f}", poa=f"{R['poa_mean']:.2f}", tmean=f"{R['t_mean']:.1f}",
             temp_loss=f"{R['temp_loss_pct']:.1f}", tcell=f"{R['tcell_day_mean']:.0f}", cf=f"{R['cap_factor']*100:.1f}")
    # sample days
    hc = lambda a: " ".join(f"({h},{v:.0f})" for h, v in zip(range(25), list(a) + [a[-1]]))
    d = R["dry"]
    P.update(dry_day=str(d["day"]), dry_pv=f"{d['pv_total']:.0f}", d_pv=hc(d["pv"]), d_ev=hc(d["ev"]),
             d_bat=hc([i - o for i, o in zip(d["bin"], d["bout"])]), d_grid=hc([i - e for i, e in zip(d["imp"], d["exp"])]))
    w = R["wet"]
    P.update(wet_days=f"{w['days'][0]}--{w['days'][-1]}", wet_pv=f"{w['pv_mean']:.0f}", wet_soc=f"{w['soc_max']:.0f}",
             w_pv=" ".join(f"({i},{v:.0f})" for i, v in enumerate(w["pv"])), w_soc=" ".join(f"({i},{v:.0f})" for i, v in enumerate(w["soc"])),
             w_imp=" ".join(f"({i},{v:.0f})" for i, v in enumerate(w["imp"])))
    # monthly
    co = lambda a: " ".join(f"({m},{v:.1f})" for m, v in zip(MONTHS, a))
    P.update(m_pv=co(mo["pv"]), m_imp=co(mo["imp"]), m_exp=co(mo["exp"]), m_billed=co(mo["billed"]))
    pk = max(range(12), key=lambda i: mo["pv"][i])
    P.update(pv_peak=f"{mo['pv'][pk]:.0f}", pv_peak_m=MONTHS[pk], pv_low=f"{min(mo['pv'][5], mo['pv'][6]):.0f}",
             imp_min=f"{min(mo['imp']):.0f}", imp_max=f"{max(mo['imp']):.0f}", bank_pk=f"{max(mo['bank']):.1f}",
             billed_jj=f"{mo['billed'][5] + mo['billed'][6]:.1f}", dpv_min=f"{R['daily']['pv_min']:.0f}", dpv_max=f"{R['daily']['pv_max']:.0f}")
    P.update(direct=f"{f['direct']:.1f}", bout=f"{f['bout']:.1f}", bloss=f"{f['bin']-f['bout']:.1f}", aux=f"{f['aux']:.1f}",
             imp=f"{f['imp']:.1f}", exp=f"{f['exp']:.1f}", billed_c=f"{f['billed_carry']:.1f}", billed_m=f"{f['billed_month']:.1f}")
    # capex table
    labels = [("pv", "PV modules"), ("inv", "Inverters"), ("bess", "BESS, PCS, EMS"), ("bos", "Mounting, BOS, installation"),
              ("ev", "Charging bays, billing"), ("grid", "Transformer, net meter"), ("civil", "Civil works")]
    rows = []
    for k, lab in labels:
        a, fr, tx = cA["rows"][k]
        z = lambda x: "--" if x == 0 else M(x)
        rows.append(f"{lab} & {M(a)} & {z(fr)} & {z(tx)} & {M(sum(cA['rows'][k]))} & {M(sum(cB['rows'][k]))} \\\\")
    P["cap_rows"] = "\n".join(rows)
    P.update(c_fob=M(cA["fob"]), c_fr=M(cA["freight"]), c_tx=M(cA["tax"]), c_subA=M(cA["sub"]), c_subB=M(cB["sub"]), c_engA=M(cA["eng"]),
             c_engB=M(cB["eng"]), c_contA=M(cA["cont"]), c_contB=M(cB["cont"]), txA=M(cA["tax"]), txB=M(cB["tax"]),
             capA_usd=f"{cA['total']/ECON.fx/1e3:.0f}", txA_pct=f"{cA['tax']/cA['total']*100:.1f}", capdiff=M(cB["total"] - cA["total"]))
    P["capA_pts"] = " ".join(f"({sum(cA['rows'][k])/1e6:.2f},{i+1})" for i, (k, _) in enumerate(labels))
    P["capB_pts"] = " ".join(f"({sum(cB['rows'][k])/1e6:.2f},{i+1})" for i, (k, _) in enumerate(labels))
    P.update(bin=f"{f['bin']:.1f}", billed_n=f"{f['billed_none']:.1f}")
    from .economics import crf
    bess_tot = sum(cA["rows"]["bess"]) * (1 + ECON.eng_frac * 0.0) * (1 + 0.113)
    bess_ann = bess_tot * crf(ECON.discount, ECON.life_years) + ECON.insurance_frac * bess_tot \
        + 0.5 * ECON.fob["bess"] * ECON.fx / (1 + ECON.discount) ** BAT.replacement_year * crf(ECON.discount, ECON.life_years)
    tou_val = f["bout"] * 1000 * (14.20 - 10.22) * (1 + TAR.bill_vat)
    P.update(tou_val=M(tou_val), bess_ann=M(bess_ann), tou_cov=f"{tou_val / bess_ann * 100:.0f}",
             b_grid=f"{TAR.energy_tk_kwh * (1 + TAR.bill_vat) * LOAD.kwh_per_vehicle:.0f}", b_comm=f"{15.36 * LOAD.kwh_per_vehicle:.0f}")
    # opex
    y1, it = b["y1"], R["y1_items"]
    P.update(y1_bill=M(y1["grid_bill"]), y1_rev=M(y1["revenue"]), y1_opex=M(y1["opex"]), y1_ebitda=M(y1["ebitda"]), gross=M(it["gross"]),
             vat=M(it["gross"] - y1["revenue"]), om=M(it["om"]), ins=M(it["insurance"]), dem_fee=M(it["demand"] + it["fee"]),
             u_cap=f"{u['capital']:.2f}", u_fix=f"{u['fixed']:.2f}", u_fee=f"{u['fees']:.2f}", u_repl=f"{u['replacement']:.2f}", u_grid=f"{u['grid']:.2f}",
             u_net=f"{u['net_price']:.2f}", u_margin=f"{u['margin']:.2f}", veh_price=f"{ECON.price_tk_kwh*LOAD.kwh_per_vehicle:.0f}",
             veh_cost=f"{u['total']*LOAD.kwh_per_vehicle:.0f}", be=f"{R['breakeven']:.1f}", be_veh=f"{R['breakeven']*LOAD.kwh_per_vehicle:.0f}")
    P["mon_tab"] = "\n".join(f"{MONTHS[m]} & {mo['ghi'][m]:.2f} & {mo['pv'][m]:.1f} & {mo['imp'][m]:.1f} & {mo['exp'][m]:.1f} & {mo['billed'][m]:.1f} \\\\" for m in range(12))
    cc = lambda c: " ".join(f"({i},{v/1e6:.1f})" for i, v in enumerate(c))
    P.update(cum_A=cc(S["Base (Scn. A, Tk 24/kWh)"]["cum"]), cum_B=cc(S["Pre-budget duties (Scn. B)"]["cum"]), cum_nb=cc(S["PV + grid only (no BESS)"]["cum"]), cum_nm=cc(S["No net-metering credit"]["cum"]))
    P["npv_A"] = " ".join(f"({p},{v/1e6:.1f})" for p, v in R["npv_price"]["A"])
    P["npv_B"] = " ".join(f"({p},{v/1e6:.1f})" for p, v in R["npv_price"]["B"])
    # sensitivity
    P["sens"] = "\n".join(f"{tex_case(s['case'])} & {M(s['capex'],1)} & {s['irr']*100:.1f} & {M(s['npv'],1)} & {s['payback'] if s['payback'] else '$>$20'} \\\\" for s in R["sens"])
    tor = [("Capex $\\pm$20\\%", "Capex +20%", "Capex -20%"), ("Price $\\pm$Tk 2", "Price Tk 26/kWh", "Price Tk 22/kWh"),
           ("Irradiation $\\pm$10\\%", "Irradiation +10%", "Irradiation -10%"), ("Throughput $\\pm$20\\%", "Throughput +20%", "Throughput -20%"),
           ("Grid tariff +10\\%", None, "Grid tariff +10%")]
    # favourable/unfavourable: capex +20 is unfavourable
    fav = {"Capex $\\pm$20\\%": "Capex -20%", "Price $\\pm$Tk 2": "Price Tk 26/kWh", "Irradiation $\\pm$10\\%": "Irradiation +10%", "Throughput $\\pm$20\\%": "Throughput +20%"}
    unf = {"Capex $\\pm$20\\%": "Capex +20%", "Price $\\pm$Tk 2": "Price Tk 22/kWh", "Irradiation $\\pm$10\\%": "Irradiation -10%", "Throughput $\\pm$20\\%": "Throughput -20%", "Grid tariff +10\\%": "Grid tariff +10%"}
    names = [t[0] for t in tor]
    P["tor_labels"] = ",".join("{" + n + "}" for n in reversed(names))
    P["tor_hi"] = " ".join(f"({(irr(fav[n]) - base_irr) if n in fav else 0:.1f},{len(names)-i})" for i, n in enumerate(names))
    P["tor_lo"] = " ".join(f"({irr(unf[n]) - base_irr:.1f},{len(names)-i})" for i, n in enumerate(names))
    P.update(irr_none=f"{irr('No net-metering credit'):.1f}", d_carry=f"{base_irr - irr('Monthly netting, no carry-forward'):.1f}",
             d_capex=f"+{irr('Capex -20%') - base_irr:.1f}/$-${base_irr - irr('Capex +20%'):.1f}",
             d_thru=f"+{irr('Throughput +20%') - base_irr:.1f}/$-${base_irr - irr('Throughput -20%'):.1f}",
             irr_B=f"{irr('Pre-budget duties (Scn. B)'):.1f}", irr_nb=f"{irr('PV + grid only (no BESS)'):.1f}")
    P.update(co2=f"{R['co2_t']:.0f}", fleet_mwh=f"{R['fleet']['mwh_day']:.0f}", fleet_mw=f"{R['fleet']['mw_avg']:.1f}",
             fleet_n=f"{R['fleet']['stations']:.0f}", fleet_cap=f"{R['fleet']['capex_tk']/1e9:.1f}")
    tex = open(os.path.join(ROOT, "paper", "template.tex")).read()
    for k, v in P.items():
        tex = tex.replace("@@" + k + "@@", str(v))
    left = set(re.findall(r"@@\w+@@", tex))
    assert not left, left
    open(os.path.join(ROOT, "paper", "main.tex"), "w").write(tex)
    print("Wrote paper/main.tex")


if __name__ == "__main__":
    main()
