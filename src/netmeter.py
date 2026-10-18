import numpy as np
from .weather import month_index


def monthly_sum(a):
    mi = month_index()
    return np.array([a[mi == m].sum() for m in range(12)])


def net_metering(imp, exp, mode="carry"):
    """Monthly billed kWh and credit-bank history.
    carry: credits roll over within the year (forfeited at year end); month: credits reset monthly;
    none: no export credit, all imports billed."""
    im, ex = monthly_sum(imp), monthly_sum(exp)
    billed, bank_hist, bank = np.zeros(12), np.zeros(12), 0.0
    for m in range(12):
        if mode == "none":
            billed[m] = im[m]
        elif mode == "month":
            billed[m] = max(im[m] - ex[m], 0.0)
        else:
            net = im[m] - ex[m]
            if net < 0:
                bank += -net
            else:
                use = min(bank, net)
                bank -= use
                billed[m] = net - use
        bank_hist[m] = bank
    return billed, bank_hist
