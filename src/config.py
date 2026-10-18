"""All model assumptions in one place. Edit here, then re-run `python -m src.run_all`."""
from dataclasses import dataclass, field

DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


@dataclass(frozen=True)
class Site:
    lat: float = 21.4394          # deg N (NASA POWER grid cell used in the data file)
    lon: float = 91.981           # deg E
    tilt: float = 15.0            # deg, south-facing fixed tilt
    albedo: float = 0.20


@dataclass(frozen=True)
class PV:
    kwp: float = 500.0
    gamma: float = -0.0035        # power temperature coefficient (1/degC)
    noct: float = 45.0            # degC
    # Non-thermal loss factors (fractions); temperature loss is computed hourly.
    losses: dict = field(default_factory=lambda: {
        "soiling": 0.03, "mismatch_dc_cabling": 0.03, "inverter": 0.025,
        "ac_cabling_transformer": 0.01, "availability": 0.01,
        "shading_iam": 0.02, "low_light_spectral": 0.01})
    degradation: float = 0.005    # per year


@dataclass(frozen=True)
class Battery:
    nominal_kwh: float = 500.0
    min_soc: float = 0.10
    rte: float = 0.90             # AC-AC round trip
    pcs_kw: float = 250.0
    fade_per_year: float = 0.02   # capacity fade until replacement
    replacement_year: int = 12


@dataclass(frozen=True)
class Load:
    vehicles_per_day: int = 370
    kwh_per_vehicle: float = 5.4  # metered AC energy per vehicle (5.0 kWh battery / 0.92 charger)
    day_hours: tuple = (8, 17)    # 08:00-17:00 daytime charging window (500 kWh/day)
    day_kwh: float = 500.0
    evening_hours: tuple = (19, 24)   # 900 kWh
    evening_kwh: float = 900.0
    night_hours: tuple = (0, 6)       # 600 kWh
    night_kwh: float = 600.0
    aux_kwh_per_day: float = 40.0


@dataclass(frozen=True)
class Tariff:
    energy_tk_kwh: float = 11.36      # BERC June 2026, LV battery-charging flat rate
    bill_vat: float = 0.05            # VAT on electricity bill (assumed)
    demand_tk_kw_month: float = 100.0 # assumed
    demand_kw: float = 250.0
    sale_vat: float = 0.15


@dataclass(frozen=True)
class Econ:
    fx: float = 122.0                 # Tk per USD (assumed)
    price_tk_kwh: float = 24.0        # selling price incl. VAT (base case)
    discount: float = 0.10            # real
    life_years: int = 20
    income_tax: float = 0.275         # assumed
    dep_years: int = 10
    staff_tk: float = 1.8e6
    land_tk: float = 0.8e6
    escalation: float = 0.05          # staff + land
    om_frac_pv_bos: float = 0.015
    insurance_frac: float = 0.004
    fee_frac_revenue: float = 0.01
    ef_t_per_mwh: float = 0.67        # grid emission factor (Hasan 2020)
    # FOB equipment prices, USD
    fob: dict = field(default_factory=lambda: {
        "pv": 65000, "inv": 22500, "bess": 85000, "bos": 110000,
        "ev": 44000, "grid": 28000, "civil": 35000})
    freight: float = 0.06
    # effective tax on imported equipment: scenario A (FY27 concessions) / B (pre-budget)
    tax_A: dict = field(default_factory=lambda: {"pv": 0.15, "inv": 0.15, "bess": 0.15})
    tax_B: dict = field(default_factory=lambda: {"pv": 1.27 * 1.15 - 1, "inv": 1.29 * 1.15 - 1, "bess": 1.30 * 1.15 - 1})
    mixed_import_share: float = 0.5   # chargers / transformer: share imported
    mixed_tax: float = 0.35
    eng_frac: float = 0.06
    cont_frac: float = 0.05


SITE, PVC, BAT, LOAD, TAR, ECON = Site(), PV(), Battery(), Load(), Tariff(), Econ()
