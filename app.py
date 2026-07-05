import streamlit as st
import streamlit.components.v1 as components
import anthropic
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


# ── Transcript via URL-parameter ──────────────────────────────────────────────
transcript = st.query_params.get("transcript", "")
if transcript and st.session_state.phase == "idle":
    st.query_params.clear()
    st.session_state.raw_text = transcript
    st.session_state.phase = "processing"
    st.rerun()

# ── Globale stijlen ────────────────────────────────────────────────────────────
st.html("""
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">
<style>
  #MainMenu, footer, header, .stDeployButton,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { display:none !important; }

  html, body {
    background: #060A12 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', sans-serif;
  }

  @keyframes hs-aurora {
    0%,100% { background-position: 0% 0%, 100% 100%, 50% 50%, 0 0; }
    50%     { background-position: 30% 20%, 70% 80%, 40% 60%, 0 0; }
  }
  [data-testid="stAppViewContainer"] {
    background:
      radial-gradient(ellipse 60% 45% at 20% 10%, rgba(220,38,38,0.28) 0%, transparent 60%),
      radial-gradient(ellipse 55% 45% at 85% 85%, rgba(99,60,240,0.22) 0%, transparent 60%),
      radial-gradient(ellipse 70% 55% at 60% 40%, rgba(20,50,120,0.25) 0%, transparent 65%),
      linear-gradient(160deg, #0B0F1E 0%, #060A12 55%, #0D0714 100%) !important;
    background-size: 160% 160%, 160% 160%, 180% 180%, 100% 100% !important;
    animation: hs-aurora 16s ease-in-out infinite;
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

  .hs-logo {
    font-size: 13px; font-weight: 700; letter-spacing: 7px;
    text-transform: uppercase; text-align: center; margin-bottom: 14px;
    background: linear-gradient(90deg, #F87171, #C084FC, #60A5FA);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; color: transparent;
  }
  .hs-exclusive {
    display: inline-block; margin: 0 auto 64px auto;
    font-size: 11px; font-weight: 600; letter-spacing: 2.5px;
    text-transform: uppercase; color: #CBD5E1;
    padding: 8px 20px; border-radius: 999px;
    border: 1px solid rgba(200,132,252,0.35);
    background: linear-gradient(90deg, rgba(220,38,38,0.14), rgba(99,60,240,0.14));
    box-shadow: 0 0 24px rgba(150,60,220,0.15);
  }
  .hs-header { text-align: center; }

  .hs-status {
    display:flex; flex-direction:column; align-items:center;
    text-align:center; padding:0 40px;
  }
  .hs-status-icon  { font-size:72px; margin-bottom:24px; line-height:1; }
  .hs-status-title { font-size:28px; font-weight:300; letter-spacing:-0.5px; margin-bottom:10px; }
  .hs-status-sub   { font-size:14px; color:#1E293B; }

  @keyframes hs-pop {
    0%   { transform: scale(0.6); opacity: 0; }
    70%  { transform: scale(1.08); }
    100% { transform: scale(1); opacity: 1; }
  }
  .hs-done { animation: hs-pop 0.45s cubic-bezier(0.34,1.56,0.64,1); }
  .hs-done .hs-status-icon {
    width: 110px; height: 110px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 56px; color: #fff; font-weight: 700;
    background: linear-gradient(145deg, #34D399 0%, #059669 100%);
    box-shadow: 0 0 60px rgba(52,211,153,0.45), 0 12px 40px rgba(0,0,0,0.6);
  }
  .hs-done .hs-status-title {
    color: #34D399; font-size: 36px; font-weight: 700; letter-spacing: -0.5px;
  }
  .hs-done .hs-status-sub { font-size: 16px; color: #94A3B8; }
  .hs-error .hs-status-title { color:#F87171; }
  .hs-error-detail {
    margin-top:20px; background:#0A0505; border:1px solid #2D1010;
    border-radius:12px; padding:14px 18px; font-size:12px;
    color:#5C2020; font-family:monospace; word-break:break-all; max-width:360px;
  }

  .stButton { display:flex; justify-content:center; margin-top:48px; }
  .stButton > button {
    background:transparent !important; border:1px solid #1A2535 !important;
    color:#2D3F55 !important; border-radius:999px !important; font-size:14px !important;
    font-weight:500 !important; padding:14px 36px !important; width:auto !important;
    box-shadow:none !important; letter-spacing:0.3px !important;
  }
  .stButton > button:hover { border-color:#2D3F55 !important; color:#4A6080 !important; }

  [data-testid="stSpinner"] { display:flex; justify-content:center; }
  [data-testid="stSpinner"] > div {
    width:44px !important; height:44px !important; border-width:3px !important;
    border-color:#DC2626 transparent transparent transparent !important;
  }
</style>
""")

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hs-header">
  <div class="hs-logo">Hersenspinsel</div>
  <div class="hs-exclusive">✦ Exclusief voor Martin Dekker ✦</div>
</div>
""", unsafe_allow_html=True)

phase = st.session_state.phase

# ── Idle: eigen opnameknop via HTML/JS + Web Speech API ───────────────────────
if phase == "idle":
    components.html("""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  @keyframes pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(220,38,38,0.6), 0 24px 80px rgba(220,38,38,0.45); }
    60%      { box-shadow: 0 0 0 36px rgba(220,38,38,0), 0 24px 80px rgba(220,38,38,0.45); }
  }
  @keyframes stop-pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(30,100,255,0.5), 0 24px 80px rgba(30,80,200,0.4); }
    60%      { box-shadow: 0 0 0 36px rgba(30,100,255,0), 0 24px 80px rgba(30,80,200,0.4); }
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
    overflow: hidden;
  }

  #label {
    font-size: 22px;
    font-weight: 600;
    color: #F1F5F9;
    letter-spacing: 0.3px;
    margin-bottom: 44px;
    transition: color 0.3s;
    text-shadow: 0 2px 12px rgba(0,0,0,0.6);
  }
  #label.recording { color: #93C5FD; }

  #btn {
    width: 260px;
    height: 260px;
    border-radius: 50%;
    border: none;
    cursor: pointer;
    outline: none;
    -webkit-tap-highlight-color: transparent;
    position: relative;
    transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1);

    background:
      url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='9' y='2' width='6' height='12' rx='3'/%3E%3Cpath d='M5 10a7 7 0 0 0 14 0'/%3E%3Cline x1='12' y1='17' x2='12' y2='21'/%3E%3Cline x1='8' y1='21' x2='16' y2='21'/%3E%3C/svg%3E") no-repeat center / 40%,
      radial-gradient(circle at 35% 32%, rgba(255,120,120,0.3), transparent 55%),
      linear-gradient(145deg, #E53E3E 0%, #9B1C1C 100%);

    box-shadow:
      0 0 0 1px rgba(255,255,255,0.06) inset,
      0 24px 80px rgba(220,38,38,0.45),
      0 8px 32px rgba(0,0,0,0.8);

    animation: pulse 2.8s ease-in-out infinite;
  }

  #btn.recording {
    background:
      url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Crect x='6' y='6' width='12' height='12' rx='2'/%3E%3C/svg%3E") no-repeat center / 36%,
      radial-gradient(circle at 35% 32%, rgba(120,160,255,0.3), transparent 55%),
      linear-gradient(145deg, #3B6EF0 0%, #1A3AA0 100%);

    box-shadow:
      0 0 0 1px rgba(255,255,255,0.06) inset,
      0 24px 80px rgba(30,80,200,0.45),
      0 8px 32px rgba(0,0,0,0.8);

    animation: stop-pulse 1.4s ease-in-out infinite;
  }

  #btn:hover  { transform: scale(1.06); }
  #btn:active { transform: scale(0.93); animation: none !important; }

  #interim {
    margin-top: 32px;
    font-size: 15px;
    color: #94A3B8;
    text-align: center;
    max-width: 280px;
    min-height: 20px;
    letter-spacing: 0.2px;
    font-style: italic;
  }
</style>
</head>
<body>
  <div id="label">Tik om op te nemen</div>
  <button id="btn"></button>
  <div id="interim"></div>

<script>
  var btn      = document.getElementById('btn');
  var label    = document.getElementById('label');
  var interim  = document.getElementById('interim');
  var isRecording = false;
  var recognition = null;
  var finalText = '';

  // Controleer browser-ondersteuning
  var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    label.textContent = 'Spraakherkenning niet beschikbaar in deze browser';
    btn.disabled = true;
  } else {
    recognition = new SpeechRecognition();
    recognition.lang = 'nl-NL';
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function(e) {
      finalText = '';
      var interimText = '';
      for (var i = 0; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript + ' ';
        else interimText += e.results[i][0].transcript;
      }
      interim.textContent = interimText || finalText;
    };

    recognition.onerror = function(e) {
      console.error('Speech error', e.error);
      stopRecording();
    };

    recognition.onend = function() {
      if (isRecording) stopRecording();
    };
  }

  function startRecording() {
    isRecording = true;
    finalText = '';
    btn.classList.add('recording');
    label.textContent = 'Tik om te stoppen';
    label.classList.add('recording');
    interim.textContent = '';
    recognition.start();
  }

  function stopRecording() {
    isRecording = false;
    btn.classList.remove('recording');
    label.textContent = 'Even geduld…';
    label.classList.remove('recording');
    try { recognition.stop(); } catch(e) {}

    var text = finalText.trim();
    if (text) {
      // Stuur transcript naar Streamlit via URL-parameter
      window.parent.location.href =
        window.parent.location.pathname +
        '?transcript=' + encodeURIComponent(text);
    } else {
      label.textContent = 'Niets gehoord — probeer opnieuw';
      setTimeout(function() { label.textContent = 'Tik om op te nemen'; }, 2000);
    }
  }

  btn.addEventListener('click', function() {
    if (!recognition) return;
    if (isRecording) stopRecording();
    else startRecording();
  });
</script>
</body>
</html>
""", height=440, scrolling=False)

# ── Processing ─────────────────────────────────────────────────────────────────
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

# ── Done ───────────────────────────────────────────────────────────────────────
elif phase == "done":
    st.markdown("""
    <div class="hs-status hs-done">
      <div class="hs-status-icon">✓</div>
      <div class="hs-status-title">Mail verzonden!</div>
      <div class="hs-status-sub">Je hersenspinsels staan in je zakelijke inbox</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Nieuwe opname"):
        st.session_state.phase = "idle"
        st.session_state.raw_text = ""
        st.rerun()
    components.html("<script>setTimeout(function(){window.parent.location.reload();},5000);</script>", height=0)

# ── Error ──────────────────────────────────────────────────────────────────────
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
