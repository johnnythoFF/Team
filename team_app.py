import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict
import os
import glob

st.set_page_config(
    page_title="NZ FF — Team Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    h1 { font-size: 1.6rem !important; }
    h2 { font-size: 1.2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── PARSE & AGGREGATE ─────────────────────────────────────────────────────────

def parse_game(df, game_name):
    """Extract team stats from a single game CSV."""

    home = df[df['Row'] == 'HOME POSSESSION'].copy()
    away = df[df['Row'] == 'AWAY POSSESSION'].copy()
    home_sp = df[df['Row'] == 'HOME SET PIECE'].copy()
    away_sp = df[df['Row'] == 'AWAY SET PIECE'].copy()

    def count_keyword(series, keyword):
        return series.dropna().str.contains(keyword, case=False, na=False).sum()

    def count_col_keyword(col_series, keyword):
        return col_series.dropna().str.contains(keyword, case=False, na=False).sum()

    # ── POSSESSION ────────────────────────────────────────────────────────────
    home_poss_count = len(home)
    away_poss_count = len(away)
    home_poss_duration = home['Duration'].sum() if 'Duration' in home.columns else 0
    away_poss_duration = away['Duration'].sum() if 'Duration' in away.columns else 0
    total_duration = home_poss_duration + away_poss_duration
    home_poss_pct = round(home_poss_duration / total_duration * 100, 1) if total_duration else 0
    home_avg_duration = round(home_poss_duration / home_poss_count, 1) if home_poss_count else 0

    # ── SHOTS (NZ attacking) ──────────────────────────────────────────────────
    shooting_col = 'SHOOTING' if 'SHOOTING' in home.columns else None
    if shooting_col:
        home_shots = count_col_keyword(home[shooting_col], 'SHOT')
        home_sot = count_col_keyword(home[shooting_col], 'ON TARGET')
        home_goals = count_col_keyword(home[shooting_col], 'GOAL')
        home_sp_shots = count_col_keyword(home_sp[shooting_col], 'SHOT') if len(home_sp) else 0
        home_sp_sot = count_col_keyword(home_sp[shooting_col], 'ON TARGET') if len(home_sp) else 0
        total_shots = home_shots + home_sp_shots
        total_sot = home_sot + home_sp_sot
    else:
        total_shots = home_sot = home_goals = total_sot = 0
        home_goals = 0

    # ── SHOTS CONCEDED (away attacking) ──────────────────────────────────────
    if shooting_col:
        away_shots = count_col_keyword(away[shooting_col], 'SHOT') if len(away) else 0
        away_sot = count_col_keyword(away[shooting_col], 'ON TARGET') if len(away) else 0
        away_sp_shots = count_col_keyword(away_sp[shooting_col], 'SHOT') if len(away_sp) else 0
        shots_conceded = away_shots + away_sp_shots
        sot_conceded = away_sot
    else:
        shots_conceded = sot_conceded = 0

    # ── CROSSES ───────────────────────────────────────────────────────────────
    cross_col = 'CROSSING' if 'CROSSING' in home.columns else None
    if cross_col:
        home_cross_success = count_col_keyword(home[cross_col], 'Cross Successful')
        home_cross_fail = count_col_keyword(home[cross_col], 'Cross Unsuccessful')
        sp_cross_success = count_col_keyword(home_sp[cross_col], 'Cross Successful') if len(home_sp) else 0
        sp_cross_fail = count_col_keyword(home_sp[cross_col], 'Cross Unsuccessful') if len(home_sp) else 0
        total_crosses = home_cross_success + home_cross_fail + sp_cross_success + sp_cross_fail
        total_cross_success = home_cross_success + sp_cross_success
    else:
        total_crosses = total_cross_success = 0

    # ── SEAM ENTRIES ──────────────────────────────────────────────────────────
    ungrouped_col = 'Ungrouped' if 'Ungrouped' in home.columns else None
    if ungrouped_col:
        seam2 = count_col_keyword(home[ungrouped_col], 'SEAM 2 ENTRY')
        seam3 = count_col_keyword(home[ungrouped_col], 'SEAM THREE ENTRY')
        sp_seam2 = count_col_keyword(home_sp[ungrouped_col], 'SEAM 2 ENTRY') if len(home_sp) else 0
        sp_seam3 = count_col_keyword(home_sp[ungrouped_col], 'SEAM THREE ENTRY') if len(home_sp) else 0
        total_seam2 = seam2 + sp_seam2
        total_seam3 = seam3 + sp_seam3
    else:
        total_seam2 = total_seam3 = 0

    # ── PEN AREA ENTRIES ──────────────────────────────────────────────────────
    pen_col = 'PEN AREA ENTRY' if 'PEN AREA ENTRY' in home.columns else None
    if pen_col:
        pen_entries = count_col_keyword(home[pen_col], 'PEN AREA ENTRY')
        sp_pen = count_col_keyword(home_sp[pen_col], 'PEN AREA ENTRY') if len(home_sp) else 0
        total_pen = pen_entries + sp_pen
    else:
        total_pen = 0

    # ── POSSESSION THIRDS ─────────────────────────────────────────────────────
    thirds_col = 'POSSESSION THIRDS' if 'POSSESSION THIRDS' in home.columns else None
    if thirds_col:
        d3 = count_col_keyword(home[thirds_col], 'P-D3')
        m3 = count_col_keyword(home[thirds_col], 'P-M3')
        f3 = count_col_keyword(home[thirds_col], 'P-F3')
    else:
        d3 = m3 = f3 = 0

    # ── SET PIECES ────────────────────────────────────────────────────────────
    home_sp_count = len(home_sp)
    away_sp_count = len(away_sp)

    # ── TRANSITIONS ───────────────────────────────────────────────────────────
    trans_col = 'TRANSITION' if 'TRANSITION' in home.columns else None
    if trans_col:
        transitions = count_col_keyword(home[trans_col], 'ATTACKING TRANSITION')
    else:
        transitions = 0

    # ── DATE ──────────────────────────────────────────────────────────────────
    date = None
    if 'Date' in df.columns:
        dates = df['Date'].dropna()
        if len(dates):
            date = dates.iloc[0]

    # ── OPPOSITION ────────────────────────────────────────────────────────────
    opposition = None
    if 'Opposition' in df.columns:
        opps = df['Opposition'].dropna()
        if len(opps):
            opposition = opps.iloc[0]

    return {
        'game': game_name,
        'date': date,
        'opposition': opposition or game_name,
        'home_poss_count': home_poss_count,
        'away_poss_count': away_poss_count,
        'home_poss_pct': home_poss_pct,
        'home_avg_duration': home_avg_duration,
        'total_shots': total_shots,
        'total_sot': total_sot,
        'home_goals': home_goals,
        'shots_conceded': shots_conceded,
        'sot_conceded': sot_conceded,
        'total_crosses': total_crosses,
        'total_cross_success': total_cross_success,
        'cross_pct': round(total_cross_success / total_crosses * 100, 1) if total_crosses else 0,
        'total_seam2': total_seam2,
        'total_seam3': total_seam3,
        'total_pen': total_pen,
        'pen_to_shot_pct': round(total_shots / total_pen * 100, 1) if total_pen else 0,
        'shot_on_target_pct': round(total_sot / total_shots * 100, 1) if total_shots else 0,
        'home_sp_count': home_sp_count,
        'away_sp_count': away_sp_count,
        'transitions': transitions,
        'd3_count': d3,
        'm3_count': m3,
        'f3_count': f3,
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
    st.markdown("## ⚽ NZ FF Team Dashboard")
    st.markdown("---")

    if repo_csvs:
        st.success(f"{len(repo_csvs)} game(s) loaded")
        for path in repo_csvs:
            st.markdown(f"- `{os.path.basename(path)}`")
        st.markdown("---")

    uploaded = st.file_uploader("Upload additional CSVs", type="csv", accept_multiple_files=True)
    if uploaded:
        for f in uploaded:
            game_name = f.name.replace('.csv', '')
            try:
                df = pd.read_csv(f, sep=None, engine='python')
                all_game_stats[game_name] = parse_game(df, game_name)
            except Exception as e:
                st.warning(f"Could not load {game_name}: {e}")

    st.markdown("---")
    page = st.radio("Page", ["Team Overview", "Trends Over Time"])

if not all_game_stats:
    st.title("⚽ NZ FF Team Dashboard")
    st.info("Add match CSVs to the `data/` folder in GitHub or upload via the sidebar.")
    st.stop()

# Sort games by date
games_list = list(all_game_stats.values())
try:
    games_list = sorted(games_list, key=lambda x: pd.to_datetime(x['date'], dayfirst=True) if x['date'] else pd.Timestamp.min)
except:
    pass

game_labels = [f"{g['opposition']} ({g['date'] or g['game']})" for g in games_list]

# ── PAGE 1: TEAM OVERVIEW ─────────────────────────────────────────────────────
if page == "Team Overview":

    if len(games_list) > 1:
        selected_label = st.selectbox("Select game", game_labels)
        g = games_list[game_labels.index(selected_label)]
    else:
        g = games_list[0]

    st.markdown(f"## vs {g['opposition']}  <span style='font-size:14px;color:grey;font-weight:normal;'>{g['date'] or ''}</span>", unsafe_allow_html=True)
    st.markdown("---")

    # ── TOP METRICS ───────────────────────────────────────────────────────────
    st.markdown("### Attacking")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Possession %", f"{g['home_poss_pct']}%")
    c2.metric("Possessions", g['home_poss_count'], f"avg {g['home_avg_duration']}s")
    c3.metric("Shots", g['total_shots'], f"{g['total_sot']} on target")
    c4.metric("Shot on target %", f"{g['shot_on_target_pct']}%")
    c5.metric("Goals", g['home_goals'])
    c6.metric("Set pieces (att)", g['home_sp_count'])

    st.markdown("---")
    st.markdown("### Chance creation")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Pen area entries", g['total_pen'])
    c2.metric("Pen entry → shot %", f"{g['pen_to_shot_pct']}%")
    c3.metric("Seam 2 entries", g['total_seam2'])
    c4.metric("Seam 3 entries", g['total_seam3'])
    c5.metric("Att transitions", g['transitions'])

    st.markdown("---")
    st.markdown("### Crosses")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total crosses", g['total_crosses'])
    c2.metric("Successful", g['total_cross_success'])
    c3.metric("Success rate", f"{g['cross_pct']}%")

    st.markdown("---")
    st.markdown("### Defensive")
    c1, c2, c3 = st.columns(3)
    c1.metric("Shots conceded", g['shots_conceded'])
    c2.metric("SOT conceded", g['sot_conceded'])
    c3.metric("Set pieces (def)", g['away_sp_count'])

    st.markdown("---")

    # ── POSSESSION THIRDS ─────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Possession thirds (NZ)**")
        thirds_total = g['d3_count'] + g['m3_count'] + g['f3_count']
        if thirds_total > 0:
            fig = go.Figure(go.Bar(
                x=['Def third', 'Mid third', 'Final third'],
                y=[g['d3_count'], g['m3_count'], g['f3_count']],
                marker_color=['#4d9fff', '#00C87A', '#ffb74d'],
                text=[g['d3_count'], g['m3_count'], g['f3_count']],
                textposition='auto',
            ))
            fig.update_layout(
                height=280, margin=dict(t=10,b=10,l=10,r=10),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No possession thirds data")

    with col2:
        st.markdown("**Possession split**")
        fig2 = go.Figure(go.Pie(
            labels=['NZ', 'Opposition'],
            values=[g['home_poss_pct'], round(100 - g['home_poss_pct'], 1)],
            hole=0.55,
            marker_colors=['#00C87A', '#ff5252'],
            textinfo='label+percent',
        ))
        fig2.update_layout(
            height=280, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── SHOT FUNNEL ───────────────────────────────────────────────────────────
    st.markdown("**Attacking funnel**")
    funnel_fig = go.Figure(go.Funnel(
        y=['Pen area entries', 'Shots', 'Shots on target', 'Goals'],
        x=[g['total_pen'], g['total_shots'], g['total_sot'], g['home_goals']],
        marker_color=['#4d9fff', '#00C87A', '#ffb74d', '#ff5252'],
        textposition='inside',
        textinfo='value+percent initial',
    ))
    funnel_fig.update_layout(
        height=300, margin=dict(t=10,b=10,l=10,r=10),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(funnel_fig, use_container_width=True)


# ── PAGE 2: TRENDS OVER TIME ──────────────────────────────────────────────────
elif page == "Trends Over Time":

    if len(games_list) < 2:
        st.info("Add more games to the `data/` folder to see trends. At least 2 games needed.")
        st.markdown("Current data from 1 game shown below for reference.")

    labels = [f"{g['opposition']}\n{g['date'] or ''}" for g in games_list]
    short_labels = [g['opposition'] for g in games_list]

    def trend_chart(title, y_values, labels, color='#00C87A', suffix='', show_avg=True):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=labels, y=y_values,
            mode='lines+markers+text',
            line=dict(color=color, width=2.5),
            marker=dict(size=8, color=color),
            text=[f"{v}{suffix}" for v in y_values],
            textposition='top center',
            textfont=dict(size=11),
            name=title,
        ))
        if show_avg and len(y_values) > 1:
            avg = round(sum(y_values) / len(y_values), 1)
            fig.add_hline(y=avg, line_dash='dot', line_color='rgba(128,128,128,0.5)',
                         annotation_text=f"avg {avg}{suffix}", annotation_position='right')
        fig.update_layout(
            height=220, margin=dict(t=10,b=10,l=10,r=10),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)', zeroline=False),
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            showlegend=False,
        )
        return fig

    st.markdown("## Trends over time")
    st.markdown("---")

    # Row 1
    st.markdown("### Shooting")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Shot on target %**")
        st.plotly_chart(trend_chart('SOT %', [g['shot_on_target_pct'] for g in games_list], short_labels, '#00C87A', '%'), use_container_width=True)
    with col2:
        st.markdown("**Total shots**")
        st.plotly_chart(trend_chart('Shots', [g['total_shots'] for g in games_list], short_labels, '#ffb74d'), use_container_width=True)

    st.markdown("---")
    st.markdown("### Chance creation")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Penalty box entries**")
        st.plotly_chart(trend_chart('Pen entries', [g['total_pen'] for g in games_list], short_labels, '#4d9fff'), use_container_width=True)
    with col2:
        st.markdown("**Pen entry → shot %**")
        st.plotly_chart(trend_chart('Pen→Shot %', [g['pen_to_shot_pct'] for g in games_list], short_labels, '#00C87A', '%'), use_container_width=True)

    st.markdown("---")
    st.markdown("### Entries")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Seam 2 entries**")
        st.plotly_chart(trend_chart('Seam 2', [g['total_seam2'] for g in games_list], short_labels, '#4d9fff'), use_container_width=True)
    with col2:
        st.markdown("**Seam 3 entries**")
        st.plotly_chart(trend_chart('Seam 3', [g['total_seam3'] for g in games_list], short_labels, '#ffb74d'), use_container_width=True)

    st.markdown("---")
    st.markdown("### Crosses")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Cross success rate %**")
        st.plotly_chart(trend_chart('Cross %', [g['cross_pct'] for g in games_list], short_labels, '#00C87A', '%'), use_container_width=True)
    with col2:
        st.markdown("**Total crosses**")
        st.plotly_chart(trend_chart('Crosses', [g['total_crosses'] for g in games_list], short_labels, '#4d9fff'), use_container_width=True)

    st.markdown("---")
    st.markdown("### Defensive")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Shots conceded**")
        st.plotly_chart(trend_chart('Shots conceded', [g['shots_conceded'] for g in games_list], short_labels, '#ff5252'), use_container_width=True)
    with col2:
        st.markdown("**SOT conceded**")
        st.plotly_chart(trend_chart('SOT conceded', [g['sot_conceded'] for g in games_list], short_labels, '#ff5252'), use_container_width=True)

    st.markdown("---")
    st.markdown("### Summary table")
    summary_rows = []
    for g in games_list:
        summary_rows.append({
            'Opposition': g['opposition'],
            'Date': g['date'] or '',
            'Poss %': f"{g['home_poss_pct']}%",
            'Shots': g['total_shots'],
            'SOT %': f"{g['shot_on_target_pct']}%",
            'Pen entries': g['total_pen'],
            'Pen→Shot %': f"{g['pen_to_shot_pct']}%",
            'Seam 2': g['total_seam2'],
            'Seam 3': g['total_seam3'],
            'Cross %': f"{g['cross_pct']}%",
            'Shots conceded': g['shots_conceded'],
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
