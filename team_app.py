import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import glob

st.set_page_config(
    page_title="Football Ferns — Team Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800;900&family=Barlow:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif;
    background-color: #0d0f14;
    color: #e8eaf0;
}
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px;
}

/* HEADER */
.ff-header {
    background: linear-gradient(135deg, #0d0f14 60%, #0a1a22);
    border-bottom: 2px solid #00d4ff;
    padding: 20px 32px 16px;
    margin-bottom: 24px;
}
.ff-supertitle {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: #00d4ff;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.ff-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 52px;
    font-weight: 900;
    color: white;
    line-height: 0.9;
    text-transform: uppercase;
    letter-spacing: -0.01em;
    -webkit-text-stroke: 1px rgba(255,255,255,0.3);
    margin-bottom: 8px;
}
.ff-subtitle {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #00d4ff;
    text-transform: uppercase;
}
.ff-vs {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-left: 8px;
}

/* SECTION LABELS */
.section-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #00d4ff;
    text-transform: uppercase;
    border-left: 3px solid #00d4ff;
    padding-left: 10px;
    margin: 20px 0 12px;
}

/* STAT CARDS */
.stat-card {
    background: #13151c;
    border: 1px solid #1e2230;
    border-top: 2px solid #00d4ff;
    border-radius: 4px;
    padding: 16px 18px;
    margin-bottom: 8px;
}
.stat-card-label {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #5a6080;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.stat-card-val {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 42px;
    font-weight: 900;
    line-height: 1;
    color: #ffffff;
}
.stat-card-val.cyan { color: #00d4ff; }
.stat-card-val.green { color: #00e5a0; }
.stat-card-val.red { color: #ff4d6a; }
.stat-card-val.amber { color: #ffb74d; }
.stat-card-sub {
    font-size: 11px;
    color: #5a6080;
    margin-top: 5px;
    font-family: 'Barlow', sans-serif;
}

/* DIVIDER */
.ff-divider {
    border: none;
    border-top: 1px solid #1e2230;
    margin: 20px 0;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #0d0f14 !important;
    border-right: 1px solid #1e2230 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 14px !important;
    letter-spacing: 0.05em;
}

/* STREAMLIT METRIC OVERRIDE */
[data-testid="metric-container"] {
    background: #13151c;
    border: 1px solid #1e2230;
    border-top: 2px solid #00d4ff;
    border-radius: 4px;
    padding: 14px 16px !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.15em !important;
    color: #5a6080 !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 36px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
}
[data-testid="stMetricDelta"] {
    font-size: 11px !important;
    color: #5a6080 !important;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────

def col_contains(series, keyword):
    return series.fillna('').str.contains(keyword, case=False, na=False)

def count_rows(series, keyword):
    return col_contains(series, keyword).sum()

def count_instances(series, keyword):
    total = 0
    for val in series.fillna(''):
        total += str(val).upper().count(keyword.upper())
    return total

def has_col(frame, col):
    return col in frame.columns and len(frame) > 0


# ── PARSE ─────────────────────────────────────────────────────────────────────

def parse_game(df, game_name):
    home    = df[df['Row'] == 'HOME POSSESSION'].copy().reset_index(drop=True)
    away    = df[df['Row'] == 'AWAY POSSESSION'].copy().reset_index(drop=True)
    home_sp = df[df['Row'] == 'HOME SET PIECE'].copy().reset_index(drop=True)
    away_sp = df[df['Row'] == 'AWAY SET PIECE'].copy().reset_index(drop=True)

    shoot  = 'SHOOTING'
    cross  = 'CROSSING'
    ung    = 'Ungrouped'
    pen    = 'PEN AREA ENTRY'
    thirds = 'POSSESSION THIRDS'
    trans  = 'TRANSITION'

    home_poss_count   = len(home)
    away_poss_count   = len(away)
    home_poss_dur     = home['Duration'].sum() if 'Duration' in home.columns else 0
    away_poss_dur     = away['Duration'].sum() if 'Duration' in away.columns else 0
    total_dur         = home_poss_dur + away_poss_dur
    home_poss_pct     = round(home_poss_dur / total_dur * 100, 1) if total_dur else 0
    home_avg_duration = round(home_poss_dur / home_poss_count, 1) if home_poss_count else 0

    home_shots  = count_instances(home[shoot], 'SHOT')      if has_col(home, shoot) else 0
    home_sot    = count_instances(home[shoot], 'ON TARGET') if has_col(home, shoot) else 0
    home_goals  = count_instances(home[shoot], 'GOAL')      if has_col(home, shoot) else 0
    sp_shots    = count_instances(home_sp[shoot], 'SHOT')      if has_col(home_sp, shoot) else 0
    sp_sot      = count_instances(home_sp[shoot], 'ON TARGET') if has_col(home_sp, shoot) else 0
    total_shots = home_shots + sp_shots
    total_sot   = home_sot + sp_sot

    away_shots    = count_instances(away[shoot], 'SHOT')         if has_col(away, shoot) else 0
    away_sot      = count_instances(away[shoot], 'ON TARGET')    if has_col(away, shoot) else 0
    away_sp_shots = count_instances(away_sp[shoot], 'SHOT')      if has_col(away_sp, shoot) else 0
    away_sp_sot   = count_instances(away_sp[shoot], 'ON TARGET') if has_col(away_sp, shoot) else 0
    shots_conceded = away_shots + away_sp_shots
    sot_conceded   = away_sot + away_sp_sot

    home_cross_ok   = count_rows(home[cross], 'Cross Successful')      if has_col(home, cross) else 0
    home_cross_fail = count_rows(home[cross], 'Cross Unsuccessful')    if has_col(home, cross) else 0
    sp_cross_ok     = count_rows(home_sp[cross], 'Cross Successful')   if has_col(home_sp, cross) else 0
    sp_cross_fail   = count_rows(home_sp[cross], 'Cross Unsuccessful') if has_col(home_sp, cross) else 0
    total_crosses       = home_cross_ok + home_cross_fail + sp_cross_ok + sp_cross_fail
    total_cross_success = home_cross_ok + sp_cross_ok
    cross_pct           = round(total_cross_success / total_crosses * 100, 1) if total_crosses else 0

    seam2    = count_rows(home[ung], 'SEAM 2 ENTRY')        if has_col(home, ung) else 0
    seam3    = count_rows(home[ung], 'SEAM THREE ENTRY')    if has_col(home, ung) else 0
    sp_seam2 = count_rows(home_sp[ung], 'SEAM 2 ENTRY')     if has_col(home_sp, ung) else 0
    sp_seam3 = count_rows(home_sp[ung], 'SEAM THREE ENTRY') if has_col(home_sp, ung) else 0
    total_seam2 = seam2 + sp_seam2
    total_seam3 = seam3 + sp_seam3

    home_pen_rows = count_rows(home[pen], 'PEN AREA ENTRY')    if has_col(home, pen) else 0
    sp_pen_rows   = count_rows(home_sp[pen], 'PEN AREA ENTRY') if has_col(home_sp, pen) else 0
    total_pen     = home_pen_rows + sp_pen_rows

    if has_col(home, pen) and has_col(home, shoot):
        home_pen_with_shot = int((col_contains(home[pen], 'PEN AREA ENTRY') & col_contains(home[shoot], 'SHOT')).sum())
    else:
        home_pen_with_shot = 0

    if has_col(home_sp, pen) and has_col(home_sp, shoot):
        sp_pen_with_shot = int((col_contains(home_sp[pen], 'PEN AREA ENTRY') & col_contains(home_sp[shoot], 'SHOT')).sum())
    else:
        sp_pen_with_shot = 0

    pen_with_shot   = home_pen_with_shot + sp_pen_with_shot
    pen_to_shot_pct = round(pen_with_shot / total_pen * 100, 1) if total_pen else 0

    d3 = count_rows(home[thirds], 'P-D3') if has_col(home, thirds) else 0
    m3 = count_rows(home[thirds], 'P-M3') if has_col(home, thirds) else 0
    f3 = count_rows(home[thirds], 'P-F3') if has_col(home, thirds) else 0

    transitions   = count_rows(home[trans], 'ATTACKING TRANSITION') if has_col(home, trans) else 0
    home_sp_count = len(home_sp)
    away_sp_count = len(away_sp)
    shot_on_target_pct = round(total_sot / total_shots * 100, 1) if total_shots else 0

    date       = df['Date'].dropna().iloc[0]       if ('Date' in df.columns and len(df['Date'].dropna())) else None
    opposition = df['Opposition'].dropna().iloc[0] if ('Opposition' in df.columns and len(df['Opposition'].dropna())) else game_name

    return {
        'game': game_name, 'date': date, 'opposition': opposition,
        'home_poss_count': home_poss_count, 'away_poss_count': away_poss_count,
        'home_poss_pct': home_poss_pct, 'home_avg_duration': home_avg_duration,
        'total_shots': total_shots, 'total_sot': total_sot, 'home_goals': home_goals,
        'shots_conceded': shots_conceded, 'sot_conceded': sot_conceded,
        'total_crosses': total_crosses, 'total_cross_success': total_cross_success, 'cross_pct': cross_pct,
        'total_seam2': total_seam2, 'total_seam3': total_seam3,
        'total_pen': total_pen, 'pen_with_shot': pen_with_shot, 'pen_to_shot_pct': pen_to_shot_pct,
        'shot_on_target_pct': shot_on_target_pct,
        'home_sp_count': home_sp_count, 'away_sp_count': away_sp_count,
        'transitions': transitions, 'd3_count': d3, 'm3_count': m3, 'f3_count': f3,
    }


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
all_game_stats = {}
data_folder = "data"
repo_csvs = sorted(glob.glob(os.path.join(data_folder, "*.csv")))

if repo_csvs:
    for path in repo_csvs:
        game_name = os.path.basename(path).replace('.csv', '')
        try:
            df = pd.read_csv(path, sep=None, engine='python')
            all_game_stats[game_name] = parse_game(df, game_name)
        except Exception as e:
            st.warning(f"Could not load {game_name}: {e}")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 8px;'>
        <div style='font-family:Barlow Condensed,sans-serif;font-size:10px;font-weight:700;letter-spacing:0.2em;color:#00d4ff;text-transform:uppercase;margin-bottom:4px;'>Football Ferns</div>
        <div style='font-family:Barlow Condensed,sans-serif;font-size:26px;font-weight:900;color:white;text-transform:uppercase;line-height:1;'>Team Dashboard</div>
    </div>
    <hr style='border-color:#1e2230;margin:12px 0;'>
    """, unsafe_allow_html=True)

    if repo_csvs:
        st.success(f"{len(repo_csvs)} game(s) loaded")
        for path in repo_csvs:
            st.markdown(f"<div style='font-size:11px;color:#5a6080;padding:2px 0;'>📄 {os.path.basename(path)}</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#1e2230;margin:12px 0;'>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload additional CSVs", type="csv", accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            game_name = f.name.replace('.csv', '')
            try:
                df = pd.read_csv(f, sep=None, engine='python')
                all_game_stats[game_name] = parse_game(df, game_name)
            except Exception as e:
                st.warning(f"Could not load {game_name}: {e}")

    st.markdown("<hr style='border-color:#1e2230;margin:12px 0;'>", unsafe_allow_html=True)
    page = st.radio("", ["Team Overview", "Trends Over Time"])

if not all_game_stats:
    st.markdown("""
    <div class='ff-header'>
        <div class='ff-supertitle'>Football Ferns</div>
        <div class='ff-title'>Team<br>Dashboard</div>
        <div class='ff-subtitle'>OFC Qualifiers</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Add match CSVs to the `data/` folder in GitHub or upload via the sidebar.")
    st.stop()

games_list = list(all_game_stats.values())
try:
    games_list = sorted(games_list, key=lambda x: pd.to_datetime(x['date'], dayfirst=True) if x['date'] else pd.Timestamp.min)
except:
    pass

game_labels = [f"vs {g['opposition']} — {g['date'] or g['game']}" for g in games_list]

CYAN   = '#00d4ff'
GREEN  = '#00e5a0'
RED    = '#ff4d6a'
AMBER  = '#ffb74d'
MUTED  = '#5a6080'
BG     = '#13151c'
BORDER = '#1e2230'

def plotly_defaults():
    return dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Barlow Condensed', color='#e8eaf0'),
        margin=dict(t=10, b=10, l=10, r=10),
    )

def section(label):
    st.markdown(f"<div class='section-label'>{label}</div>", unsafe_allow_html=True)


# ── PAGE 1: TEAM OVERVIEW ─────────────────────────────────────────────────────
if page == "Team Overview":

    if len(games_list) > 1:
        selected_label = st.selectbox("", game_labels)
        g = games_list[game_labels.index(selected_label)]
    else:
        g = games_list[0]

    # Header
    st.markdown(f"""
    <div class='ff-header'>
        <div class='ff-supertitle'>Match Report</div>
        <div class='ff-title'>Football<br>Ferns</div>
        <div class='ff-subtitle'>OFC Qualifiers <span class='ff-vs'>vs {g['opposition']}</span></div>
        <div style='font-size:11px;color:{MUTED};margin-top:6px;font-family:Barlow Condensed,sans-serif;letter-spacing:0.1em;'>{g['date'] or ''}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── POSSESSION BAR ────────────────────────────────────────────────────────
    opp_pct = round(100 - g['home_poss_pct'], 1)
    st.markdown(f"""
    <div style='background:{BG};border:1px solid {BORDER};border-radius:4px;padding:14px 20px;margin-bottom:16px;'>
        <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
            <span style='font-family:Barlow Condensed,sans-serif;font-size:13px;font-weight:700;color:{CYAN};letter-spacing:0.1em;'>NZ {g['home_poss_pct']}%</span>
            <span style='font-family:Barlow Condensed,sans-serif;font-size:10px;font-weight:700;color:{MUTED};letter-spacing:0.15em;text-transform:uppercase;'>POSSESSION</span>
            <span style='font-family:Barlow Condensed,sans-serif;font-size:13px;font-weight:700;color:{RED};letter-spacing:0.1em;'>{opp_pct}% {g['opposition']}</span>
        </div>
        <div style='height:8px;background:#1e2230;border-radius:4px;overflow:hidden;'>
            <div style='height:100%;width:{g["home_poss_pct"]}%;background:{CYAN};border-radius:4px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── ATTACKING ─────────────────────────────────────────────────────────────
    section("Attacking")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Shots", g['total_shots'])
    c2.metric("On Target", g['total_sot'])
    c3.metric("SOT %", f"{g['shot_on_target_pct']}%")
    c4.metric("Goals", g['home_goals'])
    c5.metric("Possessions", g['home_poss_count'])
    c6.metric("Avg Duration", f"{g['home_avg_duration']}s")

    # ── CHANCE CREATION ───────────────────────────────────────────────────────
    section("Chance Creation")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Pen Box Entries", g['total_pen'])
    c2.metric("Entry → Shot %", f"{g['pen_to_shot_pct']}%")
    c3.metric("Seam 2 Entries", g['total_seam2'])
    c4.metric("Seam 3 Entries", g['total_seam3'])
    c5.metric("Transitions", g['transitions'])

    # ── CROSSES ───────────────────────────────────────────────────────────────
    section("Crosses")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Crosses", g['total_crosses'])
    c2.metric("Successful", g['total_cross_success'])
    c3.metric("Success Rate", f"{g['cross_pct']}%")
    c4.metric("Set Pieces (Att)", g['home_sp_count'])

    # ── DEFENSIVE ─────────────────────────────────────────────────────────────
    section("Defensive")
    c1, c2, c3 = st.columns(3)
    c1.metric("Shots Conceded", g['shots_conceded'])
    c2.metric("SOT Conceded", g['sot_conceded'])
    c3.metric("Set Pieces (Def)", g['away_sp_count'])

    st.markdown("<hr style='border-color:#1e2230;margin:24px 0;'>", unsafe_allow_html=True)

    # ── CHARTS ROW ────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        section("Possession Thirds")
        thirds_total = g['d3_count'] + g['m3_count'] + g['f3_count']
        if thirds_total > 0:
            fig = go.Figure(go.Bar(
                x=['Def', 'Mid', 'Final'],
                y=[g['d3_count'], g['m3_count'], g['f3_count']],
                marker_color=[MUTED, CYAN, GREEN],
                text=[g['d3_count'], g['m3_count'], g['f3_count']],
                textposition='auto',
                textfont=dict(family='Barlow Condensed', size=14, color='white'),
            ))
            fig.update_layout(
                height=220,
                **plotly_defaults(),
                yaxis=dict(gridcolor='#1e2230', zeroline=False, showticklabels=False),
                xaxis=dict(tickfont=dict(family='Barlow Condensed', size=12, color=MUTED)),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        section("Attacking Funnel")
        fig2 = go.Figure(go.Funnel(
            y=['Pen Entries', 'With Shot', 'On Target', 'Goals'],
            x=[g['total_pen'], g['pen_with_shot'], g['total_sot'], g['home_goals']],
            marker_color=[CYAN, GREEN, AMBER, RED],
            textposition='inside',
            textinfo='value+percent initial',
            textfont=dict(family='Barlow Condensed', size=13),
        ))
        fig2.update_layout(height=220, **plotly_defaults())
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        section("Cross Breakdown")
        fig3 = go.Figure(go.Pie(
            labels=['Successful', 'Unsuccessful'],
            values=[g['total_cross_success'], g['total_crosses'] - g['total_cross_success']],
            hole=0.6,
            marker_colors=[CYAN, '#1e2230'],
            textinfo='label+percent',
            textfont=dict(family='Barlow Condensed', size=12),
        ))
        fig3.update_layout(
            height=220,
            **plotly_defaults(),
            showlegend=False,
            annotations=[dict(
                text=f"<b>{g['cross_pct']}%</b>",
                x=0.5, y=0.5, font=dict(size=20, family='Barlow Condensed', color='white'),
                showarrow=False
            )]
        )
        st.plotly_chart(fig3, use_container_width=True)


# ── PAGE 2: TRENDS OVER TIME ──────────────────────────────────────────────────
elif page == "Trends Over Time":

    st.markdown(f"""
    <div class='ff-header'>
        <div class='ff-supertitle'>Season Analysis</div>
        <div class='ff-title'>Trends</div>
        <div class='ff-subtitle'>OFC Qualifiers — Performance Over Time</div>
    </div>
    """, unsafe_allow_html=True)

    if len(games_list) < 2:
        st.info("Add more games to the `data/` folder to see trends. At least 2 games needed.")

    short_labels = [g['opposition'] for g in games_list]

    def trend_chart(y_values, labels, color=CYAN, suffix=''):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=labels, y=y_values,
            mode='lines+markers+text',
            line=dict(color=color, width=2.5),
            marker=dict(size=9, color=color, line=dict(color='#0d0f14', width=2)),
            text=[f"{v}{suffix}" for v in y_values],
            textposition='top center',
            textfont=dict(size=12, family='Barlow Condensed', color='white'),
        ))
        if len(y_values) > 1:
            avg = round(sum(y_values) / len(y_values), 1)
            fig.add_hline(y=avg, line_dash='dot', line_color=MUTED,
                         annotation_text=f"avg {avg}{suffix}",
                         annotation_font=dict(family='Barlow Condensed', size=11, color=MUTED),
                         annotation_position='right')
        fig.update_layout(
            height=200,
            **plotly_defaults(),
            yaxis=dict(gridcolor='#1e2230', zeroline=False, showticklabels=False),
            xaxis=dict(tickfont=dict(family='Barlow Condensed', size=11, color=MUTED)),
            showlegend=False,
        )
        return fig

    section("Shooting")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Shot on Target %</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['shot_on_target_pct'] for g in games_list], short_labels, GREEN, '%'), use_container_width=True)
    with col2:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Total Shots</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['total_shots'] for g in games_list], short_labels, CYAN), use_container_width=True)

    section("Chance Creation")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Penalty Box Entries</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['total_pen'] for g in games_list], short_labels, CYAN), use_container_width=True)
    with col2:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Pen Entry → Shot %</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['pen_to_shot_pct'] for g in games_list], short_labels, GREEN, '%'), use_container_width=True)

    section("Entries")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Seam 2 Entries</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['total_seam2'] for g in games_list], short_labels, CYAN), use_container_width=True)
    with col2:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Seam 3 Entries</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['total_seam3'] for g in games_list], short_labels, AMBER), use_container_width=True)

    section("Crosses")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Cross Success Rate %</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['cross_pct'] for g in games_list], short_labels, GREEN, '%'), use_container_width=True)
    with col2:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Total Crosses</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['total_crosses'] for g in games_list], short_labels, CYAN), use_container_width=True)

    section("Defensive")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>Shots Conceded</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['shots_conceded'] for g in games_list], short_labels, RED), use_container_width=True)
    with col2:
        st.markdown(f"<div style='font-family:Barlow Condensed;font-size:12px;color:{MUTED};letter-spacing:0.1em;text-transform:uppercase;margin-bottom:6px;'>SOT Conceded</div>", unsafe_allow_html=True)
        st.plotly_chart(trend_chart([g['sot_conceded'] for g in games_list], short_labels, RED), use_container_width=True)

    section("Summary Table")
    summary_rows = []
    for g in games_list:
        summary_rows.append({
            'Opposition': g['opposition'],
            'Date': g['date'] or '',
            'Poss %': f"{g['home_poss_pct']}%",
            'Shots': g['total_shots'],
            'SOT %': f"{g['shot_on_target_pct']}%",
            'Pen Entries': g['total_pen'],
            'Entry→Shot %': f"{g['pen_to_shot_pct']}%",
            'Seam 2': g['total_seam2'],
            'Seam 3': g['total_seam3'],
            'Cross %': f"{g['cross_pct']}%",
            'Shots Conceded': g['shots_conceded'],
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
