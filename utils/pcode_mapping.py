# Mapping PCODE WFP → Nom Province/Région + coordonnées centroïdes
# Sources : WFP HDX, OCHA COD-AB Burkina Faso, Statoids

REGION_MAP = {
    "BF13": {"name": "Boucle du Mouhoun", "lat": 12.40, "lon": -3.50},
    "BF46": {"name": "Cascades",          "lat": 10.50, "lon": -4.50},
    "BF47": {"name": "Centre",            "lat": 12.37, "lon": -1.52},
    "BF48": {"name": "Centre-Est",        "lat": 11.90, "lon": -0.30},
    "BF49": {"name": "Centre-Nord",       "lat": 13.10, "lon": -1.20},
    "BF50": {"name": "Centre-Ouest",      "lat": 12.00, "lon": -2.50},
    "BF51": {"name": "Centre-Sud",        "lat": 11.70, "lon": -1.10},
    "BF52": {"name": "Est",               "lat": 12.40, "lon":  0.90},
    "BF53": {"name": "Hauts-Bassins",     "lat": 11.30, "lon": -4.20},
    "BF54": {"name": "Nord",              "lat": 13.70, "lon": -2.20},
    "BF55": {"name": "Plateau-Central",   "lat": 12.55, "lon": -0.85},
    "BF56": {"name": "Sahel",             "lat": 14.00, "lon": -0.40},
    "BF57": {"name": "Sud-Ouest",         "lat": 10.90, "lon": -3.30},
}

PROVINCE_MAP = {
    # Boucle du Mouhoun (BF13)
    "BF1300": {"name": "Mouhoun (agrégat)",  "region": "Boucle du Mouhoun", "lat": 12.40, "lon": -3.50},

    # Cascades (BF46)
    "BF4601": {"name": "Comoé",    "region": "Cascades", "lat": 10.55, "lon": -4.65},
    "BF4602": {"name": "Léraba",   "region": "Cascades", "lat": 10.30, "lon": -5.10},
    "BF4603": {"name": "Cascades-Nord", "region": "Cascades", "lat": 10.75, "lon": -4.20},
    "BF4604": {"name": "Cascades-Est",  "region": "Cascades", "lat": 10.50, "lon": -4.00},
    "BF4605": {"name": "Cascades-Sud",  "region": "Cascades", "lat": 10.20, "lon": -4.50},
    "BF4606": {"name": "Cascades-Ouest","region": "Cascades", "lat": 10.40, "lon": -4.90},

    # Centre (BF47)
    "BF4701": {"name": "Kadiogo",        "region": "Centre", "lat": 12.37, "lon": -1.52},
    "BF4702": {"name": "Centre-Nord",    "region": "Centre", "lat": 12.60, "lon": -1.40},
    "BF4703": {"name": "Centre-Ouest",   "region": "Centre", "lat": 12.25, "lon": -1.65},

    # Centre-Est (BF48)
    "BF4801": {"name": "Boulgou",        "region": "Centre-Est", "lat": 11.78, "lon": -0.35},
    "BF4802": {"name": "Koulpélogo",     "region": "Centre-Est", "lat": 11.50, "lon": -0.10},
    "BF4803": {"name": "Kouritenga",     "region": "Centre-Est", "lat": 12.10, "lon": -0.35},

    # Centre-Nord (BF49)
    "BF4901": {"name": "Bam",            "region": "Centre-Nord", "lat": 13.30, "lon": -1.55},
    "BF4902": {"name": "Namentenga",     "region": "Centre-Nord", "lat": 13.10, "lon": -0.50},
    "BF4903": {"name": "Sanmatenga",     "region": "Centre-Nord", "lat": 13.00, "lon": -1.20},

    # Centre-Ouest (BF50)
    "BF5001": {"name": "Boulkiemdé",     "region": "Centre-Ouest", "lat": 12.20, "lon": -2.35},
    "BF5002": {"name": "Sanguié",        "region": "Centre-Ouest", "lat": 12.10, "lon": -2.75},
    "BF5003": {"name": "Sissili",        "region": "Centre-Ouest", "lat": 11.55, "lon": -2.25},
    "BF5004": {"name": "Ziro",           "region": "Centre-Ouest", "lat": 11.50, "lon": -2.00},

    # Centre-Sud (BF51)
    "BF5101": {"name": "Bazèga",         "region": "Centre-Sud", "lat": 11.95, "lon": -1.35},
    "BF5102": {"name": "Nahouri",        "region": "Centre-Sud", "lat": 11.35, "lon": -1.07},
    "BF5103": {"name": "Zoundwéogo",     "region": "Centre-Sud", "lat": 11.70, "lon": -0.85},

    # Est (BF52)
    "BF5201": {"name": "Gnagna",         "region": "Est", "lat": 12.90, "lon":  0.30},
    "BF5202": {"name": "Gourma",         "region": "Est", "lat": 12.15, "lon":  0.35},
    "BF5203": {"name": "Kompienga",      "region": "Est", "lat": 11.40, "lon":  1.00},
    "BF5204": {"name": "Komondjari",     "region": "Est", "lat": 12.60, "lon":  1.30},
    "BF5205": {"name": "Tapoa",          "region": "Est", "lat": 12.00, "lon":  1.90},

    # Hauts-Bassins (BF53)
    "BF5301": {"name": "Houet",          "region": "Hauts-Bassins", "lat": 11.18, "lon": -4.30},
    "BF5302": {"name": "Kénédougou",     "region": "Hauts-Bassins", "lat": 11.55, "lon": -4.90},
    "BF5303": {"name": "Tuy",            "region": "Hauts-Bassins", "lat": 11.30, "lon": -3.60},

    # Nord (BF54)
    "BF5401": {"name": "Loroum",         "region": "Nord", "lat": 14.05, "lon": -2.70},
    "BF5402": {"name": "Passoré",        "region": "Nord", "lat": 13.05, "lon": -2.20},
    "BF5403": {"name": "Yatenga",        "region": "Nord", "lat": 13.60, "lon": -2.35},
    "BF5404": {"name": "Zondoma",        "region": "Nord", "lat": 13.40, "lon": -2.00},

    # Plateau-Central (BF55)
    "BF5501": {"name": "Ganzourgou",     "region": "Plateau-Central", "lat": 12.45, "lon": -0.75},
    "BF5502": {"name": "Kourwéogo",      "region": "Plateau-Central", "lat": 12.45, "lon": -1.35},
    "BF5503": {"name": "Oubritenga",     "region": "Plateau-Central", "lat": 12.65, "lon": -1.15},

    # Sahel (BF56)
    "BF5601": {"name": "Oudalan",        "region": "Sahel", "lat": 14.60, "lon": -0.05},
    "BF5602": {"name": "Séno",           "region": "Sahel", "lat": 14.00, "lon":  0.00},
    "BF5603": {"name": "Soum",           "region": "Sahel", "lat": 14.20, "lon": -1.55},
    "BF5604": {"name": "Yagha",          "region": "Sahel", "lat": 13.70, "lon":  0.75},

    # Sud-Ouest (BF57)
    "BF5701": {"name": "Bougouriba",     "region": "Sud-Ouest", "lat": 10.90, "lon": -3.25},
    "BF5702": {"name": "Ioba",           "region": "Sud-Ouest", "lat": 11.05, "lon": -3.05},
    "BF5703": {"name": "Noumbiel",       "region": "Sud-Ouest", "lat": 10.30, "lon": -3.05},
    "BF5704": {"name": "Poni",           "region": "Sud-Ouest", "lat": 10.65, "lon": -3.55},
}

def get_name(pcode: str) -> str:
    if pcode in REGION_MAP:
        return REGION_MAP[pcode]["name"] + " (Région)"
    if pcode in PROVINCE_MAP:
        return PROVINCE_MAP[pcode]["name"]
    return pcode

def get_coords(pcode: str):
    if pcode in REGION_MAP:
        r = REGION_MAP[pcode]
        return r["lat"], r["lon"]
    if pcode in PROVINCE_MAP:
        p = PROVINCE_MAP[pcode]
        return p["lat"], p["lon"]
    return 12.37, -1.52  # default Ouagadougou

def get_region(pcode: str) -> str:
    if pcode in REGION_MAP:
        return REGION_MAP[pcode]["name"]
    if pcode in PROVINCE_MAP:
        return PROVINCE_MAP[pcode]["region"]
    return "Inconnu"
