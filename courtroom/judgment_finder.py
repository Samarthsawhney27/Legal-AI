import requests
from bs4 import BeautifulSoup
import streamlit as st
import ollama
import time
import re
from urllib.parse import quote, urljoin
from typing import List, Dict

# ── Constants ─────────────────────────────────────────────────────────────
INDIAN_KANOON_BASE = "https://indiankanoon.org"
SEARCH_URL = "https://indiankanoon.org/search/?formInput={query}&pagenum=0"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
REQUEST_TIMEOUT = 15
DELAY_BETWEEN_REQS = 1.5  # seconds — be respectful to the server
MAX_JUDGMENTS = 5  # fetch top 5 results
OLLAMA_MODEL = "llama3.2"  # must match your existing model


# ── Helper: clean text ────────────────────────────────────────────────────
def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Step 1: Build smart search query from case description ────────────────
def build_search_query(case_description: str, case_type: str = None) -> str:
    """
    Use Ollama to extract the best 5-8 keyword search query
    for Indian Kanoon from the case description.
    """
    prompt = f"""
You are a legal search expert for Indian courts.
Extract the most important 5-8 legal keywords from this case description
that would find similar past Indian court judgments on indiankanoon.org.

Return ONLY the keywords separated by spaces. No explanation, no punctuation.
Focus on: legal acts, sections, type of dispute, legal remedy sought.

Case Type: {case_type or 'General'}
Case Description: {case_description[:500]}

Keywords:"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        keywords = response["message"]["content"].strip()
        # Clean up — remove quotes, newlines, extra spaces
        keywords = re.sub(r'["\'\n]', " ", keywords)
        keywords = re.sub(r"\s+", " ", keywords).strip()
        return keywords[:200]  # Indian Kanoon query limit
    except Exception:
        # Fallback: use first 100 chars of case description
        return case_description[:100]


# ── Step 2: Search Indian Kanoon ──────────────────────────────────────────
def search_indian_kanoon(query: str) -> List[Dict]:
    """
    Search Indian Kanoon and return list of result dicts with:
    title, url, snippet, court, date
    """
    results = []
    try:
        encoded_query = quote(query)
        url = SEARCH_URL.format(query=encoded_query)

        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Indian Kanoon search results are in divs with class "result"
        result_divs = soup.find_all("div", class_="result")[:MAX_JUDGMENTS]

        for div in result_divs:
            try:
                # Title and URL
                title_tag = div.find("a")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                href = title_tag.get("href", "")
                full_url = urljoin(INDIAN_KANOON_BASE, href)

                # Snippet text
                snippet_div = div.find("div", class_="snippet")
                snippet = snippet_div.get_text(strip=True) if snippet_div else ""

                # Court name and date (usually in a metadata div)
                meta_div = div.find("div", class_="docsource_main")
                court_info = (
                    meta_div.get_text(strip=True) if meta_div else "Unknown Court"
                )

                # Extract year from title or court info
                year_match = re.search(
                    r"\b(19|20)\d{2}\b", title + " " + court_info
                )
                year = year_match.group() if year_match else "Unknown"

                results.append(
                    {
                        "title": title,
                        "url": full_url,
                        "snippet": _clean_text(snippet),
                        "court": court_info,
                        "year": year,
                        "full_text": None,  # filled in next step
                    }
                )

            except Exception:
                continue

        return results

    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Indian Kanoon. Check your internet connection.")
        return []
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []


# ── Step 3: Fetch full judgment text ──────────────────────────────────────
def fetch_judgment_text(url: str, max_chars: int = 3000) -> str:
    """
    Fetch the full text of a judgment page from Indian Kanoon.
    Returns first max_chars characters to keep within LLM context limits.
    """
    try:
        time.sleep(DELAY_BETWEEN_REQS)  # Respectful delay
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Main judgment text is usually in div with id="judgments" or class="judgments"
        judgment_div = (
            soup.find("div", id="judgments")
            or soup.find("div", class_="judgments")
            or soup.find("div", id="main")
            or soup.find("pre")  # some pages use pre tags
        )

        if judgment_div:
            text = judgment_div.get_text(separator="\n")
        else:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all("p")
            text = "\n".join(p.get_text() for p in paragraphs)

        return _clean_text(text)[:max_chars]

    except Exception as e:
        return f"Could not fetch judgment text: {str(e)}"


# ── Step 4: AI summarizes judgment ────────────────────────────────────────
def summarize_judgment(
    judgment_text: str, case_title: str, user_case: str
) -> Dict:
    """
    Use Ollama to extract structured info from a judgment.
    Returns dict with: verdict, key_sections, reasoning, relevance, ratio
    """
    prompt = f"""
You are an expert Indian legal analyst.
Analyze this court judgment and extract structured information.

USER'S CURRENT CASE (for relevance comparison):
{user_case[:300]}

JUDGMENT BEING ANALYZED:
Title: {case_title}
Text: {judgment_text[:2500]}

Extract and return EXACTLY in this format (no extra text):

VERDICT: [ALLOWED / DISMISSED / PARTLY ALLOWED / SETTLED / ACQUITTED / CONVICTED]
COURT_AND_YEAR: [Court name and year of judgment]
PARTIES: [Appellant vs Respondent, brief]
KEY_SECTIONS_CITED: [List the actual IPC/Contract/Consumer/Constitutional sections cited]
COURT_REASONING: [2-3 sentences on WHY the court decided this way]
FINAL_ORDER: [What the court actually ordered — compensation amount, imprisonment, etc.]
RELEVANCE_TO_USER_CASE: [HIGH / MEDIUM / LOW — explain in 1 sentence why]
RATIO_DECIDENDI: [The core legal principle established — 1 sentence]
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            stream=False,
        )
        raw = response["message"]["content"].strip()

        # Parse the structured response
        def extract_field(text: str, field: str) -> str:
            pattern = rf"{field}:\s*(.+?)(?=\n[A-Z_]+:|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else "Not found"

        return {
            "verdict": extract_field(raw, "VERDICT"),
            "court_and_year": extract_field(raw, "COURT_AND_YEAR"),
            "parties": extract_field(raw, "PARTIES"),
            "sections_cited": extract_field(raw, "KEY_SECTIONS_CITED"),
            "reasoning": extract_field(raw, "COURT_REASONING"),
            "final_order": extract_field(raw, "FINAL_ORDER"),
            "relevance": extract_field(raw, "RELEVANCE_TO_USER_CASE"),
            "ratio": extract_field(raw, "RATIO_DECIDENDI"),
            "raw": raw,
        }

    except Exception as e:
        return {
            "verdict": "Analysis failed",
            "court_and_year": "Unknown",
            "parties": case_title,
            "sections_cited": "Unknown",
            "reasoning": str(e),
            "final_order": "Unknown",
            "relevance": "Unknown",
            "ratio": "Unknown",
            "raw": "",
        }


# ── Step 5: Format past judgments for LLM agents ─────────────────────────
def format_judgments_for_agents(analyzed_judgments: List[Dict]) -> str:
    """
    Format analyzed judgments into a string that can be appended
    to prosecution/defense agent prompts as precedent context.
    """
    if not analyzed_judgments:
        return ""

    lines = [
        "\n" + "=" * 60,
        "PAST COURT JUDGMENTS (PRECEDENTS) — USE THESE IN YOUR ARGUMENTS",
        "=" * 60,
    ]

    for i, j in enumerate(analyzed_judgments, 1):
        summary = j.get("summary", {})
        lines.append(
            f"""
[PRECEDENT {i}]
Case: {j.get('title', 'Unknown')}
Court & Year: {summary.get('court_and_year', 'Unknown')}
Verdict: {summary.get('verdict', 'Unknown')}
Sections Cited: {summary.get('sections_cited', 'Unknown')}
Court's Reasoning: {summary.get('reasoning', 'Unknown')}
Final Order: {summary.get('final_order', 'Unknown')}
Legal Principle: {summary.get('ratio', 'Unknown')}
Source: {j.get('url', '')}
"""
        )

    lines.append("=" * 60)
    lines.append(
        "INSTRUCTION: Reference these precedents in your arguments. "
        "Say 'As held in [Case Name], [Year]...' when citing them."
    )

    return "\n".join(lines)


# ── MAIN FUNCTION: Full pipeline ──────────────────────────────────────────
def find_past_judgments(
    case_description: str, case_type: str = None, progress_callback=None
) -> Dict:
    """
    Full pipeline:
    1. Build search query
    2. Search Indian Kanoon
    3. Fetch each judgment
    4. AI summarize each
    5. Return everything

    Returns dict with:
    - judgments: list of analyzed judgment dicts
    - precedent_context: formatted string for LLM agents
    - search_query: the query that was used
    - total_found: int
    """

    def _progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)

    # Step 1: Build query
    _progress("🔍 Building search query from case description...")
    search_query = build_search_query(case_description, case_type)
    _progress(f"🔎 Searching: **{search_query}**")

    # Step 2: Search
    results = search_indian_kanoon(search_query)
    if not results:
        return {
            "judgments": [],
            "precedent_context": "",
            "search_query": search_query,
            "total_found": 0,
            "error": "No results found on Indian Kanoon",
        }

    _progress(f"✅ Found {len(results)} related judgments. Analyzing...")

    # Step 3 & 4: Fetch + summarize each
    analyzed = []
    for i, result in enumerate(results):
        _progress(
            f"📄 Reading judgment {i + 1}/{len(results)}: "
            f"{result['title'][:60]}..."
        )

        # Fetch full text
        full_text = fetch_judgment_text(result["url"])
        result["full_text"] = full_text

        # AI summarize
        summary = summarize_judgment(
            judgment_text=full_text,
            case_title=result["title"],
            user_case=case_description,
        )
        result["summary"] = summary
        analyzed.append(result)

    # Step 5: Format for agents
    precedent_context = format_judgments_for_agents(analyzed)

    return {
        "judgments": analyzed,
        "precedent_context": precedent_context,
        "search_query": search_query,
        "total_found": len(analyzed),
        "error": None,
    }

