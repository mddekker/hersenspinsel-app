import streamlit as st
import anthropic
import urllib.parse
from datetime import datetime

st.set_page_config(
    page_title="Hersenspinsel",
    page_icon="🧠",
    layout="centered",
)

# Mobile-first styling
st.markdown(
    """
<style>
    /* Verberg Streamlit menu en footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Tekstvak groter en duidelijker */
    .stTextArea textarea {
        font-size: 18px !important;
        min-height: 220px !important;
        line-height: 1.5;
    }

    /* Knoppen groot en goed klikbaar */
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 12px;
    }

    /* Mail-knop styling */
    .mail-button {
        display: block;
        width: 100%;
        height: 64px;
        background: #2563EB;
        color: white !important;
        text-align: center;
        line-height: 64px;
        font-size: 18px;
        font-weight: 600;
        text-decoration: none !important;
        border-radius: 12px;
        margin-top: 12px;
    }

    /* Compactere padding op mobiel */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""",
    unsafe_allow_html=True,
)

EMAIL_TO = "ma.dekker@humancapitalcare.nl"


def get_api_key() -> str:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return ""


def structureer_als_todo(api_key: str, ruwe_tekst: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Hieronder volgt een ingesproken brain dump van Martin, algemeen directeur van HumanCapitalCare.
Het bevat hersenspinsels: vaak to-do's zoals mensen terugbellen, dingen uitzoeken, afspraken inplannen.

Structureer dit als een overzichtelijke to-do lijst in het Nederlands.

Regels:
- Begin direct met de lijst, geen inleiding of afsluiting
- Groepeer per categorie waar logisch: "📞 Bellen", "🔍 Uitzoeken", "📅 Afspraken", "✉️ Mailen", "💭 Overig"
- Elk actiepunt op een eigen regel, beginnend met "- "
- Behoud alle informatie en context
- Maak het scanbaar — korte, krachtige formuleringen

Hersenspinsels:
{ruwe_tekst}
"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# --- UI ---
st.title("🧠 Hersenspinsel")
st.caption(
    "Tik in het vak, druk op het 🎤 op je toetsenbord en spreek in. "
    "Druk daarna op 'Verwerk' — je krijgt een mail-knop waarmee je het naar jezelf stuurt."
)

if "structured" not in st.session_state:
    st.session_state["structured"] = ""

ruwe_tekst = st.text_area(
    "Spreek je hersenspinsel in",
    placeholder="Tik hier, dan verschijnt het toetsenbord. Druk op 🎤 om te dicteren.",
    height=220,
    key="input",
    label_visibility="collapsed",
)

verwerk = st.button("✨ Verwerk tot to-do lijst", type="primary")

if verwerk:
    if not ruwe_tekst.strip():
        st.warning("Spreek eerst iets in.")
    else:
        api_key = get_api_key()
        if not api_key:
            st.error("API key niet gevonden — check de Streamlit-secrets.")
        else:
            with st.spinner("Bezig met structureren…"):
                try:
                    st.session_state["structured"] = structureer_als_todo(api_key, ruwe_tekst)
                except Exception as e:
                    st.error(f"Fout: {e}")

if st.session_state["structured"]:
    st.divider()
    st.markdown("### Voorbeeld")
    st.markdown(st.session_state["structured"])

    # Mailto link genereren
    subject = "Hersenspinsels"
    body = st.session_state["structured"]
    mailto = (
        f"mailto:{EMAIL_TO}"
        f"?subject={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(body)}"
    )

    st.markdown(
        f'<a href="{mailto}" class="mail-button">📧 Open in Mail-app</a>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Nieuwe hersenspinsel", use_container_width=True):
        st.session_state["structured"] = ""
        st.rerun()
