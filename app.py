import streamlit as st
import streamlit.components.v1 as components
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from streamlit_mic_recorder import speech_to_text

st.set_page_config(
    page_title="Hersenspinsel",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

EMAIL_TO = "ma.dekker@humancapitalcare.nl"

for key, val in [("phase", "idle"), ("raw_text", ""), ("error_msg", "")]:
    if key not in st.session_state:
        st.session_state[key] = val


def structureer(tekst: str) -> str:
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"""Structureer deze ingesproken brain dump van Martin (directeur HumanCapitalCare) als een to-do lijst in het Nederlands.

Regels:
- Begin direct met de lijst, geen inleiding of afsluiting
- Groepeer per categorie: "📞 Bellen", "🔍 Uitzoeken", "📅 Afspraken", "✉️ Mailen", "💭 Overig"
- Elk actiepunt op eigen regel met "- "
- Kort en krachtig

Brain dump:
{tekst}""",
        }],
    )
    return response.content[0].text.strip()


def verstuur_email(onderwerp: str, tekst: str) -> None:
    smtp_host = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(st.secrets.get("SMTP_PORT", 587))
    smtp_user = st.secrets["SMTP_USER"]
    smtp_pass = st.secrets["SMTP_PASS"]

    msg = MIMEMultipart()
    msg["Subject"] = onderwerp
    msg["From"] = smtp_user
    msg["To"] = EMAIL_TO
    msg.attach(MIMEText(tekst, "plain", "utf-8"))

    with smtplib.SMTP(smtp_host, smtp_port) as s:
        s.ehlo()
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.sendmail(smtp_user, EMAIL_TO, msg.as_string())


# SVG mic icon (wit, Feather-stijl) als data-URI voor in de CSS
MIC_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='9' y='2' width='6' height='12' rx='3'/%3E%3Cpath d='M5 10a7 7 0 0 0 14 0'/%3E%3Cline x1='12' y1='17' x2='12' y2='21'/%3E%3Cline x1='8' y1='21' x2='16' y2='21'/%3E%3C/svg%3E"
STOP_SVG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white' stroke='none'%3E%3Crect x='5' y='5' width='14' height='14' rx='2'/%3E%3C/svg%3E"

st.html(f"""
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">
<style>
  @keyframes breathe {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(220,38,38,0.5), 0 24px 80px rgba(220,38,38,0.45); }}
    50%       {{ box-shadow: 0 0 0 28px rgba(220,38,38,0), 0 24px 80px rgba(220,38,38,0.45); }}
  }}

  #MainMenu, footer, header, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] {{
    display: none !important;
  }}

  html, body {{
    background: #060A12 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
  }}

  [data-testid="stAppViewContainer"] {{
    background:
      radial-gradient(ellipse 70% 40% at 50% 0%, rgba(180,20,20,0.18) 0%, transparent 70%),
      #060A12 !important;
  }}

  .block-container {{
    padding: 0 !important;
    max-width: 480px !important;
    min-height: 100svh;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 0 !important;
  }}

  /* Logo */
  .hs-logo {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 6px;
    text-transform: uppercase;
    color: #1E293B;
    text-align: center;
    margin-bottom: 80px;
  }}

  /* Label boven de knop */
  .hs-label {{
    font-size: 15px;
    font-weight: 400;
    color: #334155;
    letter-spacing: 0.5px;
    text-align: center;
    margin-bottom: 40px;
  }}

  /* De knop zelf */
  [data-testid="stCustomComponentV1"] {{
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
  }}

  [data-testid="stCustomComponentV1"] button {{
    width: 240px !important;
    height: 240px !important;
    border-radius: 50% !important;

    /* Rijke rode gradiënt */
    background:
      radial-gradient(circle at 38% 32%, rgba(255,120,120,0.35), transparent 55%),
      radial-gradient(circle at 65% 70%, rgba(100,0,0,0.5), transparent 50%),
      linear-gradient(145deg, #E53E3E 0%, #9B1C1C 100%) !important;

    /* Verberg het emoji-lettertype, toon de SVG mic */
    color: transparent !important;
    font-size: 0 !important;
    background-image:
      url("{MIC_SVG}"),
      radial-gradient(circle at 38% 32%, rgba(255,120,120,0.35), transparent 55%),
      radial-gradient(circle at 65% 70%, rgba(100,0,0,0.5), transparent 50%),
      linear-gradient(145deg, #E53E3E 0%, #9B1C1C 100%) !important;
    background-repeat: no-repeat, no-repeat, no-repeat, no-repeat !important;
    background-position: center, center, center, center !important;
    background-size: 42%, auto, auto, auto !important;

    border: none !important;
    padding: 0 !important;
    letter-spacing: 0 !important;

    box-shadow:
      0 0 0 1px rgba(255,255,255,0.06) inset,
      0 24px 80px rgba(220,38,38,0.45),
      0 8px 32px rgba(0,0,0,0.7) !important;

    animation: breathe 3s ease-in-out infinite !important;
    transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    cursor: pointer !important;
    -webkit-tap-highlight-color: transparent !important;
  }}

  [data-testid="stCustomComponentV1"] button:hover {{
    transform: scale(1.06) !important;
  }}

  [data-testid="stCustomComponentV1"] button:active {{
    transform: scale(0.93) !important;
    animation: none !important;
    box-shadow:
      0 0 0 1px rgba(255,255,255,0.06) inset,
      0 0 0 40px rgba(220,38,38,0.08),
      0 8px 32px rgba(0,0,0,0.7) !important;
  }}

  /* Statusschermen */
  .hs-status {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 0 40px;
  }}
  .hs-status-icon {{
    font-size: 72px;
    margin-bottom: 24px;
    line-height: 1;
  }}
  .hs-status-title {{
    font-size: 28px;
    font-weight: 300;
    letter-spacing: -0.5px;
    margin-bottom: 10px;
  }}
  .hs-status-sub {{
    font-size: 14px;
    color: #1E293B;
    letter-spacing: 0.3px;
  }}

  .hs-done .hs-status-title  {{ color: #34D399; }}
  .hs-error .hs-status-title {{ color: #F87171; }}

  .hs-error-detail {{
    margin-top: 20px;
    background: #0A0505;
    border: 1px solid #2D1010;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 12px;
    color: #5C2020;
    font-family: monospace;
    word-break: break-all;
    max-width: 360px;
  }}

  /* Knop onderaan */
  .stButton {{ display: flex; justify-content: center; margin-top: 48px; }}
  .stButton > button {{
    background: transparent !important;
    border: 1px solid #1A2535 !important;
    color: #2D3F55 !important;
    border-radius: 999px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 14px 36px !important;
    width: auto !important;
    box-shadow: none !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
  }}
  .stButton > button:hover {{
    border-color: #2D3F55 !important;
    color: #4A6080 !important;
  }}

  [data-testid="stSpinner"] {{ display: flex; justify-content: center; }}
  [data-testid="stSpinner"] > div {{
    width: 44px !important; height: 44px !important;
    border-width: 3px !important;
    border-color: #DC2626 transparent transparent transparent !important;
  }}
</style>
""")

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hs-logo">Hersenspinsel</div>', unsafe_allow_html=True)

phase = st.session_state.phase

if phase == "idle":
    st.markdown('<div class="hs-label">Tik om op te nemen</div>', unsafe_allow_html=True)
    text = speech_to_text(
        language="nl-NL",
        start_prompt="🎙",
        stop_prompt="⏹",
        just_once=True,
        use_container_width=False,
        key="stt",
    )
    if text and text.strip():
        st.session_state.raw_text = text.strip()
        st.session_state.phase = "processing"
        st.rerun()

elif phase == "processing":
    st.markdown("""
    <div class="hs-status">
      <div class="hs-status-title" style="color:#94A3B8;">Verwerken…</div>
      <div class="hs-status-sub">Even geduld</div>
    </div>
    """, unsafe_allow_html=True)
    with st.spinner(""):
        try:
            gestructureerd = structureer(st.session_state.raw_text)
            body = f"{gestructureerd}\n\n---\n\nLetterlijke opname:\n{st.session_state.raw_text}"
            verstuur_email("Hersenspinsels", body)
            st.session_state.phase = "done"
        except Exception as e:
            st.session_state.error_msg = str(e)
            st.session_state.phase = "error"
    st.rerun()

elif phase == "done":
    st.markdown("""
    <div class="hs-status hs-done">
      <div class="hs-status-icon">✓</div>
      <div class="hs-status-title">Verstuurd</div>
      <div class="hs-status-sub">Je mail is onderweg</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Nieuwe opname"):
        st.session_state.phase = "idle"
        st.session_state.raw_text = ""
        st.rerun()
    components.html("""
    <script>setTimeout(function(){window.parent.location.reload();},5000);</script>
    """, height=0)

elif phase == "error":
    st.markdown(f"""
    <div class="hs-status hs-error">
      <div class="hs-status-icon">⚠</div>
      <div class="hs-status-title">Er ging iets mis</div>
      <div class="hs-error-detail">{st.session_state.error_msg}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Opnieuw proberen"):
        st.session_state.phase = "idle"
        st.rerun()
