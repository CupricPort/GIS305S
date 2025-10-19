# West Nile Virus Outbreak Simulation

This project simulates a West Nile Virus (WNV) outbreak in Boulder County, Colorado using ArcGIS Pro and Python.

## Overview

The project:
- Buffers potential mosquito breeding sites
- Intersects these buffers to find high-risk zones
- Removes zones around protected areas like schools (avoid points)
- Geocodes address submissions from a public Google Form
- Identifies and counts addresses within spraying zones
- Exports the final map layout as a PDF

## Tools Used

- Python 3.x (ArcGIS Pro's arcpy environment)
- ArcGIS Pro
- arcpy.mp
- YAML configuration files
- Google Sheets API
- U.S. Census Geocoding API

## How to Run

1. Clone the repo and open it in PyCharm or another IDE.
2. Modify `config/wnvoutbreak.yaml` with your project paths.
3. Run `finalproject.py` inside the ArcGIS Python environment.
4. Follow prompts to buffer layers and export the final map.

## Output

- A geodatabase with cleaned risk zones and addresses at risk
- A PDF map layout showing risk zones and targeted addresses
- A log file (`wnv.log`) capturing process steps and errors