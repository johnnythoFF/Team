import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# ── PASSWORD GATE ─────────────────────────────────────────────────────────────
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("⚽ NZ FF Team Dashboard")
    pwd = st.text_input("Enter password", type="password")
    if st.button("Login"):
        if pwd == st.secrets.get("APP_PASSWORD", "footballferns"):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

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

games_list = list(all_game_stats.values())
try:
    games_list = sorted(games_list, key=lambda x: pd.to_datetime(x['date'], dayfirst=True) if x['date'] else pd.Timestamp.min)
except:
    pass

game_labels = [f"{g['opposition']} ({g['date'] or g['game']})" for g in games_list]


def get_avg(games, key, exclude_idx=None, n=5):
    """Get average of last n games excluding the selected game."""
    others = [g for i, g in enumerate(games) if i != exclude_idx]
    recent = others[-n:] if len(others) >= n else others
    if not recent:
        return None
    return sum(g[key] for g in recent) / len(recent)

def delta_label(val, avg, lower_is_better=False, suffix=''):
    """Return (delta_string, delta_color) for st.metric."""
    if avg is None:
        return None, "off"
    raw_diff = val - avg
    if abs(raw_diff) < 0.05:
        return f"avg {round(avg,1)}{suffix}", "off"
    sign = "+" if raw_diff > 0 else ""
    label = f"{sign}{round(raw_diff, 1)}{suffix} vs 5-game avg"
    # For lower_is_better metrics, green = went down, red = went up
    if lower_is_better:
        color = "inverse"
    else:
        color = "normal"
    return label, color


# ── PAGE 1: TEAM OVERVIEW ─────────────────────────────────────────────────────
if page == "Team Overview":

    if len(games_list) > 1:
        selected_label = st.selectbox("Select game", game_labels)
        g_idx = game_labels.index(selected_label)
        g = games_list[g_idx]
    else:
        g = games_list[0]
        g_idx = 0

    has_history = len(games_list) > 1

    def mdelta(key, lower_is_better=False, suffix=''):
        if not has_history:
            return None, None
        avg = get_avg(games_list, key, exclude_idx=g_idx)
        return delta_label(g[key], avg, lower_is_better=lower_is_better, suffix=suffix)

    st.markdown(f"## vs {g['opposition']}  <span style='font-size:14px;color:grey;font-weight:normal;'>{g['date'] or ''}</span>", unsafe_allow_html=True)

    if has_history:
        st.caption("↑↓ vs last 5-game average (excluding this game)")

    st.markdown("---")

    st.markdown("### Attacking")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    d, dt = mdelta('home_poss_pct', suffix='%')
    c1.metric("Possession %", f"{g['home_poss_pct']}%", delta=d, delta_color=dt or "off")
    c2.metric("Possessions", g['home_poss_count'], f"avg {g['home_avg_duration']}s")
    d, dt = mdelta('total_shots')
    c3.metric("Shots", g['total_shots'], delta=d, delta_color=dt or "off")
    d, dt = mdelta('shot_on_target_pct', suffix='%')
    c4.metric("Shot on target %", f"{g['shot_on_target_pct']}%", delta=d, delta_color=dt or "off")
    d, dt = mdelta('home_goals')
    c5.metric("Goals", g['home_goals'], delta=d, delta_color=dt or "off")
    c6.metric("Set pieces (att)", g['home_sp_count'])

    st.markdown("---")
    st.markdown("### Chance creation")
    c1, c2, c3, c4, c5 = st.columns(5)
    d, dt = mdelta('total_pen')
    c1.metric("Pen area entries", g['total_pen'], delta=d, delta_color=dt or "off")
    d, dt = mdelta('pen_to_shot_pct', suffix='%')
    c2.metric("Pen entry → shot %", f"{g['pen_to_shot_pct']}%", delta=d, delta_color=dt or "off",
              help=f"{g['pen_with_shot']} of {g['total_pen']} pen entries resulted in a shot")
    d, dt = mdelta('total_seam2')
    c3.metric("Seam 2 entries", g['total_seam2'], delta=d, delta_color=dt or "off")
    d, dt = mdelta('total_seam3')
    c4.metric("Seam 3 entries", g['total_seam3'], delta=d, delta_color=dt or "off")
    d, dt = mdelta('transitions')
    c5.metric("Att transitions", g['transitions'], delta=d, delta_color=dt or "off")

    st.markdown("---")
    st.markdown("### Crosses")
    c1, c2, c3 = st.columns(3)
    d, dt = mdelta('total_crosses')
    c1.metric("Total crosses", g['total_crosses'], delta=d, delta_color=dt or "off")
    c2.metric("Successful", g['total_cross_success'])
    d, dt = mdelta('cross_pct', suffix='%')
    c3.metric("Success rate", f"{g['cross_pct']}%", delta=d, delta_color=dt or "off")

    st.markdown("---")
    st.markdown("### Defensive")
    c1, c2, c3 = st.columns(3)
    d, dt = mdelta('shots_conceded', lower_is_better=True)
    c1.metric("Shots conceded", g['shots_conceded'], delta=d, delta_color=dt or "off")
    d, dt = mdelta('sot_conceded', lower_is_better=True)
    c2.metric("SOT conceded", g['sot_conceded'], delta=d, delta_color=dt or "off")
    c3.metric("Set pieces (def)", g['away_sp_count'])

    st.markdown("---")
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

    st.markdown("**Attacking funnel**")
    funnel_fig = go.Figure(go.Funnel(
        y=['Pen area entries', 'Pen entries with shot', 'Shots on target', 'Goals'],
        x=[g['total_pen'], g['pen_with_shot'], g['total_sot'], g['home_goals']],
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
        st.markdown("**Pen entry → shot %**  *(entries that led to a shot)*")
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
