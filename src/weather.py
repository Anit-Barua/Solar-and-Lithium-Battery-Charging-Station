"""Read NASA POWER hourly CSV and compute plane-of-array irradiance and cell temperature."""
import numpy as np
from .config import SITE, PVC, DAYS_IN_MONTH


def load_nasa(path):
    """Return dict of (365, 24) arrays: ghi, dni, dhi (W/m2 hourly mean) and t2m (degC)."""
    rows = []
    with open(path, newline="") as f:
        started = False
        for line in f:
            line = line.strip()
            if line.startswith("-END HEADER-"):
                started = True
                continue
            if started and line and not line.startswith("YEAR"):
                rows.append([float(x) for x in line.split(",")])
    a = np.array(rows)
    a[a == -999] = np.nan
    if len(a) != 8760:
        raise ValueError(f"expected 8760 hourly rows, got {len(a)}")
    if np.isnan(a).any():
        raise ValueError("missing values (-999) in weather file")
    shp = (365, 24)
    return dict(ghi=a[:, 4].reshape(shp), dni=a[:, 6].reshape(shp),
                dhi=a[:, 7].reshape(shp), t2m=a[:, 8].reshape(shp))


def poa_and_tcell(w, site=SITE, pv=PVC):
    """Transpose to a south-facing fixed tilt (isotropic sky) and estimate cell temperature."""
    phi, beta = np.radians(site.lat), np.radians(site.tilt)
    n = np.arange(365)[:, None] + 1
    dec = np.radians(23.45) * np.sin(2 * np.pi * (284 + n) / 365)   # (365,1)
    hr = np.arange(24)[None, :] + 0.5                                # hour midpoint, local solar time
    om = np.radians(15 * (hr - 12))
    cos_aoi = np.sin(dec) * np.sin(phi - beta) + np.cos(dec) * np.cos(om) * np.cos(phi - beta)
    cos_aoi = np.clip(cos_aoi, 0, None)
    poa = (w["dni"] * cos_aoi + w["dhi"] * (1 + np.cos(beta)) / 2
           + w["ghi"] * site.albedo * (1 - np.cos(beta)) / 2)
    poa = np.where(w["ghi"] > 0, poa, 0.0)
    tcell = w["t2m"] + (pv.noct - 20.0) / 800.0 * poa
    return poa, tcell


def month_index():
    return np.concatenate([[m] * d for m, d in enumerate(DAYS_IN_MONTH)])
