# Solar PV + LFP battery EV-charging station for Cox's Bazar

Hourly techno-economic model of a grid-connected **500 kWp PV + 500 kWh LFP battery** charging station for battery-run
three-wheelers ("easy bikes") in Cox's Bazar, Bangladesh, driven by **real NASA POWER weather for 2025**.


## What it does
- Reads NASA POWER hourly GHI / DNI / diffuse / temperature, transposes to a 15 deg south-facing plane, and computes cell temperature and AC output.
- Runs a rule-based 8,760-hour dispatch (PV -> vehicles -> battery -> export; battery -> evening load; grid for the rest) with battery SOC, efficiency, reserve and fade.
- Applies monthly net metering (carry-forward, monthly reset, or no export credit).
- Builds capital cost with freight, duties and VAT (two tax scenarios), BERC June 2026 tariff, operating costs, unit cost, selling price, revenue, NPV, IRR, payback and 15 sensitivity cases.

## Headline results (base case, Tk 24/kWh incl. VAT)
| Item | Value |
|---|---|
| PV output | 732.0 MWh/yr (1464 kWh/kWp) |
| Energy sold | 730 MWh/yr |
| Capital cost (Scn. A / B) | Tk 59.62 M / 67.36 M |
| Levelised cost | Tk 15.53/kWh |
| Post-tax IRR / NPV / payback | 12.6% / Tk 9.0 M / 7 yr |
| Solar share (time-matched / annual net-metered) | 44% / 95% |

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate    # optional
pip install -r requirements.txt
python -m pytest -q            # energy-balance, battery-limit and net-metering tests
python -m src.run_all          # writes results/*.csv and results/results.json
python -m src.make_figures     # writes the PDF figures to paper/figures/
python -m src.build_paper      # fills paper/template.tex -> paper/main.tex
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main   # or upload paper/ to Overleaf
# or simply: make all
```

## Layout
```
data/      NASA POWER 2025 hourly CSV (+ README with source)
src/       config.py (ALL assumptions) | weather.py | pv.py | dispatch.py | netmeter.py | economics.py | run_all.py | make_figures.py | build_paper.py
tests/     test_model.py
results/   hourly_dispatch_year1.csv | monthly_summary.csv | sensitivity.csv | capex_breakdown.csv | results.json
paper/     template.tex (placeholders) | main.tex (generated, Overleaf-ready IEEEtran) | ref.bib | figures/*.pdf | main.pdf
```

## Key assumptions (edit in `src/config.py`)
Tk 122/US$; selling price Tk 24/kWh incl. 15% VAT; 10% real discount rate; 20-year life; 27.5% income tax; 5% VAT on the
electricity bill; demand charge Tk 100/kW/month; 370 vehicles/day x 5.4 kWh; PV loss factors; BESS price US$170/kWh FOB;
tax rates for Scenario A (FY2026-27 concessions) and B (pre-budget duties). **Tax rates, prices and the exchange rate are
assumptions based on press reports and must be checked against the final Finance Act, NBR schedule and supplier quotes.**

## Limitations
One reanalysis year (not on-site data); constant daily vehicle demand; no outage statistics; unlevered economics; no carbon income.

