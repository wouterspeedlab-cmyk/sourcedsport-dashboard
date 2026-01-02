"""
SourcedSport GPS Performance Dashboard
=====================================
A Streamlit dashboard for field hockey coaches to analyze GPS data.

Features:
- Upload STATSports or Catapult CSV exports
- Individual player profiles
- Team overview with traffic light system
- Weekly load progression charts
- Acute:Chronic Workload Ratio (ACWR) monitoring

To run locally:
    pip install streamlit pandas plotly numpy
    streamlit run sourcedsport_dashboard.py

To deploy free on Streamlit Community Cloud:
    1. Push this file to a GitHub repository
    2. Go to share.streamlit.io
    3. Connect your GitHub and select the repo
    4. Deploy!

Author: SourcedSport - Evidence-Based Performance Coaching
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io

# =============================================================================
# PAGE CONFIG & STYLING
# =============================================================================

st.set_page_config(
    page_title="SourcedSport GPS Dashboard",
    page_icon="🏑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional sports aesthetic
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Main styling */
    .stApp {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 500;
    }
    
    [data-testid="stMetricDelta"] {
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Traffic light badges */
    .status-green {
        background-color: #10b981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-yellow {
        background-color: #f59e0b;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-orange {
        background-color: #f97316;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-red {
        background-color: #ef4444;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        color: #e2e8f0;
    }
    
    /* Card-like containers */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 24px;
        border: 1px solid #334155;
    }
    
    /* Table styling */
    .dataframe {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.9rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom header */
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# BENCHMARK DATA (Evidence-based from Buchheit, Laursen et al.)
# =============================================================================

FIELD_HOCKEY_BENCHMARKS = {
    "total_distance": {
        "unit": "m",
        "match_avg": 9500,
        "training_target_pct": 0.70,  # 70% of match load
        "green": (6000, 8000),
        "yellow": (8000, 9500),
        "orange": (9500, 11000),
        "red_high": 11000,
        "red_low": 5000
    },
    "hsr_distance": {  # High-Speed Running >16 km/h
        "unit": "m",
        "match_avg": 1800,
        "training_target_pct": 0.65,
        "green": (1000, 1500),
        "yellow": (1500, 1800),
        "orange": (1800, 2200),
        "red_high": 2200,
        "red_low": 800
    },
    "sprint_distance": {  # >21 km/h
        "unit": "m",
        "match_avg": 450,
        "training_target_pct": 0.60,
        "green": (200, 350),
        "yellow": (350, 450),
        "orange": (450, 600),
        "red_high": 600,
        "red_low": 150
    },
    "accel_count": {  # >2.5 m/s²
        "unit": "n",
        "match_avg": 85,
        "training_target_pct": 0.70,
        "green": (50, 70),
        "yellow": (70, 85),
        "orange": (85, 100),
        "red_high": 100,
        "red_low": 40
    },
    "decel_count": {  # <-2.5 m/s²
        "unit": "n",
        "match_avg": 80,
        "training_target_pct": 0.70,
        "green": (45, 65),
        "yellow": (65, 80),
        "orange": (80, 95),
        "red_high": 95,
        "red_low": 35
    },
    "player_load": {
        "unit": "AU",
        "match_avg": 950,
        "training_target_pct": 0.70,
        "green": (500, 750),
        "yellow": (750, 900),
        "orange": (900, 1100),
        "red_high": 1100,
        "red_low": 400
    }
}

ACWR_ZONES = {
    "green": (0.8, 1.3),     # Optimal zone
    "yellow_low": (0.6, 0.8),  # Undertraining risk
    "yellow_high": (1.3, 1.5), # Moderate overload
    "red_low": 0.6,           # Significant undertraining
    "red_high": 1.5           # High injury risk
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_traffic_light(value, metric):
    """Return traffic light color based on value and metric benchmarks."""
    benchmarks = FIELD_HOCKEY_BENCHMARKS.get(metric, {})
    
    if not benchmarks:
        return "gray"
    
    green = benchmarks.get("green", (0, 0))
    yellow = benchmarks.get("yellow", (0, 0))
    orange = benchmarks.get("orange", (0, 0))
    red_high = benchmarks.get("red_high", float('inf'))
    red_low = benchmarks.get("red_low", 0)
    
    if value < red_low or value > red_high:
        return "red"
    elif orange[0] <= value <= orange[1]:
        return "orange"
    elif yellow[0] <= value <= yellow[1]:
        return "yellow"
    elif green[0] <= value <= green[1]:
        return "green"
    else:
        return "yellow"


def get_acwr_status(acwr):
    """Return status based on ACWR value."""
    if acwr is None or np.isnan(acwr):
        return "gray", "No data"
    
    if ACWR_ZONES["green"][0] <= acwr <= ACWR_ZONES["green"][1]:
        return "green", "Optimal"
    elif ACWR_ZONES["yellow_low"][0] <= acwr < ACWR_ZONES["green"][0]:
        return "yellow", "Undertraining"
    elif ACWR_ZONES["green"][1] < acwr <= ACWR_ZONES["yellow_high"][1]:
        return "yellow", "High Load"
    elif acwr < ACWR_ZONES["red_low"]:
        return "red", "Detraining Risk"
    else:
        return "red", "Injury Risk"


def calculate_acwr(weekly_loads, acute_weeks=1, chronic_weeks=4):
    """
    Calculate Acute:Chronic Workload Ratio.
    
    Uses exponentially weighted moving average (EWMA) method
    as recommended by Williams et al. (2017).
    """
    if len(weekly_loads) < chronic_weeks:
        return None
    
    # EWMA calculation
    acute_lambda = 2 / (acute_weeks * 7 + 1)
    chronic_lambda = 2 / (chronic_weeks * 7 + 1)
    
    acute_load = weekly_loads[-1]  # Most recent week
    
    # Calculate chronic using EWMA
    chronic_ewma = weekly_loads[0]
    for load in weekly_loads[1:]:
        chronic_ewma = load * chronic_lambda + chronic_ewma * (1 - chronic_lambda)
    
    if chronic_ewma == 0:
        return None
    
    return acute_load / chronic_ewma


def generate_sample_data(n_players=20, n_weeks=8):
    """Generate realistic sample GPS data for demonstration."""
    np.random.seed(42)
    
    players = [f"Player {i+1}" for i in range(n_players)]
    positions = ["GK", "DEF", "DEF", "DEF", "MID", "MID", "MID", "MID", "FWD", "FWD"]
    
    data = []
    start_date = datetime.now() - timedelta(weeks=n_weeks)
    
    for week in range(n_weeks):
        for session in range(4):  # 4 sessions per week
            session_date = start_date + timedelta(weeks=week, days=session*2)
            session_type = "Match" if session == 3 else "Training"
            
            for player in players:
                # Base values with position variation
                pos = positions[players.index(player) % len(positions)]
                pos_factor = 1.0 if pos == "MID" else 0.9 if pos in ["DEF", "FWD"] else 0.6
                
                # Match vs training factor
                match_factor = 1.3 if session_type == "Match" else 1.0
                
                # Progressive overload simulation
                week_factor = 0.85 + (week / n_weeks) * 0.3
                
                # Random variation
                rand_factor = np.random.uniform(0.85, 1.15)
                
                combined = pos_factor * match_factor * week_factor * rand_factor
                
                data.append({
                    "Date": session_date.strftime("%Y-%m-%d"),
                    "Player": player,
                    "Position": pos,
                    "Session Type": session_type,
                    "Duration (min)": int(90 * match_factor * np.random.uniform(0.9, 1.1)),
                    "Total Distance (m)": int(6500 * combined),
                    "HSR Distance (m)": int(1200 * combined),
                    "Sprint Distance (m)": int(300 * combined),
                    "Accelerations": int(60 * combined),
                    "Decelerations": int(55 * combined),
                    "Player Load (AU)": round(650 * combined, 1),
                    "Max Speed (km/h)": round(28 + np.random.uniform(-3, 3), 1)
                })
    
    return pd.DataFrame(data)


def parse_uploaded_data(uploaded_file):
    """Parse uploaded CSV file and standardize column names."""
    df = pd.read_csv(uploaded_file)
    
    # Common column name mappings for different GPS systems
    column_mappings = {
        # STATSports
        "Player Name": "Player",
        "Total Distance": "Total Distance (m)",
        "High Speed Running": "HSR Distance (m)",
        "Sprint Distance": "Sprint Distance (m)",
        "Accels": "Accelerations",
        "Decels": "Decelerations",
        "Dynamic Stress Load": "Player Load (AU)",
        
        # Catapult
        "Athlete Name": "Player",
        "Total Player Load": "Player Load (AU)",
        "Velocity Band 5 Total Distance": "HSR Distance (m)",
        "Velocity Band 6 Total Distance": "Sprint Distance (m)",
        "Acceleration Band 3 Total Effort Count": "Accelerations",
        "Deceleration Band 3 Total Effort Count": "Decelerations"
    }
    
    # Apply mappings
    df = df.rename(columns={k: v for k, v in column_mappings.items() if k in df.columns})
    
    return df


# =============================================================================
# DASHBOARD COMPONENTS
# =============================================================================

def render_header():
    """Render the main dashboard header."""
    st.markdown("""
    <div class="main-header">
        <h1>🏑 SourcedSport GPS Dashboard</h1>
        <p>Evidence-based performance monitoring for field hockey</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar(df):
    """Render sidebar with filters and data upload."""
    with st.sidebar:
        st.image("https://via.placeholder.com/200x60/1e40af/ffffff?text=SourcedSport", width=200)
        st.markdown("---")
        
        # Data source selection
        st.subheader("📊 Data Source")
        data_source = st.radio(
            "Choose data source:",
            ["Demo Data", "Upload CSV"],
            label_visibility="collapsed"
        )
        
        if data_source == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload GPS Export (CSV)",
                type=["csv"],
                help="Upload your STATSports or Catapult CSV export"
            )
            if uploaded_file:
                df = parse_uploaded_data(uploaded_file)
                st.success(f"✅ Loaded {len(df)} records")
        
        st.markdown("---")
        
        # Filters
        st.subheader("🎯 Filters")
        
        if df is not None and len(df) > 0:
            # Date filter
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                min_date = df["Date"].min()
                max_date = df["Date"].max()
                
                date_range = st.date_input(
                    "Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Player filter
            if "Player" in df.columns:
                all_players = ["All Players"] + sorted(df["Player"].unique().tolist())
                selected_player = st.selectbox("Player", all_players)
            
            # Position filter
            if "Position" in df.columns:
                all_positions = ["All Positions"] + sorted(df["Position"].unique().tolist())
                selected_position = st.selectbox("Position", all_positions)
            
            # Session type filter
            if "Session Type" in df.columns:
                all_sessions = ["All Sessions"] + sorted(df["Session Type"].unique().tolist())
                selected_session = st.selectbox("Session Type", all_sessions)
        
        st.markdown("---")
        
        # Benchmark info
        st.subheader("📚 Benchmarks")
        st.caption("Based on elite field hockey data from Buchheit & Laursen (2013), Jennings et al. (2012)")
        
        with st.expander("View Benchmarks"):
            st.markdown("""
            **Total Distance**
            - Match avg: ~9,500m
            - Training target: 70%
            
            **High-Speed Running** (>16 km/h)
            - Match avg: ~1,800m
            - Training target: 65%
            
            **Sprint Distance** (>21 km/h)
            - Match avg: ~450m
            - Training target: 60%
            
            **ACWR Zones**
            - 🟢 Optimal: 0.8-1.3
            - 🟡 Caution: 0.6-0.8 / 1.3-1.5
            - 🔴 Risk: <0.6 / >1.5
            """)
        
        return df


def render_team_overview(df):
    """Render team overview with key metrics."""
    st.subheader("📈 Team Overview")
    
    # Calculate team averages for most recent session
    latest_date = df["Date"].max()
    latest_df = df[df["Date"] == latest_date]
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        avg_dist = latest_df["Total Distance (m)"].mean()
        color = get_traffic_light(avg_dist, "total_distance")
        st.metric(
            "Avg Distance",
            f"{avg_dist:,.0f}m",
            delta=f"{((avg_dist / 6500) - 1) * 100:+.1f}% vs target"
        )
        st.markdown(f'<span class="status-{color}">●</span>', unsafe_allow_html=True)
    
    with col2:
        avg_hsr = latest_df["HSR Distance (m)"].mean()
        color = get_traffic_light(avg_hsr, "hsr_distance")
        st.metric(
            "Avg HSR",
            f"{avg_hsr:,.0f}m",
            delta=f"{((avg_hsr / 1200) - 1) * 100:+.1f}% vs target"
        )
        st.markdown(f'<span class="status-{color}">●</span>', unsafe_allow_html=True)
    
    with col3:
        avg_sprint = latest_df["Sprint Distance (m)"].mean()
        color = get_traffic_light(avg_sprint, "sprint_distance")
        st.metric(
            "Avg Sprint",
            f"{avg_sprint:,.0f}m",
            delta=f"{((avg_sprint / 300) - 1) * 100:+.1f}% vs target"
        )
        st.markdown(f'<span class="status-{color}">●</span>', unsafe_allow_html=True)
    
    with col4:
        avg_accel = latest_df["Accelerations"].mean()
        color = get_traffic_light(avg_accel, "accel_count")
        st.metric(
            "Avg Accels",
            f"{avg_accel:.0f}",
            delta=f"{((avg_accel / 60) - 1) * 100:+.1f}% vs target"
        )
        st.markdown(f'<span class="status-{color}">●</span>', unsafe_allow_html=True)
    
    with col5:
        avg_load = latest_df["Player Load (AU)"].mean()
        color = get_traffic_light(avg_load, "player_load")
        st.metric(
            "Avg Load",
            f"{avg_load:.0f} AU",
            delta=f"{((avg_load / 650) - 1) * 100:+.1f}% vs target"
        )
        st.markdown(f'<span class="status-{color}">●</span>', unsafe_allow_html=True)
    
    with col6:
        max_speed = latest_df["Max Speed (km/h)"].max()
        st.metric(
            "Peak Speed",
            f"{max_speed:.1f} km/h"
        )


def render_weekly_load_chart(df):
    """Render weekly load progression chart."""
    st.subheader("📊 Weekly Load Progression")
    
    # Aggregate by week
    df["Week"] = df["Date"].dt.isocalendar().week
    df["Year"] = df["Date"].dt.year
    df["YearWeek"] = df["Year"].astype(str) + "-W" + df["Week"].astype(str).str.zfill(2)
    
    weekly = df.groupby("YearWeek").agg({
        "Total Distance (m)": "sum",
        "HSR Distance (m)": "sum",
        "Player Load (AU)": "sum"
    }).reset_index()
    
    # Select metric to display
    metric = st.selectbox(
        "Select Metric",
        ["Total Distance (m)", "HSR Distance (m)", "Player Load (AU)"]
    )
    
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=weekly["YearWeek"],
        y=weekly[metric],
        marker_color="#3b82f6",
        name=metric
    ))
    
    # Add target line
    target = weekly[metric].mean() * 1.1
    fig.add_hline(
        y=target,
        line_dash="dash",
        line_color="#10b981",
        annotation_text="Target +10%"
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="#334155"),
        yaxis=dict(gridcolor="#334155")
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_acwr_monitor(df):
    """Render ACWR monitoring chart."""
    st.subheader("⚠️ Acute:Chronic Workload Ratio")
    
    # Calculate weekly totals per player
    df["Week"] = df["Date"].dt.isocalendar().week
    
    weekly_player = df.groupby(["Player", "Week"])["Player Load (AU)"].sum().reset_index()
    
    # Calculate ACWR for each player (most recent)
    acwr_data = []
    for player in df["Player"].unique():
        player_weeks = weekly_player[weekly_player["Player"] == player].sort_values("Week")
        weekly_loads = player_weeks["Player Load (AU)"].tolist()
        
        acwr = calculate_acwr(weekly_loads)
        if acwr:
            status_color, status_text = get_acwr_status(acwr)
            acwr_data.append({
                "Player": player,
                "ACWR": acwr,
                "Status": status_text,
                "Color": status_color
            })
    
    acwr_df = pd.DataFrame(acwr_data).sort_values("ACWR", ascending=False)
    
    # Create horizontal bar chart
    colors = acwr_df["Color"].map({
        "green": "#10b981",
        "yellow": "#f59e0b",
        "orange": "#f97316",
        "red": "#ef4444",
        "gray": "#6b7280"
    }).tolist()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=acwr_df["Player"],
        x=acwr_df["ACWR"],
        orientation="h",
        marker_color=colors,
        text=acwr_df["ACWR"].round(2),
        textposition="outside"
    ))
    
    # Add optimal zone
    fig.add_vrect(
        x0=0.8, x1=1.3,
        fillcolor="#10b981",
        opacity=0.1,
        line_width=0,
        annotation_text="Optimal Zone",
        annotation_position="top"
    )
    
    # Add danger zones
    fig.add_vrect(x0=0, x1=0.6, fillcolor="#ef4444", opacity=0.1, line_width=0)
    fig.add_vrect(x0=1.5, x1=2.0, fillcolor="#ef4444", opacity=0.1, line_width=0)
    
    fig.update_layout(
        height=max(400, len(acwr_df) * 25),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        xaxis=dict(
            gridcolor="#334155",
            range=[0, 2],
            title="ACWR"
        ),
        yaxis=dict(gridcolor="#334155")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        optimal = len(acwr_df[acwr_df["Status"] == "Optimal"])
        st.metric("🟢 Optimal", optimal)
    
    with col2:
        caution = len(acwr_df[acwr_df["Status"].isin(["Undertraining", "High Load"])])
        st.metric("🟡 Caution", caution)
    
    with col3:
        risk = len(acwr_df[acwr_df["Status"].isin(["Detraining Risk", "Injury Risk"])])
        st.metric("🔴 Risk", risk)
    
    with col4:
        avg_acwr = acwr_df["ACWR"].mean()
        st.metric("Team Avg ACWR", f"{avg_acwr:.2f}")


def render_player_comparison(df):
    """Render player comparison radar chart."""
    st.subheader("👥 Player Comparison")
    
    # Select players to compare
    players = df["Player"].unique().tolist()
    selected_players = st.multiselect(
        "Select players to compare (max 5)",
        players,
        default=players[:3],
        max_selections=5
    )
    
    if not selected_players:
        st.info("Select at least one player to display the comparison")
        return
    
    # Calculate averages for selected players
    metrics = ["Total Distance (m)", "HSR Distance (m)", "Sprint Distance (m)", 
               "Accelerations", "Decelerations", "Player Load (AU)"]
    
    # Normalize to percentage of max for radar chart
    player_data = df[df["Player"].isin(selected_players)].groupby("Player")[metrics].mean()
    
    # Normalize
    normalized = player_data.copy()
    for col in metrics:
        max_val = player_data[col].max()
        if max_val > 0:
            normalized[col] = (player_data[col] / max_val) * 100
    
    # Create radar chart
    fig = go.Figure()
    
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"]
    
    for i, player in enumerate(selected_players):
        values = normalized.loc[player].tolist()
        values.append(values[0])  # Close the polygon
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics + [metrics[0]],
            fill="toself",
            name=player,
            line_color=colors[i % len(colors)],
            opacity=0.7
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#334155"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        showlegend=True,
        height=500,
        margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0")
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_individual_player(df):
    """Render individual player profile."""
    st.subheader("👤 Individual Player Profile")
    
    selected_player = st.selectbox(
        "Select Player",
        df["Player"].unique(),
        key="individual_player"
    )
    
    player_df = df[df["Player"] == selected_player].sort_values("Date")
    
    # Player stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Position**")
        st.markdown(f"### {player_df['Position'].iloc[0]}")
    
    with col2:
        sessions = len(player_df)
        st.markdown("**Sessions**")
        st.markdown(f"### {sessions}")
    
    with col3:
        avg_load = player_df["Player Load (AU)"].mean()
        st.markdown("**Avg Load**")
        st.markdown(f"### {avg_load:.0f} AU")
    
    # Trend chart
    st.markdown("#### Load Trend")
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    
    # Total Distance trend
    fig.add_trace(
        go.Scatter(
            x=player_df["Date"],
            y=player_df["Total Distance (m)"],
            mode="lines+markers",
            name="Total Distance",
            line=dict(color="#3b82f6", width=2),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    # Player Load trend
    fig.add_trace(
        go.Scatter(
            x=player_df["Date"],
            y=player_df["Player Load (AU)"],
            mode="lines+markers",
            name="Player Load",
            line=dict(color="#10b981", width=2),
            marker=dict(size=8)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    
    st.plotly_chart(fig, use_container_width=True)


def render_data_table(df):
    """Render full data table with export option."""
    st.subheader("📋 Raw Data")
    
    # Show/hide columns
    all_columns = df.columns.tolist()
    selected_columns = st.multiselect(
        "Select columns to display",
        all_columns,
        default=all_columns
    )
    
    st.dataframe(
        df[selected_columns].sort_values("Date", ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Export button
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"gps_data_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    
    # Initialize with demo data
    df = generate_sample_data()
    
    # Render header
    render_header()
    
    # Render sidebar and get filtered data
    df = render_sidebar(df)
    
    if df is None or len(df) == 0:
        st.warning("No data available. Please upload a CSV file or use demo data.")
        return
    
    # Ensure Date is datetime
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Overview",
        "📊 Weekly Load",
        "⚠️ ACWR Monitor",
        "👥 Compare Players",
        "📋 Raw Data"
    ])
    
    with tab1:
        render_team_overview(df)
        st.markdown("---")
        render_individual_player(df)
    
    with tab2:
        render_weekly_load_chart(df)
    
    with tab3:
        render_acwr_monitor(df)
    
    with tab4:
        render_player_comparison(df)
    
    with tab5:
        render_data_table(df)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748b; font-size: 0.875rem;">
        <p>SourcedSport GPS Dashboard | Evidence-based performance monitoring</p>
        <p>Benchmarks based on Buchheit & Laursen (2013), Jennings et al. (2012), Williams et al. (2017)</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
