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


st.html("""
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">
<style>
  @keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.5), 0 32px 80px rgba(239,68,68,0.4); }
    70%  { box-shadow: 0 0 0 32px rgba(239,68,68,0), 0 32px 80px rgba(239,68,68,0.4); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0), 0 32px 80px rgba(239,68,68,0.4); }
  }

  #MainMenu, footer, header, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] {
    display: none !important;
  }

  html, body {
    background: #05090F !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
  }

  [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse 80% 60% at 50% 0%, #1a0a0a 0%, #05090F 60%) !important;
  }

  .block-container {
    padding: 0 !important;
    max-width: 480px !important;
    min-height: 100svh;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
  }

  /* Header */
  .hs-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 64px;
  }
  .hs-logo {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 5px;
    text-transform: uppercase;
    color: #1E293B;
    margin-bottom: 0;
  }

  /* Mic button area */
  .hs-mic-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 32px;
    margin-bottom: 56px;
  }

  .hs-label {
    font-size: 16px;
    font-weight: 400;
    color: #475569;
    letter-spacing: 0.3px;
    text-align: center;
  }

  /* The mic button via the custom component */
  [data-testid="stCustomComponentV1"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
  }

  [data-testid="stCustomComponentV1"] button {
    width: 200px !important;
    height: 200px !important;
    border-radius: 50% !important;
    background: radial-gradient(circle at 35% 35%, #FF6B6B, #C0392B) !important;
    color: white !important;
    border: none !important;
    font-size: 72px !important;
    font-weight: 400 !important;
    line-height: 1 !important;
    padding: 0 !important;
    letter-spacing: 0 !important;
    box-shadow:
      0 0 0 1px rgba(255,255,255,0.05) inset,
      0 32px 80px rgba(239,68,68,0.4),
      0 8px 24px rgba(0,0,0,0.6) !important;
    transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
    cursor: pointer !important;
    -webkit-tap-highlight-color: transparent !important;
  }

  [data-testid="stCustomComponentV1"] button:hover {
    transform: scale(1.07) !important;
  }

  [data-testid="stCustomComponentV1"] button:active {
    transform: scale(0.94) !important;
    animation: pulse 1s ease-out infinite !important;
  }

  /* Status states */
  .hs-status {
    text-align: center;
    padding: 0 32px;
  }
  .hs-status-icon {
    font-size: 64px;
    margin-bottom: 20px;
    line-height: 1;
  }
  .hs-status-title {
    font-size: 26px;
    font-weight: 300;
    color: #94A3B8;
    margin-bottom: 8px;
    letter-spacing: -0.3px;
  }
  .hs-status-sub {
    font-size: 14px;
    color: #1E293B;
    letter-spacing: 0.2px;
  }

  /* Done state */
  .hs-done-title { color: #34D399 !important; }

  /* Error state */
  .hs-error-title { color: #F87171 !important; }
  .hs-error-detail {
    background: #0F0A0A;
    border: 1px solid #2D1515;
    border-radius: 12px;
    padding: 16px 20px;
    margin-top: 20px;
    font-size: 13px;
    color: #7F1D1D;
    font-family: monospace;
    word-break: break-all;
  }

  /* Secondary button */
  .stButton { display: flex; justify-content: center; margin-top: 40px; }
  .stButton > button {
    background: transparent !important;
    border: 1px solid #1E293B !important;
    color: #334155 !important;
    border-radius: 999px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 14px 32px !important;
    width: auto !important;
    box-shadow: none !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
  }
  .stButton > button:hover {
    border-color: #334155 !important;
    color: #64748B !important;
    background: #0D1520 !important;
  }

  /* Spinner */
  [data-testid="stSpinner"] { display: flex; justify-content: center; }
  [data-testid="stSpinner"] > div {
    width: 40px !important;
    height: 40px !important;
    border-width: 3px !important;
    border-color: #EF4444 transparent transparent transparent !important;
  }
</style>
""")

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hs-header"><div class="hs-logo">Hersenspinsel</div></div>', unsafe_allow_html=True)

phase = st.session_state.phase

# ── Idle ─────────────────────────────────────────────────────────────────────
if phase == "idle":
    st.markdown('<div class="hs-label">Spreek je gedachten in</div>', unsafe_allow_html=True)

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

# ── Processing ────────────────────────────────────────────────────────────────
elif phase == "processing":
    st.markdown("""
    <div class="hs-status">
      <div class="hs-status-title">Verwerken…</div>
      <div class="hs-status-sub">Even geduld</div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner(""):
        try:
            gestructureerd = structureer(st.session_state.raw_text)
            body = (
                f"{gestructureerd}"
                f"\n\n---\n\nLetterlijke opname:\n{st.session_state.raw_text}"
            )
            verstuur_email("Hersenspinsels", body)
            st.session_state.phase = "done"
        except Exception as e:
            st.session_state.error_msg = str(e)
            st.session_state.phase = "error"
    st.rerun()

# ── Done ──────────────────────────────────────────────────────────────────────
elif phase == "done":
    st.markdown("""
    <div class="hs-status">
      <div class="hs-status-icon">✓</div>
      <div class="hs-status-title hs-done-title">Verstuurd</div>
      <div class="hs-status-sub">Je mail is onderweg</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Nieuwe opname"):
        st.session_state.phase = "idle"
        st.session_state.raw_text = ""
        st.rerun()

    components.html("""
    <script>
      setTimeout(function() { window.parent.location.reload(); }, 5000);
    </script>
    """, height=0)

# ── Error ─────────────────────────────────────────────────────────────────────
elif phase == "error":
    st.markdown(f"""
    <div class="hs-status">
      <div class="hs-status-icon">⚠</div>
      <div class="hs-status-title hs-error-title">Er ging iets mis</div>
      <div class="hs-error-detail">{st.session_state.error_msg}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Opnieuw proberen"):
        st.session_state.phase = "idle"
        st.rerun()
