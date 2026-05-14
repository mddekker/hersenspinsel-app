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
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
#MainMenu, footer, header, .stDeployButton,
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"],
[data-testid="stMain"] { background: #080808 !important; color: #F1F0EC; }
body { font-family: 'Inter', -apple-system, sans-serif !important; }
.block-container { padding-top: 0 !important; padding-bottom: 80px !important; max-width: 480px !important; }
.login-logo { font-size: 64px; text-align: center; margin-bottom: 6px; }
.login-title {
    font-family: 'Barlow Condensed', sans-serif; font-size: 56px; font-weight: 900;
    letter-spacing: 2px; text-transform: uppercase; text-align: center;
    background: linear-gradient(135deg, #FFD700 0%, #FF4500 60%, #CC0000 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px;
}
.login-sub { font-size: 13px; color: #555; text-align: center; text-transform: uppercase; letter-spacing: 3px; margin-bottom: 44px; }
.app-header {
    background: linear-gradient(135deg, #1a0000, #2d0000, #1a0800);
    border-bottom: 2px solid #CC0000; padding: 18px 24px 20px; margin-bottom: 24px;
    box-shadow: 0 4px 32px rgba(200,0,0,0.3);
}
.app-header-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px; }
.app-header-title {
    font-family: 'Barlow Condensed', sans-serif; font-size: 28px; font-weight: 900;
    letter-spacing: 3px; text-transform: uppercase; color: #FFD700;
}
.app-header-user {
    font-size: 12px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
    background: rgba(204,0,0,0.3); border: 1px solid rgba(204,0,0,0.5);
    border-radius: 6px; padding: 4px 10px; color: #FF6666;
}
.app-header-sub { font-size: 11px; color: #4a3a2a; letter-spacing: 2px; text-transform: uppercase; }
.card {
    background: #111; border: 1px solid #222; border-left: 3px solid #CC0000;
    border-radius: 4px 16px 16px 4px; padding: 18px 20px; margin-bottom: 14px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}
.card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.avi { width: 40px; height: 40px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.avi-martin { background: linear-gradient(135deg, #7B0000, #CC0000); }
.avi-peter  { background: linear-gradient(135deg, #7B5C00, #CC9900); }
.avi-kasper { background: linear-gradient(135deg, #4B0000, #990000); }
.card-author { font-family: 'Barlow Condensed', sans-serif; font-weight: 700; font-size: 17px; letter-spacing: 1px; text-transform: uppercase; color: #F1F0EC; }
.card-time { font-size: 11px; color: #333; margin-left: auto; }
.card-body { font-size: 15px; color: #AAA; line-height: 1.6; white-space: pre-wrap; word-break: break-word; margin-bottom: 14px; }
.section-title { font-family: 'Barlow Condensed', sans-serif; font-size: 26px; font-weight: 900; letter-spacing: 2px; text-transform: uppercase; color: #FFD700; margin: 36px 0 2px; }
.section-sub { font-size: 12px; color: #444; margin-bottom: 16px; letter-spacing: 1px; text-transform: uppercase; }
.vote-chip { font-size: 12px; color: #555; margin-top: 4px; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #111 !important; border: 1px solid #333 !important; border-radius: 8px !important; color: #F1F0EC !important;
}
.stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder { color: #444 !important; }
.stButton > button { border-radius: 8px !important; font-weight: 600 !important; border: 1px solid #2a2a2a !important; background: #111 !important; color: #888 !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #8B0000, #CC0000) !important; border: none !important; color: #FFD700 !important; font-weight: 700 !important; box-shadow: 0 4px 16px rgba(180,0,0,0.4) !important; }
.stExpander { background: #0d0d0d !important; border: 1px solid #222 !important; border-radius: 12px !important; }
.stExpander summary { color: #CC0000 !important; font-weight: 700 !important; }
label { color: #444 !important; font-size: 12px !important; }
[data-testid="stFileUploadDropzone"] { background: #0d0d0d !important; }
</style>
""")


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
    <div style="height:32px"></div>
    <div class="login-logo">🏎️</div>
    <div class="login-title">Broers</div>
    <div class="login-sub">Exclusief — Martin · Peter · Kasper</div>
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
    <div class="app-header-title">🏎️ &nbsp;Broers</div>
    <div class="app-header-user">{AVI[author]} &nbsp;{author.upper()}</div>
  </div>
  <div class="app-header-sub">🍸 &nbsp;Tips &nbsp;·&nbsp; Foto's &nbsp;·&nbsp; Video's</div>
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
<div style="height:1px;background:rgba(255,255,255,0.08);margin:32px 0 0;"></div>
<div class="section-title">🛠️ Verbeter de app</div>
<div class="section-sub">Idee? Stuur het in. De anderen kunnen stemmen.</div>
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
