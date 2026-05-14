import sqlite3
import base64
import time
import datetime
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

DB_PATH = Path(__file__).parent / "broers.db"

# ─── Database backend ────────────────────────────────────────────────────────

def _pg_url():
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        return None

def get_db():
    url = _pg_url()
    if url:
        import psycopg2
        return psycopg2.connect(url, sslmode="require")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _q(sql):
    return sql.replace("?", "%s") if _pg_url() else sql

def _rows(cursor):
    if _pg_url():
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    return [dict(r) for r in cursor.fetchall()]

def _one(cursor):
    if _pg_url():
        row = cursor.fetchone()
        return dict(zip([d[0] for d in cursor.description], row)) if row else None
    row = cursor.fetchone()
    return dict(row) if row else None

def init_db():
    conn = get_db()
    cur = conn.cursor()
    if _pg_url():
        for sql in [
            """CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY, author TEXT NOT NULL, content TEXT,
                media_data BYTEA, media_mime TEXT, media_type TEXT,
                created_at DOUBLE PRECISION NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS reactions (
                id SERIAL PRIMARY KEY, post_id INTEGER NOT NULL,
                author TEXT NOT NULL, emoji TEXT NOT NULL,
                UNIQUE(post_id, author, emoji))""",
            """CREATE TABLE IF NOT EXISTS comments (
                id SERIAL PRIMARY KEY, post_id INTEGER NOT NULL,
                author TEXT NOT NULL, content TEXT NOT NULL,
                created_at DOUBLE PRECISION NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS suggestions (
                id SERIAL PRIMARY KEY, author TEXT NOT NULL,
                content TEXT NOT NULL, created_at DOUBLE PRECISION NOT NULL)""",
            """CREATE TABLE IF NOT EXISTS suggestion_votes (
                id SERIAL PRIMARY KEY, suggestion_id INTEGER NOT NULL,
                author TEXT NOT NULL, UNIQUE(suggestion_id, author))""",
        ]:
            cur.execute(sql)
        conn.commit()
    else:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT NOT NULL,
                content TEXT, media_data BLOB, media_mime TEXT, media_type TEXT,
                created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
                author TEXT NOT NULL, emoji TEXT NOT NULL, UNIQUE(post_id, author, emoji));
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL,
                author TEXT NOT NULL, content TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT NOT NULL,
                content TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS suggestion_votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, suggestion_id INTEGER NOT NULL,
                author TEXT NOT NULL, UNIQUE(suggestion_id, author));
        """)
    conn.close()

def add_post(author, content, mb, mm, mt):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("INSERT INTO posts (author,content,media_data,media_mime,media_type,created_at) VALUES (?,?,?,?,?,?)"),
                (author, content, mb, mm, mt, time.time()))
    conn.commit(); conn.close()

def get_posts():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY created_at DESC")
    rows = _rows(cur); conn.close(); return rows

def toggle_reaction(post_id, author, emoji):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("SELECT id FROM reactions WHERE post_id=? AND author=? AND emoji=?"), (post_id, author, emoji))
    row = _one(cur)
    if row: cur.execute(_q("DELETE FROM reactions WHERE id=?"), (row["id"],))
    else:   cur.execute(_q("INSERT INTO reactions (post_id,author,emoji) VALUES (?,?,?)"), (post_id, author, emoji))
    conn.commit(); conn.close()

def get_reactions(post_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("SELECT emoji, author FROM reactions WHERE post_id=?"), (post_id,))
    rows = _rows(cur); conn.close()
    counts, by_emoji = {}, {}
    for r in rows:
        counts[r["emoji"]] = counts.get(r["emoji"], 0) + 1
        by_emoji.setdefault(r["emoji"], []).append(r["author"])
    return counts, by_emoji

def add_comment(post_id, author, content):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("INSERT INTO comments (post_id,author,content,created_at) VALUES (?,?,?,?)"),
                (post_id, author, content, time.time()))
    conn.commit(); conn.close()

def get_comments(post_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("SELECT * FROM comments WHERE post_id=? ORDER BY created_at ASC"), (post_id,))
    rows = _rows(cur); conn.close(); return rows

def add_suggestion(author, content):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("INSERT INTO suggestions (author,content,created_at) VALUES (?,?,?)"),
                (author, content, time.time()))
    conn.commit(); conn.close()

def get_suggestions():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM suggestions ORDER BY created_at DESC")
    rows = _rows(cur); conn.close(); return rows

def toggle_vote(sid, author):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("SELECT id FROM suggestion_votes WHERE suggestion_id=? AND author=?"), (sid, author))
    row = _one(cur)
    if row: cur.execute(_q("DELETE FROM suggestion_votes WHERE id=?"), (row["id"],))
    else:   cur.execute(_q("INSERT INTO suggestion_votes (suggestion_id,author) VALUES (?,?)"), (sid, author))
    conn.commit(); conn.close()

def get_voters(sid):
    conn = get_db(); cur = conn.cursor()
    cur.execute(_q("SELECT author FROM suggestion_votes WHERE suggestion_id=?"), (sid,))
    rows = _rows(cur); conn.close()
    return [r["author"] for r in rows]

# ─── Config & helpers ────────────────────────────────────────────────────────

st.set_page_config(page_title="Broers", page_icon="🥂", layout="centered",
                   initial_sidebar_state="collapsed")

NAMES  = ["Martin", "Peter", "Kasper"]
AVI    = {"Martin": "👨", "Peter": "👦", "Kasper": "🧒"}
ACLS   = {"Martin": "am", "Peter": "ap", "Kasper": "ak"}
EMOJIS = ["❤️", "😂", "🔥", "👍", "😮", "🫶"]

def ago(ts):
    diff = datetime.datetime.now() - datetime.datetime.fromtimestamp(ts)
    if diff.days == 0:
        s = diff.seconds
        if s < 60:   return "zojuist"
        if s < 3600: return f"{s//60}m"
        return f"{s//3600}u"
    if diff.days == 1: return "gisteren"
    return datetime.datetime.fromtimestamp(ts).strftime("%-d %b")

# ─── CSS ─────────────────────────────────────────────────────────────────────

st.html("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
#MainMenu,footer,header,.stDeployButton,
[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"],
[data-testid="stMain"]{background:#07070C!important;color:#EEE8D5;font-family:'Inter',sans-serif!important}
.block-container{padding:0 0 120px 0!important;max-width:500px!important}

/* HERO */
.hero{
  padding:36px 24px 28px;
  background:linear-gradient(160deg,#110600 0%,#0a0008 50%,#000a14 100%);
  border-bottom:1px solid #111118;
  position:relative;overflow:hidden;
}
.hero::after{
  content:'';position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 90% 60% at 50% 0%,rgba(200,168,75,.09) 0%,transparent 65%);
}
.hero-label{font-size:10px;letter-spacing:5px;text-transform:uppercase;color:#3a3218;margin-bottom:10px}
.hero-title{
  font-family:'Bebas Neue',sans-serif;
  font-size:80px;letter-spacing:8px;line-height:.9;
  background:linear-gradient(160deg,#FFF8E1 0%,#C8A84B 45%,#7B5E00 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:12px;
}
.hero-sub{font-size:11px;letter-spacing:4px;text-transform:uppercase;color:#2a2418;margin-bottom:20px}
/* name tabs in hero */
.ntabs{display:flex;gap:8px;margin-top:4px}
.ntab{
  flex:1;padding:12px 4px 10px;text-align:center;cursor:pointer;
  background:#0d0d10;border:1px solid #1a1a22;border-radius:14px;
  text-decoration:none;transition:all .2s;
}
.ntab.active{background:#16140a;border-color:#C8A84B55;
  box-shadow:0 0 20px rgba(200,168,75,.1)}
.ntab-icon{font-size:28px;display:block;margin-bottom:4px}
.ntab-name{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:#333;font-weight:600}
.ntab.active .ntab-name{color:#C8A84B}

/* GREETING */
.greet{
  display:flex;align-items:center;gap:14px;
  padding:16px 20px;border-bottom:1px solid #0e0e14;
  background:#09090f;
}
.g-avi{
  width:48px;height:48px;border-radius:14px;
  display:flex;align-items:center;justify-content:center;
  font-size:26px;flex-shrink:0;
}
.am{background:linear-gradient(135deg,#3a0000,#8B0000);box-shadow:0 4px 16px rgba(139,0,0,.35)}
.ap{background:linear-gradient(135deg,#3a2c00,#856500);box-shadow:0 4px 16px rgba(133,101,0,.35)}
.ak{background:linear-gradient(135deg,#1a0038,#4B008A);box-shadow:0 4px 16px rgba(75,0,138,.35)}
.g-name{font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:3px;color:#EEE8D5;line-height:1}
.g-sub{font-size:11px;color:#282828;margin-top:2px;letter-spacing:1px}

/* CARDS */
.card{
  margin:0 0 2px;
  background:#0a0a10;
  border-top:1px solid #111118;border-bottom:1px solid #111118;
  padding:20px 20px 0;
}
.card-top{display:flex;align-items:center;gap:12px;margin-bottom:14px}
.c-avi{
  width:48px;height:48px;border-radius:13px;
  display:flex;align-items:center;justify-content:center;
  font-size:25px;flex-shrink:0;
}
.c-name{font-family:'Bebas Neue',sans-serif;font-size:30px;letter-spacing:3px;color:#EEE8D5;line-height:1}
.c-time{font-size:10px;color:#1e1e28;margin-left:auto;align-self:flex-start;padding-top:5px;letter-spacing:.5px}
.c-body{font-size:15px;color:#777;line-height:1.75;white-space:pre-wrap;word-break:break-word;margin-bottom:16px}
.c-foot{padding-bottom:16px}

/* COMMENTS */
.cmt{
  background:#06060b;border-radius:12px;padding:9px 14px;
  margin-top:6px;font-size:14px;color:#666;
  border:1px solid #111118;
}
.cmt-who{font-weight:600;color:#C8A84B;margin-right:7px;font-size:13px}

/* SECTION */
.gold-div{
  height:1px;margin:28px 0 0;
  background:linear-gradient(90deg,transparent,#C8A84B22,#C8A84B44,#C8A84B22,transparent);
}
.sec-title{
  font-family:'Bebas Neue',sans-serif;font-size:44px;letter-spacing:5px;
  background:linear-gradient(135deg,#FFF8E1,#C8A84B);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  padding:20px 20px 2px;
}
.sec-sub{font-size:10px;color:#252525;letter-spacing:2px;text-transform:uppercase;padding:0 20px 16px}
.vote-by{font-size:11px;color:#333;margin-top:3px;padding-left:2px}

/* STREAMLIT */
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:#0a0a10!important;border:1px solid #16161f!important;
  border-radius:14px!important;color:#EEE8D5!important;
  font-family:'Inter',sans-serif!important;font-size:15px!important;
  caret-color:#C8A84B;
}
.stTextInput>div>div>input::placeholder,.stTextArea>div>div>textarea::placeholder{color:#222!important}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:#C8A84B66!important;box-shadow:0 0 0 3px rgba(200,168,75,.08)!important}
.stButton>button{
  border-radius:12px!important;font-family:'Inter',sans-serif!important;
  font-weight:600!important;font-size:13px!important;
  border:1px solid #16161f!important;background:#0a0a10!important;color:#333!important;
}
.stButton>button:hover{border-color:#2a2a35!important;color:#666!important}
.stButton>button[kind="primary"]{
  background:linear-gradient(135deg,#120d00,#2a1e00)!important;
  border:1px solid #C8A84B44!important;color:#C8A84B!important;
  font-family:'Bebas Neue',sans-serif!important;
  font-size:18px!important;letter-spacing:3px!important;
  box-shadow:0 4px 24px rgba(200,168,75,.12)!important;
}
.stExpander{background:#09090f!important;border:1px solid #13131a!important;border-radius:16px!important;margin:0 0 8px!important}
.stExpander summary{color:#C8A84B!important;font-weight:600!important;font-size:13px!important;letter-spacing:.5px}
label{color:#1e1e28!important;font-size:12px!important}
[data-testid="stFileUploadDropzone"]{background:#09090f!important;border:1px dashed #16161f!important}
.stAlert{border-radius:12px!important}
</style>""")

# ─── Init ────────────────────────────────────────────────────────────────────

init_db()

if "show_comments" not in st.session_state:
    st.session_state["show_comments"] = {}

# ─── Wie ben je? (localStorage — geen herhaald inloggen) ─────────────────────

# JS injecteert de opgeslagen naam als query-param bij elke paginalading
components.html("""
<script>
(function(){
  var stored = localStorage.getItem('broers_user');
  var params = new URLSearchParams(window.parent.location.search);
  if (stored && !params.get('who')) {
    params.set('who', stored);
    window.parent.location.search = params.toString();
  }
})();
</script>
""", height=0)

who_param = st.query_params.get("who", "")
author = who_param if who_param in NAMES else None

# ─── Hero + naamkeuze ────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
  <div class="hero-label">Exclusief voor</div>
  <div class="hero-title">BROERS</div>
  <div class="hero-sub">Tips &nbsp;·&nbsp; Foto's &nbsp;·&nbsp; Video's &nbsp;·&nbsp; Avonturen</div>
  <div style="font-size:11px;color:#1e1810;letter-spacing:1px;margin-bottom:14px">Wie ben jij vandaag?</div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(3)
for i, name in enumerate(NAMES):
    with cols[i]:
        active = author == name
        if st.button(
            f"{AVI[name]}\n{name}",
            key=f"pick_{name}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            # Store in query params; JS will persist to localStorage
            st.query_params["who"] = name
            components.html(f"""
            <script>localStorage.setItem('broers_user','{name}');</script>
            """, height=0)
            st.rerun()

if not author:
    st.stop()

# ─── Greeting bar ────────────────────────────────────────────────────────────

st.markdown(f"""
<div class="greet">
  <div class="g-avi {ACLS[author]}">{AVI[author]}</div>
  <div>
    <div class="g-name">{author.upper()}</div>
    <div class="g-sub">Welkom terug</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ─── Nieuwe post ─────────────────────────────────────────────────────────────

with st.expander("  ＋  NIEUWE POST", expanded=False):
    new_content = st.text_area("", placeholder="Deel een tip, idee of bericht…",
                                height=90, label_visibility="collapsed")
    uploaded = st.file_uploader("Foto of video",
                                 type=["jpg","jpeg","png","gif","webp","mp4","mov","avi","webm"])
    pcol, _ = st.columns([1, 2])
    with pcol:
        if st.button("POSTEN", type="primary", use_container_width=True,
                     disabled=(not new_content.strip() and uploaded is None)):
            mb = mm = mt = None
            if uploaded:
                mb = uploaded.read(); mm = uploaded.type
                mt = "video" if uploaded.type.startswith("video") else "photo"
            add_post(author, new_content.strip(), mb, mm, mt)
            st.success("Geplaatst!")
            time.sleep(0.4)
            st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─── Feed ────────────────────────────────────────────────────────────────────

posts = get_posts()

if not posts:
    st.markdown("""
    <div style="text-align:center;padding:64px 24px">
      <div style="font-size:48px;margin-bottom:16px;opacity:.3">📭</div>
      <div style="font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:3px;color:#1e1e28">NOG NIKS GEDEELD</div>
      <div style="font-size:13px;color:#1a1a22;margin-top:6px;letter-spacing:1px">Wees de eerste</div>
    </div>""", unsafe_allow_html=True)
else:
    for post in posts:
        pid = post["id"]
        reactions, by_emoji = get_reactions(pid)
        comments = get_comments(pid)
        show_c = st.session_state["show_comments"].get(pid, False)
        acls = ACLS.get(post["author"], "am")

        st.markdown(f"""
        <div class="card">
          <div class="card-top">
            <div class="c-avi {acls}">{AVI.get(post["author"],"👤")}</div>
            <div class="c-name">{post["author"].upper()}</div>
            <div class="c-time">{ago(post["created_at"])}</div>
          </div>
          {"<div class='c-body'>" + post["content"] + "</div>" if post["content"] else ""}
        </div>""", unsafe_allow_html=True)

        if post["media_data"]:
            if post["media_type"] == "video":
                st.video(post["media_data"])
            else:
                b64 = base64.b64encode(bytes(post["media_data"])).decode()
                mime = post["media_mime"] or "image/jpeg"
                st.markdown(
                    f'<img src="data:{mime};base64,{b64}" style="width:100%;display:block;margin-bottom:2px"/>',
                    unsafe_allow_html=True)

        rcols = st.columns(len(EMOJIS) + 1)
        for i, emoji in enumerate(EMOJIS):
            count = reactions.get(emoji, 0)
            mine = author in by_emoji.get(emoji, [])
            with rcols[i]:
                if st.button(f"{emoji}{count}" if count else emoji,
                             key=f"r_{pid}_{emoji}", use_container_width=True,
                             type="primary" if mine else "secondary"):
                    toggle_reaction(pid, author, emoji); st.rerun()

        with rcols[-1]:
            n = len(comments)
            if st.button(f"💬{n}" if n else "💬", key=f"tc_{pid}", use_container_width=True):
                st.session_state["show_comments"][pid] = not show_c; st.rerun()

        if show_c:
            for c in comments:
                st.markdown(
                    f'<div class="cmt"><span class="cmt-who">{AVI.get(c["author"],"👤")} {c["author"]}</span>{c["content"]}</div>',
                    unsafe_allow_html=True)
            new_c = st.text_input("", key=f"ci_{pid}", placeholder="Reageer…",
                                  label_visibility="collapsed")
            sc, _ = st.columns([1, 3])
            with sc:
                if st.button("STUUR", key=f"sc_{pid}", type="primary"):
                    if new_c.strip():
                        add_comment(pid, author, new_c.strip()); st.rerun()

        st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ─── Verbeteringen ───────────────────────────────────────────────────────────

st.markdown("""
<div class="gold-div"></div>
<div class="sec-title">VERBETER DE APP</div>
<div class="sec-sub">Idee of wens? Stuur het in — de anderen stemmen mee</div>
""", unsafe_allow_html=True)

with st.expander("  ＋  NIEUW IDEE", expanded=False):
    sug = st.text_area("", placeholder="Bijv. notificaties, donkere modus, zoeken…",
                        height=80, label_visibility="collapsed", key="sug_in")
    sc2, _ = st.columns([1, 2])
    with sc2:
        if st.button("INSTUREN", disabled=not sug.strip(),
                     use_container_width=True, type="primary", key="sug_sub"):
            add_suggestion(author, sug.strip())
            st.success("Ingediend!")
            time.sleep(0.4); st.rerun()

for s in get_suggestions():
    sid = s["id"]
    voters = get_voters(sid)
    voted = author in voters
    acls = ACLS.get(s["author"], "am")

    st.markdown(f"""
    <div class="card">
      <div class="card-top">
        <div class="c-avi {acls}">{AVI.get(s["author"],"👤")}</div>
        <div class="c-name">{s["author"].upper()}</div>
        <div class="c-time">{ago(s["created_at"])}</div>
      </div>
      <div class="c-body">{s["content"]}</div>
      {"<div class='vote-by'>👍 " + "  ·  ".join(voters) + "</div>" if voters else ""}
      <div style='height:14px'></div>
    </div>""", unsafe_allow_html=True)

    vc, _ = st.columns([1, 3])
    with vc:
        label = ("✓ " if voted else "") + (f"👍 {len(voters)}" if voters else "👍")
        if st.button(label, key=f"v_{sid}", use_container_width=True,
                     type="primary" if voted else "secondary"):
            toggle_vote(sid, author); st.rerun()
