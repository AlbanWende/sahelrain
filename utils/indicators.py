"""
utils/indicators.py
Calculs agro-climatiques : SPI, anomalies, dry spells, faux démarrages
Basé sur les colonnes réelles du dataset CHIRPS HDX BFA
"""
import pandas as pd
import numpy as np
from scipy import stats


# ── Chargement & préparation ────────────────────────────────────

def load_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=["date"], low_memory=False)
    df = df.sort_values(["PCODE", "date"]).reset_index(drop=True)

    # Colonnes numériques
    for col in ["rfh", "rfh_avg", "r1h", "r1h_avg", "r3h", "r3h_avg",
                "rfq", "r1q", "r3q", "n_pixels"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Informations temporelles
    df["year"]    = df["date"].dt.year
    df["month"]   = df["date"].dt.month
    df["dekad"]   = df["date"].apply(lambda d: 1 if d.day <= 10 else (2 if d.day <= 20 else 3))
    df["year_month"] = df["date"].dt.to_period("M")

    return df


def enrich_names(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute colonnes nom_zone et region au DataFrame."""
    from utils.pcode_mapping import get_name, get_region
    df = df.copy()
    df["nom_zone"] = df["PCODE"].map(get_name)
    df["region"]   = df["PCODE"].map(get_region)
    return df


# ── Filtres ─────────────────────────────────────────────────────

def filter_data(df, pcode, year_start, year_end, adm_level=None):
    mask = (df["PCODE"] == pcode) & \
           (df["year"] >= year_start) & \
           (df["year"] <= year_end)
    if adm_level is not None:
        mask &= df["adm_level"] == adm_level
    return df[mask].copy()


# ── Anomalies pluviométriques ────────────────────────────────────

def compute_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les anomalies décadaires et mensuelles.
    rfq est déjà dans le dataset (%), on l'utilise directement.
    On recalcule aussi une anomalie en mm.
    """
    df = df.copy()
    df["anom_dekad_mm"]  = df["rfh"]  - df["rfh_avg"]
    df["anom_1m_mm"]     = df["r1h"]  - df["r1h_avg"]
    df["anom_3m_mm"]     = df["r3h"]  - df["r3h_avg"]

    # Catégorie anomalie décadaire
    def cat_anom(pct):
        if pd.isna(pct):   return "N/A"
        if pct < 60:       return "Déficit sévère"
        if pct < 80:       return "Déficit modéré"
        if pct <= 120:     return "Normal"
        if pct <= 150:     return "Excédent modéré"
        return "Excédent fort"

    df["cat_anom"] = df["rfq"].apply(cat_anom)
    return df


# ── Aggregation mensuelle ────────────────────────────────────────

def monthly_agg(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les décades en mois pour graphiques temporels."""
    grp = df.groupby(["year", "month"]).agg(
        rfh_month    = ("rfh",     "sum"),
        rfh_avg_month= ("rfh_avg", "sum"),
        r1h          = ("r1h",     "last"),   # cumul déjà mensuel
        r1h_avg      = ("r1h_avg", "last"),
        r3h          = ("r3h",     "last"),
        r3h_avg      = ("r3h_avg", "last"),
    ).reset_index()

    grp["anom_mm"]  = grp["rfh_month"] - grp["rfh_avg_month"]
    grp["anom_pct"] = np.where(
        grp["rfh_avg_month"] > 0,
        (grp["rfh_month"] / grp["rfh_avg_month"] * 100).round(1),
        np.nan
    )
    grp["date"] = pd.to_datetime(
        grp["year"].astype(str) + "-" + grp["month"].astype(str).str.zfill(2) + "-01"
    )
    return grp.sort_values("date")


# ── SPI (Standardized Precipitation Index) ──────────────────────

def compute_spi(df: pd.DataFrame, scale: int = 1) -> pd.DataFrame:
    """
    Calcule le SPI à l'échelle souhaitée (1 = mensuel, 3 = trimestriel).
    Utilise r1h pour scale=1, r3h pour scale=3.
    Distribution gamma ajustée par mois calendaire.
    """
    col = "r1h" if scale == 1 else "r3h"
    avg_col = "r1h_avg" if scale == 1 else "r3h_avg"

    # Agrégation mensuelle d'abord
    mdf = monthly_agg(df)[["year", "month", "date", col, avg_col]].dropna(subset=[col])
    if mdf.empty:
        return mdf

    spi_vals = []
    for month in range(1, 13):
        sub = mdf[mdf["month"] == month][col].values
        if len(sub) < 5:
            spi_vals.extend([np.nan] * len(mdf[mdf["month"] == month]))
            continue
        # Ajustement distribution normale des log-précipitations
        sub_pos = sub[sub > 0]
        if len(sub_pos) < 3:
            spi_vals.extend([np.nan] * len(mdf[mdf["month"] == month]))
            continue
        mu, sigma = np.mean(sub_pos), np.std(sub_pos)
        if sigma == 0:
            spi_vals.extend([0.0] * len(mdf[mdf["month"] == month]))
            continue
        z = (sub - mu) / sigma
        spi_vals.extend(z.tolist())

    # Réassigner dans le bon ordre
    mdf = mdf.sort_values(["year", "month"]).reset_index(drop=True)
    spi_by_month = []
    for _, row in mdf.iterrows():
        m = int(row["month"])
        sub = mdf[mdf["month"] == m][col].values
        val = row[col]
        if pd.isna(val) or np.std(sub[sub > 0] if any(sub > 0) else sub) == 0:
            spi_by_month.append(np.nan)
        else:
            sub_pos = sub[sub > 0]
            mu, sigma = np.mean(sub_pos), np.std(sub_pos)
            spi_by_month.append(round((val - mu) / sigma, 2) if sigma > 0 else 0.0)

    mdf["spi"] = spi_by_month

    def spi_category(s):
        if pd.isna(s):      return "N/A"
        if s <= -2.0:       return "Sécheresse extrême"
        if s <= -1.5:       return "Sécheresse sévère"
        if s <= -1.0:       return "Sécheresse modérée"
        if s >= 2.0:        return "Excédent extrême"
        if s >= 1.5:        return "Excédent fort"
        if s >= 1.0:        return "Excédent modéré"
        return "Normal"

    mdf["spi_category"] = mdf["spi"].apply(spi_category)
    mdf["spi_scale"] = scale
    return mdf


# ── Détection des séquences sèches (dry spells) ─────────────────

def compute_dry_spells(df: pd.DataFrame, threshold_mm: float = 1.0) -> pd.DataFrame:
    """
    Estime les dry spells à partir des données décadaires CHIRPS.
    Approche : une décade est « sèche » si rfh < threshold * 10 jours.
    On compte les séquences consécutives de décades sèches par année.
    """
    df = df.copy().sort_values("date")
    df["dry_dekad"] = df["rfh"] < (threshold_mm * 10)

    results = []
    for year, grp in df.groupby("year"):
        grp = grp.sort_values("date")
        dry_seq = grp["dry_dekad"].values
        # Saison des pluies : décades de mai (mois 5) à octobre (mois 10)
        rain_season = grp[grp["month"].between(5, 10)]
        dry_rain = rain_season["dry_dekad"].values

        # Compter les séquences
        max_dry = 0
        curr = 0
        total_dry_dekads = 0
        for d in dry_rain:
            if d:
                curr += 1
                total_dry_dekads += 1
                max_dry = max(max_dry, curr)
            else:
                curr = 0

        results.append({
            "year": year,
            "max_dry_spell_dekads": max_dry,
            "max_dry_spell_days_est": max_dry * 10,
            "total_dry_dekads_season": total_dry_dekads,
            "pct_dry_season": round(total_dry_dekads / max(len(dry_rain), 1) * 100, 1)
        })

    return pd.DataFrame(results)


# ── Détection des faux démarrages ────────────────────────────────

def detect_false_starts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Détecte les faux démarrages de saison des pluies par année.
    Critère FAO/AGRHYMET adapté aux données décadaires :
    - Première décade avec rfh >= 20mm après le 1er avril
    - Suivie d'au moins 2 décades sèches (rfh < 5mm) dans les 4 décades suivantes
    """
    results = []
    df = df.copy().sort_values("date")

    for year, grp in df.groupby("year"):
        grp = grp.sort_values("date").reset_index(drop=True)
        # Fenêtre avril–juillet
        window = grp[grp["month"].between(4, 7)].reset_index(drop=True)
        if len(window) < 4:
            continue

        false_start = False
        onset_date = None
        onset_rf = None

        for i, row in window.iterrows():
            if row["rfh"] >= 20:  # Déclencheur : décade humide
                # Vérifier les 3 décades suivantes
                next_dekads = window.iloc[i+1:i+4]
                if len(next_dekads) >= 2:
                    dry_after = (next_dekads["rfh"] < 5).sum()
                    if dry_after >= 2:
                        false_start = True
                        onset_date = row["date"]
                        onset_rf = row["rfh"]
                        break

        results.append({
            "year": year,
            "false_start_detected": false_start,
            "false_start_date": onset_date,
            "false_start_rfh": onset_rf,
        })

    rdf = pd.DataFrame(results)
    rdf["false_start_rate"] = rdf["false_start_detected"].expanding().mean().round(2)
    return rdf


# ── Statistiques annuelles ───────────────────────────────────────

def annual_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Résumé annuel : total précipitations, anomalie, catégorie."""
    grp = df.groupby("year").agg(
        total_rfh   = ("rfh", "sum"),
        total_avg   = ("rfh_avg", "sum"),
        n_dekads    = ("rfh", "count"),
    ).reset_index()
    grp["anom_mm"]  = grp["total_rfh"] - grp["total_avg"]
    grp["anom_pct"] = np.where(
        grp["total_avg"] > 0,
        (grp["total_rfh"] / grp["total_avg"] * 100).round(1),
        np.nan
    )
    def cat(p):
        if pd.isna(p):  return "N/A"
        if p < 70:      return "Déficit sévère"
        if p < 85:      return "Déficit modéré"
        if p <= 115:    return "Normal"
        if p <= 130:    return "Excédent modéré"
        return "Excédent fort"
    grp["category"] = grp["anom_pct"].apply(cat)
    return grp


# ── Couleurs standardisées ───────────────────────────────────────

DROUGHT_COLORS = {
    "Sécheresse extrême":  "#8B0000",
    "Sécheresse sévère":   "#D73027",
    "Sécheresse modérée":  "#FC8D59",
    "Normal":              "#74ADD1",
    "Excédent modéré":     "#4575B4",
    "Excédent fort":       "#313695",
    "Excédent extrême":    "#023858",
    "N/A":                 "#CCCCCC",
}

ANOM_COLORS = {
    "Déficit sévère":   "#D73027",
    "Déficit modéré":   "#FC8D59",
    "Normal":           "#74ADD1",
    "Excédent modéré":  "#4575B4",
    "Excédent fort":    "#313695",
    "N/A":              "#CCCCCC",
}
