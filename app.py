"""
SahelRain Dashboard
Agro-Climatic Rainfall Monitor for Burkina Faso
Basé sur les données CHIRPS v2 – WFP/HDX (1981–2026)
Développé par Pragmatix Africa | Alban W.G. OUEDRAOGO
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from utils.indicators import (
    load_data, enrich_names, filter_data,
    compute_anomalies, monthly_agg, compute_spi,
    compute_dry_spells, detect_false_starts, annual_stats,
    DROUGHT_COLORS, ANOM_COLORS
)
from utils.pcode_mapping import REGION_MAP, PROVINCE_MAP, get_name

# ── Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="SahelRain Dashboard",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #1A1A2E; }
    [data-testid="stSidebar"] * { color: #F0F0F0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label { color: #E8571A !important; font-weight: 600 !important; }
    .metric-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border-left: 4px solid #E8571A;
        border-radius: 8px;
        padding: 16px 20px;
        color: white;
        margin-bottom: 8px;
    }
    .metric-value { font-size: 2rem; font-weight: 700; color: #E8571A; }
    .metric-label { font-size: 0.85rem; color: #AAAAAA; margin-top: 2px; }
    .metric-delta { font-size: 0.9rem; margin-top: 4px; }
    .section-header {
        background: linear-gradient(90deg, #E8571A22, transparent);
        border-left: 4px solid #E8571A;
        padding: 8px 16px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0 8px 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #1A1A2E;
    }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #E8571A !important; border-bottom: 3px solid #E8571A; }
    .drought-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: white;
    }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ─────────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "bfa-rainfall-subnat-full.csv")

@st.cache_data(show_spinner="⏳ Chargement des données CHIRPS...")
def get_data():
    df = load_data(DATA_PATH)
    df = enrich_names(df)
    return df


# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 16px 0 8px 0;'>
        <div style='font-size:1.6rem; font-weight:800; color:#E8571A;'>🌧️ SahelRain</div>
        <div style='font-size:0.8rem; color:#AAAAAA; margin-top:2px;'>Agro-Climatic Monitor · Burkina Faso</div>
        <div style='font-size:0.72rem; color:#666; margin-top:2px;'>CHIRPS v2 · WFP/HDX · 1981–2026</div>
    </div>
    <hr style='border-color:#333; margin:8px 0;'>
    """, unsafe_allow_html=True)

    # Vérification fichier
    if not os.path.exists(DATA_PATH):
        st.error("📂 Fichier de données introuvable.\n\nPlacez `bfa-rainfall-subnat-full.csv` dans le dossier `data/`.")
        st.markdown("[📥 Télécharger sur HDX](https://data.humdata.org/dataset/bfa-rainfall-subnational)")
        st.stop()

    df_full = get_data()

    st.markdown("**🗺️ Niveau géographique**")
    adm_choice = st.radio("", ["Région (adm1)", "Province (adm2)"], horizontal=True, label_visibility="collapsed")
    adm_level = 1 if adm_choice == "Région (adm1)" else 2

    # Sélection région
    regions_pcodes = sorted([p for p in df_full["PCODE"].unique() if len(p) == 4])
    region_options = {get_name(p): p for p in regions_pcodes}
    selected_region_name = st.selectbox("🌍 Région", list(region_options.keys()))
    selected_region_pcode = region_options[selected_region_name]

    # Sélection zone (région ou province)
    if adm_level == 1:
        selected_pcode = selected_region_pcode
        zone_label = selected_region_name.replace(" (Région)", "")
    else:
        province_pcodes = sorted([
            p for p in df_full["PCODE"].unique()
            if p.startswith(selected_region_pcode) and len(p) == 6
        ])
        if not province_pcodes:
            st.warning("Aucune province disponible pour cette région.")
            st.stop()
        prov_options = {get_name(p): p for p in province_pcodes}
        selected_prov_name = st.selectbox("🏛️ Province", list(prov_options.keys()))
        selected_pcode = prov_options[selected_prov_name]
        zone_label = selected_prov_name

    st.markdown("<hr style='border-color:#333; margin:8px 0;'>", unsafe_allow_html=True)
    st.markdown("**📅 Période d'analyse**")
    year_min = int(df_full["year"].min())
    year_max = int(df_full["year"].max())
    year_range = st.slider("", year_min, year_max, (1990, year_max), label_visibility="collapsed")

    st.markdown("<hr style='border-color:#333; margin:8px 0;'>", unsafe_allow_html=True)
    st.markdown("**⚙️ Paramètres**")
    spi_scale = st.selectbox("Échelle SPI", [1, 3], format_func=lambda x: f"SPI-{x} ({'mensuel' if x==1 else 'trimestriel'})")
    dry_threshold = st.number_input("Seuil dry spell (mm/jour)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

    st.markdown("<hr style='border-color:#333; margin:8px 0;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.72rem; color:#666; text-align:center;'>
        Pragmatix Africa · Ouagadougou, BF<br>
        <a href='https://github.com/albano-wende/sahelrain' style='color:#E8571A;'>GitHub</a> ·
        <a href='https://data.humdata.org/dataset/bfa-rainfall-subnational' style='color:#E8571A;'>Source HDX</a>
    </div>
    """, unsafe_allow_html=True)


# ── Main header ──────────────────────────────────────────────────
st.markdown(f"""
<div style='background: linear-gradient(135deg, #1A1A2E, #16213E);
     padding: 20px 28px; border-radius: 12px; margin-bottom: 20px;
     border-left: 5px solid #E8571A;'>
    <div style='font-size:1.6rem; font-weight:800; color:white;'>
        🌧️ SahelRain Dashboard
        <span style='font-size:1rem; font-weight:400; color:#AAAAAA; margin-left:12px;'>
        {zone_label} · {year_range[0]}–{year_range[1]}
        </span>
    </div>
    <div style='font-size:0.85rem; color:#888; margin-top:4px;'>
        Outil de monitoring agro-climatique · Données CHIRPS v2 · Climate Hazards Center UCSB & WFP
    </div>
</div>
""", unsafe_allow_html=True)


# ── Load & filter data ───────────────────────────────────────────
df_zone = filter_data(df_full, selected_pcode, year_range[0], year_range[1], adm_level)

if df_zone.empty:
    st.warning(f"Aucune donnée disponible pour {zone_label} sur la période sélectionnée.")
    st.stop()

df_zone = compute_anomalies(df_zone)
df_annual = annual_stats(df_zone)
df_monthly = monthly_agg(df_zone)
df_spi = compute_spi(df_zone, scale=spi_scale)
df_dry = compute_dry_spells(df_zone, threshold_mm=dry_threshold)
df_false = detect_false_starts(df_zone)


# ── KPI Cards ────────────────────────────────────────────────────
total_years = year_range[1] - year_range[0] + 1
avg_annual = df_annual["total_rfh"].mean()
avg_lta = df_annual["total_avg"].mean()
anom_overall = ((avg_annual / avg_lta * 100) - 100) if avg_lta > 0 else 0
pct_dry_years = (df_annual["category"].isin(["Déficit sévère", "Déficit modéré"])).mean() * 100
avg_max_dry_spell = df_dry["max_dry_spell_days_est"].mean()
pct_false_starts = df_false["false_start_detected"].mean() * 100

spi_last = df_spi["spi"].dropna().iloc[-1] if not df_spi.empty and "spi" in df_spi.columns and df_spi["spi"].notna().any() else np.nan

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    delta_color = "🟢" if anom_overall >= 0 else "🔴"
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-value'>{avg_annual:.0f}<span style='font-size:1rem;'> mm</span></div>
        <div class='metric-label'>Pluie annuelle moyenne</div>
        <div class='metric-delta'>{delta_color} {anom_overall:+.1f}% vs LTA</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-value'>{pct_dry_years:.0f}<span style='font-size:1rem;'>%</span></div>
        <div class='metric-label'>Années en déficit</div>
        <div class='metric-delta'>sur {total_years} ans analysés</div>
    </div>""", unsafe_allow_html=True)
with c3:
    spi_disp = f"{spi_last:.2f}" if not np.isnan(spi_last) else "N/A"
    spi_col = "#D73027" if (not np.isnan(spi_last) and spi_last < -1) else ("#4575B4" if (not np.isnan(spi_last) and spi_last > 1) else "#E8571A")
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-value' style='color:{spi_col};'>{spi_disp}</div>
        <div class='metric-label'>SPI-{spi_scale} (dernière valeur)</div>
        <div class='metric-delta'>Échelle {spi_scale} mois</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-value'>{avg_max_dry_spell:.0f}<span style='font-size:1rem;'> j</span></div>
        <div class='metric-label'>Dry spell max moyen</div>
        <div class='metric-delta'>saison des pluies</div>
    </div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class='metric-card'>
        <div class='metric-value'>{pct_false_starts:.0f}<span style='font-size:1rem;'>%</span></div>
        <div class='metric-label'>Faux démarrages</div>
        <div class='metric-delta'>des années analysées</div>
    </div>""", unsafe_allow_html=True)


# ── Onglets ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Anomalies & Pluies",
    "🌵 Sécheresse (SPI)",
    "💧 Séquences sèches",
    "🌱 Faux démarrages",
    "📥 Export données"
])


# ════ TAB 1 : Anomalies ══════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-header'>Pluviométrie annuelle et anomalies</div>", unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])

    with col_a:
        # Graphique barres annuelles avec LTA
        fig_ann = go.Figure()
        colors_bar = [ANOM_COLORS.get(c, "#888") for c in df_annual["category"]]
        fig_ann.add_trace(go.Bar(
            x=df_annual["year"], y=df_annual["total_rfh"],
            name="Pluie totale (mm)", marker_color=colors_bar,
            hovertemplate="<b>%{x}</b><br>Pluie : %{y:.1f} mm<extra></extra>"
        ))
        if df_annual["total_avg"].notna().any():
            fig_ann.add_trace(go.Scatter(
                x=df_annual["year"], y=df_annual["total_avg"],
                name="Moyenne LTA", line=dict(color="#E8571A", width=2, dash="dash"),
                hovertemplate="LTA : %{y:.1f} mm<extra></extra>"
            ))
        fig_ann.update_layout(
            title=f"Pluviométrie annuelle — {zone_label}",
            xaxis_title="Année", yaxis_title="Précipitations (mm)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            plot_bgcolor="white", height=350, margin=dict(t=50, b=40)
        )
        fig_ann.update_xaxes(gridcolor="#F0F0F0")
        fig_ann.update_yaxes(gridcolor="#F0F0F0")
        st.plotly_chart(fig_ann, use_container_width=True)

    with col_b:
        # Distribution des catégories
        cat_counts = df_annual["category"].value_counts().reset_index()
        cat_counts.columns = ["Catégorie", "Nb années"]
        cat_counts["Couleur"] = cat_counts["Catégorie"].map(ANOM_COLORS)
        fig_pie = px.pie(
            cat_counts, values="Nb années", names="Catégorie",
            color="Catégorie", color_discrete_map=ANOM_COLORS,
            title="Répartition des années"
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(height=350, showlegend=False, margin=dict(t=50, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("<div class='section-header'>Anomalies décadaires (% vs LTA)</div>", unsafe_allow_html=True)

    # Heatmap décadaire
    df_heat = df_zone[df_zone["rfh_avg"] > 0].copy()
    df_heat["dekad_label"] = df_heat["month"].astype(str).str.zfill(2) + "-D" + df_heat["dekad"].astype(str)
    if not df_heat.empty:
        pivot = df_heat.pivot_table(index="year", columns="dekad_label", values="rfq", aggfunc="mean")
        # Garder saison des pluies (mai–octobre)
        rain_cols = [c for c in pivot.columns if c[:2] in ["05","06","07","08","09","10"]]
        pivot_rain = pivot[sorted(rain_cols)]
        fig_heat = px.imshow(
            pivot_rain,
            color_continuous_scale=[[0,"#8B0000"],[0.4,"#FC8D59"],[0.5,"#FFFFBF"],
                                     [0.6,"#74ADD1"],[1,"#023858"]],
            range_color=[40, 160],
            labels=dict(color="% LTA", x="Décade", y="Année"),
            title="Anomalies décadaires (%) – Saison des pluies (mai–octobre)",
            aspect="auto"
        )
        fig_heat.update_layout(height=420, margin=dict(t=50, b=60))
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("<div class='section-header'>Profil saisonnier mensuel</div>", unsafe_allow_html=True)

    # Sélection années de comparaison
    available_years = sorted(df_monthly["year"].unique())
    default_years = [available_years[-1], available_years[-2]] if len(available_years) >= 2 else available_years
    selected_years = st.multiselect("Comparer des années spécifiques :", available_years, default=default_years, key="years_compare")

    fig_seasonal = go.Figure()
    # LTA
    lta_monthly = df_monthly.groupby("month").agg(lta=("rfh_avg_month","mean")).reset_index()
    fig_seasonal.add_trace(go.Scatter(
        x=lta_monthly["month"], y=lta_monthly["lta"],
        name="Moyenne LTA", line=dict(color="#888", width=2, dash="dot"),
        fill=None
    ))
    colors_years = px.colors.qualitative.Bold
    for i, yr in enumerate(selected_years):
        sub = df_monthly[df_monthly["year"] == yr]
        fig_seasonal.add_trace(go.Scatter(
            x=sub["month"], y=sub["rfh_month"],
            name=str(yr),
            line=dict(color=colors_years[i % len(colors_years)], width=2),
            mode="lines+markers"
        ))
    month_labels = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    fig_seasonal.update_layout(
        xaxis=dict(tickvals=list(range(1,13)), ticktext=month_labels),
        yaxis_title="Précipitations (mm)", title="Profil saisonnier",
        plot_bgcolor="white", height=350, legend=dict(orientation="h"),
        margin=dict(t=50, b=40)
    )
    fig_seasonal.update_xaxes(gridcolor="#F0F0F0")
    fig_seasonal.update_yaxes(gridcolor="#F0F0F0")
    st.plotly_chart(fig_seasonal, use_container_width=True)


# ════ TAB 2 : SPI ════════════════════════════════════════════════
with tab2:
    st.markdown(f"<div class='section-header'>Indice de sécheresse normalisé SPI-{spi_scale}</div>", unsafe_allow_html=True)

    if df_spi.empty or "spi" not in df_spi.columns:
        st.warning("Données SPI insuffisantes pour cette zone/période.")
    else:
        df_spi_plot = df_spi.dropna(subset=["spi"])

        # Graphique SPI temporel
        fig_spi = go.Figure()
        fig_spi.add_hline(y=0, line_color="#888", line_width=1)
        fig_spi.add_hline(y=-1, line_color="#FC8D59", line_width=1, line_dash="dot",
                          annotation_text="Sécheresse modérée", annotation_position="left")
        fig_spi.add_hline(y=-1.5, line_color="#D73027", line_width=1, line_dash="dot",
                          annotation_text="Sécheresse sévère", annotation_position="left")
        fig_spi.add_hline(y=1, line_color="#74ADD1", line_width=1, line_dash="dot")

        colors_spi = ["#D73027" if v < -1.5 else "#FC8D59" if v < -1 else
                      "#4575B4" if v > 1 else "#74ADD1" if v > 0 else "#AAAAAA"
                      for v in df_spi_plot["spi"]]

        fig_spi.add_trace(go.Bar(
            x=df_spi_plot["date"], y=df_spi_plot["spi"],
            marker_color=colors_spi, name=f"SPI-{spi_scale}",
            hovertemplate="<b>%{x|%b %Y}</b><br>SPI : %{y:.2f}<extra></extra>"
        ))
        fig_spi.update_layout(
            title=f"SPI-{spi_scale} — {zone_label} ({year_range[0]}–{year_range[1]})",
            yaxis_title=f"SPI-{spi_scale}", xaxis_title="",
            plot_bgcolor="white", height=380, margin=dict(t=50, b=40)
        )
        fig_spi.update_xaxes(gridcolor="#F0F0F0")
        fig_spi.update_yaxes(gridcolor="#F0F0F0")
        st.plotly_chart(fig_spi, use_container_width=True)

        # Répartition catégories SPI
        col_s1, col_s2 = st.columns([1, 2])
        with col_s1:
            st.markdown("<div class='section-header'>Répartition des catégories</div>", unsafe_allow_html=True)
            cat_spi = df_spi_plot["spi_category"].value_counts().reset_index()
            cat_spi.columns = ["Catégorie", "Nb mois"]
            fig_cat = px.bar(
                cat_spi, x="Nb mois", y="Catégorie", orientation="h",
                color="Catégorie", color_discrete_map=DROUGHT_COLORS,
                title=""
            )
            fig_cat.update_layout(showlegend=False, height=320, margin=dict(t=10, b=40))
            st.plotly_chart(fig_cat, use_container_width=True)

        with col_s2:
            st.markdown("<div class='section-header'>Années les plus sèches (SPI moyen annuel)</div>", unsafe_allow_html=True)
            spi_annual = df_spi_plot.groupby(df_spi_plot["date"].dt.year)["spi"].mean().reset_index()
            spi_annual.columns = ["Année", "SPI moyen"]
            spi_annual = spi_annual.sort_values("SPI moyen")
            worst_10 = spi_annual.head(10)
            fig_worst = px.bar(
                worst_10, x="Année", y="SPI moyen",
                color="SPI moyen",
                color_continuous_scale=[[0,"#8B0000"],[0.5,"#FC8D59"],[1,"#FFFFBF"]],
                range_color=[worst_10["SPI moyen"].min(), 0],
                title="Top 10 années les plus sèches"
            )
            fig_worst.update_layout(height=320, margin=dict(t=40, b=40), coloraxis_showscale=False)
            st.plotly_chart(fig_worst, use_container_width=True)


# ════ TAB 3 : Dry Spells ═════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-header'>Séquences sèches durant la saison des pluies (mai–octobre)</div>", unsafe_allow_html=True)

    if df_dry.empty:
        st.warning("Données insuffisantes.")
    else:
        col_d1, col_d2 = st.columns(2)

        with col_d1:
            fig_dry = go.Figure()
            fig_dry.add_trace(go.Bar(
                x=df_dry["year"],
                y=df_dry["max_dry_spell_days_est"],
                name="Dry spell max (jours estimés)",
                marker_color=["#D73027" if v > 20 else "#FC8D59" if v > 10 else "#74ADD1"
                              for v in df_dry["max_dry_spell_days_est"]],
                hovertemplate="<b>%{x}</b><br>Dry spell max : ~%{y} jours<extra></extra>"
            ))
            avg_dry = df_dry["max_dry_spell_days_est"].mean()
            fig_dry.add_hline(y=avg_dry, line_color="#E8571A", line_dash="dash",
                              annotation_text=f"Moy. {avg_dry:.0f}j", annotation_position="right")
            fig_dry.update_layout(
                title=f"Dry spell maximum estimé par année — {zone_label}",
                yaxis_title="Jours", xaxis_title="",
                plot_bgcolor="white", height=350, margin=dict(t=50, b=40)
            )
            fig_dry.update_xaxes(gridcolor="#F0F0F0")
            fig_dry.update_yaxes(gridcolor="#F0F0F0")
            st.plotly_chart(fig_dry, use_container_width=True)

        with col_d2:
            fig_pct = px.area(
                df_dry, x="year", y="pct_dry_season",
                title="% de décades sèches pendant la saison des pluies",
                color_discrete_sequence=["#E8571A"],
                labels={"pct_dry_season": "% décades sèches", "year": ""},
            )
            avg_pct = df_dry["pct_dry_season"].mean()
            fig_pct.add_hline(y=avg_pct, line_color="#1A1A2E", line_dash="dash",
                              annotation_text=f"Moy. {avg_pct:.1f}%")
            fig_pct.update_layout(plot_bgcolor="white", height=350, margin=dict(t=50, b=40))
            fig_pct.update_xaxes(gridcolor="#F0F0F0")
            fig_pct.update_yaxes(gridcolor="#F0F0F0")
            st.plotly_chart(fig_pct, use_container_width=True)

        st.markdown("<div class='section-header'>Tendance des dry spells (régression linéaire)</div>", unsafe_allow_html=True)
        from scipy.stats import linregress
        x = df_dry["year"].values
        y = df_dry["max_dry_spell_days_est"].values
        slope, intercept, r, p, _ = linregress(x, y)
        trend_line = slope * x + intercept

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=x, y=y, mode="markers+lines", name="Dry spell max",
                                       line=dict(color="#74ADD1", width=1.5),
                                       marker=dict(size=5)))
        fig_trend.add_trace(go.Scatter(x=x, y=trend_line, mode="lines", name=f"Tendance (slope={slope:+.2f}j/an)",
                                       line=dict(color="#E8571A", width=2, dash="dash")))
        trend_dir = "à la hausse 📈" if slope > 0.1 else "à la baisse 📉" if slope < -0.1 else "stable ↔"
        fig_trend.update_layout(
            title=f"Tendance des dry spells — {trend_dir} ({slope:+.2f} j/an, p={p:.3f})",
            plot_bgcolor="white", height=320, margin=dict(t=50, b=40),
            legend=dict(orientation="h")
        )
        fig_trend.update_xaxes(gridcolor="#F0F0F0")
        fig_trend.update_yaxes(gridcolor="#F0F0F0", title="Jours")
        st.plotly_chart(fig_trend, use_container_width=True)


# ════ TAB 4 : Faux démarrages ════════════════════════════════════
with tab4:
    st.markdown("<div class='section-header'>Détection des faux démarrages de saison des pluies</div>", unsafe_allow_html=True)
    st.caption("Critère FAO/AGRHYMET adapté : décade ≥ 20mm suivie de ≥ 2 décades sèches (< 5mm) dans les 4 décades suivantes (avril–juillet).")

    if df_false.empty:
        st.warning("Données insuffisantes.")
    else:
        col_f1, col_f2 = st.columns([2, 1])

        with col_f1:
            # Timeline faux démarrages
            fig_fs = go.Figure()
            colors_fs = ["#D73027" if v else "#74ADD1" for v in df_false["false_start_detected"]]
            fig_fs.add_trace(go.Bar(
                x=df_false["year"],
                y=[1] * len(df_false),
                marker_color=colors_fs,
                hovertext=df_false.apply(
                    lambda r: f"{'⚠️ Faux démarrage détecté' if r['false_start_detected'] else '✅ Pas de faux démarrage'}"
                              + (f"<br>Date : {r['false_start_date'].strftime('%d %b') if pd.notna(r['false_start_date']) else ''}" if r['false_start_detected'] else ""),
                    axis=1
                ),
                hoverinfo="text",
                name="Faux démarrage",
                showlegend=True
            ))
            fig_fs.update_layout(
                title=f"Occurrence des faux démarrages — {zone_label}",
                yaxis=dict(showticklabels=False, title=""),
                xaxis_title="",
                barmode="overlay", height=220,
                plot_bgcolor="white", margin=dict(t=50, b=40),
                legend=dict(orientation="h")
            )
            st.plotly_chart(fig_fs, use_container_width=True)

        with col_f2:
            n_fs = df_false["false_start_detected"].sum()
            n_total = len(df_false)
            rate = n_fs / n_total * 100 if n_total > 0 else 0
            st.markdown(f"""
            <div class='metric-card' style='margin-top:20px;'>
                <div class='metric-value'>{n_fs} / {n_total}</div>
                <div class='metric-label'>Années avec faux démarrage</div>
                <div class='metric-delta'>soit {rate:.1f}% des années</div>
            </div>
            """, unsafe_allow_html=True)

        # Taux cumulatif
        fig_rate = px.line(
            df_false, x="year", y="false_start_rate",
            title="Taux de faux démarrages cumulatif",
            labels={"false_start_rate": "Taux cumulatif", "year": ""},
            color_discrete_sequence=["#E8571A"]
        )
        fig_rate.add_hline(y=0.3, line_dash="dot", line_color="#D73027",
                           annotation_text="Seuil alerte 30%")
        fig_rate.update_layout(
            plot_bgcolor="white", height=300,
            margin=dict(t=50, b=40), yaxis_tickformat=".0%"
        )
        fig_rate.update_yaxes(tickformat=".0%", gridcolor="#F0F0F0")
        fig_rate.update_xaxes(gridcolor="#F0F0F0")
        st.plotly_chart(fig_rate, use_container_width=True)

        # Tableau récapitulatif faux démarrages
        with st.expander("📋 Détail par année"):
            df_fs_display = df_false[["year","false_start_detected","false_start_date","false_start_rfh"]].copy()
            df_fs_display.columns = ["Année","Faux démarrage","Date","Pluie décade (mm)"]
            df_fs_display["Faux démarrage"] = df_fs_display["Faux démarrage"].map({True: "⚠️ Oui", False: "✅ Non"})
            df_fs_display["Date"] = pd.to_datetime(df_fs_display["Date"]).dt.strftime("%d %b").fillna("—")
            df_fs_display["Pluie décade (mm)"] = df_fs_display["Pluie décade (mm)"].apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "—")
            st.dataframe(df_fs_display, use_container_width=True, hide_index=True)


# ════ TAB 5 : Export ══════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-header'>Téléchargement des données analysées</div>", unsafe_allow_html=True)

    col_e1, col_e2, col_e3 = st.columns(3)

    with col_e1:
        st.markdown("**📊 Données annuelles**")
        csv_annual = df_annual.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Télécharger CSV", csv_annual,
                           file_name=f"sahelrain_annual_{selected_pcode}_{year_range[0]}_{year_range[1]}.csv",
                           mime="text/csv")
        st.dataframe(df_annual.head(10), use_container_width=True, hide_index=True)

    with col_e2:
        st.markdown("**🌵 Données SPI**")
        if not df_spi.empty:
            csv_spi = df_spi.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Télécharger CSV", csv_spi,
                               file_name=f"sahelrain_spi{spi_scale}_{selected_pcode}.csv",
                               mime="text/csv")
            st.dataframe(df_spi[["date","year","month","spi","spi_category"]].head(10),
                         use_container_width=True, hide_index=True)

    with col_e3:
        st.markdown("**💧 Dry spells**")
        csv_dry = df_dry.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Télécharger CSV", csv_dry,
                           file_name=f"sahelrain_dryspells_{selected_pcode}.csv",
                           mime="text/csv")
        st.dataframe(df_dry.head(10), use_container_width=True, hide_index=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size:0.8rem; color:#888; text-align:center; padding:8px;'>
        <b>Source des données :</b> Climate Hazards Center UCSB & WFP — CHIRPS v2
        (<a href='https://data.humdata.org/dataset/bfa-rainfall-subnational'>HDX</a>)
        · Licence : CC BY-IGO 3.0<br>
        <b>Développé par :</b> Pragmatix Africa · Alban Wendé Gûudi OUEDRAOGO
        · <a href='mailto:manager@pragmatix-africa.com'>manager@pragmatix-africa.com</a>
    </div>
    """, unsafe_allow_html=True)
