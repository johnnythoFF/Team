import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os
from collections import Counter

st.set_page_config(page_title="Football Ferns — Tactical Analysis", layout="wide")

st.markdown('<link href="https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">', unsafe_allow_html=True)

st.markdown("""
<style>
  html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'Nunito Sans', sans-serif !important;
  }
  .stApp { background:#f5f6f7; }
  section[data-testid="stSidebar"] { background:#ffffff; border-right:2px solid #e8e8e8; }
  .page-header {
    background:linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    padding:24px 32px 20px; border-radius:12px; margin-bottom:20px;
  }
  .page-header h1 { color:#ffffff; font-size:24px; font-weight:800; margin:0; }
  .page-header p  { color:#a0aec0; font-size:13px; margin:4px 0 0; }
  .header-badge {
    background:rgba(255,255,255,0.12); border:1px solid rgba(255,255,255,0.2);
    border-radius:20px; padding:4px 12px; font-size:12px; color:#e2e8f0;
    display:inline-block; margin-top:8px;
  }
  .metric-card {
    background:#ffffff; border:1px solid #e8e8e8; border-radius:10px;
    padding:16px 14px; text-align:center; border-top:3px solid #0f3460;
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
  }
  .metric-card.green { border-top-color:#2d6a4f; }
  .metric-card.red   { border-top-color:#e63946; }
  .metric-card.amber { border-top-color:#e07b00; }
  .metric-label { font-size:10px; color:#718096; text-transform:uppercase;
    letter-spacing:1.2px; margin-bottom:6px; font-weight:600; }
  .metric-value { font-size:26px; font-weight:800; color:#1a1a2e; line-height:1; }
  .metric-value.green { color:#2d6a4f; }
  .metric-value.red   { color:#e63946; }
  .metric-value.amber { color:#e07b00; }
  .metric-sub   { font-size:11px; color:#a0aec0; margin-top:4px; }
  .section-title {
    font-size:15px; font-weight:700; color:#1a1a2e; text-transform:uppercase;
    letter-spacing:1px; border-bottom:2px solid #0f3460; padding-bottom:6px;
    margin:24px 0 14px;
  }
  .chart-wrap {
    background:#ffffff; border:1px solid #e8e8e8; border-radius:10px;
    padding:4px; box-shadow:0 1px 4px rgba(0,0,0,0.05); margin-bottom:8px;
  }
  .sidebar-header { font-size:13px; font-weight:700; color:#1a1a2e;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

NAVY="#0f3460"; NAVY2="#1a1a2e"; RED="#e63946"; GRID="#f0f0f0"
GRAY="#718096"; WHITE="#ffffff"; GREEN="#2d6a4f"; AMBER="#e07b00"

def load_all():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = glob.glob(os.path.join(script_dir, "data", "*.csv"))
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if 'Row' in df.columns and 'POSSESSION THIRDS' in df.columns:
                name = os.path.splitext(f)[0].replace("_", " ")
                df['Match'] = name
                dfs.append(df)
        except:
            pass
    if not dfs:
        return pd.DataFrame()
    combined = pd.concat(dfs, ignore_index=True)
    if 'Date' in combined.columns:
        combined['Date_parsed'] = pd.to_datetime(combined['Date'], dayfirst=True, errors='coerce')
    return combined

def parse_multi(series):
    vals = []
    for v in series.dropna():
        for p in str(v).split(','):
            vals.append(p.strip())
    return Counter(vals)

def shots_from(df):
    v = parse_multi(df['SHOOTING'])
    return v.get('SHOT', 0), v.get('ON TARGET', 0), v.get('GOAL', 0)

def pct(n, d, fmt=True):
    if d == 0: return "0%" if fmt else 0
    val = round(n / d * 100)
    return f"{val}%" if fmt else val

raw = load_all()

if raw.empty:
    st.error("No CSV files found. Add your Sportscode team CSV files to the same folder as this app.")
    st.stop()

if 'Date_parsed' in raw.columns:
    match_dates = raw.dropna(subset=['Date_parsed']).groupby('Match')['Date_parsed'].min().sort_values()
    matches = list(match_dates.index)
else:
    matches = sorted(raw['Match'].dropna().unique())

with st.sidebar:
    st.markdown('<div class="sidebar-header">Football Ferns</div>', unsafe_allow_html=True)
    st.markdown("<small style='color:#718096;'>Tactical Analysis</small>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.rerun()
    st.divider()
    st.markdown('<div class="sidebar-header">Filter</div>', unsafe_allow_html=True)
    sel_matches = st.multiselect("Match", matches, default=[], placeholder="All matches")
    st.divider()
    st.markdown('<div class="sidebar-header">Matches loaded</div>', unsafe_allow_html=True)
    for m in matches:
        opp = raw[raw['Match']==m]['Opposition'].dropna()
        date = raw[raw['Match']==m]['Date'].dropna()
        o = opp.iloc[0] if not opp.empty else ""
        d = date.iloc[0] if not date.empty else ""
        st.markdown(f"<small style='color:#4a5568;'><b>vs {o}</b> · {d}</small>", unsafe_allow_html=True)

df_v = raw.copy()
if sel_matches:
    df_v = df_v[df_v['Match'].isin(sel_matches)]

home    = df_v[df_v['Row'] == 'HOME POSSESSION'].copy()
away    = df_v[df_v['Row'] == 'AWAY POSSESSION'].copy()
home_sp = df_v[df_v['Row'] == 'HOME SET PIECE'].copy()

s2 = home[home['Ungrouped'].str.contains('SEAM 2 ENTRY', na=False)]
s3 = home[home['Ungrouped'].str.contains('SEAM THREE ENTRY', na=False)]

match_label = ', '.join(sel_matches) if sel_matches else f"All {len(matches)} matches"
st.markdown(f"""
<div class="page-header">
  <h1>Football Ferns — Tactical Analysis</h1>
  <p>Sportscode possession data · seam entry & sequence analysis</p>
  <span class="header-badge">{match_label}</span>
</div>
""", unsafe_allow_html=True)

_cc = [0]
def wrap(fig):
    _cc[0] += 1
    st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=f"tc_{_cc[0]}")
    st.markdown('</div>', unsafe_allow_html=True)

def kpi(col, label, value, sub="", color=""):
    col.markdown(f'<div class="metric-card {color}"><div class="metric-label">{label}</div><div class="metric-value {color}">{value}</div><div class="metric-sub">{sub}</div></div>', unsafe_allow_html=True)

def lay(fig, title, h=300, show_legend=True):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color=NAVY2, size=13, family="Nunito Sans, sans-serif"), x=0),
        paper_bgcolor=WHITE, plot_bgcolor=WHITE, font=dict(color=GRAY, family="Nunito Sans, sans-serif"),
        margin=dict(t=50, b=10, l=10, r=10), height=h,
        xaxis=dict(gridcolor=GRID, linecolor="#e8e8e8", tickfont=dict(size=10, color=GRAY)),
        yaxis=dict(gridcolor=GRID, linecolor="#e8e8e8", tickfont=dict(size=10, color=GRAY)),
        legend=dict(font=dict(size=10, color=GRAY), orientation="h", y=1.12, x=1, xanchor="right") if show_legend else dict(visible=False),
        bargap=0.3,
    )
    return fig

def donut(labels, values, title, colors, h=290):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=colors, line=dict(color=WHITE, width=2)),
        textfont=dict(size=11, family="Nunito Sans, sans-serif"),
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>"
    ))
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", font=dict(color=NAVY2, size=13, family="Nunito Sans, sans-serif"), x=0),
        paper_bgcolor=WHITE, font=dict(color=GRAY, family="Nunito Sans, sans-serif"),
        legend=dict(font=dict(size=10, color=GRAY), orientation="h", y=-0.08, x=0.5, xanchor="center"),
        margin=dict(t=50, b=40, l=10, r=10), height=h,
    )
    return fig

def line_chart(x, metrics, title, h=300):
    colors = [NAVY, RED, GREEN, AMBER, "#7c3aed"]
    fig = go.Figure()
    for i, (label, y) in enumerate(metrics):
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines+markers", name=label,
            line=dict(color=colors[i % len(colors)], width=2.5),
            marker=dict(size=7, color=colors[i % len(colors)], line=dict(color=WHITE, width=1.5)),
        ))
    return lay(fig, title, h)

def match_stats_all():
    rows = []
    for m in matches:
        mdf   = raw[raw['Match'] == m]
        mhome = mdf[mdf['Row'] == 'HOME POSSESSION']
        maway = mdf[mdf['Row'] == 'AWAY POSSESSION']
        msp   = mdf[mdf['Row'] == 'HOME SET PIECE']
        ms2   = mhome[mhome['Ungrouped'].str.contains('SEAM 2 ENTRY', na=False)]
        ms3   = mhome[mhome['Ungrouped'].str.contains('SEAM THREE ENTRY', na=False)]
        sh, ot, g   = shots_from(mhome)
        sh3, ot3, g3 = shots_from(ms3)
        cr = parse_multi(mhome['CROSSING'])
        opp  = mdf['Opposition'].dropna().iloc[0] if not mdf['Opposition'].dropna().empty else m
        at   = parse_multi(maway['POSSESSION THIRDS'])
        rows.append({
            'Match': m, 'Label': f"vs {opp}",
            'Poss': len(mhome), 'S2': len(ms2), 'S3': len(ms3),
            'Shots': sh, 'OnTarget': ot, 'Goals': g,
            'S3_Shots': sh3, 'S3_OT': ot3, 'S3_Goals': g3,
            'PenEntry': mhome['PEN AREA ENTRY'].notna().sum(),
            'CrossSucc': cr.get('Cross Successful', 0),
            'CrossFail': cr.get('Cross Unsuccessful', 0),
            'Trans': parse_multi(mhome['TRANSITION']).get('ATTACKING TRANSITION', 0),
            'SP_Shots': shots_from(msp)[0],
            'Away_D3': at.get('P-D3', 0), 'Away_M3': at.get('P-M3', 0), 'Away_F3': at.get('P-F3', 0),
            'Away_Shots': shots_from(maway)[0],
        })
    return pd.DataFrame(rows)

trend_df = match_stats_all()
tlabels  = list(trend_df['Label'])

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Seam 2", "Seam 3", "Possession", "Set Pieces", "Opposition", "Trends"
])

with tab1:
    shots2, ot2, g2 = shots_from(s2)
    pen2 = s2['PEN AREA ENTRY'].notna().sum()
    cr2  = parse_multi(s2['CROSSING'])
    cs2  = cr2.get('Cross Successful', 0)
    ct2  = cs2 + cr2.get('Cross Unsuccessful', 0)
    t2   = parse_multi(s2['POSSESSION THIRDS'])

    st.markdown('<div class="section-title">Seam 2 — key metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, "Seam 2 entries", len(s2), "sequences")
    kpi(c2, "Shots", shots2, f"{pct(shots2,len(s2))} of entries")
    kpi(c3, "On target", ot2, f"{pct(ot2,shots2)} of shots", "green")
    kpi(c4, "Pen area entries", pen2, f"{pct(pen2,len(s2))} of entries", "amber")
    kpi(c5, "Cross success", f"{cs2}/{ct2}", f"{pct(cs2,ct2)}" if ct2 else "n/a")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
            [t2.get('P-D3',0), t2.get('P-M3',0), t2.get('P-F3',0)],
            "Possession thirds in seam 2 sequences", [RED, AMBER, GREEN]))
    with c2:
        hs2 = s2['SHOOTING'].notna().sum()
        hp2 = s2['PEN AREA ENTRY'].notna().sum()
        hc2 = s2['CROSSING'].notna().sum()
        no2 = len(s2) - s2[['SHOOTING','PEN AREA ENTRY','CROSSING']].notna().any(axis=1).sum()
        wrap(donut(["Shot","Pen area entry","Cross","No outcome"],
            [hs2, hp2, hc2, max(0,no2)],
            "What happened after seam 2 entry", [NAVY, GREEN, AMBER, GRAY]))

with tab2:
    shots3, ot3, g3 = shots_from(s3)
    pen3 = s3['PEN AREA ENTRY'].notna().sum()
    t3   = parse_multi(s3['POSSESSION THIRDS'])

    st.markdown('<div class="section-title">Seam 3 — key metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, "Seam 3 entries", len(s3), "sequences")
    kpi(c2, "Shots", shots3, f"{pct(shots3,len(s3))} of entries")
    kpi(c3, "On target", ot3, f"{pct(ot3,shots3)} of shots", "green")
    kpi(c4, "Goals", g3, "from seam 3", "green" if g3>0 else "")
    kpi(c5, "Pen area entries", pen3, f"{pct(pen3,len(s3))} of entries", "amber")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
            [t3.get('P-D3',0), t3.get('P-M3',0), t3.get('P-F3',0)],
            "Possession thirds in seam 3 sequences", [RED, AMBER, GREEN]))
    with c2:
        hs3 = s3['SHOOTING'].notna().sum()
        hp3 = s3['PEN AREA ENTRY'].notna().sum()
        no3 = len(s3) - s3[['SHOOTING','PEN AREA ENTRY','CROSSING']].notna().any(axis=1).sum()
        wrap(donut(["Shot","Pen area entry","No outcome"],
            [hs3, hp3, max(0,no3)],
            "What happened after seam 3 entry", [NAVY, GREEN, GRAY]))

    st.markdown('<div class="section-title">Seam 2 vs Seam 3</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Seam 2", x=["Entries","Shots","On Target","Pen Entry"],
            y=[len(s2),shots2,ot2,pen2], marker_color=NAVY, marker_line_width=0))
        fig.add_trace(go.Bar(name="Seam 3", x=["Entries","Shots","On Target","Pen Entry"],
            y=[len(s3),shots3,ot3,pen3], marker_color=RED, marker_line_width=0))
        fig.update_layout(barmode="group")
        wrap(lay(fig, "Seam 2 vs Seam 3 — counts"))
    with c2:
        wrap(donut(["Shot","No shot"],[shots2,max(0,len(s2)-shots2)],"Seam 2 — shot rate",[NAVY,GRID]))
    with c3:
        wrap(donut(["Shot","No shot"],[shots3,max(0,len(s3)-shots3)],"Seam 3 — shot rate",[RED,GRID]))

with tab3:
    all_sh, all_ot, all_g = shots_from(home)
    all_pen    = home['PEN AREA ENTRY'].notna().sum()
    all_cr     = parse_multi(home['CROSSING'])
    all_cs     = all_cr.get('Cross Successful', 0)
    all_ct     = all_cs + all_cr.get('Cross Unsuccessful', 0)
    all_trans  = parse_multi(home['TRANSITION']).get('ATTACKING TRANSITION', 0)
    all_thirds = parse_multi(home['POSSESSION THIRDS'])
    fp = parse_multi(home['FIRST PHASE'])
    sp = parse_multi(home['SECOND PHASE'])

    st.markdown('<div class="section-title">Overall possession — key metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    kpi(c1, "Possessions", len(home), "sequences")
    kpi(c2, "Shots", all_sh, f"{pct(all_sh,len(home))} of poss")
    kpi(c3, "On target", all_ot, f"{pct(all_ot,all_sh)} of shots", "green")
    kpi(c4, "Goals", all_g, "scored", "green" if all_g>0 else "")
    kpi(c5, "Pen entries", all_pen, f"{pct(all_pen,len(home))} of poss", "amber")
    kpi(c6, "Transitions", all_trans, "attacking")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
            [all_thirds.get('P-D3',0), all_thirds.get('P-M3',0), all_thirds.get('P-F3',0)],
            "Where NZ had possession", [RED, AMBER, GREEN]))
    with c2:
        s2c = home['Ungrouped'].str.contains('SEAM 2 ENTRY', na=False).sum()
        s3c = home['Ungrouped'].str.contains('SEAM THREE ENTRY', na=False).sum()
        wrap(donut(
            ["Seam 2 entry","Seam 3 entry","Cross","Transition","Other"],
            [s2c, s3c, all_ct, all_trans, max(0, len(home)-s2c-s3c-all_ct-all_trans)],
            "Possession sequence types", [NAVY, RED, AMBER, GREEN, GRAY]))

    if fp or sp:
        st.markdown('<div class="section-title">Phase data</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if fp:
                fig = go.Figure(go.Bar(x=list(fp.keys()), y=list(fp.values()),
                    marker_color=NAVY, marker_line_width=0,
                    text=list(fp.values()), textposition="outside",
                    textfont=dict(color=NAVY2, size=11)))
                wrap(lay(fig, "First phase outcomes", show_legend=False))
        with c2:
            if sp:
                fig = go.Figure(go.Bar(x=list(sp.keys()), y=list(sp.values()),
                    marker_color=GREEN, marker_line_width=0,
                    text=list(sp.values()), textposition="outside",
                    textfont=dict(color=NAVY2, size=11)))
                wrap(lay(fig, "Second phase outcomes", show_legend=False))

with tab4:
    sp_sh, sp_ot, sp_g = shots_from(home_sp)
    sp_pen = home_sp['PEN AREA ENTRY'].notna().sum()

    st.markdown('<div class="section-title">Set pieces — key metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    kpi(c1, "Set piece sequences", len(home_sp), "total")
    kpi(c2, "Shots", sp_sh, f"{pct(sp_sh,len(home_sp))} of SP" if len(home_sp) else "")
    kpi(c3, "On target", sp_ot, f"{pct(sp_ot,sp_sh)} of shots", "green")
    kpi(c4, "Goals", sp_g, "from set pieces", "green" if sp_g>0 else "")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        sp_t = parse_multi(home_sp['POSSESSION THIRDS'])
        wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
            [sp_t.get('P-D3',0), sp_t.get('P-M3',0), sp_t.get('P-F3',0)],
            "Set piece possession zones", [RED, AMBER, GREEN]))
    with c2:
        sp_trans = parse_multi(home_sp['TRANSITION']).get('ATTACKING TRANSITION', 0)
        sp_cr = parse_multi(home_sp['CROSSING'])
        sp_ct = sp_cr.get('Cross Successful',0) + sp_cr.get('Cross Unsuccessful',0)
        fig = go.Figure(go.Bar(
            x=["Shots","On Target","Goals","Pen Entries","Crosses","Transitions"],
            y=[sp_sh, sp_ot, sp_g, sp_pen, sp_ct, sp_trans],
            marker_color=[NAVY, GREEN, GREEN, AMBER, NAVY, RED],
            marker_line_width=0,
            text=[sp_sh, sp_ot, sp_g, sp_pen, sp_ct, sp_trans],
            textposition="outside", textfont=dict(color=NAVY2, size=11)
        ))
        wrap(lay(fig, "Set piece outcomes", show_legend=False))

with tab5:
    away_sh, away_ot, away_g = shots_from(away)
    away_thirds = parse_multi(away['POSSESSION THIRDS'])
    away_trans  = parse_multi(away['TRANSITION']).get('ATTACKING TRANSITION', 0)
    away_fp     = parse_multi(away['FIRST PHASE'])
    away_pen    = away['PEN AREA ENTRY'].notna().sum()

    st.markdown('<div class="section-title">Opposition possession — key metrics</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, "Opp possessions", len(away), "sequences")
    kpi(c2, "Opp shots", away_sh, f"{pct(away_sh,len(away))} of poss")
    kpi(c3, "Opp on target", away_ot, f"{pct(away_ot,away_sh)} of shots", "red")
    kpi(c4, "Goals conceded", away_g, "conceded", "red" if away_g>0 else "green")
    kpi(c5, "Opp transitions", away_trans, "attacking")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
            [away_thirds.get('P-D3',0), away_thirds.get('P-M3',0), away_thirds.get('P-F3',0)],
            "Where opposition had possession", [GREEN, AMBER, RED]))
    with c2:
        if away_fp:
            fig = go.Figure(go.Bar(x=list(away_fp.keys()), y=list(away_fp.values()),
                marker_color=RED, marker_line_width=0,
                text=list(away_fp.values()), textposition="outside",
                textfont=dict(color=NAVY2, size=11)))
            wrap(lay(fig, "Opposition first phase outcomes", show_legend=False))
        else:
            wrap(donut(["NZ possession","Opp possession"],
                [len(home), len(away)], "Possession share", [NAVY, RED]))

    st.markdown('<div class="section-title">NZ vs Opposition</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(name="NZ", x=["Possessions","Shots","On Target","Pen Entries"],
            y=[len(home),all_sh,all_ot,all_pen], marker_color=NAVY, marker_line_width=0))
        fig.add_trace(go.Bar(name="Opposition", x=["Possessions","Shots","On Target","Pen Entries"],
            y=[len(away),away_sh,away_ot,away_pen], marker_color=RED, marker_line_width=0))
        fig.update_layout(barmode="group")
        wrap(lay(fig, "NZ vs Opposition — head to head"))
    with c2:
        wrap(donut(["NZ possession","Opp possession"],
            [len(home), len(away)], "Possession share", [NAVY, RED]))

with tab6:
    if len(matches) < 2:
        st.info("Add more match CSVs to the same folder and click Refresh Data to view trends across games.")
    else:
        st.markdown('<div class="section-title">Seam entry trends</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            wrap(line_chart(tlabels,
                [("Seam 2 entries", trend_df['S2'].tolist()),
                 ("Seam 3 entries", trend_df['S3'].tolist())],
                "Seam entries per match"))
        with c2:
            s2p = [pct(r.S2, r.Poss, fmt=False) for r in trend_df.itertuples()]
            s3p = [pct(r.S3, r.Poss, fmt=False) for r in trend_df.itertuples()]
            wrap(line_chart(tlabels,
                [("Seam 2 % of poss", s2p), ("Seam 3 % of poss", s3p)],
                "Seam entries as % of possession"))

        st.markdown('<div class="section-title">Attacking trends</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            wrap(line_chart(tlabels,
                [("Shots", trend_df['Shots'].tolist()),
                 ("On Target", trend_df['OnTarget'].tolist()),
                 ("Goals", trend_df['Goals'].tolist())],
                "Shots, on target & goals per match"))
        with c2:
            wrap(line_chart(tlabels,
                [("Pen area entries", trend_df['PenEntry'].tolist()),
                 ("Transitions", trend_df['Trans'].tolist())],
                "Pen area entries & transitions"))

        st.markdown('<div class="section-title">Crossing trends</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            wrap(line_chart(tlabels,
                [("Successful", trend_df['CrossSucc'].tolist()),
                 ("Unsuccessful", trend_df['CrossFail'].tolist())],
                "Crossing per match"))
        with c2:
            cxp = [pct(r.CrossSucc, r.CrossSucc+r.CrossFail, fmt=False) for r in trend_df.itertuples()]
            wrap(line_chart(tlabels, [("Cross accuracy %", cxp)], "Cross accuracy % per match"))

        st.markdown('<div class="section-title">Opposition trends</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            wrap(line_chart(tlabels,
                [("Opp final 3rd", trend_df['Away_F3'].tolist()),
                 ("Opp shots", trend_df['Away_Shots'].tolist())],
                "Opposition threat per match"))
        with c2:
            af3p = [pct(r.Away_F3, r.Away_D3+r.Away_M3+r.Away_F3, fmt=False) for r in trend_df.itertuples()]
            wrap(line_chart(tlabels, [("Opp final 3rd %", af3p)], "Opposition final 3rd possession %"))

st.markdown("<br><small style='color:#cbd5e0;'>Data: Sportscode · NZ Football Ferns</small>", unsafe_allow_html=True)
