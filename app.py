import streamlit as st
import anthropic
import urllib.parse
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="Hersenspinsel",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Heavy custom styling — geen Streamlit-look ---
st.markdown(
    """
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">

<style>
    /* Streamlit-elementen verbergen */
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    /* Achtergrond + typografie */
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }

    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 520px !important;
    }

    /* App-titel */
    .app-title {
        font-size: 32px;
        font-weight: 700;
        color: #0F172A;
        text-align: center;
        margin-bottom: 4px;
        letter-spacing: -0.5px;
    }
    .app-subtitle {
        font-size: 15px;
        color: #64748B;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* Container van de microfoon-knop centreren */
    [data-testid="stCustomComponentV1"] {
        display: flex !important;
        justify-content: center !important;
        margin: 40px auto !important;
    }

    /* De grote ronde opnameknop */
    [data-testid="stCustomComponentV1"] button {
        background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 240px !important;
        height: 240px !important;
        font-size: 22px !important;
        font-weight: 600 !important;
        padding: 0 !important;
        box-shadow:
            0 20px 50px rgba(37, 99, 235, 0.35),
            0 0 0 0 rgba(59, 130, 246, 0.5) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        letter-spacing: -0.2px !important;
        cursor: pointer !important;
        animation: pulse 2.5s infinite !important;
    }

    @keyframes pulse {
        0%   { box-shadow: 0 20px 50px rgba(37, 99, 235, 0.35), 0 0 0 0 rgba(59, 130, 246, 0.5); }
        70%  { box-shadow: 0 20px 50px rgba(37, 99, 235, 0.35), 0 0 0 30px rgba(59, 130, 246, 0); }
        100% { box-shadow: 0 20px 50px rgba(37, 99, 235, 0.35), 0 0 0 0 rgba(59, 130, 246, 0); }
    }

    [data-testid="stCustomComponentV1"] button:hover {
        transform: translateY(-2px) scale(1.02) !important;
    }

    [data-testid="stCustomComponentV1"] button:active {
        transform: scale(0.96) !important;
    }

    /* Reset/secundaire knop niet rond */
    .stButton > button {
        background: white !important;
        color: #475569 !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 14px !important;
        padding: 16px !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        transition: transform 0.15s ease !important;
    }
    .stButton > button:hover { transform: translateY(-1px) !important; }
    .stButton > button:active { transform: scale(0.98) !important; }

    /* Resultaat-kaart */
    .result-card {
        background: white;
        border-radius: 20px;
        padding: 24px;
        margin-top: 24px;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
        border: 1px solid #E2E8F0;
    }

    .result-card h3 {
        margin-top: 0;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748B;
        font-weight: 600;
    }

    /* Mail-knop */
    .mail-button {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        width: 100%;
        height: 64px;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white !important;
        text-decoration: none !important;
        font-size: 18px;
        font-weight: 600;
        border-radius: 16px;
        margin-top: 16px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
        transition: transform 0.15s ease;
    }

    .mail-button:hover { transform: translateY(-1px); }
    .mail-button:active { transform: scale(0.98); }

    /* Reset-knop subtieler */
    div[data-testid="column"]:last-child .stButton > button {
        background: white !important;
        color: #475569 !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
        padding: 16px !important;
    }

    /* Status-tekst */
    .status-text {
        text-align: center;
        color: #64748B;
        font-size: 14px;
        margin-top: 16px;
    }

    /* Spinner styling */
    .stSpinner > div { border-color: #3B82F6 !important; }
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
st.markdown('<div class="app-title">🧠 Hersenspinsel</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Tik op de knop, spreek je gedachten in, klaar.</div>',
    unsafe_allow_html=True,
)

if "structured" not in st.session_state:
    st.session_state["structured"] = ""
if "raw_text" not in st.session_state:
    st.session_state["raw_text"] = ""

# Microfoon-knop met directe spraakherkenning
text = speech_to_text(
    language="nl-NL",
    start_prompt="🎙",
    stop_prompt="⏹",
    just_once=True,
    use_container_width=False,
    key="stt",
)

# Als er nieuwe spraak is herkend en het verschilt van wat we al hebben
if text and text != st.session_state.get("raw_text", ""):
    st.session_state["raw_text"] = text
    api_key = get_api_key()
    if not api_key:
        st.error("API key niet gevonden — check de Streamlit-secrets.")
    else:
        with st.spinner("Even structureren…"):
            try:
                st.session_state["structured"] = structureer_als_todo(api_key, text)
            except Exception as e:
                st.error(f"Fout: {e}")

if st.session_state["structured"]:
    st.markdown(
        f"""
<div class="result-card">
<h3>To-do lijst</h3>
{st.session_state["structured"]}
</div>
""",
        unsafe_allow_html=True,
    )

    subject = "Hersenspinsels"
    body = (
        f"{st.session_state['structured']}\n\n"
        f"---\n\n"
        f"Letterlijke opname:\n{st.session_state['raw_text']}"
    )
    mailto = (
        f"mailto:{EMAIL_TO}"
        f"?subject={urllib.parse.quote(subject)}"
        f"&body={urllib.parse.quote(body)}"
    )

    st.markdown(
        f'<a href="{mailto}" class="mail-button">📧 Verstuur naar mijn mail</a>',
        unsafe_allow_html=True,
    )

    if st.button("Nieuwe hersenspinsel", use_container_width=True, key="reset"):
        st.session_state["structured"] = ""
        st.session_state["raw_text"] = ""
        st.rerun()
elif st.session_state.get("raw_text"):
    st.markdown(
        f'<div class="status-text">📝 Opgenomen: <em>"{st.session_state["raw_text"][:100]}…"</em></div>',
        unsafe_allow_html=True,
    )
