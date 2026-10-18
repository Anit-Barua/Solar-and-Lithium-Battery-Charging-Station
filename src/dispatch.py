"""Rule-based hourly dispatch (load following with net metering)."""
import numpy as np
from .config import BAT, LOAD


def ev_profile(load=LOAD, scale=1.0):
    p = np.zeros(24)
    a, b = load.day_hours;     p[a:b] = load.day_kwh / (b - a)
    a, b = load.evening_hours; p[a:b] = load.evening_kwh / (b - a)
    a, b = load.night_hours;   p[a:b] = load.night_kwh / (b - a)
    return p * scale


def simulate(pv_kw, bat=BAT, load=LOAD, bess=True, fade=1.0, ev_scale=1.0):
    """pv_kw: (365,24) AC kW. Returns dict of (365,24) arrays in kWh per hour.
    Rules: (1) PV serves daytime vehicles + auxiliaries; (2) surplus charges the BESS (<= PCS kW, <= 100% SOC);
    (3) remaining surplus is exported; (4) from the evening window the BESS discharges evenly over the
    remaining hours down to the minimum SOC; (5) any residual load is bought from the grid."""
    evp = ev_profile(load, ev_scale)
    aux = load.aux_kwh_per_day / 24
    eta = np.sqrt(bat.rte)
    cap = bat.nominal_kwh * fade if bess else 0.0
    smin, smax = bat.min_soc * cap, cap
    soc = smin
    out = {k: np.zeros((365, 24)) for k in ("pv", "ev", "imp", "exp", "soc", "bin", "bout")}
    for d in range(365):
        for h in range(24):
            ev, pv = evp[h], pv_kw[d, h]
            ld = aux + ev
            net = pv - ld
            imp = exp = bi = bo = 0.0
            if net >= 0:
                pc = min(net, bat.pcs_kw, (smax - soc) / eta) if bess else 0.0
                soc += pc * eta
                bi, exp = pc, net - pc
            else:
                deficit = -net
                dis = 0.0
                if bess and ev > 0 and h >= load.evening_hours[0]:
                    dis = min(deficit, (soc - smin) * eta / (24 - h), bat.pcs_kw)
                    soc -= dis / eta
                    bo = dis
                imp = deficit - dis
            out["pv"][d, h], out["ev"][d, h], out["imp"][d, h] = pv, ev, imp
            out["exp"][d, h], out["soc"][d, h], out["bin"][d, h], out["bout"][d, h] = exp, soc, bi, bo
    out["aux"] = np.full((365, 24), aux)
    return out
