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
    margin:28px 0 14px;
  }
  .chart-wrap {
    background:#ffffff; border:1px solid #e8e8e8; border-radius:10px;
    padding:4px; box-shadow:0 1px 4px rgba(0,0,0,0.05); margin-bottom:8px;
  }
  .sidebar-header { font-size:13px; font-weight:700; color:#1a1a2e;
    text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }
  .game-card {
    background:#ffffff; border:1px solid #e8e8e8; border-radius:12px;
    padding:20px; margin-bottom:12px;
  }
  .game-card-header {
    display:flex; justify-content:space-between; align-items:center;
    margin-bottom:14px;
  }
  .game-card-title { font-size:16px; font-weight:700; color:#1a1a2e; margin:0; }
  .game-card-count { font-size:28px; font-weight:800; color:#1a1a2e; }
  .bar-track {
    height:8px; background:#f0f0f0; border-radius:4px;
    margin:8px 0 6px; overflow:hidden;
  }
  .bar-fill { height:100%; border-radius:4px; }
  .success-line { font-size:13px; color:#718096; margin-bottom:14px; }
  .success-line strong { color:#1a1a2e; }
  .outcome-grid {
    display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:10px;
  }
  .outcome-box { background:#f7f7f7; border-radius:8px; padding:10px 12px; }
  .outcome-val { font-size:20px; font-weight:800; color:#1a1a2e; line-height:1; }
  .outcome-lbl { font-size:11px; color:#718096; margin-top:3px; }
  .no-success-note { font-size:12px; color:#a0aec0; margin-top:6px; }
  .seam2-bar { background:#378ADD; }
  .seam3-bar { background:#1D9E75; }
  .match-label { font-size:14px; font-weight:700; color:#1a1a2e;
    margin:24px 0 8px; padding-bottom:6px; border-bottom:1px solid #e8e8e8; }
  .match-label span { font-weight:400; color:#718096; }
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
                name = os.path.splitext(os.path.basename(f))[0].replace("_", " ")
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
    v = parse_multi(df['SHOOTING']) if 'SHOOTING' in df.columns else Counter()
    return v.get('SHOT', 0), v.get('ON TARGET', 0), v.get('GOAL', 0)

def pct(n, d, fmt=True):
    if d == 0: return "0%" if fmt else 0
    val = round(n / d * 100)
    return f"{val}%" if fmt else val

def success_count(df):
    pen   = df['PEN AREA ENTRY'].notna() if 'PEN AREA ENTRY' in df.columns else pd.Series(False, index=df.index)
    cross = df['CROSSING'].notna()       if 'CROSSING'       in df.columns else pd.Series(False, index=df.index)
    shot  = df['SHOOTING'].notna()       if 'SHOOTING'       in df.columns else pd.Series(False, index=df.index)
    return (pen | cross | shot).sum()

def detailed_success(df):
    pen   = df['PEN AREA ENTRY'].notna() if 'PEN AREA ENTRY' in df.columns else pd.Series(False, index=df.index)
    cross = df['CROSSING'].notna()       if 'CROSSING'       in df.columns else pd.Series(False, index=df.index)
    shot  = df['SHOOTING'].notna()       if 'SHOOTING'       in df.columns else pd.Series(False, index=df.index)
    return (
        ( pen & ~cross & ~shot).sum(),
        (~pen &  cross & ~shot).sum(),
        (~pen & ~cross &  shot).sum(),
        ( pen & ~cross &  shot).sum(),
        ( pen &  cross & ~shot).sum(),
        (~pen &  cross &  shot).sum(),
        ( pen &  cross &  shot).sum(),
        (~pen & ~cross & ~shot).sum(),
    )

raw = load_all()

if raw.empty:
    st.error("No CSV files found. Add your Sportscode CSV files to the data/ folder.")
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
        opp  = raw[raw['Match']==m]['Opposition'].dropna()
        date = raw[raw['Match']==m]['Date'].dropna()
        o = opp.iloc[0]  if not opp.empty  else ""
        d = date.iloc[0] if not date.empty else ""
        st.markdown(f"<small style='color:#4a5568;'><b>vs {o}</b> · {d}</small>", unsafe_allow_html=True)

df_v = raw.copy()
if sel_matches:
    df_v = df_v[df_v['Match'].isin(sel_matches)]

home = df_v[df_v['Row'] == 'HOME POSSESSION'].copy()
s2   = home[home['Ungrouped'].str.contains('SEAM 2 ENTRY',     na=False)]
s3   = home[home['Ungrouped'].str.contains('SEAM THREE ENTRY',  na=False)]

match_label = ', '.join(sel_matches) if sel_matches else f"All {len(matches)} matches"
st.markdown(f"""
<div class="page-header">
  <h1>Football Ferns — Seam Entry Analysis</h1>
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

def seam_game_card(df_home, seam_label, seam_str, bar_class):
    s = df_home[df_home['Ungrouped'].str.contains(seam_str, na=False)]
    total = len(s)
    if total == 0:
        st.markdown(f"""
        <div class="game-card">
          <div class="game-card-header">
            <span class="game-card-title">{seam_label} entries</span>
            <span class="game-card-count">0</span>
          </div>
          <p class="no-success-note">No {seam_label} entries recorded.</p>
        </div>""", unsafe_allow_html=True)
        return
    succ     = success_count(s)
    succ_pct = round(succ / total * 100)
    pen_only, cross_only, shot_only, pen_shot, pen_cross, cross_shot, all_three, none = detailed_success(s)
    _, _, goals = shots_from(s)
    notes = []
    if goals > 0:
        notes.append(f"<strong style='color:#2d6a4f;'>{goals} goal{'s' if goals != 1 else ''}</strong>")
    if none > 0:
        notes.append(f"{none} possession{'s' if none != 1 else ''} with no follow-up action")
    if all_three > 0:
        notes.append(f"{all_three} with all three")
    note_html = " &nbsp;·&nbsp; ".join(notes)
    st.markdown(f"""
    <div class="game-card">
      <div class="game-card-header">
        <span class="game-card-title">{seam_label} entries</span>
        <span class="game-card-count">{total}</span>
      </div>
      <div class="bar-track"><div class="bar-fill {bar_class}" style="width:{succ_pct}%;"></div></div>
      <div class="success-line">{succ} successful &nbsp;·&nbsp; <strong>{succ_pct}%</strong></div>
      <div class="outcome-grid">
        <div class="outcome-box"><div class="outcome-val">{pen_only}</div><div class="outcome-lbl">Pen area only</div></div>
        <div class="outcome-box"><div class="outcome-val">{cross_only}</div><div class="outcome-lbl">Cross only</div></div>
        <div class="outcome-box"><div class="outcome-val">{shot_only}</div><div class="outcome-lbl">Shot only</div></div>
        <div class="outcome-box"><div class="outcome-val">{pen_shot}</div><div class="outcome-lbl">Pen + shot</div></div>
        <div class="outcome-box"><div class="outcome-val">{pen_cross}</div><div class="outcome-lbl">Pen + cross</div></div>
        <div class="outcome-box"><div class="outcome-val">{cross_shot}</div><div class="outcome-lbl">Cross + shot</div></div>
      </div>
      <p class="no-success-note">{note_html}</p>
    </div>""", unsafe_allow_html=True)

# ── COMBINED SUMMARY ───────────────────────────────────────────────────────────
shots2, ot2, g2 = shots_from(s2)
shots3, ot3, g3 = shots_from(s3)
pen2 = s2['PEN AREA ENTRY'].notna().sum() if 'PEN AREA ENTRY' in s2.columns else 0
pen3 = s3['PEN AREA ENTRY'].notna().sum() if 'PEN AREA ENTRY' in s3.columns else 0
cr2  = parse_multi(s2['CROSSING']) if 'CROSSING' in s2.columns else Counter()
cr3  = parse_multi(s3['CROSSING']) if 'CROSSING' in s3.columns else Counter()
cs2  = cr2.get('Cross Successful', 0); ct2 = cs2 + cr2.get('Cross Unsuccessful', 0)
cs3  = cr3.get('Cross Successful', 0); ct3 = cs3 + cr3.get('Cross Unsuccessful', 0)
t2   = parse_multi(s2['POSSESSION THIRDS']) if 'POSSESSION THIRDS' in s2.columns else Counter()
t3   = parse_multi(s3['POSSESSION THIRDS']) if 'POSSESSION THIRDS' in s3.columns else Counter()
total_seam  = len(s2) + len(s3)
total_shots = shots2 + shots3
total_ot    = ot2 + ot3
total_g     = g2 + g3
total_pen   = pen2 + pen3
total_cs    = cs2 + cs3
total_ct    = ct2 + ct3

st.markdown('<div class="section-title">Combined summary — Seam 2 + 3</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
kpi(c1, "Total seam entries", total_seam, f"S2: {len(s2)}  ·  S3: {len(s3)}")
kpi(c2, "Shots", total_shots, f"{pct(total_shots, total_seam)} of entries")
kpi(c3, "On target", total_ot, f"{pct(total_ot, total_shots)} of shots", "green")
kpi(c4, "Goals", total_g, "from seam entries", "green" if total_g > 0 else "")
kpi(c5, "Pen area entries", total_pen, f"{pct(total_pen, total_seam)} of entries", "amber")
kpi(c6, "Cross success", f"{total_cs}/{total_ct}", f"{pct(total_cs, total_ct)}" if total_ct else "n/a")

# ── SEAM 2 OVERALL ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Seam 2 — overall</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
kpi(c1, "Seam 2 entries", len(s2), "sequences")
kpi(c2, "Shots", shots2, f"{pct(shots2, len(s2))} of entries")
kpi(c3, "On target", ot2, f"{pct(ot2, shots2)} of shots", "green")
kpi(c4, "Goals", g2, f"{pct(g2, shots2)} of shots", "green" if g2 > 0 else "")
kpi(c5, "Pen area entries", pen2, f"{pct(pen2, len(s2))} of entries", "amber")
kpi(c6, "Cross success", f"{cs2}/{ct2}", f"{pct(cs2,ct2)}" if ct2 else "n/a")

st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
        [t2.get('P-D3',0), t2.get('P-M3',0), t2.get('P-F3',0)],
        "Possession thirds in seam 2 sequences", [RED, AMBER, GREEN]))
with c2:
    hs2 = s2['SHOOTING'].notna().sum()       if 'SHOOTING'       in s2.columns else 0
    hp2 = s2['PEN AREA ENTRY'].notna().sum() if 'PEN AREA ENTRY' in s2.columns else 0
    hc2 = s2['CROSSING'].notna().sum()       if 'CROSSING'       in s2.columns else 0
    cols_check = [c for c in ['SHOOTING','PEN AREA ENTRY','CROSSING'] if c in s2.columns]
    no2 = len(s2) - s2[cols_check].notna().any(axis=1).sum() if cols_check else len(s2)
    gs2 = parse_multi(s2['SHOOTING']).get('GOAL', 0) if 'SHOOTING' in s2.columns else 0
    wrap(donut(["Goal","Shot","Pen area entry","Cross","No outcome"],
        [gs2, max(0,hs2-gs2), hp2, hc2, max(0,no2)],
        "What happened after seam 2 entry", [GREEN, NAVY, AMBER, "#378ADD", GRAY]))

# ── SEAM 3 OVERALL ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Seam 3 — overall</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5 = st.columns(5)
kpi(c1, "Seam 3 entries", len(s3), "sequences")
kpi(c2, "Shots", shots3, f"{pct(shots3, len(s3))} of entries")
kpi(c3, "On target", ot3, f"{pct(ot3, shots3)} of shots", "green")
kpi(c4, "Goals", g3, "from seam 3", "green" if g3 > 0 else "")
kpi(c5, "Pen area entries", pen3, f"{pct(pen3, len(s3))} of entries", "amber")

st.markdown("<br>", unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    wrap(donut(["Defensive 3rd","Middle 3rd","Final 3rd"],
        [t3.get('P-D3',0), t3.get('P-M3',0), t3.get('P-F3',0)],
        "Possession thirds in seam 3 sequences", [RED, AMBER, GREEN]))
with c2:
    hs3 = s3['SHOOTING'].notna().sum()       if 'SHOOTING'       in s3.columns else 0
    hp3 = s3['PEN AREA ENTRY'].notna().sum() if 'PEN AREA ENTRY' in s3.columns else 0
    cols_check3 = [c for c in ['SHOOTING','PEN AREA ENTRY','CROSSING'] if c in s3.columns]
    no3 = len(s3) - s3[cols_check3].notna().any(axis=1).sum() if cols_check3 else len(s3)
    wrap(donut(["Shot","Pen area entry","No outcome"],
        [hs3, hp3, max(0,no3)],
        "What happened after seam 3 entry", [NAVY, GREEN, GRAY]))

# ── COMPARISON ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Seam 2 vs Seam 3 — comparison</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    s2_succ = success_count(s2)
    s3_succ = success_count(s3)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Successful", x=["Seam 2", "Seam 3"], y=[s2_succ, s3_succ],
        marker_color=GREEN, marker_line_width=0,
        text=[f"{s2_succ} ({pct(s2_succ,len(s2))})", f"{s3_succ} ({pct(s3_succ,len(s3))})"],
        textposition="inside", textfont=dict(color="white", size=11)
    ))
    fig.add_trace(go.Bar(
        name="No outcome", x=["Seam 2", "Seam 3"], y=[len(s2)-s2_succ, len(s3)-s3_succ],
        marker_color=GRAY, marker_line_width=0,
        text=[len(s2)-s2_succ, len(s3)-s3_succ],
        textposition="inside", textfont=dict(color="white", size=11)
    ))
    fig.update_layout(barmode="stack")
    wrap(lay(fig, "Success rate — Seam 2 vs Seam 3"))
with c2:
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Seam 2", x=["Entries","Shots","On Target","Goals","Pen Entry"],
        y=[len(s2),shots2,ot2,g2,pen2], marker_color=NAVY, marker_line_width=0))
    fig.add_trace(go.Bar(name="Seam 3", x=["Entries","Shots","On Target","Goals","Pen Entry"],
        y=[len(s3),shots3,ot3,g3,pen3], marker_color=RED, marker_line_width=0))
    fig.update_layout(barmode="group")
    wrap(lay(fig, "Seam 2 vs Seam 3 — counts"))
with c3:
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Seam 2", x=["Pen area","Cross","Shot"],
        y=[pen2, ct2, shots2], marker_color=NAVY, marker_line_width=0,
        text=[pen2, ct2, shots2], textposition="outside", textfont=dict(color=NAVY2, size=11)))
    fig.add_trace(go.Bar(name="Seam 3", x=["Pen area","Cross","Shot"],
        y=[pen3, ct3, shots3], marker_color=RED, marker_line_width=0,
        text=[pen3, ct3, shots3], textposition="outside", textfont=dict(color=NAVY2, size=11)))
    fig.update_layout(barmode="group")
    wrap(lay(fig, "Outcome breakdown — Seam 2 vs Seam 3"))

# ── PER-GAME CARDS ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Per-game breakdown</div>', unsafe_allow_html=True)

active_matches = sel_matches if sel_matches else matches
for m in active_matches:
    mdf   = raw[raw['Match'] == m]
    mhome = mdf[mdf['Row'] == 'HOME POSSESSION']
    opp   = mdf['Opposition'].dropna().iloc[0] if not mdf['Opposition'].dropna().empty else m
    date  = mdf['Date'].dropna().iloc[0]       if not mdf['Date'].dropna().empty       else ""
    st.markdown(f"<p class='match-label'>vs {opp} &nbsp;·&nbsp; <span>{date}</span></p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        seam_game_card(mhome, "Seam 2", "SEAM 2 ENTRY",     "seam2-bar")
    with c2:
        seam_game_card(mhome, "Seam 3", "SEAM THREE ENTRY",  "seam3-bar")

st.markdown("<br><small style='color:#cbd5e0;'>Data: Sportscode · NZ Football Ferns</small>", unsafe_allow_html=True)
