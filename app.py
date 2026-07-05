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


# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">
<style>
  #MainMenu, footer, header, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"] {
    display: none !important;
  }

  html, body, [data-testid="stAppViewContainer"] {
    background: #080D1A !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
    color: #E2E8F0;
  }

  .block-container {
    padding: 0 24px !important;
    max-width: 440px !important;
    min-height: 100svh;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
  }

  .hs-wordmark {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: #334155;
    text-align: center;
    margin-bottom: 72px;
  }

  .hs-status {
    font-size: 20px;
    font-weight: 300;
    color: #64748B;
    text-align: center;
    margin-bottom: 52px;
    line-height: 1.6;
    min-height: 64px;
  }

  .hs-ring {
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(239,68,68,0.10) 0%, transparent 70%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 52px auto;
  }

  [data-testid="stCustomComponentV1"] {
    display: flex !important;
    justify-content: center !important;
    width: 100% !important;
  }

  [data-testid="stCustomComponentV1"] button {
    width: 160px !important;
    height: 160px !important;
    border-radius: 50% !important;
    background: linear-gradient(145deg, #EF4444 0%, #B91C1C 100%) !important;
    color: white !important;
    border: none !important;
    font-size: 54px !important;
    font-weight: 400 !important;
    line-height: 1 !important;
    padding: 0 !important;
    letter-spacing: 0 !important;
    box-shadow:
      0 0 0 12px rgba(239,68,68,0.08),
      0 0 0 28px rgba(239,68,68,0.04),
      0 20px 60px rgba(239,68,68,0.35) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
    cursor: pointer !important;
  }

  [data-testid="stCustomComponentV1"] button:hover {
    transform: scale(1.05) !important;
    box-shadow:
      0 0 0 16px rgba(239,68,68,0.10),
      0 0 0 36px rgba(239,68,68,0.05),
      0 24px 72px rgba(239,68,68,0.45) !important;
  }

  [data-testid="stCustomComponentV1"] button:active {
    transform: scale(0.97) !important;
  }

  .hs-hint {
    font-size: 13px;
    color: #1E293B;
    text-align: center;
    letter-spacing: 0.5px;
    margin-top: -36px;
  }

  .hs-done {
    width: 100%;
    background: #0C1929;
    border: 1px solid #1E3A5F;
    border-radius: 24px;
    padding: 48px 32px;
    text-align: center;
    margin-bottom: 32px;
  }
  .hs-done-icon { font-size: 56px; margin-bottom: 16px; line-height: 1; }
  .hs-done-title { font-size: 24px; font-weight: 500; color: #38BDF8; margin-bottom: 8px; }
  .hs-done-sub { font-size: 14px; color: #334155; }

  .hs-error {
    width: 100%;
    background: #160A0A;
    border: 1px solid #3F1515;
    border-radius: 24px;
    padding: 28px 24px;
    text-align: center;
    color: #FCA5A5;
    font-size: 14px;
    margin-bottom: 24px;
    line-height: 1.6;
  }

  .stButton { display: flex; justify-content: center; }
  .stButton > button {
    background: transparent !important;
    border: 1px solid #1E293B !important;
    color: #475569 !important;
    border-radius: 999px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    padding: 12px 28px !important;
    width: auto !important;
    box-shadow: none !important;
    letter-spacing: 0.2px !important;
    transition: border-color 0.15s, color 0.15s !important;
  }
  .stButton > button:hover {
    border-color: #334155 !important;
    color: #94A3B8 !important;
  }

  [data-testid="stSpinner"] > div {
    border-color: #3B82F6 transparent transparent transparent !important;
  }
</style>
""", unsafe_allow_html=True)

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hs-wordmark">Hersenspinsel</div>', unsafe_allow_html=True)

phase = st.session_state.phase

if phase == "idle":
    st.markdown(
        '<div class="hs-status">Tik en spreek je<br>gedachten in</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hs-ring">', unsafe_allow_html=True)
    text = speech_to_text(
        language="nl-NL",
        start_prompt="🎙",
        stop_prompt="⏹",
        just_once=True,
        use_container_width=False,
        key="stt",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="hs-hint">tik om op te nemen</div>', unsafe_allow_html=True)

    if text and text.strip():
        st.session_state.raw_text = text.strip()
        st.session_state.phase = "processing"
        st.rerun()

elif phase == "processing":
    st.markdown(
        '<div class="hs-status">Verwerken en<br>versturen…</div>',
        unsafe_allow_html=True,
    )
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

elif phase == "done":
    st.markdown("""
    <div class="hs-done">
      <div class="hs-done-icon">✓</div>
      <div class="hs-done-title">Verstuurd</div>
      <div class="hs-done-sub">Je mail is onderweg</div>
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

elif phase == "error":
    st.markdown(
        f'<div class="hs-error">⚠ {st.session_state.error_msg}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Opnieuw proberen"):
        st.session_state.phase = "idle"
        st.rerun()
