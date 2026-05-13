import sqlite3
import base64
import time
import datetime
import streamlit as st
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "broers.db"

st.set_page_config(
    page_title="Broers",
    page_icon="📸",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Broers">
<style>
    #MainMenu, footer, header, .stDeployButton { display: none !important; }
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 520px !important;
    }
    .app-title {
        font-size: 28px; font-weight: 700; color: #0F172A;
        text-align: center; margin-bottom: 2px; letter-spacing: -0.5px;
    }
    .app-subtitle {
        font-size: 14px; color: #64748B; text-align: center; margin-bottom: 20px;
    }
    .post-card {
        background: white; border-radius: 20px; padding: 18px 20px;
        margin-bottom: 16px; box-shadow: 0 2px 12px rgba(15,23,42,0.07);
        border: 1px solid #E2E8F0;
    }
    .post-header {
        display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
    }
    .avatar {
        width: 38px; height: 38px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px; flex-shrink: 0;
    }
    .avatar-martin { background: #DBEAFE; }
    .avatar-peter  { background: #D1FAE5; }
    .avatar-kasper { background: #FEF3C7; }
    .author-name { font-weight: 600; font-size: 15px; color: #0F172A; }
    .post-time { font-size: 12px; color: #94A3B8; margin-left: auto; }
    .post-content {
        font-size: 15px; color: #1E293B; line-height: 1.55;
        white-space: pre-wrap; word-break: break-word;
        margin-bottom: 12px;
    }
    .reactions-bar {
        display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px;
    }
    .reaction-chip {
        display: inline-flex; align-items: center; gap: 3px;
        background: #F1F5F9; border-radius: 20px;
        padding: 4px 10px; font-size: 14px; color: #475569;
        border: 1px solid #E2E8F0; cursor: pointer;
    }
    .reaction-chip.mine {
        background: #EFF6FF; border-color: #BFDBFE; color: #1D4ED8;
    }
    .reaction-count { font-size: 12px; font-weight: 600; }
    .comment-item {
        background: #F8FAFC; border-radius: 12px; padding: 8px 12px;
        margin-top: 6px; font-size: 14px; color: #334155;
    }
    .comment-author { font-weight: 600; color: #0F172A; margin-right: 6px; }
    .divider { height: 1px; background: #F1F5F9; margin: 8px 0; }
    .who-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: white; border: 2px solid #E2E8F0; border-radius: 14px;
        padding: 10px 16px; font-size: 15px; font-weight: 600;
        color: #0F172A; margin-bottom: 16px; width: 100%;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }
    .post-btn > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
        color: white !important; border: none !important;
        border-radius: 14px !important; padding: 14px !important;
        font-size: 16px !important; font-weight: 600 !important;
        width: 100% !important; box-shadow: 0 4px 14px rgba(99,102,241,0.35) !important;
    }
    .stButton > button {
        border-radius: 12px !important; font-size: 14px !important;
        padding: 8px 14px !important;
    }
    .empty-state {
        text-align: center; padding: 48px 24px; color: #94A3B8;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)


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
        """)


def add_post(author, content, media_bytes, media_mime, media_type):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO posts (author, content, media_data, media_mime, media_type, created_at) VALUES (?,?,?,?,?,?)",
            (author, content, media_bytes, media_mime, media_type, time.time()),
        )


def get_posts():
    with get_db() as conn:
        return conn.execute("SELECT * FROM posts ORDER BY created_at DESC").fetchall()


def toggle_reaction(post_id, author, emoji):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM reactions WHERE post_id=? AND author=? AND emoji=?",
            (post_id, author, emoji),
        ).fetchone()
        if existing:
            conn.execute("DELETE FROM reactions WHERE id=?", (existing["id"],))
        else:
            conn.execute(
                "INSERT INTO reactions (post_id, author, emoji) VALUES (?,?,?)",
                (post_id, author, emoji),
            )


def get_reactions(post_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT emoji, author FROM reactions WHERE post_id=?", (post_id,)
        ).fetchall()
    counts = {}
    authors_per_emoji = {}
    for r in rows:
        counts[r["emoji"]] = counts.get(r["emoji"], 0) + 1
        authors_per_emoji.setdefault(r["emoji"], []).append(r["author"])
    return counts, authors_per_emoji


def add_comment(post_id, author, content):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (post_id, author, content, created_at) VALUES (?,?,?,?)",
            (post_id, author, content, time.time()),
        )


def get_comments(post_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM comments WHERE post_id=? ORDER BY created_at ASC", (post_id,)
        ).fetchall()


# ─── Helpers ────────────────────────────────────────────────────────────────

AVATAR = {"Martin": "👨", "Peter": "👦", "Kasper": "🧒"}
AVATAR_CLASS = {"Martin": "avatar-martin", "Peter": "avatar-peter", "Kasper": "avatar-kasper"}
EMOJIS = ["❤️", "😂", "🔥", "👍", "😮", "🫶"]


def format_time(ts):
    dt = datetime.datetime.fromtimestamp(ts)
    now = datetime.datetime.now()
    diff = now - dt
    if diff.seconds < 60 and diff.days == 0:
        return "zojuist"
    if diff.seconds < 3600 and diff.days == 0:
        return f"{diff.seconds // 60}m geleden"
    if diff.days == 0:
        return f"{diff.seconds // 3600}u geleden"
    if diff.days == 1:
        return "gisteren"
    return dt.strftime("%-d %b")


# ─── Init ───────────────────────────────────────────────────────────────────

init_db()

if "author" not in st.session_state:
    st.session_state["author"] = "Martin"
if "show_comments" not in st.session_state:
    st.session_state["show_comments"] = {}
if "comment_text" not in st.session_state:
    st.session_state["comment_text"] = {}

# ─── Header ─────────────────────────────────────────────────────────────────

st.markdown('<div class="app-title">📸 Broers</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Tips, foto\'s en video\'s met Martin, Peter & Kasper</div>', unsafe_allow_html=True)

# Wie ben je?
cols = st.columns(3)
for i, name in enumerate(["Martin", "Peter", "Kasper"]):
    with cols[i]:
        active = st.session_state["author"] == name
        label = f"{'✓ ' if active else ''}{AVATAR[name]} {name}"
        if st.button(label, key=f"who_{name}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state["author"] = name
            st.rerun()

author = st.session_state["author"]
st.markdown("<br>", unsafe_allow_html=True)

# ─── Nieuwe post ────────────────────────────────────────────────────────────

with st.expander(f"➕  Nieuwe post als {AVATAR[author]} {author}", expanded=False):
    new_content = st.text_area(
        "Tekst (tip, bericht, idee…)",
        placeholder="Deel iets met je broers…",
        height=100,
        label_visibility="collapsed",
    )
    uploaded = st.file_uploader(
        "Foto of video",
        type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "webm"],
        label_visibility="visible",
    )

    submit_col, _ = st.columns([1, 2])
    with submit_col:
        post_disabled = not new_content.strip() and uploaded is None
        if st.button("📤 Posten", disabled=post_disabled, use_container_width=True, type="primary"):
            media_bytes = None
            media_mime = None
            media_type = None
            if uploaded:
                media_bytes = uploaded.read()
                media_mime = uploaded.type
                media_type = "video" if uploaded.type.startswith("video") else "photo"
            add_post(author, new_content.strip(), media_bytes, media_mime, media_type)
            st.success("Geplaatst! 🎉")
            time.sleep(0.6)
            st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ─── Feed ────────────────────────────────────────────────────────────────────

posts = get_posts()

if not posts:
    st.markdown("""
    <div class="empty-state">
        📭<br><br>
        Nog geen posts.<br>
        Wees de eerste — deel een tip, foto of video!
    </div>
    """, unsafe_allow_html=True)
else:
    for post in posts:
        pid = post["id"]
        reactions, authors_per_emoji = get_reactions(pid)
        comments = get_comments(pid)
        show_comments = st.session_state["show_comments"].get(pid, False)

        # ── Post card (HTML) ──
        avatar_cls = AVATAR_CLASS.get(post["author"], "avatar-martin")
        avatar_icon = AVATAR.get(post["author"], "👤")
        time_str = format_time(post["created_at"])

        header_html = f"""
        <div class="post-card">
          <div class="post-header">
            <div class="avatar {avatar_cls}">{avatar_icon}</div>
            <div>
              <div class="author-name">{post["author"]}</div>
            </div>
            <div class="post-time">{time_str}</div>
          </div>
        """
        if post["content"]:
            header_html += f'<div class="post-content">{post["content"]}</div>'
        header_html += "</div>"

        st.markdown(header_html, unsafe_allow_html=True)

        # ── Media ──
        if post["media_data"]:
            if post["media_type"] == "video":
                st.video(post["media_data"])
            else:
                img_b64 = base64.b64encode(post["media_data"]).decode()
                mime = post["media_mime"] or "image/jpeg"
                st.markdown(
                    f'<img src="data:{mime};base64,{img_b64}" style="width:100%;border-radius:14px;margin-bottom:10px;" />',
                    unsafe_allow_html=True,
                )

        # ── Reactions row ──
        reaction_cols = st.columns(len(EMOJIS) + 1)
        for i, emoji in enumerate(EMOJIS):
            count = reactions.get(emoji, 0)
            mine = author in authors_per_emoji.get(emoji, [])
            label = f"{emoji} {count}" if count else emoji
            with reaction_cols[i]:
                if st.button(label, key=f"react_{pid}_{emoji}",
                             use_container_width=True,
                             type="primary" if mine else "secondary"):
                    toggle_reaction(pid, author, emoji)
                    st.rerun()

        # ── Comments toggle ──
        n_comments = len(comments)
        comment_label = f"💬 {n_comments}" if n_comments else "💬"
        with reaction_cols[-1]:
            if st.button(comment_label, key=f"toggle_comments_{pid}", use_container_width=True):
                st.session_state["show_comments"][pid] = not show_comments
                st.rerun()

        # ── Comments section ──
        if show_comments:
            if comments:
                for c in comments:
                    st.markdown(
                        f'<div class="comment-item">'
                        f'<span class="comment-author">{AVATAR.get(c["author"], "👤")} {c["author"]}</span>'
                        f'{c["content"]}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

            comment_key = f"comment_input_{pid}"
            new_comment = st.text_input(
                "Reageer…",
                key=comment_key,
                placeholder="Typ je reactie…",
                label_visibility="collapsed",
            )
            send_col, _ = st.columns([1, 3])
            with send_col:
                if st.button("Stuur", key=f"send_comment_{pid}", type="primary"):
                    if new_comment.strip():
                        add_comment(pid, author, new_comment.strip())
                        st.rerun()

        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)
