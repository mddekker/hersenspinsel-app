import json
import os
from datetime import date, datetime, timedelta

import anthropic
import streamlit as st

st.set_page_config(
    page_title="Verjaardagen",
    page_icon="🎂",
    layout="centered",
    initial_sidebar_state="collapsed",
)

BIRTHDAYS_FILE = os.path.join(os.path.dirname(__file__), "birthdays.json")

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
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 4rem !important;
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
    .birthday-card {
        background: white; border-radius: 18px; padding: 16px 20px;
        margin-bottom: 12px; box-shadow: 0 2px 12px rgba(15,23,42,0.07);
        border: 1px solid #E2E8F0; cursor: pointer;
    }
    .birthday-card.soon {
        border-left: 4px solid #F59E0B;
        background: linear-gradient(135deg, #FFFBEB 0%, white 100%);
    }
    .birthday-card.today {
        border-left: 4px solid #10B981;
        background: linear-gradient(135deg, #ECFDF5 0%, white 100%);
    }
    .birthday-name {
        font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 2px;
    }
    .birthday-meta {
        font-size: 13px; color: #64748B;
    }
    .days-badge {
        float: right; font-size: 13px; font-weight: 600;
        padding: 4px 10px; border-radius: 20px; background: #F1F5F9; color: #475569;
    }
    .days-badge.soon { background: #FEF3C7; color: #B45309; }
    .days-badge.today { background: #D1FAE5; color: #065F46; }
    .section-header {
        font-size: 13px; font-weight: 600; color: #94A3B8;
        text-transform: uppercase; letter-spacing: 1px;
        margin: 20px 0 10px 0;
    }
    .message-card {
        background: white; border-radius: 20px; padding: 24px;
        margin-top: 16px; box-shadow: 0 4px 20px rgba(15,23,42,0.08);
        border: 1px solid #E2E8F0; white-space: pre-wrap; line-height: 1.6;
        font-size: 15px; color: #0F172A;
    }
    .stButton > button {
        background: white !important; color: #475569 !important;
        border: 1px solid #E2E8F0 !important; border-radius: 14px !important;
        padding: 14px !important; font-size: 15px !important;
        font-weight: 500 !important; width: 100% !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    .primary-btn > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important; border: none !important;
        box-shadow: 0 8px 24px rgba(99,102,241,0.3) !important;
    }
    .danger-btn > button {
        color: #EF4444 !important;
    }
    div[data-testid="stForm"] {
        background: white; border-radius: 20px; padding: 20px;
        box-shadow: 0 4px 20px rgba(15,23,42,0.08); border: 1px solid #E2E8F0;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 10px !important; border-color: #E2E8F0 !important;
        font-size: 16px !important;
    }
    [data-baseweb="tab-list"] {
        background: #F1F5F9 !important; border-radius: 14px !important;
        padding: 4px !important; gap: 4px !important;
    }
    [data-baseweb="tab"] {
        border-radius: 10px !important; font-size: 14px !important;
        font-weight: 500 !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
        background: white !important; box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- Data helpers ---

def load_birthdays() -> list[dict]:
    if not os.path.exists(BIRTHDAYS_FILE):
        return []
    with open(BIRTHDAYS_FILE, "r") as f:
        return json.load(f)


def save_birthdays(data: list[dict]):
    with open(BIRTHDAYS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def days_until_birthday(month: int, day: int) -> int:
    today = date.today()
    next_bd = date(today.year, month, day)
    if next_bd < today:
        next_bd = date(today.year + 1, month, day)
    return (next_bd - today).days


def age_on_next_birthday(birth_year: int, month: int, day: int) -> int | None:
    if not birth_year:
        return None
    today = date.today()
    next_bd = date(today.year, month, day)
    if next_bd < today:
        return today.year + 1 - birth_year
    return today.year - birth_year


def get_api_key() -> str:
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return ""


def generate_message(api_key: str, person: dict, style: str, extras: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    age_info = ""
    if person.get("birth_year"):
        age = age_on_next_birthday(person["birth_year"], person["month"], person["day"])
        if age:
            age_info = f"Ze/hij wordt {age} jaar."
    notes = person.get("notes", "").strip()
    prompt = f"""Schrijf een persoonlijk verjaardagsbericht voor {person['name']}.

Details:
- Relatie: {person.get('relationship', 'bekende')}
{age_info}
- Toon: {style}
{f"- Persoonlijke info: {notes}" if notes else ""}
{f"- Extra aanwijzingen: {extras}" if extras else ""}

Schrijf alleen het bericht zelf, klaar om te versturen. Geen uitleg of inleiding.
Gebruik Nederlands, tenzij de persoon duidelijk een andere taal vereist."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# --- State ---
if "view" not in st.session_state:
    st.session_state.view = "list"  # list | add | detail
if "selected_id" not in st.session_state:
    st.session_state.selected_id = None
if "generated_message" not in st.session_state:
    st.session_state.generated_message = ""
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False


# --- Header ---
st.markdown('<div class="app-title">🎂 Verjaardagen</div>', unsafe_allow_html=True)

birthdays = load_birthdays()

# ================================================================
# VIEW: LIST
# ================================================================
if st.session_state.view == "list":
    st.markdown(
        '<div class="app-subtitle">Nooit meer een verjaardag vergeten.</div>',
        unsafe_allow_html=True,
    )

    tab_upcoming, tab_all = st.tabs(["📅 Aankomend", "📋 Alle"])

    with tab_upcoming:
        if not birthdays:
            st.info("Nog geen verjaardagen opgeslagen. Voeg er een toe!")
        else:
            sorted_bds = sorted(
                birthdays,
                key=lambda b: days_until_birthday(b["month"], b["day"]),
            )
            for bd in sorted_bds[:20]:
                days = days_until_birthday(bd["month"], bd["day"])
                if days == 0:
                    badge_cls = "today"
                    badge_txt = "🎉 Vandaag!"
                    card_cls = "today"
                elif days <= 14:
                    badge_cls = "soon"
                    badge_txt = f"Nog {days}d"
                    card_cls = "soon"
                else:
                    badge_cls = ""
                    badge_txt = f"Nog {days}d"
                    card_cls = ""

                age_str = ""
                if bd.get("birth_year"):
                    age = age_on_next_birthday(bd["birth_year"], bd["month"], bd["day"])
                    if age:
                        age_str = f" · wordt {age}"

                if st.button(
                    f"**{bd['name']}**  \n{bd['day']:02d}/{bd['month']:02d}{age_str} · {bd.get('relationship','')}\n{'🎉 Vandaag!' if days == 0 else f'Nog {days} dag(en)'}",
                    key=f"upcoming_{bd['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_id = bd["id"]
                    st.session_state.view = "detail"
                    st.session_state.generated_message = ""
                    st.rerun()

    with tab_all:
        if not birthdays:
            st.info("Nog geen verjaardagen opgeslagen.")
        else:
            sorted_alpha = sorted(birthdays, key=lambda b: b["name"].lower())
            for bd in sorted_alpha:
                days = days_until_birthday(bd["month"], bd["day"])
                if st.button(
                    f"**{bd['name']}**  \n{bd['day']:02d}/{bd['month']:02d} · {bd.get('relationship','')} · nog {days}d",
                    key=f"all_{bd['id']}",
                    use_container_width=True,
                ):
                    st.session_state.selected_id = bd["id"]
                    st.session_state.view = "detail"
                    st.session_state.generated_message = ""
                    st.rerun()

    st.markdown("")
    col_add, = st.columns([1])
    with st.container():
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("＋ Verjaardag toevoegen", use_container_width=True):
            st.session_state.view = "add"
            st.session_state.edit_mode = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# VIEW: ADD / EDIT
# ================================================================
elif st.session_state.view == "add":
    editing = st.session_state.edit_mode
    edit_data = {}
    if editing and st.session_state.selected_id:
        edit_data = next(
            (b for b in birthdays if b["id"] == st.session_state.selected_id), {}
        )

    st.markdown(
        f'<div class="app-subtitle">{"Verjaardag bewerken" if editing else "Nieuwe verjaardag toevoegen"}</div>',
        unsafe_allow_html=True,
    )

    with st.form("add_form"):
        name = st.text_input("Naam *", value=edit_data.get("name", ""), placeholder="bijv. Oma Riet")

        col_day, col_month = st.columns(2)
        with col_day:
            day = st.number_input("Dag *", min_value=1, max_value=31, value=int(edit_data.get("day", 1)), step=1)
        with col_month:
            month = st.number_input("Maand *", min_value=1, max_value=12, value=int(edit_data.get("month", 1)), step=1)

        birth_year = st.number_input(
            "Geboortejaar (optioneel)",
            min_value=1900, max_value=date.today().year,
            value=int(edit_data["birth_year"]) if edit_data.get("birth_year") else date.today().year - 30,
            step=1,
        )
        use_year = st.checkbox("Geboortejaar gebruiken voor leeftijd", value=bool(edit_data.get("birth_year")))

        relationship = st.selectbox(
            "Relatie",
            ["Partner", "Kind", "Ouder", "Broer/Zus", "Vriend/Vriendin", "Collega", "Familielid", "Overig"],
            index=["Partner", "Kind", "Ouder", "Broer/Zus", "Vriend/Vriendin", "Collega", "Familielid", "Overig"].index(
                edit_data.get("relationship", "Overig")
            ) if edit_data.get("relationship") in ["Partner", "Kind", "Ouder", "Broer/Zus", "Vriend/Vriendin", "Collega", "Familielid", "Overig"] else 7,
        )

        notes = st.text_area(
            "Persoonlijke notities (voor AI-bericht)",
            value=edit_data.get("notes", ""),
            placeholder="bijv. houdt van tuinieren, gaat binnenkort met pensioen, fan van Ajax…",
            height=100,
        )

        submitted = st.form_submit_button("Opslaan" if editing else "Toevoegen", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Vul een naam in.")
        else:
            entry = {
                "id": edit_data.get("id", datetime.now().isoformat()),
                "name": name.strip(),
                "day": int(day),
                "month": int(month),
                "birth_year": int(birth_year) if use_year else None,
                "relationship": relationship,
                "notes": notes.strip(),
            }
            if editing:
                birthdays = [b if b["id"] != entry["id"] else entry for b in birthdays]
            else:
                birthdays.append(entry)
            save_birthdays(birthdays)
            st.session_state.view = "list"
            st.session_state.edit_mode = False
            st.rerun()

    if st.button("← Annuleren", use_container_width=True):
        st.session_state.view = "list"
        st.session_state.edit_mode = False
        st.rerun()


# ================================================================
# VIEW: DETAIL / MESSAGE GENERATOR
# ================================================================
elif st.session_state.view == "detail":
    person = next((b for b in birthdays if b["id"] == st.session_state.selected_id), None)

    if not person:
        st.error("Persoon niet gevonden.")
        st.session_state.view = "list"
        st.rerun()

    days = days_until_birthday(person["month"], person["day"])
    age = age_on_next_birthday(person.get("birth_year"), person["month"], person["day"]) if person.get("birth_year") else None

    st.markdown(f"### {person['name']}")
    st.markdown(
        f"**{person['day']:02d}/{person['month']:02d}** · {person.get('relationship','')} "
        f"{'· wordt ' + str(age) + ' jaar' if age else ''}"
    )
    if days == 0:
        st.success("🎉 Vandaag jarig!")
    elif days <= 7:
        st.warning(f"⏰ Nog {days} dag(en)!")
    else:
        st.info(f"Nog {days} dagen")

    if person.get("notes"):
        st.markdown(f"*{person['notes']}*")

    st.markdown('<div class="section-header">Verjaardagsbericht genereren</div>', unsafe_allow_html=True)

    style = st.selectbox(
        "Toon",
        ["Warm & persoonlijk", "Grappig & luchtig", "Formeel", "Kort & krachtig", "Poëtisch"],
    )
    extras = st.text_input("Extra aanwijzingen (optioneel)", placeholder="bijv. noem haar hond Bobby")

    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    generate_clicked = st.button("✨ Genereer bericht", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if generate_clicked:
        api_key = get_api_key()
        if not api_key:
            st.error("API key niet gevonden — check de Streamlit-secrets.")
        else:
            with st.spinner("Bericht schrijven…"):
                try:
                    st.session_state.generated_message = generate_message(api_key, person, style, extras)
                except Exception as e:
                    st.error(f"Fout: {e}")

    if st.session_state.generated_message:
        st.markdown(
            f'<div class="message-card">{st.session_state.generated_message}</div>',
            unsafe_allow_html=True,
        )

        import urllib.parse
        whatsapp_url = (
            "https://wa.me/?text=" + urllib.parse.quote(st.session_state.generated_message)
        )
        mailto_url = (
            f"mailto:?subject=Gefeliciteerd {person['name']}!&body="
            + urllib.parse.quote(st.session_state.generated_message)
        )

        col_wa, col_mail = st.columns(2)
        with col_wa:
            st.markdown(
                f'<a href="{whatsapp_url}" target="_blank" style="display:flex;align-items:center;justify-content:center;gap:6px;height:52px;background:linear-gradient(135deg,#25D366,#128C7E);color:white;text-decoration:none;font-size:16px;font-weight:600;border-radius:14px;box-shadow:0 6px 20px rgba(37,211,102,0.3);">📱 WhatsApp</a>',
                unsafe_allow_html=True,
            )
        with col_mail:
            st.markdown(
                f'<a href="{mailto_url}" style="display:flex;align-items:center;justify-content:center;gap:6px;height:52px;background:linear-gradient(135deg,#6366F1,#4F46E5);color:white;text-decoration:none;font-size:16px;font-weight:600;border-radius:14px;box-shadow:0 6px 20px rgba(99,102,241,0.3);">📧 E-mail</a>',
                unsafe_allow_html=True,
            )

        if st.button("🔄 Opnieuw genereren", use_container_width=True):
            st.session_state.generated_message = ""
            st.rerun()

    st.markdown("---")
    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button("✏️ Bewerken", use_container_width=True):
            st.session_state.view = "add"
            st.session_state.edit_mode = True
            st.rerun()
    with col_del:
        st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
        if st.button("🗑 Verwijderen", use_container_width=True):
            birthdays = [b for b in birthdays if b["id"] != person["id"]]
            save_birthdays(birthdays)
            st.session_state.view = "list"
            st.session_state.selected_id = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("← Terug", use_container_width=True):
        st.session_state.view = "list"
        st.session_state.generated_message = ""
        st.rerun()
