import streamlit as st
from groq import Groq
from tavily import TavilyClient
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Factify AI – Fake News Detector",
    page_icon="🔍",
    layout="centered"
)

st.markdown("""
<style>
    .title-block {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .title-block h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.3rem;
    }
    .title-block p {
        color: #9ca3af;
        font-size: 1.05rem;
    }
    .verdict-fake {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 4px;
    }
    .verdict-real {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 4px;
    }
    .verdict-suspicious {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 1.2rem 2rem;
        border-radius: 16px;
        font-size: 2rem;
        font-weight: 800;
        text-align: center;
        letter-spacing: 4px;
    }
    .reason-card {
        background: #1e2030;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 0.9rem 1.2rem;
        margin: 0.5rem 0;
        color: #e5e7eb;
        font-size: 0.95rem;
    }
    .search-card {
        background: #0f2027;
        border-left: 4px solid #10b981;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin: 0.4rem 0;
        color: #9ca3af;
        font-size: 0.85rem;
    }
    .confidence-label {
        text-align: center;
        font-size: 1.1rem;
        color: #9ca3af;
        margin-top: 0.5rem;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin-top: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-block">
    <h1>🔍 Factify AI</h1>
    <p>Detect fake news instantly using real-time AI + web search</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── API Setup ────────────────────────────────────────────────
groq_key = os.getenv("GROQ_API_KEY")
tavily_key = os.getenv("TAVILY_API_KEY")

if not groq_key:
    st.error("⚠️ GROQ_API_KEY not found in .env file!")
    st.stop()

if not tavily_key:
    st.error("⚠️ TAVILY_API_KEY not found in .env file!")
    st.stop()

client = Groq(api_key=groq_key)
tavily = TavilyClient(api_key=tavily_key)

# ── Web Search ───────────────────────────────────────────────
def search_web(query):
    try:
        response = tavily.search(query=query, max_results=4)
        snippets = []
        for r in response.get("results", []):
            snippets.append(f"- {r['title']}: {r['content']}")
        return "\n".join(snippets) if snippets else "No results found."
    except Exception as e:
        return f"Search failed: {str(e)}"

# ── AI Analysis ──────────────────────────────────────────────
def analyze_news(text, search_results):
    prompt = f"""You are an expert fact-checker with access to real-time web search results.

Use the search results below to verify the news/claim. Then give your verdict.

SEARCH RESULTS FROM WEB:
{search_results}

NEWS/CLAIM TO ANALYZE:
{text}

Respond ONLY with valid JSON. No extra text, no markdown:

{{
  "verdict": "FAKE",
  "confidence": 92,
  "reasons": [
    "Reason one based on search results",
    "Reason two based on search results",
    "Reason three based on search results"
  ]
}}

verdict must be exactly: FAKE, REAL, or SUSPICIOUS
confidence is 0-100
reasons must be exactly 3 strings mentioning what web search found"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a fact-checker. Use web search results to verify claims. Always respond with valid JSON only. No markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()

# ── Input ────────────────────────────────────────────────────
news_input = st.text_area(
    "📋 Paste your news article or message below:",
    height=200,
    placeholder="e.g. GT defeated KKR in yesterday's IPL match..."
)

with st.expander("💡 Try a demo example"):
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔴 Fake example"):
            st.session_state["demo_text"] = "NASA confirms the moon is made of cheese. Apollo missions discovered edible dairy material on the lunar surface."
    with col2:
        if st.button("🟢 Real example"):
            st.session_state["demo_text"] = "GT defeated KKR in a close IPL match yesterday."
    with col3:
        if st.button("🟡 Suspicious example"):
            st.session_state["demo_text"] = "New study shows chocolate makes you 50% smarter if eaten daily from an unnamed university."

if "demo_text" in st.session_state:
    st.info(st.session_state["demo_text"])

analyze_btn = st.button("🔍 Analyze Now")

# ── Main Logic ───────────────────────────────────────────────
if analyze_btn:
    text_to_check = news_input.strip()

    if not text_to_check:
        st.warning("⚠️ Please paste some text first!")
    elif len(text_to_check) < 10:
        st.warning("⚠️ Text too short!")
    else:
        with st.spinner("🌐 Searching web for real-time info..."):
            search_results = search_web(text_to_check)

        with st.expander("🔎 Web sources found"):
            for line in search_results.split("\n"):
                if line.strip():
                    st.markdown(
                        f'<div class="search-card">{line}</div>',
                        unsafe_allow_html=True
                    )

        with st.spinner("🧠 AI analyzing with web data..."):
            try:
                raw = analyze_news(text_to_check, search_results)

                cleaned = raw
                if "```" in cleaned:
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                cleaned = cleaned.strip()

                result     = json.loads(cleaned)
                verdict    = result.get("verdict", "SUSPICIOUS").upper()
                confidence = int(result.get("confidence", 50))
                reasons    = result.get("reasons", ["No reasons provided."])

                st.markdown("---")
                st.markdown("### 📊 Analysis Results")

                css_class = {
                    "FAKE": "verdict-fake",
                    "REAL": "verdict-real",
                    "SUSPICIOUS": "verdict-suspicious"
                }.get(verdict, "verdict-suspicious")

                icon = {
                    "FAKE": "🚨",
                    "REAL": "✅",
                    "SUSPICIOUS": "⚠️"
                }.get(verdict, "⚠️")

                st.markdown(
                    f'<div class="{css_class}">{icon} {verdict}</div>',
                    unsafe_allow_html=True
                )

                bar_color = {
                    "FAKE": "#ef4444",
                    "REAL": "#10b981",
                    "SUSPICIOUS": "#f59e0b"
                }.get(verdict, "#6366f1")

                st.markdown(
                    f'<div class="confidence-label">Confidence: {confidence}%</div>',
                    unsafe_allow_html=True
                )
                st.markdown(f"""
                    <div style="background:#2d2d2d;border-radius:99px;height:12px;margin:0.5rem 0 1.5rem 0;">
                        <div style="background:{bar_color};width:{confidence}%;height:12px;border-radius:99px;"></div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("#### 🧾 Why this verdict?")
                symbols = ["①", "②", "③"]
                for i, reason in enumerate(reasons[:3]):
                    st.markdown(
                        f'<div class="reason-card">{symbols[i]} {reason}</div>',
                        unsafe_allow_html=True
                    )

                st.success("✅ Analysis complete!")

            except json.JSONDecodeError:
                st.error("❌ AI returned invalid response. Try again.")
                st.code(raw)
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")