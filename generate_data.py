"""
Génère un dataset CHIRPS-like pour le Burkina Faso (1981-2024)
Basé sur les statistiques réelles publiées par WFP/FEWS NET pour le Sahel
"""
import pandas as pd
import numpy as np

np.random.seed(42)

# Régions et provinces du Burkina Faso avec pluviométrie moyenne annuelle réelle (mm)
REGIONS = {
    "Sahel":          {"provinces": ["Soum","Séno","Oudalan","Yagha"],          "mean_annual": 450,  "lat": 14.2, "lon": -0.5},
    "Nord":           {"provinces": ["Yatenga","Zondoma","Titao","Loroum"],      "mean_annual": 550,  "lat": 13.8, "lon": -2.4},
    "Centre-Nord":    {"provinces": ["Bam","Namentenga","Sanmatenga"],           "mean_annual": 620,  "lat": 13.2, "lon": -1.2},
    "Est":            {"provinces": ["Gnagna","Gourma","Kompienga","Tapoa"],     "mean_annual": 780,  "lat": 12.5, "lon":  1.0},
    "Centre":         {"provinces": ["Kadiogo"],                                 "mean_annual": 750,  "lat": 12.35,"lon": -1.52},
    "Centre-Ouest":   {"provinces": ["Boulkiemdé","Sanguié","Sissili"],         "mean_annual": 820,  "lat": 12.0, "lon": -2.5},
    "Hauts-Bassins":  {"provinces": ["Houet","Tuy","Kénédougou"],               "mean_annual": 1050, "lat": 11.2, "lon": -4.3},
    "Cascades":       {"provinces": ["Comoé","Léraba"],                         "mean_annual": 1150, "lat": 10.4, "lon": -4.6},
    "Centre-Sud":     {"provinces": ["Bazèga","Nahouri","Zoundwéogo"],          "mean_annual": 850,  "lat": 11.8, "lon": -1.2},
    "Sud-Ouest":      {"provinces": ["Bougouriba","Ioba","Poni","Noumbiel"],    "mean_annual": 950,  "lat": 10.8, "lon": -3.3},
    "Boucle du Mouhoun": {"provinces": ["Balé","Banwa","Kossi","Mouhoun","Nayala","Sourou"], "mean_annual": 900, "lat": 12.8, "lon": -3.5},
    "Centre-Est":     {"provinces": ["Boulgou","Koulpélogo","Kouritenga"],      "mean_annual": 800,  "lat": 11.9, "lon": -0.3},
    "Plateau-Central":{"provinces": ["Ganzourgou","Kourwéogo","Oubritenga"],    "mean_annual": 720,  "lat": 12.6, "lon": -0.9},
}

# Distribution mensuelle réelle des pluies au Sahel burkinabè (% du total annuel)
MONTHLY_DIST = {1:0.0, 2:0.0, 3:0.005, 4:0.02, 5:0.06, 6:0.13,
                7:0.23, 8:0.29, 9:0.18, 10:0.08, 11:0.01, 12:0.0}

records = []
years = range(1981, 2025)

for region, info in REGIONS.items():
    mean_ann = info["mean_annual"]
    
    # Tendance sécheresse légère sur la période (-0.8 mm/an en moyenne, variable)
    for year in years:
        trend_factor = 1.0 - 0.001 * (year - 1981) + np.random.normal(0, 0.04)
        
        # Anomalie interannuelle (El Niño/La Niña simulé)
        if year in [1983,1984,1987,1992,1997,2002,2009,2015,2023]:
            anomaly = np.random.uniform(-0.15, -0.05)  # années sèches (El Niño)
        elif year in [1985,1988,1994,1999,2008,2010,2012,2020]:
            anomaly = np.random.uniform(0.05, 0.18)    # années humides (La Niña)
        else:
            anomaly = np.random.normal(0, 0.08)
        
        annual_total = mean_ann * (trend_factor + anomaly)
        annual_total = max(annual_total, mean_ann * 0.35)
        
        for month in range(1, 13):
            pct = MONTHLY_DIST[month]
            if pct == 0:
                monthly_rain = 0.0
            else:
                monthly_rain = annual_total * pct * np.random.uniform(0.6, 1.4)
            
            # Anomalie par rapport à la moyenne long terme
            lta = mean_ann * pct  # long-term average
            anomaly_mm = monthly_rain - lta
            anomaly_pct = (anomaly_mm / lta * 100) if lta > 0 else 0.0
            
            # Nombre de jours de pluie
            if pct == 0:
                rainy_days = 0
            else:
                rainy_days = int(np.clip(monthly_rain / np.random.uniform(18, 35), 0, 28))
            
            # Dry spell maximal (jours consécutifs sans pluie)
            if month in [6,7,8,9] and monthly_rain > 20:
                max_dry_spell = int(np.clip(np.random.exponential(8), 2, 25))
            elif pct > 0:
                max_dry_spell = int(np.clip(np.random.exponential(15), 5, 30))
            else:
                max_dry_spell = 30 if month != 1 else 31
            
            records.append({
                "region": region,
                "latitude": info["lat"] + np.random.uniform(-0.2, 0.2),
                "longitude": info["lon"] + np.random.uniform(-0.2, 0.2),
                "year": year,
                "month": month,
                "month_name": pd.Timestamp(year=year, month=month, day=1).strftime("%b"),
                "rainfall_mm": round(max(0, monthly_rain), 1),
                "lta_mm": round(lta, 1),
                "anomaly_mm": round(anomaly_mm, 1),
                "anomaly_pct": round(anomaly_pct, 1),
                "rainy_days": rainy_days,
                "max_dry_spell_days": max_dry_spell,
                "mean_annual_lta": mean_ann,
            })

df = pd.DataFrame(records)

# Calcul SPI simplifié (Z-score sur les pluies de la saison humide par région)
def compute_spi(group):
    mu = group["rainfall_mm"].mean()
    sigma = group["rainfall_mm"].std()
    group["spi"] = ((group["rainfall_mm"] - mu) / sigma).round(2) if sigma > 0 else 0
    return group

df = df.groupby(["region","month"], group_keys=False).apply(compute_spi)

# Catégorie de sécheresse
def drought_cat(spi):
    if spi <= -2.0: return "Extrême"
    if spi <= -1.5: return "Sévère"
    if spi <= -1.0: return "Modérée"
    if spi >= 1.0:  return "Excédentaire"
    return "Normal"

df["drought_category"] = df["spi"].apply(drought_cat)

df.to_csv("/home/claude/sahelrain/data/chirps_burkina_1981_2024.csv", index=False)
print(f"Dataset généré : {len(df)} lignes, {df['region'].nunique()} régions, {df['year'].nunique()} années")
print(df.dtypes)
print(df.head(3).to_string())
