# 🌧️ SahelRain Dashboard

**Agro-Climatic Rainfall Monitor for Burkina Faso**

An interactive web application for monitoring rainfall anomalies, drought indices, and agro-climatic risk indicators across Burkina Faso, built on CHIRPS v2 satellite data.

Developed by **[Pragmatix Africa](https://pragmatix-africa.com)** — Alban Wendé Gûudi OUEDRAOGO

---

## Features

| Module | Description |
|---|---|
| 📊 Anomalies & Rainfall | Annual totals, dekadal anomaly heatmap, seasonal profiles vs LTA |
| 🌵 Drought (SPI) | Standardized Precipitation Index (SPI-1 or SPI-3), category classification, driest years ranking |
| 💧 Dry Spells | Maximum dry spell detection during the rainy season (May–Oct), trend analysis |
| 🌱 False Season Starts | FAO/AGRHYMET-based false start detection, cumulative rate over time |
| 📥 Data Export | Download all computed indicators as CSV |

## Data Source

- **CHIRPS v2** — Climate Hazards Group InfraRed Precipitation with Station data
- **Provider**: Climate Hazards Center, UC Santa Barbara & WFP
- **Coverage**: Burkina Faso, January 1981 – present (updated every 2 weeks)
- **Download**: [HDX – Burkina Faso Rainfall Indicators at Subnational Level](https://data.humdata.org/dataset/bfa-rainfall-subnational)
- **License**: CC BY-IGO 3.0

## Installation

```bash
git clone https://github.com/albano-wende/sahelrain.git
cd sahelrain
pip install -r requirements.txt
```

## Usage

1. Download `bfa-rainfall-subnat-full.csv` from [HDX](https://data.humdata.org/dataset/bfa-rainfall-subnational)
2. Place the file in the `data/` folder
3. Run the application:

```bash
streamlit run app.py
```

4. Open your browser at `http://localhost:8501`

## Project Structure

```
sahelrain/
├── app.py                    # Main Streamlit application
├── requirements.txt
├── README.md
├── data/
│   └── bfa-rainfall-subnat-full.csv   # CHIRPS data (download from HDX)
└── utils/
    ├── indicators.py         # SPI, dry spells, false starts, anomalies
    └── pcode_mapping.py      # PCODE → Province/Region names & coordinates
```

## Indicators Methodology

- **Anomalies**: Ratio of observed rainfall to Long-Term Average (LTA, 1981–2010)
- **SPI**: Z-score normalized precipitation index, computed by calendar month (WMO standard)
- **Dry Spells**: Consecutive dekads with rainfall < threshold × 10 days, during rainy season
- **False Season Start**: FAO/AGRHYMET criterion adapted for dekadal data — first dekad ≥ 20mm followed by ≥ 2 dry dekads (< 5mm) in the next 4 dekads

## Relevance to WASCAL / AgInfo

This dashboard was developed to demonstrate the technical approach proposed for the **AgInfo** application (CICLES Project, WASCAL/BMFTR-PT-DLR). It implements the four core functional modules required by the Terms of Reference using real CHIRPS data for Burkina Faso.

## Author

**Alban Wendé Gûudi OUEDRAOGO**  
CEO, Pragmatix Africa | Data Scientist, Orange Burkina Faso  
Enseignant, ISSP/Université Joseph KI-ZERBO & Université Unité Africaine  
📧 manager@pragmatix-africa.com  
🔗 [linkedin.com/in/alban-wende-ouedraogo](https://linkedin.com/in/alban-wende-ouedraogo)  
📍 Ouagadougou, Burkina Faso
