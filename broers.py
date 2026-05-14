import sqlite3
import base64
import time
import datetime
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

DB_PATH = Path(__file__).parent / "broers.db"

# ─── Inlogcodes ──────────────────────────────────────────────────────────────
CODES = {
    "Martin": "1234",
    "Peter":  "5678",
    "Kasper": "9012",
}

st.set_page_config(
    page_title="Broers",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.html("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; }

#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], [data-testid="stMain"] {
    background: #05050A !important; color: #EDE8D8;
    font-family: 'Inter', sans-serif !important;
}

/* ── Nacht-sfeer achtergrond ── */
[data-testid="stApp"]::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 100% 50% at 50% -10%, rgba(180,10,10,0.22) 0%, transparent 65%),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(160,120,0,0.12) 0%, transparent 55%),
        radial-gradient(ellipse 50% 30% at 0% 60%, rgba(100,0,0,0.10) 0%, transparent 50%);
}

.block-container {
    padding-top: 0 !important; padding-bottom: 80px !important;
    max-width: 480px !important; position: relative; z-index: 1;
}

/* ── Login ── */
.login-scene {
    text-align: center; padding: 48px 0 32px;
    background: linear-gradient(180deg, #1a0000 0%, #05050A 100%);
    margin: -1rem -1rem 32px; border-bottom: 1px solid #1a0000;
}
.login-icon { font-size: 80px; display: block; margin-bottom: 8px; }
.login-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 88px; letter-spacing: 8px; line-height: 0.9;
    background: linear-gradient(180deg, #FFE566 0%, #FFB800 40%, #CC4400 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: block; margin-bottom: 10px;
}
.login-tagline {
    font-size: 11px; letter-spacing: 5px; text-transform: uppercase;
    color: #3a2a2a; margin-bottom: 36px;
}
.login-deco {
    font-size: 28px; letter-spacing: 12px; opacity: 0.35;
    margin-bottom: 32px; display: block;
}

/* ── App header ── */
.app-header {
    background: linear-gradient(135deg, #130000 0%, #200000 50%, #0d0500 100%);
    border-bottom: 1px solid #2a0000;
    padding: 16px 20px 18px; margin-bottom: 20px;
    box-shadow: 0 8px 40px rgba(160,0,0,0.25);
    position: relative; overflow: hidden;
}
.app-header::before {
    content: '🏎️💨';
    position: absolute; right: -4px; top: 50%; transform: translateY(-50%);
    font-size: 52px; opacity: 0.12; letter-spacing: -4px;
}
.app-header-top { display: flex; align-items: center; justify-content: space-between; }
.app-header-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 38px; letter-spacing: 5px;
    background: linear-gradient(135deg, #FFE566, #FFB800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.app-header-user {
    font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
    background: rgba(180,0,0,0.25); border: 1px solid #5a0000;
    border-radius: 4px; padding: 5px 11px; color: #FF7070;
}
.app-header-sub {
    font-size: 10px; color: #2d1a1a; letter-spacing: 3px;
    text-transform: uppercase; margin-top: 2px;
}

/* ── Cards ── */
.card {
    background: linear-gradient(135deg, #0e0e0e 0%, #0a0a0a 100%);
    border: 1px solid #1c1c1c;
    border-top: 1px solid #252525;
    border-radius: 16px; padding: 20px; margin-bottom: 14px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,220,100,0.04);
    position: relative; overflow: hidden;
}
.card::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: linear-gradient(180deg, #FFB800, #CC0000);
}
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.avi {
    width: 52px; height: 52px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; flex-shrink: 0; border: 1px solid #2a2a2a;
}
.avi-martin { background: linear-gradient(135deg, #5a0000, #AA0000); box-shadow: 0 4px 16px rgba(170,0,0,0.4); }
.avi-peter  { background: linear-gradient(135deg, #5a4200, #AA7D00); box-shadow: 0 4px 16px rgba(170,125,0,0.4); }
.avi-kasper { background: linear-gradient(135deg, #3a0033, #880077); box-shadow: 0 4px 16px rgba(136,0,119,0.4); }

.card-author {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 32px; letter-spacing: 3px; color: #EDE8D8;
    text-shadow: 0 2px 12px rgba(255,180,0,0.15);
    line-height: 1;
}
.card-time { font-size: 10px; color: #2a2a2a; margin-left: auto; letter-spacing: 1px; align-self: flex-start; padding-top: 4px; }
.card-body { font-size: 15px; color: #888; line-height: 1.65; white-space: pre-wrap; word-break: break-word; margin-bottom: 14px; padding-left: 4px; }

/* ── Decoratieve scheidingslijn ── */
.vibe-strip {
    text-align: center; font-size: 18px; letter-spacing: 8px;
    opacity: 0.15; margin: 28px 0 4px;
}

/* ── Section titles ── */
.section-title {
    font-family: 'Bebas Neue', sans-serif; font-size: 40px; letter-spacing: 4px;
    background: linear-gradient(135deg, #FFE566, #FFB800);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 12px 0 2px;
}
.section-sub { font-size: 11px; color: #333; margin-bottom: 16px; letter-spacing: 2px; text-transform: uppercase; }
.vote-chip { font-size: 12px; color: #444; margin-top: 4px; }

/* ── Streamlit overrides ── */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #0d0d0d !important; border: 1px solid #222 !important;
    border-radius: 10px !important; color: #EDE8D8 !important;
    font-family: 'Inter', sans-serif !important; font-size: 15px !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: #333 !important; }
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #8B0000 !important; box-shadow: 0 0 0 2px rgba(140,0,0,0.2) !important;
}
.stButton > button {
    border-radius: 10px !important; font-weight: 600 !important; font-size: 13px !important;
    border: 1px solid #1e1e1e !important; background: #0d0d0d !important; color: #555 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7B0000, #CC0000) !important;
    border: none !important; color: #FFE566 !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 17px !important; letter-spacing: 2px !important;
    box-shadow: 0 6px 20px rgba(160,0,0,0.45) !important;
}
.stExpander { background: #0a0a0a !important; border: 1px solid #1a1a1a !important; border-radius: 12px !important; }
.stExpander summary { color: #8B0000 !important; font-weight: 700 !important; font-size: 14px !important; }
label { color: #333 !important; font-size: 12px !important; }
[data-testid="stFileUploadDropzone"] { background: #0a0a0a !important; border-color: #1a1a1a !important; }
.stAlert { border-radius: 10px !important; }
</style>""")


# ─── Database ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                author     TEXT NOT NULL,
                content    TEXT,
                media_data BLOB,
                media_mime TEXT,
                media_type TEXT,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reactions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id    INTEGER NOT NULL,
                author     TEXT NOT NULL,
                emoji      TEXT NOT NULL,
                UNIQUE(post_id, author, emoji)
            );
            CREATE TABLE IF NOT EXISTS comments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id    INTEGER NOT NULL,
                author     TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suggestions (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                author     TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id INTEGER NOT NULL,
                author        TEXT NOT NULL,
                UNIQUE(suggestion_id, author)
            );
        """)


def add_post(author, content, media_bytes, media_mime, media_type):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO posts (author,content,media_data,media_mime,media_type,created_at) VALUES (?,?,?,?,?,?)",
            (author, content, media_bytes, media_mime, media_type, time.time()),
        )


def get_posts():
    with get_db() as conn:
        return conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()


def toggle_reaction(post_id, author, emoji):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM reactions WHERE post_id=? AND author=? AND emoji=?",
            (post_id, author, emoji),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM reactions WHERE id=?", (row["id"],))
        else:
            conn.execute(
                "INSERT INTO reactions (post_id,author,emoji) VALUES (?,?,?)",
                (post_id, author, emoji),
            )


def get_reactions(post_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT emoji, author FROM reactions WHERE post_id=?", (post_id,)
        ).fetchall()
    counts, by_emoji = {}, {}
    for r in rows:
        counts[r["emoji"]] = counts.get(r["emoji"], 0) + 1
        by_emoji.setdefault(r["emoji"], []).append(r["author"])
    return counts, by_emoji


def add_comment(post_id, author, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (post_id,author,content,created_at) VALUES (?,?,?,?)",
            (post_id, author, content, time.time()),
        )


def get_comments(post_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM comments WHERE post_id=? ORDER BY created_at ASC", (post_id,)
        ).fetchall()


def add_suggestion(author, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO suggestions (author,content,created_at) VALUES (?,?,?)",
            (author, content, time.time()),
        )


def get_suggestions():
    with get_db() as conn:
        return conn.execute("SELECT * FROM suggestions ORDER BY created_at DESC").fetchall()


def toggle_vote(suggestion_id, author):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM suggestion_votes WHERE suggestion_id=? AND author=?",
            (suggestion_id, author),
        ).fetchone()
        if row:
            conn.execute("DELETE FROM suggestion_votes WHERE id=?", (row["id"],))
        else:
            conn.execute(
                "INSERT INTO suggestion_votes (suggestion_id,author) VALUES (?,?)",
                (suggestion_id, author),
            )


def get_voters(suggestion_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT author FROM suggestion_votes WHERE suggestion_id=?", (suggestion_id,)
        ).fetchall()
    return [r["author"] for r in rows]


# ─── Helpers ────────────────────────────────────────────────────────────────

AVI      = {"Martin": "👨", "Peter": "👦", "Kasper": "🧒"}
AVI_CLS  = {"Martin": "avi-martin", "Peter": "avi-peter", "Kasper": "avi-kasper"}
EMOJIS   = ["❤️", "😂", "🔥", "👍", "😮", "🫶"]


def ago(ts):
    diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(ts)
    if diff.days == 0:
        s = diff.seconds
        if s < 60:   return "zojuist"
        if s < 3600: return f"{s // 60}m"
        return f"{s // 3600}u"
    if diff.days == 1: return "gisteren"
    return datetime.datetime.fromtimestamp(ts).strftime("%-d %b")


# ─── Init ───────────────────────────────────────────────────────────────────

init_db()

if "user" not in st.session_state:
    st.session_state["user"] = None
if "show_comments" not in st.session_state:
    st.session_state["show_comments"] = {}

# ─── Login ──────────────────────────────────────────────────────────────────

if not st.session_state["user"]:
    st.markdown("""
    <div class="login-scene">
      <span class="login-icon">🏎️</span>
      <span class="login-title">BROERS</span>
      <span class="login-deco">💃 🥂 🏁</span>
      <span class="login-tagline">Alleen voor Martin &nbsp;·&nbsp; Peter &nbsp;·&nbsp; Kasper</span>
    </div>
    """, unsafe_allow_html=True)

    if "login_name" not in st.session_state:
        st.session_state["login_name"] = None

    cols = st.columns(3)
    for i, name in enumerate(["Martin", "Peter", "Kasper"]):
        with cols[i]:
            selected = st.session_state["login_name"] == name
            if st.button(
                f"{AVI[name]} {name}",
                key=f"pick_{name}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state["login_name"] = name
                st.rerun()

    if st.session_state["login_name"]:
        name = st.session_state["login_name"]
        st.markdown("<br>", unsafe_allow_html=True)
        code = st.text_input(
            f"Code van {name}",
            type="password",
            placeholder="Voer je code in",
            key="code_input",
        )
        login_col, _ = st.columns([1, 2])
        with login_col:
            if st.button("Inloggen →", type="primary", use_container_width=True):
                if code == CODES[name]:
                    st.session_state["user"] = name
                    st.rerun()
                else:
                    st.error("Verkeerde code. Probeer opnieuw.")
    st.stop()

# ─── App (ingelogd) ─────────────────────────────────────────────────────────

author = st.session_state["user"]

st.markdown(f"""
<div class="app-header">
  <div class="app-header-top">
    <div class="app-header-title">BROERS</div>
    <div class="app-header-user">{AVI[author]} {author.upper()}</div>
  </div>
  <div class="app-header-sub">💃 &nbsp; Tips · Foto's · Video's · Avonturen &nbsp; 🥂</div>
</div>
""", unsafe_allow_html=True)

logout_col, _ = st.columns([1, 4])
with logout_col:
    if st.button("Uitloggen", key="logout"):
        st.session_state["user"] = None
        st.session_state["login_name"] = None
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ─── Nieuwe post ────────────────────────────────────────────────────────────

with st.expander(f"➕  Nieuwe post", expanded=False):
    new_content = st.text_area(
        "Tekst",
        placeholder="Deel een tip, idee of bericht…",
        height=90,
        label_visibility="collapsed",
    )
    uploaded = st.file_uploader(
        "Foto of video (optioneel)",
        type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "webm"],
    )
    post_col, _ = st.columns([1, 2])
    with post_col:
        if st.button("📤 Posten", type="primary", use_container_width=True,
                     disabled=(not new_content.strip() and uploaded is None)):
            mb = mm = mt = None
            if uploaded:
                mb = uploaded.read()
                mm = uploaded.type
                mt = "video" if uploaded.type.startswith("video") else "photo"
            add_post(author, new_content.strip(), mb, mm, mt)
            st.success("Geplaatst! 🎉")
            time.sleep(0.5)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ─── Feed ────────────────────────────────────────────────────────────────────

posts = get_posts()

if not posts:
    st.markdown("""
    <div style="text-align:center;padding:60px 24px;color:#334155;">
        <div style="font-size:48px;margin-bottom:12px;">📭</div>
        <div style="font-size:16px;font-weight:600;color:#64748B;">Nog niks gedeeld</div>
        <div style="font-size:14px;color:#475569;margin-top:4px;">Wees de eerste!</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for post in posts:
        pid = post["id"]
        reactions, by_emoji = get_reactions(pid)
        comments = get_comments(pid)
        show_comments = st.session_state["show_comments"].get(pid, False)

        card_html = f"""
        <div class="card">
          <div class="card-header">
            <div class="avi {AVI_CLS.get(post['author'], 'avi-martin')}">{AVI.get(post['author'], '👤')}</div>
            <div>
              <div class="card-author">{post['author']}</div>
            </div>
            <div class="card-time">{ago(post['created_at'])}</div>
          </div>
          {"<div class='card-body'>" + post['content'] + "</div>" if post['content'] else ""}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        if post["media_data"]:
            if post["media_type"] == "video":
                st.video(post["media_data"])
            else:
                b64 = base64.b64encode(post["media_data"]).decode()
                mime = post["media_mime"] or "image/jpeg"
                st.markdown(
                    f'<img src="data:{mime};base64,{b64}" '
                    f'style="width:100%;border-radius:16px;margin:-6px 0 12px;" />',
                    unsafe_allow_html=True,
                )

        rcols = st.columns(len(EMOJIS) + 1)
        for i, emoji in enumerate(EMOJIS):
            count = reactions.get(emoji, 0)
            mine = author in by_emoji.get(emoji, [])
            with rcols[i]:
                if st.button(
                    f"{emoji} {count}" if count else emoji,
                    key=f"r_{pid}_{emoji}",
                    use_container_width=True,
                    type="primary" if mine else "secondary",
                ):
                    toggle_reaction(pid, author, emoji)
                    st.rerun()

        n = len(comments)
        with rcols[-1]:
            if st.button(f"💬 {n}" if n else "💬", key=f"tc_{pid}", use_container_width=True):
                st.session_state["show_comments"][pid] = not show_comments
                st.rerun()

        if show_comments:
            for c in comments:
                st.markdown(
                    f'<div style="background:rgba(255,255,255,0.05);border-radius:12px;'
                    f'padding:8px 14px;margin-top:6px;font-size:14px;color:#CBD5E1;">'
                    f'<span style="font-weight:700;color:#F1F5F9;margin-right:6px;">'
                    f'{AVI.get(c["author"],"👤")} {c["author"]}</span>{c["content"]}</div>',
                    unsafe_allow_html=True,
                )
            new_c = st.text_input("", key=f"ci_{pid}", placeholder="Reageer…",
                                  label_visibility="collapsed")
            sc, _ = st.columns([1, 3])
            with sc:
                if st.button("Stuur", key=f"sc_{pid}", type="primary"):
                    if new_c.strip():
                        add_comment(pid, author, new_c.strip())
                        st.rerun()

        st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)

# ─── Verbeteringen ───────────────────────────────────────────────────────────

st.markdown("""
<div class="vibe-strip">🏎️ 💃 🥂 🏁 💃 🏎️</div>
<div style="height:1px;background:linear-gradient(90deg,transparent,#3a0000,transparent);margin-bottom:24px;"></div>
<div class="section-title">VERBETER DE APP</div>
<div class="section-sub">Idee? Stuur het in — de anderen stemmen mee.</div>
""", unsafe_allow_html=True)

with st.expander("➕  Nieuw idee", expanded=False):
    sug_text = st.text_area("Idee", placeholder="Bijv. 'donkere modus', 'zoeken', 'notificaties'…",
                             height=80, label_visibility="collapsed", key="sug_in")
    sc2, _ = st.columns([1, 2])
    with sc2:
        if st.button("💡 Insturen", disabled=not sug_text.strip(),
                     use_container_width=True, type="primary", key="sug_submit"):
            add_suggestion(author, sug_text.strip())
            st.success("Ingediend!")
            time.sleep(0.5)
            st.rerun()

for s in get_suggestions():
    sid = s["id"]
    voters = get_voters(sid)
    voted = author in voters
    n_votes = len(voters)

    st.markdown(f"""
    <div class="card" style="margin-bottom:10px;">
      <div class="card-header">
        <div class="avi {AVI_CLS.get(s['author'],'avi-martin')}">{AVI.get(s['author'],'👤')}</div>
        <div><div class="card-author">{s['author']}</div></div>
        <div class="card-time">{ago(s['created_at'])}</div>
      </div>
      <div class="card-body" style="margin-bottom:6px;">{s['content']}</div>
      {"<div class='vote-chip'>👍 " + " · ".join(voters) + "</div>" if voters else ""}
    </div>
    """, unsafe_allow_html=True)

    vc, _ = st.columns([1, 3])
    with vc:
        if st.button(
            ("✓ " if voted else "") + (f"👍 {n_votes}" if n_votes else "👍"),
            key=f"v_{sid}",
            use_container_width=True,
            type="primary" if voted else "secondary",
        ):
            toggle_vote(sid, author)
            st.rerun()
