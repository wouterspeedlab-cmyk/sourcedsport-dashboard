# SourcedSport GPS Dashboard

Een evidence-based GPS monitoring dashboard voor field hockey coaches, gebouwd met Streamlit.

![Dashboard Preview](preview.png)

## Features

- **Team Overview**: Real-time overzicht van teamgemiddelden met traffic light systeem
- **Weekly Load Progression**: Wekelijkse belastingstrends visualiseren
- **ACWR Monitor**: Acute:Chronic Workload Ratio per speler met risico-indicatie
- **Player Comparison**: Radar charts om spelers te vergelijken
- **Individual Profiles**: Gedetailleerde trends per speler
- **Data Export**: Download gefilterde data als CSV

## Benchmarks

Gebaseerd op evidence-based bronnen:
- Buchheit & Laursen (2013) - High-intensity interval training
- Jennings et al. (2012) - GPS analysis in field hockey
- Williams et al. (2017) - ACWR methodology

### Field Hockey Benchmarks
| Metric | Match Avg | Training Target |
|--------|-----------|-----------------|
| Total Distance | ~9,500m | 70% |
| HSR (>16 km/h) | ~1,800m | 65% |
| Sprint (>21 km/h) | ~450m | 60% |
| Accelerations | ~85 | 70% |
| Player Load | ~950 AU | 70% |

### ACWR Zones
- 🟢 **Optimal**: 0.8 - 1.3
- 🟡 **Caution**: 0.6 - 0.8 (undertraining) / 1.3 - 1.5 (high load)
- 🔴 **Risk**: <0.6 (detraining) / >1.5 (injury risk)

## Installatie (Lokaal)

```bash
# 1. Clone of download de repository
git clone https://github.com/[jouw-username]/sourcedsport-dashboard.git
cd sourcedsport-dashboard

# 2. Maak een virtual environment (optioneel maar aanbevolen)
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 3. Installeer dependencies
pip install -r requirements.txt

# 4. Start de app
streamlit run sourcedsport_dashboard.py
```

De app opent automatisch in je browser op `http://localhost:8501`

## Deployment (Gratis op Streamlit Cloud)

### Stap 1: GitHub Repository
1. Maak een GitHub account als je die nog niet hebt
2. Maak een nieuwe repository (bijv. `sourcedsport-dashboard`)
3. Upload deze bestanden:
   - `sourcedsport_dashboard.py`
   - `requirements.txt`
   - `README.md`

### Stap 2: Deploy op Streamlit Cloud
1. Ga naar [share.streamlit.io](https://share.streamlit.io)
2. Klik "New app"
3. Selecteer je GitHub repository
4. Kies `sourcedsport_dashboard.py` als main file
5. Klik "Deploy"

Je app is nu live op een URL zoals: `https://[jouw-app].streamlit.app`

## Data Format

### CSV Upload (STATSports/Catapult)

De app herkent automatisch de meest voorkomende column names van STATSports en Catapult exports. Voor beste resultaten, zorg dat je CSV minimaal deze kolommen bevat:

| Kolom | Beschrijving |
|-------|--------------|
| Date | Datum (YYYY-MM-DD) |
| Player / Player Name / Athlete Name | Spelernaam |
| Total Distance | Totale afstand in meters |
| High Speed Running / HSR Distance | HSR afstand (>16 km/h) |
| Sprint Distance | Sprint afstand (>21 km/h) |
| Accels / Accelerations | Aantal acceleraties |
| Decels / Decelerations | Aantal deceleraties |
| Player Load / Dynamic Stress Load | Belasting in AU |
| Max Speed | Maximale snelheid |

### Demo Data

Zonder CSV upload toont de app automatisch gegenereerde demo data voor 20 spelers over 8 weken.

## Customization

### Benchmarks aanpassen

In het bestand `sourcedsport_dashboard.py`, zoek de `FIELD_HOCKEY_BENCHMARKS` dictionary om de targets aan te passen aan jouw team niveau of sport:

```python
FIELD_HOCKEY_BENCHMARKS = {
    "total_distance": {
        "match_avg": 9500,  # Pas aan naar jouw niveau
        "green": (6000, 8000),
        # ...
    }
}
```

### ACWR Zones aanpassen

```python
ACWR_ZONES = {
    "green": (0.8, 1.3),     # Optimal zone
    "yellow_low": (0.6, 0.8),
    # ...
}
```

## Toekomstige Features

- [ ] Meerdere seizoenen vergelijken
- [ ] PDF rapport generatie
- [ ] E-mail alerts bij hoge ACWR
- [ ] Integratie met Google Sheets
- [ ] Player availability predictor

## Support

Vragen of suggesties? Contact via [SourcedSport](https://sourcedsport.com)

---

**SourcedSport** - Evidence-based performance coaching
