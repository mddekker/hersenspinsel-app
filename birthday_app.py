import json
import urllib.parse
from datetime import date, datetime

import anthropic
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Verjaardagen",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8E%82%3C/text%3E%3C/svg%3E">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Verjaardagen">
<style>
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 4rem !important; max-width: 520px !important; }
    .app-title { font-size: 32px; font-weight: 700; color: #0F172A; text-align: center; margin-bottom: 4px; letter-spacing: -0.5px; }
    .app-subtitle { font-size: 15px; color: #64748B; text-align: center; margin-bottom: 24px; font-weight: 400; }
    .message-card { background: white; border-radius: 20px; padding: 24px; margin-top: 16px;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08); border: 1px solid #E2E8F0;
        white-space: pre-wrap; line-height: 1.6; font-size: 15px; color: #0F172A; }
    .section-header { font-size: 13px; font-weight: 600; color: #94A3B8; text-transform: uppercase;
        letter-spacing: 1px; margin: 20px 0 10px 0; }
    .stButton > button { background: white !important; color: #475569 !important;
        border: 1px solid #E2E8F0 !important; border-radius: 14px !important; padding: 14px !important;
        font-size: 15px !important; font-weight: 500 !important; width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important; }
    .primary-btn > button { background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important; border: none !important; box-shadow: 0 8px 24px rgba(99,102,241,0.3) !important; }
    .danger-btn > button { color: #EF4444 !important; }
    div[data-testid="stForm"] { background: white; border-radius: 20px; padding: 20px;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08); border: 1px solid #E2E8F0; }
    .stTextInput input, .stTextArea textarea { border-radius: 10px !important; border-color: #E2E8F0 !important; font-size: 16px !important; }
    [data-baseweb="tab-list"] { background: #F1F5F9 !important; border-radius: 14px !important; padding: 4px !important; gap: 4px !important; }
    [data-baseweb="tab"] { border-radius: 10px !important; font-size: 14px !important; font-weight: 500 !important; }
    [aria-selected="true"][data-baseweb="tab"] { background: white !important; box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important; }
</style>
""",
    unsafe_allow_html=True,
)

STORAGE_KEY = "verjaardagen_v1"


def storage_bridge() -> str:
    """Renders a hidden component that reads localStorage and returns JSON via query param."""
    return components.html(
        f"""
<script>
(function() {{
  const data = localStorage.getItem('{STORAGE_KEY}') || '[]';
  // Write to parent URL so Streamlit can read it via query_params
  const url = new URL(window.parent.location.href);
  if (url.searchParams.get('_bd') !== data) {{
    url.searchParams.set('_bd', data);
    window.parent.history.replaceState(null, '', url.toString());
  }}
}})();
</script>
""",
        height=0,
    )


def save_to_storage(birthdays: list[dict]):
    """Saves birthdays list to localStorage via a hidden form/script."""
    encoded = json.dumps(birthdays, ensure_ascii=False)
    safe = encoded.replace("\\", "\\\\").replace("`", "\\`")
    components.html(
        f"""
<script>
localStorage.setItem('{STORAGE_KEY}', `{safe}`);
</script>
""",
        height=0,
    )


def load_birthdays() -> list[dict]:
    raw = st.query_params.get("_bd", "")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def days_until(month: int, day: int) -> int:
    today = date.today()
    bd = date(today.year, month, day)
    if bd < today:
        bd = date(today.year + 1, month, day)
    return (bd - today).days


def next_age(birth_year: int | None, month: int, day: int) -> int | None:
    if not birth_year:
        return None
    today = date.today()
    bd = date(today.year, month, day)
    return (today.year + (0 if bd >= today else 1)) - birth_year


def get_api_key() -> str:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return ""


def generate_message(person: dict, style: str, extras: str) -> str:
    api_key = get_api_key()
    if not api_key:
        st.error("API key niet gevonden — check de Streamlit-secrets.")
        return ""
    client = anthropic.Anthropic(api_key=api_key)
    age = next_age(person.get("birth_year"), person["month"], person["day"])
    notes = person.get("notes", "").strip()
    prompt = f"""Schrijf een persoonlijk verjaardagsbericht voor {person['name']}.

Details:
- Relatie: {person.get('relationship', 'bekende')}
{f'- Wordt {age} jaar' if age else ''}
- Toon: {style}
{f'- Persoonlijke info: {notes}' if notes else ''}
{f'- Extra aanwijzingen: {extras}' if extras else ''}

Schrijf alleen het bericht zelf, klaar om te versturen. Geen uitleg of inleiding. Gebruik Nederlands."""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# --- Session state ---
for k, v in [("view", "list"), ("sel", None), ("msg", ""), ("edit", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# Read birthdays from localStorage (via query param written by JS)
storage_bridge()
birthdays: list[dict] = load_birthdays()

st.markdown('<div class="app-title">🎂 Verjaardagen</div>', unsafe_allow_html=True)

RELATIONSHIPS = ["Partner", "Kind", "Ouder", "Broer/Zus", "Vriend/Vriendin", "Collega", "Familielid", "Overig"]

# ================================================================
# LIST VIEW
# ================================================================
if st.session_state.view == "list":
    st.markdown('<div class="app-subtitle">Nooit meer een verjaardag vergeten.</div>', unsafe_allow_html=True)

    tab_soon, tab_all = st.tabs(["📅 Aankomend", "📋 Alle"])

    def bd_button(bd: dict, prefix: str):
        days = days_until(bd["month"], bd["day"])
        age = next_age(bd.get("birth_year"), bd["month"], bd["day"])
        age_str = f" · wordt {age}" if age else ""
        when = "🎉 Vandaag!" if days == 0 else f"Nog {days} dag(en)"
        label = f"**{bd['name']}**  \n{bd['day']:02d}/{bd['month']:02d}{age_str} · {bd.get('relationship','')}  \n{when}"
        if st.button(label, key=f"{prefix}_{bd['id']}", use_container_width=True):
            st.session_state.sel = bd["id"]
            st.session_state.view = "detail"
            st.session_state.msg = ""
            st.rerun()

    with tab_soon:
        if not birthdays:
            st.info("Nog geen verjaardagen. Voeg er een toe!")
        else:
            for bd in sorted(birthdays, key=lambda b: days_until(b["month"], b["day"]))[:30]:
                bd_button(bd, "s")

    with tab_all:
        if not birthdays:
            st.info("Nog geen verjaardagen.")
        else:
            for bd in sorted(birthdays, key=lambda b: b["name"].lower()):
                bd_button(bd, "a")

    st.markdown("")
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("＋ Verjaardag toevoegen", use_container_width=True):
        st.session_state.view = "add"
        st.session_state.edit = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# ADD / EDIT VIEW
# ================================================================
elif st.session_state.view == "add":
    ed = next((b for b in birthdays if b["id"] == st.session_state.sel), {}) if st.session_state.edit else {}
    st.markdown(
        f'<div class="app-subtitle">{"Bewerken" if st.session_state.edit else "Nieuwe verjaardag"}</div>',
        unsafe_allow_html=True,
    )

    with st.form("bd_form"):
        name = st.text_input("Naam *", value=ed.get("name", ""), placeholder="bijv. Oma Riet")
        col1, col2 = st.columns(2)
        with col1:
            day = st.number_input("Dag *", 1, 31, int(ed.get("day", 1)))
        with col2:
            month = st.number_input("Maand *", 1, 12, int(ed.get("month", 1)))
        use_year = st.checkbox("Geboortejaar (voor leeftijd)", value=bool(ed.get("birth_year")))
        birth_year = st.number_input("Geboortejaar", 1900, date.today().year,
                                     int(ed["birth_year"]) if ed.get("birth_year") else date.today().year - 30)
        rel_idx = RELATIONSHIPS.index(ed["relationship"]) if ed.get("relationship") in RELATIONSHIPS else 7
        relationship = st.selectbox("Relatie", RELATIONSHIPS, index=rel_idx)
        notes = st.text_area("Notities (voor AI-bericht)", value=ed.get("notes", ""),
                             placeholder="bijv. houdt van tuinieren, fan van Ajax…", height=80)
        save = st.form_submit_button("Opslaan", use_container_width=True)

    if save:
        if not name.strip():
            st.error("Vul een naam in.")
        else:
            entry = {
                "id": ed.get("id", datetime.now().isoformat()),
                "name": name.strip(), "day": int(day), "month": int(month),
                "birth_year": int(birth_year) if use_year else None,
                "relationship": relationship, "notes": notes.strip(),
            }
            if st.session_state.edit:
                birthdays = [b if b["id"] != entry["id"] else entry for b in birthdays]
            else:
                birthdays.append(entry)
            save_to_storage(birthdays)
            # Also update query param so next load picks it up
            st.query_params["_bd"] = json.dumps(birthdays, ensure_ascii=False)
            st.session_state.view = "list"
            st.session_state.edit = False
            st.rerun()

    if st.button("← Annuleren", use_container_width=True):
        st.session_state.view = "list"
        st.rerun()


# ================================================================
# DETAIL / MESSAGE VIEW
# ================================================================
elif st.session_state.view == "detail":
    person = next((b for b in birthdays if b["id"] == st.session_state.sel), None)
    if not person:
        st.session_state.view = "list"
        st.rerun()

    days = days_until(person["month"], person["day"])
    age = next_age(person.get("birth_year"), person["month"], person["day"])

    st.markdown(f"### {person['name']}")
    st.markdown(
        f"**{person['day']:02d}/{person['month']:02d}** · {person.get('relationship', '')} "
        f"{'· wordt ' + str(age) + ' jaar' if age else ''}"
    )
    if days == 0:
        st.success("🎉 Vandaag jarig!")
    elif days <= 7:
        st.warning(f"⏰ Nog {days} dag(en)!")
    else:
        st.info(f"Nog {days} dagen")

    if person.get("notes"):
        st.caption(person["notes"])

    st.markdown('<div class="section-header">Verjaardagsbericht</div>', unsafe_allow_html=True)

    style = st.selectbox("Toon", ["Warm & persoonlijk", "Grappig & luchtig", "Formeel", "Kort & krachtig", "Poëtisch"])
    extras = st.text_input("Extra aanwijzingen (optioneel)", placeholder="bijv. noem haar hond Bobby")

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    if st.button("✨ Genereer bericht", use_container_width=True):
        with st.spinner("Bericht schrijven…"):
            try:
                st.session_state.msg = generate_message(person, style, extras)
            except Exception as e:
                st.error(f"Fout: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.msg:
        st.markdown(f'<div class="message-card">{st.session_state.msg}</div>', unsafe_allow_html=True)

        wa = "https://wa.me/?text=" + urllib.parse.quote(st.session_state.msg)
        mail = f"mailto:?subject=Gefeliciteerd {person['name']}!&body=" + urllib.parse.quote(st.session_state.msg)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f'<a href="{wa}" target="_blank" style="display:flex;align-items:center;justify-content:center;'
                f'gap:6px;height:52px;background:linear-gradient(135deg,#25D366,#128C7E);color:white;'
                f'text-decoration:none;font-size:16px;font-weight:600;border-radius:14px;'
                f'box-shadow:0 6px 20px rgba(37,211,102,0.3);">📱 WhatsApp</a>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f'<a href="{mail}" style="display:flex;align-items:center;justify-content:center;'
                f'gap:6px;height:52px;background:linear-gradient(135deg,#6366F1,#4F46E5);color:white;'
                f'text-decoration:none;font-size:16px;font-weight:600;border-radius:14px;'
                f'box-shadow:0 6px 20px rgba(99,102,241,0.3);">📧 E-mail</a>',
                unsafe_allow_html=True,
            )
        if st.button("🔄 Opnieuw genereren", use_container_width=True):
            st.session_state.msg = ""
            st.rerun()

    st.markdown("---")
    col_e, col_d = st.columns(2)
    with col_e:
        if st.button("✏️ Bewerken", use_container_width=True):
            st.session_state.view = "add"
            st.session_state.edit = True
            st.rerun()
    with col_d:
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("🗑 Verwijderen", use_container_width=True):
            birthdays = [b for b in birthdays if b["id"] != person["id"]]
            save_to_storage(birthdays)
            st.query_params["_bd"] = json.dumps(birthdays, ensure_ascii=False)
            st.session_state.view = "list"
            st.session_state.sel = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Terug", use_container_width=True):
        st.session_state.view = "list"
        st.session_state.msg = ""
        st.rerun()
