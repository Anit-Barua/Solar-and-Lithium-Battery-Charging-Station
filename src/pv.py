import numpy as np
from .config import PVC


def other_loss_factor(pv=PVC):
    f = 1.0
    for v in pv.losses.values():
        f *= (1 - v)
    return f


def pv_ac_kw(poa, tcell, pv=PVC, scale=1.0, year=1):
    """Hourly AC output (kW) for (365,24) POA / cell-temperature arrays."""
    temp = 1 + pv.gamma * (tcell - 25.0)
    p = pv.kwp * (poa / 1000.0) * temp * other_loss_factor(pv)
    return p * scale * (1 - pv.degradation) ** (year - 1)
