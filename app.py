import streamlit as st
import streamlit.components.v1 as components
import anthropic
import urllib.parse

st.set_page_config(
    page_title="Hersenspinsel",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- Styling ---
st.markdown(
    """
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%A7%A0%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hersenspinsel">

<style>
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 520px !important;
    }
    .app-title {
        font-size: 32px; font-weight: 700; color: #0F172A;
        text-align: center; margin-bottom: 4px; letter-spacing: -0.5px;
    }
    .app-subtitle {
        font-size: 15px; color: #64748B; text-align: center;
        margin-bottom: 24px; font-weight: 400;
    }

    /* Reset/secundaire knop */
    .stButton > button {
        background: white !important; color: #475569 !important;
        border: 1px solid #E2E8F0 !important; border-radius: 14px !important;
        padding: 16px !important; font-size: 15px !important;
        font-weight: 500 !important; width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }

    .result-card {
        background: white; border-radius: 20px; padding: 24px;
        margin-top: 24px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.08);
        border: 1px solid #E2E8F0;
    }
    .result-card h3 {
        margin-top: 0; font-size: 13px; text-transform: uppercase;
        letter-spacing: 1px; color: #64748B; font-weight: 600;
    }

    .mail-button {
        display: flex; align-items: center; justify-content: center; gap: 8px;
        width: 100%; height: 64px;
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white !important; text-decoration: none !important;
        font-size: 18px; font-weight: 600; border-radius: 16px;
        margin-top: 16px; box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    }
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


# --- Header ---
st.markdown('<div class="app-title">🧠 Hersenspinsel</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Tik op de knop, spreek je gedachten in, klaar.</div>',
    unsafe_allow_html=True,
)

# Init state
if "structured" not in st.session_state:
    st.session_state["structured"] = ""
if "raw_text" not in st.session_state:
    st.session_state["raw_text"] = ""

# Lees query param (komt binnen via custom HTML knop hieronder)
qp_text = st.query_params.get("spinsel", "")
if qp_text and qp_text != st.session_state.get("raw_text", ""):
    st.session_state["raw_text"] = qp_text
    st.query_params.clear()
    api_key = get_api_key()
    if not api_key:
        st.error("API key niet gevonden — check de Streamlit-secrets.")
    else:
        with st.spinner("Even structureren…"):
            try:
                st.session_state["structured"] = structureer_als_todo(api_key, qp_text)
            except Exception as e:
                st.error(f"Fout: {e}")

# --- DE GROTE RONDE OPNAMEKNOP (volledig custom HTML/JS) ---
components.html(
    """
<!DOCTYPE html>
<html>
<head>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 30px 0 20px 0; background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    display: flex; flex-direction: column; align-items: center;
  }
  #micbtn {
    width: 240px; height: 240px; border-radius: 50%;
    background: linear-gradient(145deg, #EF4444 0%, #DC2626 100%);
    color: white; border: none; font-size: 96px;
    line-height: 1; cursor: pointer;
    box-shadow: 0 20px 50px rgba(220, 38, 38, 0.35);
    transition: transform 0.15s ease;
    animation: pulse 2.5s ease-out infinite;
    display: flex; align-items: center; justify-content: center;
    -webkit-tap-highlight-color: transparent;
  }
  @keyframes pulse {
    0%   { box-shadow: 0 20px 50px rgba(220,38,38,0.35), 0 0 0 0 rgba(239,68,68,0.5); }
    70%  { box-shadow: 0 20px 50px rgba(220,38,38,0.35), 0 0 0 30px rgba(239,68,68,0); }
    100% { box-shadow: 0 20px 50px rgba(220,38,38,0.35), 0 0 0 0 rgba(239,68,68,0); }
  }
  #micbtn:active { transform: scale(0.95); }
  #micbtn.recording {
    background: linear-gradient(145deg, #1F2937 0%, #111827 100%);
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    animation: recording-pulse 1.2s ease-out infinite;
  }
  @keyframes recording-pulse {
    0%   { box-shadow: 0 20px 50px rgba(0,0,0,0.4), 0 0 0 0 rgba(220,38,38,0.7); }
    100% { box-shadow: 0 20px 50px rgba(0,0,0,0.4), 0 0 0 40px rgba(220,38,38,0); }
  }
  #status {
    margin-top: 20px; color: #64748B; font-size: 14px;
    min-height: 22px; text-align: center; max-width: 320px;
    padding: 0 16px;
  }
</style>
</head>
<body>
  <button id="micbtn">🎙</button>
  <div id="status">Tik om te beginnen</div>
  <script>
    const btn = document.getElementById('micbtn');
    const status = document.getElementById('status');
    let recognition = null;
    let recording = false;
    let fullText = '';
    let interimText = '';
    let manuallyStopped = false;

    function handleTap(e) {
      if (e) e.preventDefault();
      if (!recording) startRec(); else stopRec();
    }
    btn.addEventListener('click', handleTap);
    btn.addEventListener('touchend', handleTap);

    function startRec() {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) {
        status.textContent = '❌ Spraakherkenning niet ondersteund. Gebruik Safari op iPhone.';
        return;
      }
      recognition = new SR();
      recognition.lang = 'nl-NL';
      // continuous=false werkt veel betrouwbaarder op iOS Safari
      recognition.continuous = false;
      recognition.interimResults = true;
      fullText = '';
      interimText = '';
      manuallyStopped = false;

      recognition.onresult = (e) => {
        interimText = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) fullText += e.results[i][0].transcript + ' ';
          else interimText += e.results[i][0].transcript;
        }
        const display = (fullText + interimText).trim();
        status.textContent = display.length > 80 ? '...' + display.slice(-80) : display;
      };

      recognition.onerror = (e) => {
        if (e.error === 'no-speech' || e.error === 'aborted') return;
        status.textContent = 'Fout: ' + e.error + '. Probeer opnieuw.';
        recording = false;
        btn.textContent = '🎙';
        btn.classList.remove('recording');
      };

      recognition.onend = () => {
        // Auto-stop na pauze OF handmatig gestopt → verwerken
        if (recording) finishRec();
      };

      try { recognition.start(); } catch(e) {
        status.textContent = 'Kon niet starten: ' + e.message;
        return;
      }
      recording = true;
      btn.textContent = '⏹';
      btn.classList.add('recording');
      status.textContent = '🔴 Aan het luisteren — tik om te stoppen';
    }

    function stopRec() {
      manuallyStopped = true;
      // Gebruik stop() zodat pending resultaten gefinaliseerd worden
      if (recognition) {
        try {
          recognition.onend = () => finishRec();
          recognition.stop();
        } catch(e) {
          finishRec();
        }
      } else {
        finishRec();
      }
      // Veiligheidsnet: als stop niet snel genoeg een onend triggert, alsnog finishen
      setTimeout(() => { if (recording) finishRec(); }, 600);
    }

    function finishRec() {
      if (!recording) return;  // voorkom dubbele uitvoer
      recording = false;
      btn.textContent = '⏳';
      btn.classList.remove('recording');
      status.textContent = 'Verwerken...';

      // Combineer finale + nog-niet-finale tekst
      const text = (fullText + ' ' + interimText).trim();
      if (!text) {
        status.textContent = 'Niets opgenomen. Probeer opnieuw.';
        btn.textContent = '🎙';
        return;
      }

      const url = new URL(window.parent.location.href);
      url.searchParams.set('spinsel', text);
      window.parent.location.href = url.toString();
    }
  </script>
</body>
</html>
""",
    height=360,
)

# --- Resultaat tonen ---
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
