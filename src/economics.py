"""Capital cost, cash flow, IRR/NPV, unit cost and sensitivities."""
import functools
import numpy as np
from .config import ECON, TAR, BAT, PVC
from .dispatch import simulate
from .netmeter import net_metering
from .pv import pv_ac_kw
from .weather import load_nasa, poa_and_tcell

IMPORTED = ("pv", "inv", "bess")
MIXED = ("ev", "grid")


def capex(scn="A", bess=True, e=ECON):
    """Return (rows, subtotal, engineering, contingency, total) in Tk. rows[k] = (fob, freight, tax) in Tk."""
    rates = e.tax_A if scn == "A" else e.tax_B
    rows = {}
    for k, v in e.fob.items():
        if k == "bess" and not bess:
            continue
        if k in IMPORTED:
            fr = e.freight * v
            tx = (v + fr) * rates[k]
        elif k in MIXED:
            fr = v * e.mixed_import_share * e.freight
            tx = v * e.mixed_import_share * e.mixed_tax
        else:
            fr = tx = 0.0
        rows[k] = (v * e.fx, fr * e.fx, tx * e.fx)
    sub = sum(sum(r) for r in rows.values())
    eng = e.eng_frac * sum(r[0] for r in rows.values())
    cont = e.cont_frac * (sub + eng)
    return rows, sub, eng, cont, sub + eng + cont


def irr(cf):
    lo, hi = -0.95, 1.0
    for _ in range(300):
        m = (lo + hi) / 2
        v = sum(c / (1 + m) ** i for i, c in enumerate(cf))
        lo, hi = (m, hi) if v > 0 else (lo, m)
    return m


def crf(i, n):
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


class Model:
    def __init__(self, csv_path):
        self.w = load_nasa(csv_path)
        self.poa, self.tcell = poa_and_tcell(self.w)
        self._cache = {}

    def year(self, y=1, bess=True, pv_scale=1.0, ev_scale=1.0):
        key = (y, bess, round(pv_scale, 4), round(ev_scale, 4))
        if key not in self._cache:
            fade = 1.0
            if bess:
                r = BAT.replacement_year
                fade = 1 - BAT.fade_per_year * ((y - 1) if y <= r else (y - r - 1))
            pv = pv_ac_kw(self.poa, self.tcell, scale=pv_scale, year=y)
            self._cache[key] = simulate(pv, bess=bess, fade=fade, ev_scale=ev_scale)
        return self._cache[key]

    def cashflow(self, capex_tk, price=ECON.price_tk_kwh, tax=ECON.income_tax, bess=True,
                 mode="carry", pv_scale=1.0, ev_scale=1.0, tariff=TAR.energy_tk_kwh, e=ECON):
        cf, cfp, det = [-capex_tk], [-capex_tk], []
        base_pvbos = (e.fob["pv"] + e.fob["inv"] + e.fob["bos"]) * e.fx
        dep = capex_tk / e.dep_years
        for y in range(1, e.life_years + 1):
            o = self.year(y, bess, pv_scale, ev_scale)
            billed, _ = net_metering(o["imp"], o["exp"], mode)
            bill = billed.sum() * tariff * (1 + TAR.bill_vat)
            sold = o["ev"].sum()
            rev = sold * price / (1 + TAR.sale_vat)
            esc = (1 + e.escalation) ** (y - 1)
            demand = TAR.demand_kw * TAR.demand_tk_kw_month * 12
            opex = (e.om_frac_pv_bos * base_pvbos + e.insurance_frac * capex_tk
                    + (e.staff_tk + e.land_tk) * esc + e.fee_frac_revenue * rev + bill + demand)
            ebitda = rev - opex
            repl = ((0.5 * e.fob["bess"] if bess else 0) + 0.6 * e.fob["inv"]) * e.fx if y == BAT.replacement_year else 0.0
            tx = max(ebitda - (dep if y <= e.dep_years else 0), 0) * tax
            cf.append(ebitda - repl - tx)
            cfp.append(ebitda - repl)
            det.append(dict(year=y, revenue=rev, opex=opex, grid_bill=bill, ebitda=ebitda, tax=tx,
                            billed_kwh=billed.sum(), sold_kwh=sold, replacement=repl))
        cf, cfp = np.array(cf), np.array(cfp)
        cum = np.cumsum(cf)
        pb = next((i for i, v in enumerate(cum) if v >= 0), None)
        npv = sum(c / (1 + e.discount) ** i for i, c in enumerate(cf))
        return dict(irr=irr(cf), irr_pre=irr(cfp), npv=npv, payback=pb, cf=cf, cum=cum, detail=det)

    def breakeven_price(self, capex_tk, **kw):
        lo, hi = 5.0, 60.0
        for _ in range(30):
            m = (lo + hi) / 2
            lo, hi = (m, hi) if self.cashflow(capex_tk, price=m, **kw)["npv"] < 0 else (lo, m)
        return m
