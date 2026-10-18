# Data

`nasa_power_cox_bazar_2025_hourly.csv` - NASA POWER hourly point data (LST) for 21.4394 N, 91.981 E,
1 Jan - 31 Dec 2025 (8,760 rows).

Parameters: `ALLSKY_SFC_SW_DWN` (GHI), `CLRSKY_SFC_SW_DWN`, `ALLSKY_SFC_SW_DNI`, `ALLSKY_SFC_SW_DIFF` (all Wh/m^2 per hour,
i.e. W/m^2 hourly mean) and `T2M` (deg C). Irradiance is CERES SYN1deg; temperature is MERRA-2.

Source: NASA Langley Research Center POWER Project, https://power.larc.nasa.gov (accessed October 2026).
NASA POWER data are freely available; please cite NASA POWER if you reuse them.
To use another year or site, download the same parameters in the same CSV format and point
`src/run_all.py` (variable `CSV`) at the new file.
