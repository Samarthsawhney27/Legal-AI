import streamlit as st

VERDICT_COLORS = {
    "ALLOWED": ("#00ff88", "✅"),
    "DISMISSED": ("#ff4444", "❌"),
    "PARTLY ALLOWED": ("#ffaa00", "⚖️"),
    "ACQUITTED": ("#00ccff", "🔵"),
    "CONVICTED": ("#ff0066", "🔴"),
    "SETTLED": ("#aaaaaa", "🤝"),
}

RELEVANCE_COLORS = {
    "HIGH": "#00ff88",
    "MEDIUM": "#ffaa00",
    "LOW": "#888888",
}


def display_judgment_card(judgment: dict, index: int) -> None:
    """Display a single judgment as a styled card."""
    summary = judgment.get("summary", {})
    verdict = summary.get("verdict", "Unknown").upper()
    relevance = summary.get("relevance", "Unknown").upper()

    # Get verdict color
    verdict_color, verdict_icon = VERDICT_COLORS.get(verdict, ("#888888", "⚖️"))

    # Get relevance color (just first word)
    rel_word = relevance.split()[0] if relevance else "LOW"
    rel_color = RELEVANCE_COLORS.get(rel_word, "#888888")

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(145deg, #0d1117, #161b22);
        border: 1px solid #30363d;
        border-left: 4px solid {verdict_color};
        border-radius: 10px;
        padding: 16px 20px;
        margin: 12px 0;
    ">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="flex:1;">
                <h4 style="color:#e6edf3; margin:0 0 6px 0; font-size:14px;">
                    {verdict_icon} {judgment.get('title', 'Unknown Case')[:80]}
                </h4>
                <p style="color:#8b949e; font-size:12px; margin:0 0 10px 0;">
                    🏛️ {summary.get('court_and_year', 'Unknown Court')} &nbsp;|&nbsp;
                    👥 {summary.get('parties', '')[:60]}
                </p>
            </div>
            <div style="text-align:right; min-width:120px;">
                <span style="
                    background:{verdict_color}22;
                    color:{verdict_color};
                    border:1px solid {verdict_color};
                    padding:3px 10px;
                    border-radius:20px;
                    font-size:11px;
                    font-weight:bold;
                ">{verdict}</span>
                <br><br>
                <span style="
                    background:{rel_color}22;
                    color:{rel_color};
                    border:1px solid {rel_color};
                    padding:2px 8px;
                    border-radius:20px;
                    font-size:10px;
                ">Relevance: {rel_word}</span>
            </div>
        </div>

        <div style="
            background:#21262d;
            border-radius:6px;
            padding:10px 14px;
            margin:8px 0;
        ">
            <p style="color:#cdd9e5; font-size:12px; margin:0 0 6px 0;">
                <b style="color:#7ee787;">📋 Sections Cited:</b>
                {summary.get('sections_cited', 'N/A')}
            </p>
            <p style="color:#cdd9e5; font-size:12px; margin:0 0 6px 0;">
                <b style="color:#79c0ff;">⚖️ Court's Reasoning:</b>
                {summary.get('reasoning', 'N/A')}
            </p>
            <p style="color:#cdd9e5; font-size:12px; margin:0 0 6px 0;">
                <b style="color:#ffa657;">📌 Final Order:</b>
                {summary.get('final_order', 'N/A')}
            </p>
            <p style="color:#cdd9e5; font-size:12px; margin:0;">
                <b style="color:#d2a8ff;">💡 Legal Principle:</b>
                {summary.get('ratio', 'N/A')}
            </p>
        </div>

        <a href="{judgment.get('url', '#')}" target="_blank"
           style="color:#58a6ff; font-size:11px; text-decoration:none;">
            🔗 Read Full Judgment on Indian Kanoon →
        </a>
    </div>
    """,
        unsafe_allow_html=True,
    )


def display_all_judgments(judgment_data: dict) -> None:
    """Display full judgment finder results section."""
    if not judgment_data or not judgment_data.get("judgments"):
        st.warning("No past judgments found for this case.")
        return

    judgments = judgment_data["judgments"]
    query = judgment_data.get("search_query", "")

    st.markdown(f"**Search Query Used:** `{query}`")
    st.markdown(
        f"**{len(judgments)} past judgments analyzed from Indian Kanoon**"
    )
    st.markdown("---")

    for i, judgment in enumerate(judgments):
        display_judgment_card(judgment, i + 1)

