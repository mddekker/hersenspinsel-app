"""
RBT WK 2026 Voetbalpool — HumanTotalCare directieteam.

Streamlit-app waar collega's hun voorspellingen voor de groepsfase
invullen. Klassieke scoring: 3 punten voor exacte uitslag, 1 punt
voor juiste toto (W/G/V). Admin voert de echte uitslagen in.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, date
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "wk_pool.db"
NL_TZ = ZoneInfo("Europe/Amsterdam")
DEFAULT_KICKOFF = "21:00"

st.set_page_config(
    page_title="RBT WK Pool 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _admin_password() -> str:
    try:
        return st.secrets["WK_POOL_ADMIN_PASSWORD"]
    except Exception:
        return "rbt2026"


# ---------------------------------------------------------------------------
# Speelschema — WK 2026 (12 groepen, 72 wedstrijden)
# Bron: FIFA loting 5 dec 2025
# ---------------------------------------------------------------------------

GROUPS: dict[str, list[str]] = {
    "A": ["Mexico", "Zuid-Afrika", "Zuid-Korea", "Tsjechië"],
    "B": ["Canada", "Bosnië-Herzegovina", "Zwitserland", "Qatar"],
    "C": ["Brazilië", "Marokko", "Schotland", "Haïti"],
    "D": ["Verenigde Staten", "Paraguay", "Australië", "Turkije"],
    "E": ["Duitsland", "Curaçao", "Ivoorkust", "Ecuador"],
    "F": ["Nederland", "Japan", "Zweden", "Tunesië"],
    "G": ["België", "Egypte", "Iran", "Nieuw-Zeeland"],
    "H": ["Spanje", "Kaapverdië", "Saoedi-Arabië", "Uruguay"],
    "I": ["Frankrijk", "Senegal", "Noorwegen", "Irak"],
    "J": ["Argentinië", "Algerije", "Oostenrijk", "Jordanië"],
    "K": ["Portugal", "Oezbekistan", "Colombia", "DR Congo"],
    "L": ["Engeland", "Kroatië", "Ghana", "Panama"],
}

FLAGS: dict[str, str] = {
    "Mexico": "🇲🇽", "Zuid-Afrika": "🇿🇦", "Zuid-Korea": "🇰🇷", "Tsjechië": "🇨🇿",
    "Canada": "🇨🇦", "Bosnië-Herzegovina": "🇧🇦", "Zwitserland": "🇨🇭", "Qatar": "🇶🇦",
    "Brazilië": "🇧🇷", "Marokko": "🇲🇦", "Schotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Haïti": "🇭🇹",
    "Verenigde Staten": "🇺🇸", "Paraguay": "🇵🇾", "Australië": "🇦🇺", "Turkije": "🇹🇷",
    "Duitsland": "🇩🇪", "Curaçao": "🇨🇼", "Ivoorkust": "🇨🇮", "Ecuador": "🇪🇨",
    "Nederland": "🇳🇱", "Japan": "🇯🇵", "Zweden": "🇸🇪", "Tunesië": "🇹🇳",
    "België": "🇧🇪", "Egypte": "🇪🇬", "Iran": "🇮🇷", "Nieuw-Zeeland": "🇳🇿",
    "Spanje": "🇪🇸", "Kaapverdië": "🇨🇻", "Saoedi-Arabië": "🇸🇦", "Uruguay": "🇺🇾",
    "Frankrijk": "🇫🇷", "Senegal": "🇸🇳", "Noorwegen": "🇳🇴", "Irak": "🇮🇶",
    "Argentinië": "🇦🇷", "Algerije": "🇩🇿", "Oostenrijk": "🇦🇹", "Jordanië": "🇯🇴",
    "Portugal": "🇵🇹", "Oezbekistan": "🇺🇿", "Colombia": "🇨🇴", "DR Congo": "🇨🇩",
    "Engeland": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Kroatië": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦",
}

# Indicatieve datums per groep en speelronde. Admin kan ze later wijzigen.
GROUP_DATES: dict[str, tuple[str, str, str]] = {
    "A": ("2026-06-11", "2026-06-17", "2026-06-24"),
    "B": ("2026-06-12", "2026-06-18", "2026-06-24"),
    "C": ("2026-06-13", "2026-06-19", "2026-06-25"),
    "D": ("2026-06-12", "2026-06-18", "2026-06-25"),
    "E": ("2026-06-13", "2026-06-19", "2026-06-25"),
    "F": ("2026-06-14", "2026-06-20", "2026-06-26"),
    "G": ("2026-06-13", "2026-06-19", "2026-06-25"),
    "H": ("2026-06-14", "2026-06-20", "2026-06-26"),
    "I": ("2026-06-14", "2026-06-20", "2026-06-26"),
    "J": ("2026-06-15", "2026-06-21", "2026-06-27"),
    "K": ("2026-06-15", "2026-06-21", "2026-06-27"),
    "L": ("2026-06-15", "2026-06-21", "2026-06-27"),
}


# ---------------------------------------------------------------------------
# Knockout-fase — alleen wedstrijden waar beide teams bekend zijn worden
# geseed. Bij elke nieuwe ronde voegen we hieronder de matchups toe en
# pushen we de code; bestaande matches in de DB worden niet aangetast.
# ---------------------------------------------------------------------------

ROUND_LABELS: dict[str, str] = {
    "group": "Groepsfase",
    "r32": "Zestiende finale",
    "r16": "Achtste finale",
    "qf": "Kwartfinale",
    "sf": "Halve finale",
    "3rd": "Troostfinale",
    "final": "Finale",
}
ROUND_ORDER: list[str] = ["r32", "r16", "qf", "sf", "3rd", "final"]

# Kickoff is in Europe/Amsterdam tijd, omgezet vanuit de stadion-aftrap.
# match_date is de FIFA-datum (lokale stadion-datum) zodat het schema
# leesbaar blijft.
KNOCKOUTS: list[dict] = [
    # Round of 32 — bevestigd op 26 juni 2026
    {"round": "r32", "date": "2026-06-28", "kickoff": "2026-06-29 00:00",
     "home": "Zuid-Afrika", "away": "Canada"},
    {"round": "r32", "date": "2026-06-29", "kickoff": "2026-06-29 20:00",
     "home": "Brazilië", "away": "Japan"},
    {"round": "r32", "date": "2026-06-30", "kickoff": "2026-07-01 04:00",
     "home": "Nederland", "away": "Marokko"},
    {"round": "r32", "date": "2026-07-02", "kickoff": "2026-07-03 05:00",
     "home": "Verenigde Staten", "away": "Bosnië-Herzegovina"},
]


def build_matches() -> list[dict]:
    """72 wedstrijden volgens FIFA-rotatie 1v2/3v4, 1v3/4v2, 4v1/2v3."""
    out: list[dict] = []
    for code, teams in GROUPS.items():
        d1, d2, d3 = GROUP_DATES[code]
        out.extend([
            {"group": code, "matchday": 1, "date": d1, "home": teams[0], "away": teams[1]},
            {"group": code, "matchday": 1, "date": d1, "home": teams[2], "away": teams[3]},
            {"group": code, "matchday": 2, "date": d2, "home": teams[0], "away": teams[2]},
            {"group": code, "matchday": 2, "date": d2, "home": teams[3], "away": teams[1]},
            {"group": code, "matchday": 3, "date": d3, "home": teams[3], "away": teams[0]},
            {"group": code, "matchday": 3, "date": d3, "home": teams[1], "away": teams[2]},
        ])
    return out


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

@st.cache_resource
def get_conn() -> sqlite3.Connection:
    con = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            group_code TEXT NOT NULL,
            matchday INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            home TEXT NOT NULL,
            away TEXT NOT NULL,
            actual_home INTEGER,
            actual_away INTEGER,
            kickoff TEXT,
            round TEXT NOT NULL DEFAULT 'group',
            actual_winner TEXT
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL COLLATE NOCASE
        );
        CREATE TABLE IF NOT EXISTS predictions (
            user_id INTEGER NOT NULL,
            match_id INTEGER NOT NULL,
            pred_home INTEGER NOT NULL,
            pred_away INTEGER NOT NULL,
            pred_winner TEXT,
            PRIMARY KEY (user_id, match_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
        );
        """
    )
    # Migraties voor bestaande databases — voeg kolommen idempotent toe.
    for ddl in (
        "ALTER TABLE matches ADD COLUMN kickoff TEXT",
        "ALTER TABLE matches ADD COLUMN round TEXT DEFAULT 'group'",
        "ALTER TABLE matches ADD COLUMN actual_winner TEXT",
        "ALTER TABLE predictions ADD COLUMN pred_winner TEXT",
    ):
        try:
            con.execute(ddl)
        except sqlite3.OperationalError:
            pass

    if con.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0:
        con.executemany(
            "INSERT INTO matches(group_code, matchday, match_date, home, away, kickoff, round) "
            "VALUES (?, ?, ?, ?, ?, ?, 'group')",
            [
                (m["group"], m["matchday"], m["date"], m["home"], m["away"],
                 f'{m["date"]} {DEFAULT_KICKOFF}')
                for m in build_matches()
            ],
        )

    # Backfill voor rijen zonder kickoff/round (oude DBs).
    con.execute(
        "UPDATE matches SET kickoff = match_date || ' ' || ? WHERE kickoff IS NULL OR kickoff = ''",
        (DEFAULT_KICKOFF,),
    )
    con.execute("UPDATE matches SET round = 'group' WHERE round IS NULL OR round = ''")
    con.commit()

    # Knockout-wedstrijden idempotent invoegen.
    seed_knockouts(con)
    return con


def seed_knockouts(con: sqlite3.Connection) -> None:
    """Voegt nieuwe knockoutwedstrijden toe — bestaande matches (gematcht
    op ronde + thuis + uit) worden overgeslagen, dus dit is veilig om
    elke deploy opnieuw te draaien."""
    for ko in KNOCKOUTS:
        exists = con.execute(
            "SELECT 1 FROM matches WHERE round = ? AND home = ? AND away = ?",
            (ko["round"], ko["home"], ko["away"]),
        ).fetchone()
        if exists:
            continue
        con.execute(
            "INSERT INTO matches(group_code, matchday, match_date, home, away, "
            "kickoff, round) VALUES ('KO', 0, ?, ?, ?, ?, ?)",
            (ko["date"], ko["home"], ko["away"], ko["kickoff"], ko["round"]),
        )
    con.commit()


def get_or_create_user(con: sqlite3.Connection, name: str) -> int:
    name = name.strip()
    row = con.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    cur = con.execute("INSERT INTO users(name) VALUES (?)", (name,))
    con.commit()
    return cur.lastrowid


def all_users(con: sqlite3.Connection) -> list[tuple[int, str]]:
    return list(con.execute("SELECT id, name FROM users ORDER BY name").fetchall())


def matches_df(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT id, group_code, matchday, match_date, home, away, "
        "actual_home, actual_away, kickoff, round, actual_winner "
        "FROM matches ORDER BY match_date, group_code, matchday, id",
        con,
    )


def is_locked(match_row) -> bool:
    """Voorspelling vergrendeld zodra de aftrap is geweest, of de admin
    een uitslag heeft ingevoerd."""
    if match_row["actual_home"] is not None and match_row["actual_away"] is not None:
        return True
    kickoff = match_row.get("kickoff") if hasattr(match_row, "get") else match_row["kickoff"]
    if not kickoff:
        return False
    try:
        ko = datetime.strptime(str(kickoff), "%Y-%m-%d %H:%M").replace(tzinfo=NL_TZ)
    except ValueError:
        return False
    return datetime.now(NL_TZ) >= ko


def predictions_for(con: sqlite3.Connection, user_id: int) -> dict[int, dict]:
    rows = con.execute(
        "SELECT match_id, pred_home, pred_away, pred_winner "
        "FROM predictions WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return {mid: {"home": ph, "away": pa, "winner": pw} for mid, ph, pa, pw in rows}


def save_prediction(
    con: sqlite3.Connection,
    user_id: int,
    match_id: int,
    h: int,
    a: int,
    winner: str | None = None,
) -> None:
    con.execute(
        "INSERT INTO predictions(user_id, match_id, pred_home, pred_away, pred_winner) "
        "VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(user_id, match_id) DO UPDATE SET "
        "pred_home=excluded.pred_home, "
        "pred_away=excluded.pred_away, "
        "pred_winner=excluded.pred_winner",
        (user_id, match_id, h, a, winner),
    )
    con.commit()


def set_actual(con: sqlite3.Connection, match_id: int, h: int | None, a: int | None) -> None:
    con.execute(
        "UPDATE matches SET actual_home = ?, actual_away = ? WHERE id = ?",
        (h, a, match_id),
    )
    con.commit()


def set_actual_winner(con: sqlite3.Connection, match_id: int, winner: str | None) -> None:
    con.execute(
        "UPDATE matches SET actual_winner = ? WHERE id = ?",
        (winner, match_id),
    )
    con.commit()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_points(pred_h: int, pred_a: int, act_h: int | None, act_a: int | None) -> int | None:
    """3 voor exacte uitslag, 1 voor juiste toto (W/G/V), 0 anders."""
    if act_h is None or act_a is None:
        return None
    if pred_h == act_h and pred_a == act_a:
        return 3
    pred = (pred_h > pred_a) - (pred_h < pred_a)
    actual = (act_h > act_a) - (act_h < act_a)
    return 1 if pred == actual else 0


def winner_bonus(pred_winner: str | None, actual_winner: str | None) -> int | None:
    """Bonuspunt voor knockout: 1 als de voorspelde winnaar klopt
    (na evt. verlenging/penalty's)."""
    if not actual_winner:
        return None
    if not pred_winner:
        return 0
    return 1 if pred_winner == actual_winner else 0


def leaderboard(con: sqlite3.Connection) -> pd.DataFrame:
    rows = con.execute(
        """
        SELECT u.id, u.name,
               p.pred_home, p.pred_away, p.pred_winner,
               m.actual_home, m.actual_away, m.actual_winner, m.round
        FROM users u
        LEFT JOIN predictions p ON p.user_id = u.id
        LEFT JOIN matches m ON m.id = p.match_id
        """
    ).fetchall()
    stats: dict[int, dict] = {}
    for uid, name, ph, pa, pw, ah, aa, aw, rnd in rows:
        s = stats.setdefault(
            uid,
            {"name": name, "points": 0, "bullseyes": 0, "tos": 0,
             "bonus": 0, "predicted": 0, "scored": 0},
        )
        if ph is None:
            continue
        s["predicted"] += 1
        pts = score_points(ph, pa, ah, aa)
        if pts is None:
            continue
        s["scored"] += 1
        s["points"] += pts
        if pts == 3:
            s["bullseyes"] += 1
        elif pts == 1:
            s["tos"] += 1
        if rnd and rnd != "group":
            wb = winner_bonus(pw, aw)
            if wb:
                s["points"] += wb
                s["bonus"] += wb
    df = pd.DataFrame(stats.values())
    if df.empty:
        return pd.DataFrame(columns=["name", "points", "bullseyes", "tos", "bonus", "predicted", "scored"])
    return df.sort_values(
        ["points", "bullseyes", "tos", "bonus"], ascending=False
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

st.markdown(
    """
<style>
    #MainMenu, footer, header, .stDeployButton { display: none !important; }

    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0B3D2E 0%, #156645 60%, #0B3D2E 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 720px !important;
    }
    .hero {
        text-align: center;
        color: white;
        margin-bottom: 12px;
    }
    .hero-title {
        font-size: 34px; font-weight: 800; letter-spacing: -0.5px;
        text-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }
    .hero-sub {
        font-size: 14px; opacity: 0.85; font-weight: 400;
        margin-top: -4px;
    }
    .pill {
        display:inline-block; padding: 2px 10px; border-radius: 999px;
        background: rgba(255,255,255,0.18); color: white; font-size: 11px;
        font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase;
    }

    .stTabs [role="tablist"] {
        background: rgba(255,255,255,0.08); border-radius: 14px;
        padding: 4px; gap: 4px;
    }
    .stTabs [role="tab"] {
        color: white !important; font-weight: 600;
        border-radius: 10px; padding: 6px 14px;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: white !important; color: #0B3D2E !important;
    }

    .card {
        background: white; border-radius: 18px; padding: 18px 18px 6px 18px;
        margin: 12px 0; box-shadow: 0 6px 24px rgba(0,0,0,0.15);
    }
    .card h3 {
        margin: 0 0 4px 0; color: #0B3D2E; font-size: 18px; font-weight: 700;
    }
    .card .group-meta {
        font-size: 12px; color: #64748B; margin-bottom: 8px;
    }

    .match-row {
        display: flex; align-items: center; gap: 8px;
        padding: 8px 0; border-top: 1px solid #F1F5F9;
    }
    .match-row:first-child { border-top: 0; }
    .team-name { font-weight: 600; color: #0F172A; }
    .match-date { font-size: 11px; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }
    .actual {
        background: #0B3D2E; color: white; padding: 2px 8px; border-radius: 6px;
        font-size: 12px; font-weight: 700; margin-left: 8px;
    }

    .stNumberInput input {
        text-align: center; font-weight: 700; font-size: 18px;
    }

    .lb-row {
        display: flex; align-items: center; gap: 12px;
        padding: 12px 16px; background: white; border-radius: 14px;
        margin: 6px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .lb-rank {
        font-size: 24px; font-weight: 800; min-width: 40px; text-align:center;
    }
    .lb-name { flex: 1; font-weight: 600; color: #0F172A; }
    .lb-points {
        background: linear-gradient(135deg,#10B981,#059669); color: white;
        padding: 6px 14px; border-radius: 12px; font-weight: 800; font-size: 18px;
    }
    .lb-meta { font-size: 11px; color: #64748B; }
</style>
""",
    unsafe_allow_html=True,
)


def flag(team: str) -> str:
    return FLAGS.get(team, "🏳️")


def format_dutch_date(iso: str) -> str:
    months = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    d = datetime.strptime(iso, "%Y-%m-%d").date()
    return f"{d.day} {months[d.month - 1]}"


# ---------------------------------------------------------------------------
# Header + login
# ---------------------------------------------------------------------------

con = get_conn()

st.markdown(
    """
<div class="hero">
  <div class="hero-title">⚽ RBT WK Pool 2026</div>
  <div class="hero-sub">HumanTotalCare directieteam · 11 jun – 19 jul</div>
</div>
""",
    unsafe_allow_html=True,
)

if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
    st.session_state["user_name"] = ""

if st.session_state["user_id"] is None:
    st.markdown(
        '<div class="card"><h3>👋 Welkom bij de pool</h3>'
        '<div class="group-meta">Vul je naam in om je voorspellingen te kunnen invoeren.</div></div>',
        unsafe_allow_html=True,
    )
    with st.form("login", clear_on_submit=False):
        name = st.text_input("Jouw naam", placeholder="bijv. Martin Dekker", label_visibility="collapsed")
        submitted = st.form_submit_button("Start mijn pool", use_container_width=True)
        if submitted and name.strip():
            uid = get_or_create_user(con, name.strip())
            st.session_state["user_id"] = uid
            st.session_state["user_name"] = name.strip()
            st.rerun()

    st.markdown(
        '<div class="card"><h3>📜 Spelregels</h3>'
        '<ul style="margin: 6px 0 12px 0; color:#334155; font-size:14px; line-height:1.6;">'
        '<li><b>3 punten</b> voor een exacte uitslag (na 90 min)</li>'
        '<li><b>1 punt</b> voor de juiste toto (winst / gelijk / verlies)</li>'
        '<li><b>+1 bonuspunt</b> bij knockouts voor de juiste winnaar (na evt. verlenging/penalty\'s)</li>'
        '<li>Voorspellingen aanpassen kan tot de aftrap</li>'
        '<li>Groepsfase + knockouts tellen mee</li>'
        '</ul></div>',
        unsafe_allow_html=True,
    )
    st.stop()

# Logged in
st.markdown(
    f'<div style="text-align:center; margin: -4px 0 8px 0;">'
    f'<span class="pill">Speler: {st.session_state["user_name"]}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

tab_predict, tab_board, tab_rules, tab_admin = st.tabs(
    ["📋 Voorspellen", "🏆 Stand", "📜 Regels", "🔐 Admin"]
)


# ---------------------------------------------------------------------------
# Tab: voorspellen
# ---------------------------------------------------------------------------

def _render_match_row(m, pred: dict | None, is_knockout: bool) -> None:
    mid = int(m["id"])
    ph = pred["home"] if pred else None
    pa = pred["away"] if pred else None
    pw = pred["winner"] if pred else None
    has_actual = m["actual_home"] is not None and m["actual_away"] is not None
    locked = is_locked(m)

    col_label, col_h, col_dash, col_a = st.columns([5, 1.2, 0.3, 1.2])
    with col_label:
        if has_actual:
            badge = f'<span class="actual">{int(m["actual_home"])}-{int(m["actual_away"])}</span>'
        elif locked:
            badge = '<span class="actual" style="background:#94A3B8;">🔒 gesloten</span>'
        else:
            badge = ""
        if is_knockout:
            top = f'{ROUND_LABELS.get(str(m["round"]), str(m["round"])).upper()} · {format_dutch_date(m["match_date"])}'
        else:
            top = f'SPEELRONDE {m["matchday"]} · {format_dutch_date(m["match_date"])}'
        st.markdown(
            f'<div class="match-date">{top}</div>'
            f'<div><span>{flag(m["home"])}</span> '
            f'<span class="team-name">{m["home"]}</span> '
            f'<span style="color:#94A3B8;">vs</span> '
            f'<span class="team-name">{m["away"]}</span> '
            f'<span>{flag(m["away"])}</span>'
            + badge
            + "</div>",
            unsafe_allow_html=True,
        )
    with col_h:
        new_h = st.number_input(
            f"h_{mid}", min_value=0, max_value=20, step=1,
            value=int(ph) if ph is not None else 0,
            key=f"h_{mid}", label_visibility="collapsed",
            disabled=locked,
        )
    with col_dash:
        st.markdown(
            '<div style="text-align:center; padding-top: 8px; color:#94A3B8; font-weight:700;">–</div>',
            unsafe_allow_html=True,
        )
    with col_a:
        new_a = st.number_input(
            f"a_{mid}", min_value=0, max_value=20, step=1,
            value=int(pa) if pa is not None else 0,
            key=f"a_{mid}", label_visibility="collapsed",
            disabled=locked,
        )

    new_winner = pw
    if is_knockout:
        options = ["— nog geen keuze —", m["home"], m["away"]]
        current_idx = 0
        if pw == m["home"]:
            current_idx = 1
        elif pw == m["away"]:
            current_idx = 2
        choice = st.radio(
            f"Wie wint? (na evt. verlenging/penalty's)",
            options=options,
            index=current_idx,
            horizontal=True,
            key=f"w_{mid}",
            disabled=locked,
        )
        new_winner = None if choice == options[0] else choice

    if locked:
        return

    user_id = st.session_state["user_id"]
    if pred is not None:
        score_changed = (int(ph), int(pa)) != (int(new_h), int(new_a))
        winner_changed = (pw or "") != (new_winner or "")
        if score_changed or winner_changed:
            save_prediction(con, user_id, mid, int(new_h), int(new_a), new_winner)
    else:
        # Nieuwe voorspelling — pas opslaan bij echte invoer (niet de
        # default 0-0 zonder winnaarskeuze).
        if (int(new_h), int(new_a)) != (0, 0) or new_winner:
            save_prediction(con, user_id, mid, int(new_h), int(new_a), new_winner)


def render_predict_tab():
    df = matches_df(con)
    preds = predictions_for(con, st.session_state["user_id"])
    total_matches = len(df)
    total_made = sum(1 for mid in df["id"] if mid in preds)

    st.markdown(
        f'<div style="color:white; text-align:center; margin: 6px 0 4px 0; font-size:13px;">'
        f'Je hebt <b>{total_made}/{total_matches}</b> wedstrijden voorspeld'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.progress(total_made / total_matches if total_matches else 0.0)

    rounds_present = [r for r in ROUND_ORDER if (df["round"] == r).any()]
    filter_opts = ["Alle wedstrijden"] + [f"Groep {g}" for g in GROUPS.keys()] \
        + [ROUND_LABELS[r] for r in rounds_present]
    selected = st.selectbox("Filter", filter_opts, label_visibility="collapsed")

    def show_group(code: str) -> None:
        group_df = df[(df["group_code"] == code) & (df["round"] == "group")]
        if group_df.empty:
            return
        teams = " · ".join(f"{flag(t)} {t}" for t in GROUPS[code])
        st.markdown(
            f'<div class="card"><h3>Groep {code}</h3>'
            f'<div class="group-meta">{teams}</div></div>',
            unsafe_allow_html=True,
        )
        for _, m in group_df.iterrows():
            _render_match_row(m, preds.get(int(m["id"])), is_knockout=False)

    def show_round(round_key: str) -> None:
        sub = df[df["round"] == round_key]
        if sub.empty:
            return
        st.markdown(
            f'<div class="card"><h3>🏆 {ROUND_LABELS.get(round_key, round_key)}</h3>'
            f'<div class="group-meta">Knockout — +1 bonuspunt voor de juiste winnaar</div></div>',
            unsafe_allow_html=True,
        )
        for _, m in sub.iterrows():
            _render_match_row(m, preds.get(int(m["id"])), is_knockout=True)

    if selected == "Alle wedstrijden":
        for code in GROUPS.keys():
            show_group(code)
        for r in rounds_present:
            show_round(r)
    elif selected.startswith("Groep "):
        show_group(selected[-1])
    else:
        match_key = next((k for k, v in ROUND_LABELS.items() if v == selected), None)
        if match_key:
            show_round(match_key)


# ---------------------------------------------------------------------------
# Tab: stand
# ---------------------------------------------------------------------------

def render_board_tab():
    lb = leaderboard(con)
    if lb.empty or lb["scored"].sum() == 0:
        st.markdown(
            '<div class="card"><h3>🏁 Nog geen punten</h3>'
            '<div style="color:#64748B; font-size:14px;">Zodra de admin de eerste uitslagen invoert verschijnen hier de scores.</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div style="color:white; margin-top:16px; font-weight:600;">Deelnemers</div>', unsafe_allow_html=True)
        for _, row in lb.iterrows():
            st.markdown(
                f'<div class="lb-row"><div class="lb-rank">·</div>'
                f'<div class="lb-name">{row["name"]}<div class="lb-meta">{int(row["predicted"])}/72 voorspeld</div></div></div>',
                unsafe_allow_html=True,
            )
        return

    medals = {0: "🥇", 1: "🥈", 2: "🥉"}
    for i, row in lb.iterrows():
        rank = medals.get(i, f"{i+1}.")
        bonus = int(row.get("bonus", 0) or 0)
        bonus_str = f" · 🎯 {bonus} bonus" if bonus else ""
        st.markdown(
            f'<div class="lb-row">'
            f'<div class="lb-rank">{rank}</div>'
            f'<div class="lb-name">{row["name"]}'
            f'<div class="lb-meta">{int(row["bullseyes"])} bullseyes · {int(row["tos"])} toto · {int(row["scored"])} gespeeld{bonus_str}</div>'
            f'</div>'
            f'<div class="lb-points">{int(row["points"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Tab: regels
# ---------------------------------------------------------------------------

def render_rules_tab():
    st.markdown(
        '<div class="card"><h3>📜 Spelregels</h3>'
        '<ul style="margin: 6px 0 4px 0; color:#334155; font-size:14px; line-height:1.7;">'
        '<li><b>3 punten</b> — exacte uitslag na 90 minuten goed</li>'
        '<li><b>1 punt</b> — juiste toto (winst / gelijk / verlies)</li>'
        '<li><b>0 punten</b> — toto fout</li>'
        '<li><b>+1 bonuspunt</b> bij knockouts — voor de juiste winnaar (na evt. verlenging/penalty\'s)</li>'
        '<li>Deadline: tot de aftrap (groepsfase 21:00 NL, knockouts per wedstrijd)</li>'
        '<li>Bij gelijke stand: meeste bullseyes wint, daarna meeste toto\'s, daarna meeste bonuspunten</li>'
        '</ul></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="card"><h3>💡 Tip</h3>'
        '<div style="color:#334155; font-size:14px;">'
        'Vul vooraf alle wedstrijden in om geen punten te missen. '
        'Bij knockoutwedstrijden krijg je een extra bonuspunt als je de uiteindelijke winnaar goed hebt — '
        'dus vergeet die niet aan te vinken!'
        '</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tab: admin
# ---------------------------------------------------------------------------

def render_admin_tab():
    if "admin_ok" not in st.session_state:
        st.session_state["admin_ok"] = False

    if not st.session_state["admin_ok"]:
        pwd = st.text_input("Admin wachtwoord", type="password")
        if st.button("Inloggen", use_container_width=True):
            if pwd == _admin_password():
                st.session_state["admin_ok"] = True
                st.rerun()
            else:
                st.error("Onjuist wachtwoord.")
        return

    df = matches_df(con)

    st.markdown(
        '<div class="card"><h3>📥 Uitslagen invoeren</h3>'
        '<div class="group-meta">Voer per wedstrijd de eindstand na 90 minuten in. Bij knockouts ook de winnaar (na evt. verlenging/penalty\'s).</div></div>',
        unsafe_allow_html=True,
    )

    rounds_present = [r for r in ROUND_ORDER if (df["round"] == r).any()]
    section_opts = [f"Groep {g}" for g in GROUPS.keys()] + [ROUND_LABELS[r] for r in rounds_present]
    section = st.selectbox("Sectie", section_opts, key="admin_section")

    if section.startswith("Groep "):
        group = section[-1]
        md = st.radio("Speelronde", [1, 2, 3], horizontal=True, key="admin_md")
        sub = df[(df["group_code"] == group) & (df["matchday"] == md) & (df["round"] == "group")]
        is_ko = False
    else:
        round_key = next((k for k, v in ROUND_LABELS.items() if v == section), None)
        sub = df[df["round"] == round_key] if round_key else df.iloc[0:0]
        is_ko = True

    for _, m in sub.iterrows():
        mid = int(m["id"])
        cols = st.columns([5, 1.2, 0.3, 1.2, 1.2])
        with cols[0]:
            st.markdown(
                f'**{flag(m["home"])} {m["home"]}** vs **{m["away"]} {flag(m["away"])}**  \n'
                f'<span style="color:#64748B; font-size:11px;">{format_dutch_date(m["match_date"])}</span>',
                unsafe_allow_html=True,
            )
        with cols[1]:
            h = st.number_input(
                f"ah_{mid}", min_value=0, max_value=20, step=1,
                value=int(m["actual_home"]) if m["actual_home"] is not None else 0,
                key=f"ah_{mid}", label_visibility="collapsed",
            )
        with cols[2]:
            st.markdown('<div style="text-align:center; padding-top:8px;">–</div>', unsafe_allow_html=True)
        with cols[3]:
            a = st.number_input(
                f"aa_{mid}", min_value=0, max_value=20, step=1,
                value=int(m["actual_away"]) if m["actual_away"] is not None else 0,
                key=f"aa_{mid}", label_visibility="collapsed",
            )
        with cols[4]:
            if st.button("Opslaan", key=f"save_{mid}"):
                set_actual(con, mid, int(h), int(a))
                st.success("Opgeslagen")
                st.rerun()
            if m["actual_home"] is not None and st.button("Wissen", key=f"clear_{mid}"):
                set_actual(con, mid, None, None)
                if is_ko:
                    set_actual_winner(con, mid, None)
                st.rerun()

        if is_ko:
            win_opts = ["— nog niet bekend —", m["home"], m["away"]]
            current = 0
            if m["actual_winner"] == m["home"]:
                current = 1
            elif m["actual_winner"] == m["away"]:
                current = 2
            wcols = st.columns([2, 5])
            with wcols[0]:
                st.markdown(
                    '<div style="padding-top:8px; font-size:13px; color:#64748B;">Winnaar:</div>',
                    unsafe_allow_html=True,
                )
            with wcols[1]:
                winner = st.radio(
                    f"winnaar_{mid}",
                    options=win_opts,
                    index=current,
                    horizontal=True,
                    key=f"win_{mid}",
                    label_visibility="collapsed",
                )
                new_winner = None if winner == win_opts[0] else winner
                if (m["actual_winner"] or None) != new_winner:
                    set_actual_winner(con, mid, new_winner)
                    st.rerun()

    st.divider()
    st.markdown('<div class="card"><h3>👥 Deelnemers</h3></div>', unsafe_allow_html=True)
    total_matches = len(df)
    for uid, name in all_users(con):
        cnt = con.execute("SELECT COUNT(*) FROM predictions WHERE user_id = ?", (uid,)).fetchone()[0]
        st.markdown(f"- **{name}** — {cnt}/{total_matches} voorspeld")


with tab_predict:
    render_predict_tab()
with tab_board:
    render_board_tab()
with tab_rules:
    render_rules_tab()
with tab_admin:
    render_admin_tab()

st.markdown(
    '<div style="text-align:center; color:rgba(255,255,255,0.6); font-size:11px; margin-top:24px;">'
    'Gemaakt voor het RBT directieteam · HumanTotalCare'
    '</div>',
    unsafe_allow_html=True,
)
