"""
MarketPulse AI v2.1 — Enterprise Web Scraping, SQL & Repricing Intelligence SaaS
================================================================================
Full-theme override (including stHeader, sidebar labels, inputs, and buttons)
so Dark Mode and Light Mode render with 100% contrast on any browser configuration.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import scraper_pipeline

DB_NAME = "market_intelligence.db"

st.set_page_config(
    page_title="MarketPulse AI | Web Scraping & SQL Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Compatibility Helpers (Zero Deprecation Warnings)
# ---------------------------------------------------------------------------
def render_plotly(fig: go.Figure) -> None:
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


def render_table(df_or_styler, height: int = 400) -> None:
    try:
        st.dataframe(df_or_styler, width="stretch", height=height)
    except TypeError:
        st.dataframe(df_or_styler, use_container_width=True, height=height)


# ---------------------------------------------------------------------------
# Database Connection & Data Loading
# ---------------------------------------------------------------------------
def ensure_database_exists() -> None:
    if not os.path.exists(DB_NAME):
        scraper_pipeline.main()


@st.cache_data(ttl=300)
def load_joined_catalog() -> pd.DataFrame:
    ensure_database_exists()
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT 
        p.product_id,
        p.sku,
        p.title,
        c.category_name,
        c.target_margin_pct,
        p.our_price,
        p.competitor_price,
        p.price_diff_pct,
        p.price_status,
        p.rating,
        p.stock_quantity,
        p.est_monthly_sales,
        p.est_monthly_revenue,
        p.scraped_at
    FROM products p
    INNER JOIN categories c ON p.category_id = c.category_id
    ORDER BY p.est_monthly_revenue DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def run_safe_sql_query(sql_text: str) -> pd.DataFrame:
    cleaned = sql_text.strip()
    if not cleaned.upper().startswith("SELECT"):
        raise ValueError("Only read-only SELECT queries are permitted in the SQL studio.")
    conn = sqlite3.connect(DB_NAME)
    try:
        result_df = pd.read_sql_query(cleaned, conn)
    finally:
        conn.close()
    return result_df


raw_df = load_joined_catalog()


# ---------------------------------------------------------------------------
# Sidebar Controls & Sleek Filter Architecture
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-box">
            <div class="brand-icon">⚡</div>
            <div class="brand-title">MarketPulse AI</div>
            <div class="brand-sub">WEB SCRAPING & SQL ENGINE</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section-title">APPEARANCE & THEME</div>', unsafe_allow_html=True)
    dark_mode = st.toggle("Cyberpunk Dark Mode", value=True)

    st.divider()
    st.markdown('<div class="sidebar-section-title">ETL PIPELINE ACTION</div>', unsafe_allow_html=True)
    if st.button("🔄 Trigger Live Scrape & SQL Sync"):
        with st.spinner("Running BeautifulSoup4 Scraper & Rebuilding SQLite DB..."):
            scraper_pipeline.main()
            st.cache_data.clear()
        st.success("239 SKUs synced to SQLite!")

    st.divider()
    st.markdown('<div class="sidebar-section-title">GLOBAL SQL FILTERS</div>', unsafe_allow_html=True)

    all_categories = sorted(raw_df["category_name"].unique().tolist())
    filter_all_cats = st.checkbox("Include All 15 Categories", value=True)
    if filter_all_cats:
        selected_categories = all_categories
    else:
        selected_categories = st.multiselect(
            "Select Specific Categories:",
            options=all_categories,
            default=all_categories[:5],
        )

    all_statuses = [
        "Undercutting (Cheaper)",
        "Price Match (Competitive)",
        "Overpriced (At Risk)",
    ]
    selected_statuses = st.multiselect(
        "Price Positioning:",
        options=all_statuses,
        default=all_statuses,
    )

    min_rating = st.slider("Minimum Star Rating (★)", 1, 5, 1, 1)
    max_price_val = float(max(65.0, raw_df["our_price"].max()))
    max_price_filter = st.slider("Max Product Price ($)", 15.0, max_price_val, max_price_val, 5.0)

    st.divider()
    st.markdown('<div class="sidebar-section-title">🧠 AI PRICING STRATEGIST</div>', unsafe_allow_html=True)
    user_question = st.text_area(
        "Ask AI Strategist:",
        placeholder="e.g. Which overpriced products hurt revenue the most?",
        height=80,
        label_visibility="collapsed",
    )
    if st.button("⚡ Generate AI Strategy", type="primary"):
        q_lower = user_question.lower().strip()
        over_df = raw_df[raw_df["price_status"] == "Overpriced (At Risk)"]
        top_cat = raw_df.groupby("category_name")["est_monthly_revenue"].sum().idxmax()
        if any(w in q_lower for w in ["overprice", "risk", "competitor", "price", "expensive"]):
            st.info(
                f"🎯 **Retention & Repricing Alert:** **{len(over_df)} SKUs** are priced >3% above market, "
                f"putting **${over_df['est_monthly_revenue'].sum():,.0f}/mo** at risk. "
                f"Applying a **6% automated markdown** recovers competitiveness immediately."
            )
        elif any(w in q_lower for w in ["category", "top", "best", "revenue", "margin"]):
            st.success(
                f"📈 **Category Winner:** **{top_cat}** generates the highest monthly volume. "
                f"Catalog average price is **${raw_df['our_price'].mean():.2f}** vs. market **${raw_df['competitor_price'].mean():.2f}**."
            )
        else:
            st.info(
                f"🤖 **Executive Brief:** Auditing **{len(raw_df)} SKUs** across **15 SQL categories**. "
                f"**{len(raw_df[raw_df['price_status']=='Undercutting (Cheaper)'])} SKUs** beat competitor pricing, while **{len(over_df)} SKUs** need repricing."
            )


# ---------------------------------------------------------------------------
# Dynamic Theme Palette & Complete High-Contrast CSS Override
# ---------------------------------------------------------------------------
if dark_mode:
    BG_MAIN = "#070B14"
    BG_CARD = "linear-gradient(145deg, #111827 0%, #0D1322 100%)"
    BG_CARD_SOLID = "#111827"
    BG_INPUT = "#161F33"
    BG_SIDEBAR = "#0A0F1D"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_MUTED = "#CBD5E1"
    BORDER_COLOR = "rgba(56, 189, 248, 0.28)"
    GLOW_SHADOW = "0 8px 30px rgba(6, 182, 212, 0.08)"
    ACCENT_CYAN = "#06B6D4"
    ACCENT_PURPLE = "#8B5CF6"
    ACCENT_PINK = "#F43F5E"
    ACCENT_GREEN = "#10B981"
    ACCENT_AMBER = "#F59E0B"
    CHART_TEMPLATE = "plotly_dark"
    GRID_COLOR = "rgba(148, 163, 184, 0.12)"
else:
    BG_MAIN = "#F1F5F9"
    BG_CARD = "linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)"
    BG_CARD_SOLID = "#FFFFFF"
    BG_INPUT = "#FFFFFF"
    BG_SIDEBAR = "#FFFFFF"
    TEXT_PRIMARY = "#0F172A"
    TEXT_MUTED = "#475569"
    BORDER_COLOR = "rgba(15, 23, 42, 0.14)"
    GLOW_SHADOW = "0 6px 24px rgba(15, 23, 42, 0.05)"
    ACCENT_CYAN = "#0284C7"
    ACCENT_PURPLE = "#6D28D9"
    ACCENT_PINK = "#E11D48"
    ACCENT_GREEN = "#059669"
    ACCENT_AMBER = "#D97706"
    CHART_TEMPLATE = "plotly_white"
    GRID_COLOR = "rgba(15, 23, 42, 0.08)"

st.markdown(
    f"""
    <style>
        /* 1. Main App & Top Header Bar (Fixes white top bar in Dark Mode!) */
        .stApp {{
            background-color: {BG_MAIN} !important;
            color: {TEXT_PRIMARY} !important;
        }}
        header[data-testid="stHeader"] {{
            background-color: {BG_MAIN} !important;
            color: {TEXT_PRIMARY} !important;
            border-bottom: 1px solid {BORDER_COLOR};
        }}
        header[data-testid="stHeader"] * {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* 2. Sidebar Background & Full Text Visibility Override */
        section[data-testid="stSidebar"] {{
            background-color: {BG_SIDEBAR} !important;
            border-right: 1px solid {BORDER_COLOR} !important;
        }}
        .sidebar-section-title {{
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1.3px;
            text-transform: uppercase;
            color: {ACCENT_CYAN} !important;
            margin: 6px 0 8px 0;
        }}
        /* Force all widget labels, checkboxes, toggles, and sliders to be bright & readable */
        [data-testid="stWidgetLabel"],
        [data-testid="stWidgetLabel"] p,
        [data-testid="stWidgetLabel"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] label p,
        section[data-testid="stSidebar"] label span,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stTickBarMin"],
        [data-testid="stTickBarMax"] {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600 !important;
        }}

        /* 3. Buttons (Fixes white button with invisible text in sidebar!) */
        div.stButton > button {{
            width: 100%;
            background-color: {BG_INPUT} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {ACCENT_CYAN} !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            padding: 8px 14px !important;
            transition: all 0.2s ease;
        }}
        div.stButton > button:hover {{
            border-color: {ACCENT_PURPLE} !important;
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.35) !important;
        }}
        div.stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, {ACCENT_PURPLE}, {ACCENT_CYAN}) !important;
            color: #FFFFFF !important;
            border: none !important;
        }}
        div.stButton > button * {{
            color: inherit !important;
        }}

        /* 4. Inputs, Selectboxes, Multiselects & SQL Textarea */
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        textarea {{
            background-color: {BG_INPUT} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {BORDER_COLOR} !important;
            border-radius: 10px !important;
        }}
        textarea::placeholder {{
            color: {TEXT_MUTED} !important;
            opacity: 0.75 !important;
        }}
        div[data-baseweb="select"] span {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* Sleek Cyan/Purple Multiselect Pills */
        span[data-baseweb="tag"] {{
            background: linear-gradient(135deg, {ACCENT_PURPLE}, {ACCENT_CYAN}) !important;
            color: #FFFFFF !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }}
        span[data-baseweb="tag"] span {{
            color: #FFFFFF !important;
        }}

        /* 5. Brand Box & Hero Banner */
        .brand-box {{
            text-align: center;
            padding: 12px 10px 16px 10px;
            border-radius: 14px;
            background: {BG_CARD};
            border: 1px solid {BORDER_COLOR};
            margin-bottom: 14px;
        }}
        .brand-icon {{
            font-size: 30px;
            margin-bottom: 4px;
        }}
        .brand-title {{
            font-size: 20px;
            font-weight: 800;
            color: {ACCENT_CYAN} !important;
            letter-spacing: 0.4px;
        }}
        .brand-sub {{
            font-size: 10px;
            font-weight: 700;
            color: {TEXT_MUTED} !important;
            letter-spacing: 1.5px;
            margin-top: 3px;
        }}
        .hero-banner {{
            background: {BG_CARD};
            border: 1px solid {BORDER_COLOR};
            border-left: 5px solid {ACCENT_CYAN};
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: {GLOW_SHADOW};
            margin-bottom: 16px;
        }}
        .hero-title {{
            font-size: 27px;
            font-weight: 800;
            color: {TEXT_PRIMARY} !important;
            margin: 0;
            letter-spacing: -0.3px;
        }}
        .hero-accent {{
            color: {ACCENT_CYAN} !important;
        }}
        .hero-sub {{
            font-size: 14px;
            color: {TEXT_MUTED} !important;
            margin: 6px 0 14px 0;
        }}
        .pipeline-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 10px;
        }}
        .pipe-step {{
            background: rgba(6, 182, 212, 0.08);
            border: 1px solid {BORDER_COLOR};
            border-radius: 10px;
            padding: 8px 12px;
            font-size: 12px;
            color: {TEXT_PRIMARY} !important;
            font-weight: 700;
        }}
        .pipe-step span {{
            display: block;
            font-size: 11px;
            color: {TEXT_MUTED} !important;
            font-weight: 500;
            margin-top: 2px;
        }}

        /* 6. KPI Cards & Progress Bars */
        .kpi-card {{
            background: {BG_CARD};
            border: 1px solid {BORDER_COLOR};
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow: {GLOW_SHADOW};
            position: relative;
            overflow: hidden;
            margin-bottom: 12px;
        }}
        .kpi-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .kpi-label {{
            font-size: 11.5px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.1px;
            color: {TEXT_MUTED} !important;
        }}
        .kpi-icon {{
            font-size: 18px;
            padding: 6px 9px;
            border-radius: 10px;
            background: rgba(139, 92, 246, 0.16);
        }}
        .kpi-value {{
            font-size: 29px;
            font-weight: 800;
            color: {TEXT_PRIMARY} !important;
            line-height: 1.15;
        }}
        .kpi-sub {{
            font-size: 12px;
            font-weight: 600;
            margin-top: 6px;
        }}
        .progress-track {{
            width: 100%;
            height: 6px;
            background: rgba(148, 163, 184, 0.22);
            border-radius: 999px;
            margin-top: 10px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 999px;
        }}

        /* 7. Section & Chart Card Headers */
        .section-header {{
            font-size: 12.5px;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: {ACCENT_CYAN} !important;
            margin: 24px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 1px solid {BORDER_COLOR};
        }}
        .chart-header-box {{
            background: {BG_CARD};
            border: 1px solid {BORDER_COLOR};
            border-radius: 14px;
            padding: 14px 18px 6px 18px;
            margin-bottom: 4px;
        }}
        .chart-title {{
            font-size: 15.5px;
            font-weight: 800;
            color: {TEXT_PRIMARY} !important;
            margin: 0;
        }}
        .chart-subtitle {{
            font-size: 12px;
            color: {TEXT_MUTED} !important;
            margin: 2px 0 6px 0;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Filter Synchronization
# ---------------------------------------------------------------------------
filtered_df = raw_df[
    (raw_df["category_name"].isin(selected_categories))
    & (raw_df["price_status"].isin(selected_statuses))
    & (raw_df["rating"] >= min_rating)
    & (raw_df["our_price"] <= max_price_filter)
].copy()

last_scraped = raw_df["scraped_at"].iloc[0] if not raw_df.empty else "Live"


# ---------------------------------------------------------------------------
# Hero Architecture Banner
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-banner">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap;">
            <div>
                <h1 class="hero-title">
                    ⚡ MarketPulse AI — <span class="hero-accent">Automated Web Scraping & SQL Price Intelligence</span>
                </h1>
                <p class="hero-sub">
                    End-to-end data engineering & competitive pricing suite: live HTML extraction, normalized relational SQLite storage, and AI repricing simulation.
                </p>
            </div>
            <div style="background:rgba(16,185,129,0.14); border:1px solid {ACCENT_GREEN}; color:{ACCENT_GREEN};
                        padding:5px 14px; border-radius:999px; font-size:12px; font-weight:700;">
                ● SQLite Engine Online ({len(raw_df)} SKUs | Synced: {last_scraped})
            </div>
        </div>
        <div class="pipeline-grid">
            <div class="pipe-step">1. 🌐 Target E-Commerce<span>books.toscrape.com (15 Categories)</span></div>
            <div class="pipe-step">2. 🕷️ BeautifulSoup4 Scraper<span>HTML Parsing & Regex Price Cleaning</span></div>
            <div class="pipe-step">3. 🗄️ Relational SQLite3 DB<span>2 Tables (PK/FK Normalized Schema)</span></div>
            <div class="pipe-step">4. 📊 Live Price & Margin AI<span>Real-Time Parity & Repricing Engine</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.warning("No products match the current sidebar filter selection. Please enable more categories or broaden price filters.")
    st.stop()


# ---------------------------------------------------------------------------
# Top KPI Cards with Mini Progress Bars
# ---------------------------------------------------------------------------
total_skus = len(filtered_df)
catalog_share_pct = (total_skus / len(raw_df) * 100) if len(raw_df) > 0 else 0
overpriced_count = int((filtered_df["price_status"] == "Overpriced (At Risk)").sum())
overpriced_pct = (overpriced_count / total_skus * 100) if total_skus > 0 else 0.0
competitive_pct = ((total_skus - overpriced_count) / total_skus * 100) if total_skus > 0 else 0.0
total_est_rev = float(filtered_df["est_monthly_revenue"].sum())
avg_margin = float(filtered_df["target_margin_pct"].mean())
avg_diff_pct = float(filtered_df["price_diff_pct"].mean())

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-label">INDEXED SQL CATALOG</span>
                <span class="kpi-icon">🗄️</span>
            </div>
            <div class="kpi-value">{total_skus:,} <span style="font-size:15px; font-weight:600; color:{TEXT_MUTED};">SKUs</span></div>
            <div class="kpi-sub" style="color:{ACCENT_CYAN};">
                {filtered_df['category_name'].nunique()} Active Categories ({catalog_share_pct:.0f}% of DB)
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{min(100, catalog_share_pct):.0f}%; background:{ACCENT_CYAN};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-label">OVERPRICED (AT RISK)</span>
                <span class="kpi-icon">⚠️</span>
            </div>
            <div class="kpi-value">{overpriced_count:,} <span style="font-size:15px; font-weight:600; color:{ACCENT_PINK};">({overpriced_pct:.1f}%)</span></div>
            <div class="kpi-sub" style="color:{ACCENT_PINK};">
                Priced >3% above competitor benchmark
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{min(100, overpriced_pct):.0f}%; background:{ACCENT_PINK};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-label">EST. MONTHLY REVENUE</span>
                <span class="kpi-icon">💰</span>
            </div>
            <div class="kpi-value">${total_est_rev:,.0f}</div>
            <div class="kpi-sub" style="color:{ACCENT_GREEN};">
                Avg Target Gross Margin: {avg_margin:.1f}%
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{min(100, avg_margin * 2.2):.0f}%; background:{ACCENT_GREEN};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    diff_sign = "+" if avg_diff_pct > 0 else ""
    idx_color = ACCENT_GREEN if avg_diff_pct <= 0 else ACCENT_AMBER
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-top">
                <span class="kpi-label">COMPETITIVE HEALTH SCORE</span>
                <span class="kpi-icon">🎯</span>
            </div>
            <div class="kpi-value">{competitive_pct:.1f}%</div>
            <div class="kpi-sub" style="color:{idx_color};">
                Net Price Spread: {diff_sign}{avg_diff_pct:.2f}% vs. Market
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width:{min(100, competitive_pct):.0f}%; background:{ACCENT_PURPLE};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Row 1: Market Positioning Split & Category Price Benchmark (Zero Overlap)
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">📊 COMPETITIVE POSITIONING & CATEGORY PRICING BENCHMARK</div>', unsafe_allow_html=True)

r1_col1, r1_col2 = st.columns([1, 1.45])

with r1_col1:
    st.markdown(
        """
        <div class="chart-header-box">
            <div class="chart-title">Catalog Price Positioning Split</div>
            <div class="chart-subtitle">Share of scraped SKUs by competitive price tier</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    status_order = ["Undercutting (Cheaper)", "Price Match (Competitive)", "Overpriced (At Risk)"]
    status_counts = filtered_df["price_status"].value_counts().reindex(status_order, fill_value=0)

    fig_donut = go.Figure(
        data=[
            go.Pie(
                labels=status_counts.index.tolist(),
                values=status_counts.values.tolist(),
                hole=0.64,
                marker=dict(
                    colors=[ACCENT_CYAN, ACCENT_GREEN, ACCENT_PINK],
                    line=dict(color=BG_CARD_SOLID, width=2),
                ),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>SKUs: %{value}<br>Share: %{percent}<extra></extra>",
            )
        ]
    )
    fig_donut.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=340,
        margin=dict(t=15, b=55, l=15, r=15),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.06,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT_PRIMARY, size=11.5),
        ),
        annotations=[
            dict(
                text=f"<b>{total_skus}</b><br><span style='font-size:12px;'>SKUs</span>",
                x=0.5,
                y=0.5,
                font=dict(size=19, color=TEXT_PRIMARY),
                showarrow=False,
            )
        ],
    )
    render_plotly(fig_donut)

with r1_col2:
    st.markdown(
        """
        <div class="chart-header-box">
            <div class="chart-title">Our Avg Price vs. Competitor Benchmark by Category</div>
            <div class="chart-subtitle">SQL INNER JOIN aggregation across top revenue-generating categories</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cat_summary = (
        filtered_df.groupby("category_name", as_index=False)
        .agg(
            our_avg=("our_price", "mean"),
            comp_avg=("competitor_price", "mean"),
            total_rev=("est_monthly_revenue", "sum"),
        )
        .sort_values("total_rev", ascending=False)
        .head(10)
    )

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            x=cat_summary["category_name"],
            y=cat_summary["our_avg"].round(2),
            name="Our Avg Price ($)",
            marker_color=ACCENT_PURPLE,
        )
    )
    fig_bar.add_trace(
        go.Bar(
            x=cat_summary["category_name"],
            y=cat_summary["comp_avg"].round(2),
            name="Competitor Avg ($)",
            marker_color=ACCENT_CYAN,
        )
    )
    fig_bar.update_layout(
        template=CHART_TEMPLATE,
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=340,
        margin=dict(t=15, b=65, l=45, r=15),
        xaxis=dict(tickfont=dict(color=TEXT_PRIMARY, size=11), tickangle=-20),
        yaxis=dict(
            title=dict(text="Avg Price ($)", font=dict(color=TEXT_MUTED, size=12)),
            tickfont=dict(color=TEXT_PRIMARY),
            gridcolor=GRID_COLOR,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT_PRIMARY, size=11.5),
        ),
    )
    render_plotly(fig_bar)


# ---------------------------------------------------------------------------
# Row 2: Price Parity Scatter Matrix & Category Revenue Ranking
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">🎯 SKU PRICE PARITY MATRIX & CATEGORY REVENUE EXPOSURE</div>', unsafe_allow_html=True)

r2_col1, r2_col2 = st.columns(2)

with r2_col1:
    st.markdown(
        """
        <div class="chart-header-box">
            <div class="chart-title">SKU Price Parity Matrix (Bubble Size = Monthly Sales)</div>
            <div class="chart-subtitle">Points above the dashed parity line are priced higher than competitors</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    color_map = {
        "Undercutting (Cheaper)": ACCENT_CYAN,
        "Price Match (Competitive)": ACCENT_GREEN,
        "Overpriced (At Risk)": ACCENT_PINK,
    }
    fig_scatter = go.Figure()
    for status_label in ["Undercutting (Cheaper)", "Price Match (Competitive)", "Overpriced (At Risk)"]:
        group_df = filtered_df[filtered_df["price_status"] == status_label]
        if group_df.empty:
            continue
        fig_scatter.add_trace(
            go.Scatter(
                x=group_df["competitor_price"],
                y=group_df["our_price"],
                mode="markers",
                name=status_label,
                marker=dict(
                    size=np.clip(group_df["est_monthly_sales"] / 5.2, 8, 19),
                    color=color_map.get(status_label, ACCENT_PURPLE),
                    opacity=0.88,
                    line=dict(width=1, color="rgba(255,255,255,0.45)"),
                ),
                text=group_df["title"],
                hovertemplate=(
                    "<b>%{text}</b><br>Competitor Price: $%{x:.2f}<br>"
                    "Our Price: $%{y:.2f}<extra></extra>"
                ),
            )
        )

    min_p = float(min(filtered_df["our_price"].min(), filtered_df["competitor_price"].min()))
    max_p = float(max(filtered_df["our_price"].max(), filtered_df["competitor_price"].max()))
    fig_scatter.add_trace(
        go.Scatter(
            x=[min_p, max_p],
            y=[min_p, max_p],
            mode="lines",
            name="Parity Line (Our = Comp)",
            line=dict(color=TEXT_MUTED, dash="dash", width=1.6),
            hoverinfo="skip",
        )
    )
    fig_scatter.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360,
        margin=dict(t=15, b=75, l=45, r=15),
        xaxis=dict(
            title=dict(text="Competitor Price ($)", font=dict(color=TEXT_MUTED, size=12)),
            tickfont=dict(color=TEXT_PRIMARY),
            gridcolor=GRID_COLOR,
        ),
        yaxis=dict(
            title=dict(text="Our Price ($)", font=dict(color=TEXT_MUTED, size=12)),
            tickfont=dict(color=TEXT_PRIMARY),
            gridcolor=GRID_COLOR,
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color=TEXT_PRIMARY, size=11),
        ),
    )
    render_plotly(fig_scatter)

with r2_col2:
    st.markdown(
        """
        <div class="chart-header-box">
            <div class="chart-title">Top 10 Categories by Estimated Monthly Revenue ($)</div>
            <div class="chart-subtitle">Ranked by total projected revenue across scraped inventory</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    rev_by_cat = (
        filtered_df.groupby("category_name", as_index=False)["est_monthly_revenue"]
        .sum()
        .sort_values("est_monthly_revenue", ascending=True)
        .tail(10)
    )
    fig_rev = go.Figure(
        go.Bar(
            x=rev_by_cat["est_monthly_revenue"].round(0),
            y=rev_by_cat["category_name"],
            orientation="h",
            marker=dict(
                color=rev_by_cat["est_monthly_revenue"],
                colorscale=[[0, ACCENT_CYAN], [1, ACCENT_PURPLE]],
            ),
            text=[f"${v:,.0f}" for v in rev_by_cat["est_monthly_revenue"]],
            textposition="inside",
            insidetextanchor="end",
            hovertemplate="<b>%{y}</b><br>Est. Monthly Revenue: $%{x:,.2f}<extra></extra>",
        )
    )
    fig_rev.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=360,
        margin=dict(t=15, b=55, l=45, r=20),
        xaxis=dict(
            title=dict(text="Estimated Monthly Revenue ($)", font=dict(color=TEXT_MUTED, size=12)),
            tickfont=dict(color=TEXT_PRIMARY),
            gridcolor=GRID_COLOR,
        ),
        yaxis=dict(title=dict(text=""), tickfont=dict(color=TEXT_PRIMARY, size=11.5)),
    )
    render_plotly(fig_rev)


# ---------------------------------------------------------------------------
# Row 3: Interactive "What-If" Automated Repricing Simulator
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">🚀 AI AUTOMATED REPRICING SIMULATOR (WHAT-IF IMPACT ENGINE)</div>', unsafe_allow_html=True)

sim_col1, sim_col2 = st.columns([1.05, 1.45])

with sim_col1:
    st.markdown(
        """
        <div class="chart-header-box">
            <div class="chart-title">Simulate Automated Markdown on Overpriced SKUs</div>
            <div class="chart-subtitle">Test how discounting overpriced items recaptures market competitiveness & sales volume</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    markdown_pct = st.slider(
        "Apply Automated Discount (%) to 'Overpriced (At Risk)' SKUs:",
        min_value=0,
        max_value=20,
        value=8,
        step=1,
    )

    sim_df = filtered_df.copy()
    is_over = sim_df["price_status"] == "Overpriced (At Risk)"
    sim_df["new_price"] = np.where(is_over, sim_df["our_price"] * (1 - markdown_pct / 100.0), sim_df["our_price"])
    sim_df["new_diff_pct"] = ((sim_df["new_price"] - sim_df["competitor_price"]) / sim_df["competitor_price"]) * 100.0

    volume_boost = np.where(is_over, 1.0 + (markdown_pct * 0.018), 1.0)
    sim_df["projected_revenue"] = sim_df["new_price"] * (sim_df["est_monthly_sales"] * volume_boost)

    remaining_overpriced = int((sim_df["new_diff_pct"] > 3.0).sum())
    converted_to_safe = max(0, overpriced_count - remaining_overpriced)
    rev_delta = float(sim_df["projected_revenue"].sum() - total_est_rev)

with sim_col2:
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">SKUS RECOVERED TO SAFE</div>
                <div class="kpi-value" style="color:{ACCENT_CYAN} !important;">+{converted_to_safe} <span style="font-size:14px;">SKUs</span></div>
                <div class="kpi-sub" style="color:{TEXT_MUTED};">Remaining At-Risk: {remaining_overpriced}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s2:
        new_health = ((total_skus - remaining_overpriced) / total_skus * 100) if total_skus > 0 else 0
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">NEW COMPETITIVE SCORE</div>
                <div class="kpi-value" style="color:{ACCENT_GREEN} !important;">{new_health:.1f}%</div>
                <div class="kpi-sub" style="color:{ACCENT_GREEN};">↑ +{new_health - competitive_pct:.1f}% improvement</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with s3:
        delta_sign = "+" if rev_delta >= 0 else ""
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">PROJECTED MONTHLY REV</div>
                <div class="kpi-value">${sim_df['projected_revenue'].sum():,.0f}</div>
                <div class="kpi-sub" style="color:{ACCENT_PURPLE};">{delta_sign}${rev_delta:,.0f}/mo Net Impact</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Row 4: Live Relational SQL Query Studio
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">🗄️ LIVE RELATIONAL SQL QUERY WORKBENCH (SQLITE3 ENGINE)</div>', unsafe_allow_html=True)

preset_queries = {
    "1. Category Revenue & Price Gap Summary (INNER JOIN + GROUP BY)": """SELECT 
    c.category_name AS Category,
    COUNT(p.product_id) AS Total_SKUs,
    ROUND(AVG(p.our_price), 2) AS Our_Avg_Price,
    ROUND(AVG(p.competitor_price), 2) AS Comp_Avg_Price,
    ROUND(AVG(p.price_diff_pct), 2) AS Avg_Diff_Pct,
    ROUND(SUM(p.est_monthly_revenue), 2) AS Est_Revenue
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
GROUP BY c.category_name
ORDER BY Est_Revenue DESC;""",
    "2. High-Risk Overpriced Products Hurting High-Margin Categories (JOIN + WHERE)": """SELECT 
    p.sku AS SKU,
    p.title AS Product_Title,
    c.category_name AS Category,
    p.our_price AS Our_Price,
    p.competitor_price AS Comp_Price,
    p.price_diff_pct AS Markup_Pct,
    p.est_monthly_revenue AS Revenue_At_Risk
FROM products p
INNER JOIN categories c ON p.category_id = c.category_id
WHERE p.price_status = 'Overpriced (At Risk)'
  AND p.price_diff_pct > 8.0
ORDER BY p.price_diff_pct DESC
LIMIT 15;""",
    "3. Star Rating Impact on Sales Volume & Pricing Power (GROUP BY + HAVING)": """SELECT 
    p.rating AS Star_Rating,
    COUNT(*) AS SKU_Count,
    ROUND(AVG(p.our_price), 2) AS Avg_Price,
    ROUND(AVG(p.est_monthly_sales), 1) AS Avg_Units_Sold,
    ROUND(SUM(p.est_monthly_revenue), 2) AS Total_Revenue
FROM products p
GROUP BY p.rating
HAVING COUNT(*) >= 5
ORDER BY p.rating DESC;""",
}

sql_col1, sql_col2 = st.columns([1.05, 1.35])

with sql_col1:
    selected_preset = st.selectbox("Choose Analytical SQL Query Template:", list(preset_queries.keys()))
    custom_sql = st.text_area(
        "Interactive SQL Editor (Read-Only SELECT against `market_intelligence.db`):",
        value=preset_queries[selected_preset],
        height=205,
    )

with sql_col2:
    st.markdown('<div class="sidebar-section-title">LIVE SQL QUERY RESULT SET</div>', unsafe_allow_html=True)
    try:
        sql_result_df = run_safe_sql_query(custom_sql)
        render_table(sql_result_df, height=255)
    except Exception as sql_exc:
        st.error(f"SQL Error: {sql_exc}")


# ---------------------------------------------------------------------------
# Row 5: Synchronized Catalog & Repricing Action Table
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">📋 SCRAPED PRODUCT CATALOG & REPRICING ACTION TABLE</div>', unsafe_allow_html=True)

display_cols = [
    "sku",
    "title",
    "category_name",
    "our_price",
    "competitor_price",
    "price_diff_pct",
    "price_status",
    "rating",
    "stock_quantity",
    "est_monthly_revenue",
]

catalog_view = (
    filtered_df[display_cols]
    .sort_values("price_diff_pct", ascending=False)
    .rename(
        columns={
            "sku": "SKU",
            "title": "Product Title",
            "category_name": "Category",
            "our_price": "Our Price ($)",
            "competitor_price": "Competitor ($)",
            "price_diff_pct": "Price Diff (%)",
            "price_status": "Positioning",
            "rating": "Rating (★)",
            "stock_quantity": "Stock",
            "est_monthly_revenue": "Est. Revenue ($)",
        }
    )
)

styled_catalog = (
    catalog_view.style.format(
        {
            "Our Price ($)": "${:.2f}",
            "Competitor ($)": "${:.2f}",
            "Price Diff (%)": "{:+.2f}%",
            "Est. Revenue ($)": "${:,.2f}",
        }
    ).background_gradient(subset=["Price Diff (%)"], cmap="coolwarm")
)

render_table(styled_catalog, height=410)

st.markdown(
    f"""
    <div style="text-align:center; padding:18px 0 8px 0; color:{TEXT_MUTED}; font-size:12px;">
        MarketPulse AI v2.1 · Automated Web Scraping (BeautifulSoup4) & Relational SQLite3 Engine · Built with Streamlit & Plotly
    </div>
    """,
    unsafe_allow_html=True,
)