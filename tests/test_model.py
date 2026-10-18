"""Run with: python -m pytest -q   (or python tests/test_model.py)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import numpy as np
from src.economics import Model, capex
from src.netmeter import net_metering

CSV = os.path.join(os.path.dirname(__file__), "..", "data", "nasa_power_cox_bazar_2025_hourly.csv")


def test_energy_balance():
    o = Model(CSV).year(1)
    lhs = o["pv"].sum() + o["imp"].sum() + o["bout"].sum()
    rhs = o["ev"].sum() + o["aux"].sum() + o["exp"].sum() + o["bin"].sum()
    assert abs(lhs - rhs) < 1e-6 * lhs


def test_soc_bounds_and_efficiency():
    o = Model(CSV).year(1)
    assert o["soc"].min() >= 50 - 1e-9 and o["soc"].max() <= 500 + 1e-9
    assert o["bout"].sum() <= 0.9 * o["bin"].sum() + 1e-6   # cannot beat RTE


def test_net_metering_modes():
    imp = np.ones((365, 24)); exp = np.zeros((365, 24)); exp[100:200] = 2.0
    c, _ = net_metering(imp, exp, "carry"); m, _ = net_metering(imp, exp, "month"); n, _ = net_metering(imp, exp, "none")
    assert c.sum() <= m.sum() <= n.sum()


def test_capex_scenarios():
    assert capex("B")[4] > capex("A")[4] > capex("A", bess=False)[4]


if __name__ == "__main__":
    for f in (test_energy_balance, test_soc_bounds_and_efficiency, test_net_metering_modes, test_capex_scenarios):
        f(); print("ok", f.__name__)
