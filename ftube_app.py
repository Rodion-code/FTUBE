import streamlit as st
import tempfile
import os
import json
import requests
import re
import hashlib
from supabase import create_client

st.set_page_config(page_title="FTUBE", page_icon="▶", layout="wide")

# ── Supabase 연결 ─────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background-color: #111318 !important;
    color: #d4d8e2;
    font-family: 'Inter', sans-serif;
}
[data-testid="stAppViewContainer"] > .main {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 28px;
}
[data-testid="block-container"] {
    padding: 28px 0 60px 0 !important;
    max-width: 100% !important;
}
.ftube-header {
    padding: 22px 0 18px 0;
    border-bottom: 1px solid #1e2230;
    margin-bottom: 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.ftube-logo { font-size: 1rem; font-weight: 700; letter-spacing: 0.18em; color: #e8ecf4; }
.ftube-logo span { color: #5b8af5; }
.header-sub { font-size: 0.7rem; color: #3a3f52; letter-spacing: 0.1em; }
.header-user { font-size: 0.78rem; color: #5b8af5; }

[data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid #1e2230 !important;
    gap: 8px !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    color: #4a5068 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    padding: 12px 32px !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    transition: color 0.2s !important;
    min-width: 100px !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #c8d0e8 !important;
    border-bottom: 2px solid #5b8af5 !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"]:hover { color: #8890aa !important; }
[data-testid="stTabContent"] { padding-top: 28px !important; }

.section-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    color: #3a3f52;
    text-transform: uppercase;
    margin-bottom: 14px;
}

.stTextInput input {
    background-color: #161b27 !important;
    border: 1px solid #1e2230 !important;
    border-radius: 8px !important;
    color: #d4d8e2 !important;
    padding: 11px 16px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.87rem !important;
    width: 100% !important;
    transition: border-color 0.2s !important;
}
.stTextInput input:focus {
    border-color: #5b8af5 !important;
    box-shadow: 0 0 0 3px rgba(91,138,245,0.08) !important;
    outline: none !important;
}
.stTextInput input::placeholder { color: #3a3f52 !important; }

.stButton button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    background-color: #5b8af5 !important;
    color: #fff !important;
    border: none !important;
    padding: 10px 18px !important;
}
.stButton button:hover { background-color: #4a79e4 !important; }

.btn-ghost button {
    background-color: transparent !important;
    border: 1px solid #1e2230 !important;
    color: #4a5068 !important;
    padding: 8px 14px !important;
}
.btn-ghost button:hover {
    border-color: #2e3450 !important;
    color: #8890aa !important;
    background-color: #161b27 !important;
}
.btn-fav button {
    background-color: transparent !important;
    border: 1px solid #1e2230 !important;
    color: #5b8af5 !important;
    padding: 8px 14px !important;
}
.btn-fav button:hover { background-color: #161b27 !important; border-color: #2e3450 !important; }
.btn-sm button {
    background-color: transparent !important;
    border: 1px solid #1e2230 !important;
    color: #4a5068 !important;
    padding: 5px 10px !important;
    font-size: 0.75rem !important;
}
.btn-sm button:hover { color: #8890aa !important; background-color: #161b27 !important; }

.search-card {
    background: #161b27;
    border: 1px solid #1e2230;
    border-radius: 10px;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.search-card:hover { border-color: #2e3450; transform: translateY(-2px); }
.search-thumb { width: 100%; aspect-ratio: 16/9; object-fit: cover; display: block; }
.search-thumb-placeholder { width: 100%; aspect-ratio: 16/9; background: #1e2230; display: flex; align-items: center; justify-content: center; font-size: 2rem; }
.search-info { padding: 12px 14px 14px; }
.search-title { font-size: 0.83rem; font-weight: 500; color: #c8d0e8; line-height: 1.45; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 6px; min-height: 2.4em; }
.search-meta { font-size: 0.7rem; color: #3a3f52; }

.fav-card { background: #161b27; border: 1px solid #1e2230; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.fav-card:hover { border-color: #2e3450; }
.fav-title { font-size: 0.85rem; color: #c8d0e8; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fav-url { font-size: 0.7rem; color: #3a3f52; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fav-empty { text-align: center; padding: 52px 0; color: #2e3450; font-size: 0.82rem; line-height: 1.8; }

.pl-card { background: #161b27; border: 1px solid #1e2230; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.pl-card:hover { border-color: #2e3450; }
.pl-name { font-size: 0.88rem; color: #c8d0e8; font-weight: 500; }
.pl-count { font-size: 0.72rem; color: #3a3f52; margin-top: 3px; }
.pl-item { background: #13181f; border: 1px solid #1e2230; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }
.pl-item-title { font-size: 0.82rem; color: #c8d0e8; }
.pl-item-url { font-size: 0.68rem; color: #3a3f52; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.player-wrap { background: #13181f; border: 1px solid #1e2230; border-radius: 12px; overflow: hidden; padding: 22px; }
.player-title { font-size: 1rem; font-weight: 500; color: #d4d8e2; margin-top: 18px; line-height: 1.45; }
.player-sub { font-size: 0.73rem; color: #2e3450; margin-top: 6px; }

.auth-wrap { max-width: 360px; margin: 20px auto; background: #161b27; border: 1px solid #1e2230; border-radius: 12px; padding: 24px; }
.auth-title { font-size: 1rem; font-weight: 600; color: #e8ecf4; margin-bottom: 16px; text-align: center; }

hr { border-color: #1e2230 !important; margin: 22px 0 !important; }
[data-testid="stHorizontalBlock"] { gap: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ── 헬퍼 ──────────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def sinit(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

sinit("view", "home")
sinit("url", "")
sinit("title", "")
sinit("local_tmp", None)
sinit("edit_fav_idx", None)
sinit("pl_open", None)
sinit("pl_queue", [])
sinit("pl_pos", 0)
sinit("search_results", [])
sinit("search_query", "")
sinit("search_page", 1)
sinit("search_bonus", "")
sinit("user", None)        # 로그인한 유저 {id, username}
sinit("auth_mode", "login")  # login / register

def get_favorites():
    if not st.session_state.user:
        return []
    res = sb.table("favorites").select("*").eq("user_id", st.session_state.user["id"]).execute()
    return res.data or []

def get_playlists():
    if not st.session_state.user:
        return []
    res = sb.table("playlists").select("*").eq("user_id", st.session_state.user["id"]).execute()
    return res.data or []

def toggle_fav(title, url):
    if not st.session_state.user:
        return
    uid = st.session_state.user["id"]
    existing = sb.table("favorites").select("id").eq("user_id", uid).eq("url", url).execute()
    if existing.data:
        sb.table("favorites").delete().eq("id", existing.data[0]["id"]).execute()
    else:
        sb.table("favorites").insert({"user_id": uid, "title": title, "url": url}).execute()

def is_fav(url):
    if not st.session_state.user:
        return False
    uid = st.session_state.user["id"]
    res = sb.table("favorites").select("id").eq("user_id", uid).eq("url", url).execute()
    return bool(res.data)

def play(url, title, queue=None, pos=0):
    st.session_state.url      = url
    st.session_state.title    = title
    st.session_state.view     = "player"
    st.session_state.pl_queue = queue or []
    st.session_state.pl_pos   = pos
    # 재생기록 저장
    if st.session_state.user and url and not url.endswith(".mp4"):
        try:
            sb.table("history").insert({
                "user_id": st.session_state.user["id"],
                "title": title,
                "url": url
            }).execute()
        except: pass
    st.rerun()

def get_history(limit=50):
    if not st.session_state.user:
        return []
    res = sb.table("history").select("*").eq("user_id", st.session_state.user["id"]).order("watched_at", desc=True).limit(limit).execute()
    return res.data or []

def get_recommendations():
    history = get_history(20)
    if not history:
        return []
    # 최근 본 영상 제목에서 키워드 추출
    keywords = []
    for h in history[:5]:
        words = h["title"].split()
        keywords.extend([w for w in words if len(w) > 1])
    if not keywords:
        return []
    # 가장 많이 나온 키워드로 검색
    from collections import Counter
    top_keyword = Counter(keywords).most_common(1)[0][0]
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
        resp = requests.get(f"https://www.youtube.com/results?search_query={requests.utils.quote(top_keyword)}", headers=headers)
        raw = re.findall(r'var ytInitialData = ({.*?});</script>', resp.text)
        if not raw:
            return []
        data = json.loads(raw[0])
        items = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
        results = []
        for item in items:
            if "videoRenderer" in item and len(results) < 6:
                v = item["videoRenderer"]
                vid_id   = v.get("videoId", "")
                title    = v.get("title", {}).get("runs", [{}])[0].get("text", "")
                channel  = v.get("ownerText", {}).get("runs", [{}])[0].get("text", "")
                duration = v.get("lengthText", {}).get("simpleText", "")
                thumbs   = v.get("thumbnail", {}).get("thumbnails", [])
                thumb    = thumbs[-1]["url"] if thumbs else None
                results.append({"id": vid_id, "title": title, "channel": {"name": channel}, "duration": duration, "thumbnails": [{"url": thumb}] if thumb else []})
        return results, top_keyword
    except:
        return [], ""

def yt_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"

def clean_tmp():
    if st.session_state.local_tmp and os.path.exists(st.session_state.local_tmp):
        os.unlink(st.session_state.local_tmp)
        st.session_state.local_tmp = None

# ══════════════════════════════════════════════════════
# 로그인 / 회원가입 화면
# ══════════════════════════════════════════════════════
if not st.session_state.user:
    st.markdown("""
    <div class="ftube-header">
        <span class="ftube-logo">F<span>TUBE</span></span>
        <span class="header-sub">광고 없는 플레이어</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)

    if st.session_state.auth_mode == "login":
        st.markdown('<div class="auth-title">로그인</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("아이디", placeholder="아이디 입력")
            password = st.text_input("비밀번호", placeholder="비밀번호 입력", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)
            if submitted:
                if username and password:
                    res = sb.table("users").select("*").eq("username", username).eq("password", hash_pw(password)).execute()
                    if res.data:
                        st.session_state.user = {"id": res.data[0]["id"], "username": res.data[0]["username"]}
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀렸어.")
                else:
                    st.warning("아이디와 비밀번호를 입력해줘.")

        st.write("")
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("계정이 없어? 회원가입", use_container_width=True):
            st.session_state.auth_mode = "register"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown('<div class="auth-title">회원가입</div>', unsafe_allow_html=True)
        with st.form("register_form"):
            username = st.text_input("아이디", placeholder="사용할 아이디")
            password = st.text_input("비밀번호", placeholder="비밀번호", type="password")
            password2 = st.text_input("비밀번호 확인", placeholder="비밀번호 재입력", type="password")
            submitted = st.form_submit_button("가입하기", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.warning("아이디와 비밀번호를 입력해줘.")
                elif password != password2:
                    st.error("비밀번호가 일치하지 않아.")
                else:
                    existing = sb.table("users").select("id").eq("username", username).execute()
                    if existing.data:
                        st.error("이미 있는 아이디야.")
                    else:
                        sb.table("users").insert({"username": username, "password": hash_pw(password)}).execute()
                        st.success("가입 완료! 로그인해봐.")
                        st.session_state.auth_mode = "login"
                        st.rerun()

        st.write("")
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("이미 계정 있어? 로그인", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════
# 헤더 (로그인 후)
# ══════════════════════════════════════════════════════
col_logo, col_user = st.columns([4, 1])
with col_logo:
    st.markdown("""
    <div class="ftube-header">
        <span class="ftube-logo">F<span>TUBE</span></span>
        <span class="header-sub">광고 없는 플레이어</span>
    </div>
    """, unsafe_allow_html=True)
with col_user:
    st.write("")
    st.write("")
    st.markdown(f'<div class="header-user">👤 {st.session_state.user["username"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 홈
# ══════════════════════════════════════════════════════
if st.session_state.view == "home":

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["추천", "검색", "URL / 파일", "즐겨찾기", "플레이리스트", "기록"])

    # ── 탭1: 추천 ─────────────────────────────────────
    with tab1:
        st.markdown('<div class="section-label">회원님을 위한 추천</div>', unsafe_allow_html=True)
        rec_result = get_recommendations()
        if not rec_result or not rec_result[0]:
            st.markdown('<div class="fav-empty">영상을 몇 개 보면<br>취향에 맞는 영상을 추천해줄게.</div>', unsafe_allow_html=True)
        else:
            recs, keyword = rec_result
            st.markdown(f'<div style="font-size:0.72rem;color:#3a3f52;margin-bottom:16px;">"{keyword}" 기반 추천</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            for i, r in enumerate(recs):
                vid_id    = r.get("id", "")
                title     = r.get("title", "제목 없음")
                channel   = r.get("channel", {}).get("name", "")
                duration  = r.get("duration", "")
                thumbs    = r.get("thumbnails", [])
                thumb_url = thumbs[0]["url"] if thumbs else None
                url       = yt_url(vid_id)
                with cols[i % 3]:
                    if thumb_url:
                        st.markdown(f'''<div class="search-card"><img class="search-thumb" src="{thumb_url}" /><div class="search-info"><div class="search-title">{title}</div><div class="search-meta">{channel} · {duration}</div></div></div>''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''<div class="search-card"><div class="search-thumb-placeholder">▶</div><div class="search-info"><div class="search-title">{title}</div><div class="search-meta">{channel} · {duration}</div></div></div>''', unsafe_allow_html=True)
                    bc, fc = st.columns([3, 1])
                    with bc:
                        if st.button("▶ 재생", key=f"rec_play_{i}", use_container_width=True):
                            play(url, title)
                    with fc:
                        st.markdown('<div class="btn-fav">', unsafe_allow_html=True)
                        if st.button("☆", key=f"rec_fav_{i}", use_container_width=True):
                            toggle_fav(title, url)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")

    # ── 탭2: 검색 ─────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-label">YouTube 검색</div>', unsafe_allow_html=True)
        with st.form(key="search_form"):
            s1, s2 = st.columns([5, 1])
            with s1:
                query = st.text_input("", placeholder="검색어 입력", label_visibility="collapsed")
            with s2:
                search_btn = st.form_submit_button("검색", use_container_width=True)

        if search_btn and query.strip():
            with st.spinner("검색 중..."):
                try:
                    # 재생기록 기반 키워드 추출해서 검색어 보강
                    history = get_history(10)
                    bonus_keyword = ""
                    if history:
                        from collections import Counter
                        words = []
                        for h in history[:5]:
                            words.extend([w for w in h["title"].split() if len(w) > 1])
                        if words:
                            top = Counter(words).most_common(3)
                            # 검색어랑 겹치지 않는 키워드만 추가
                            for w, _ in top:
                                if w not in query.strip():
                                    bonus_keyword = w
                                    break
                    final_query = (query.strip() + " " + bonus_keyword).strip()
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
                    resp = requests.get(f"https://www.youtube.com/results?search_query={requests.utils.quote(final_query)}", headers=headers)
                    raw = re.findall(r'var ytInitialData = ({.*?});</script>', resp.text)
                    if not raw:
                        st.error("검색 결과를 가져오지 못했어.")
                    else:
                        data = json.loads(raw[0])
                        items = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"]["contents"]
                        results = []
                        for item in items:
                            if "videoRenderer" in item and len(results) < 27:
                                v = item["videoRenderer"]
                                vid_id   = v.get("videoId", "")
                                title    = v.get("title", {}).get("runs", [{}])[0].get("text", "제목 없음")
                                channel  = v.get("ownerText", {}).get("runs", [{}])[0].get("text", "")
                                duration = v.get("lengthText", {}).get("simpleText", "")
                                thumbs   = v.get("thumbnail", {}).get("thumbnails", [])
                                thumb    = thumbs[-1]["url"] if thumbs else None
                                results.append({"id": vid_id, "title": title, "channel": {"name": channel}, "duration": duration, "thumbnails": [{"url": thumb}] if thumb else []})
                        st.session_state.search_results = results
                        st.session_state.search_query   = query.strip()
                        st.session_state.search_page    = 1
                        st.session_state.search_bonus   = bonus_keyword
                except Exception as e:
                    st.error(f"검색 실패: {e}")

        if st.session_state.search_results:
            st.write("")
            if st.session_state.search_bonus:
                st.markdown(f'<div style="font-size:0.72rem;color:#3a3f52;margin-bottom:12px;">🎯 "{st.session_state.search_bonus}" 키워드 반영됨</div>', unsafe_allow_html=True)
            page    = st.session_state.search_page
            visible = st.session_state.search_results[:page * 9]
            cols    = st.columns(3)
            for i, r in enumerate(visible):
                vid_id    = r.get("id", "")
                title     = r.get("title", "제목 없음")
                channel   = r.get("channel", {}).get("name", "")
                duration  = r.get("duration", "")
                thumbs    = r.get("thumbnails", [])
                thumb_url = thumbs[0]["url"] if thumbs else None
                url       = yt_url(vid_id)

                with cols[i % 3]:
                    if thumb_url:
                        st.markdown(f'''<div class="search-card"><img class="search-thumb" src="{thumb_url}" /><div class="search-info"><div class="search-title">{title}</div><div class="search-meta">{channel} · {duration}</div></div></div>''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''<div class="search-card"><div class="search-thumb-placeholder">▶</div><div class="search-info"><div class="search-title">{title}</div><div class="search-meta">{channel} · {duration}</div></div></div>''', unsafe_allow_html=True)

                    bc, fc = st.columns([3, 1])
                    with bc:
                        if st.button("▶ 재생", key=f"sr_play_{i}", use_container_width=True):
                            play(url, title)
                    with fc:
                        st.markdown('<div class="btn-fav">', unsafe_allow_html=True)
                        if st.button("☆", key=f"sr_fav_{i}", use_container_width=True):
                            toggle_fav(title, url)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")

            if len(st.session_state.search_results) > page * 9:
                st.write("")
                if st.button("더 보기", key="load_more", use_container_width=False):
                    st.session_state.search_page += 1
                    st.rerun()

    # ── 탭3: URL / 파일 ───────────────────────────────
    with tab3:
        st.markdown('<div class="section-label">URL로 재생</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([5, 1])
        with c1:
            url_input = st.text_input("", placeholder="YouTube 링크 또는 MP4 주소 붙여넣기", label_visibility="collapsed", key="url_input")
        with c2:
            if st.button("재생", use_container_width=True, key="url_play"):
                if url_input.strip():
                    play(url_input.strip(), "외부 영상")
                else:
                    st.warning("URL을 입력해주세요.")

        if url_input.strip():
            ca, cb = st.columns([2, 4])
            with ca:
                st.markdown('<div class="btn-fav">', unsafe_allow_html=True)
                if st.button("☆ 즐겨찾기 추가", key="url_fav"):
                    toggle_fav("외부 영상", url_input.strip())
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-label">로컬 파일 재생</div>', unsafe_allow_html=True)
        st.caption("mp4 파일을 올려주세요.")
        f = st.file_uploader("", type=["mp4"], label_visibility="collapsed", key="file_up")
        if f:
            clean_tmp()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.write(f.getvalue())
            tmp.close()
            st.session_state.local_tmp = tmp.name
            play(tmp.name, f.name)

    # ── 탭4: 즐겨찾기 ─────────────────────────────────
    with tab4:
        st.markdown('<div class="section-label">저장된 영상</div>', unsafe_allow_html=True)
        favs = get_favorites()
        if not favs:
            st.markdown('<div class="fav-empty">저장된 영상이 없어.<br>☆ 버튼으로 추가해봐.</div>', unsafe_allow_html=True)
        else:
            for idx, fv in enumerate(favs):
                if st.session_state.edit_fav_idx == fv["id"]:
                    new_title = st.text_input("제목 수정", value=fv["title"], key=f"edit_title_{idx}")
                    sc1, sc2 = st.columns([1, 1])
                    with sc1:
                        if st.button("저장", key=f"save_edit_{idx}", use_container_width=True):
                            sb.table("favorites").update({"title": new_title}).eq("id", fv["id"]).execute()
                            st.session_state.edit_fav_idx = None
                            st.rerun()
                    with sc2:
                        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                        if st.button("취소", key=f"cancel_edit_{idx}", use_container_width=True):
                            st.session_state.edit_fav_idx = None
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="fav-card"><div class="fav-title">{fv['title']}</div><div class="fav-url">{fv['url'][:70]}{'...' if len(fv['url']) > 70 else ''}</div></div>""", unsafe_allow_html=True)
                    pc, ec, dc = st.columns([3, 1, 1])
                    with pc:
                        if st.button("▶ 재생", key=f"fp_{idx}", use_container_width=True):
                            play(fv["url"], fv["title"])
                    with ec:
                        st.markdown('<div class="btn-sm">', unsafe_allow_html=True)
                        if st.button("수정", key=f"edit_{idx}", use_container_width=True):
                            st.session_state.edit_fav_idx = fv["id"]
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    with dc:
                        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"fd_{idx}", use_container_width=True):
                            sb.table("favorites").delete().eq("id", fv["id"]).execute()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                st.write("")

    # ── 탭5: 플레이리스트 ─────────────────────────────
    with tab5:
        pls = get_playlists()

        if st.session_state.pl_open is not None:
            pi  = st.session_state.pl_open
            pld = next((p for p in pls if p["id"] == pi), None)
            if not pld:
                st.session_state.pl_open = None
                st.rerun()

            items = json.loads(pld["items"] or "[]")

            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if st.button("← 목록으로", key="pl_back", use_container_width=False):
                st.session_state.pl_open = None
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.write("")
            st.markdown(f'<div class="section-label">{pld["name"]}</div>', unsafe_allow_html=True)

            if items:
                if st.button("▶ 전체 재생", key="pl_play_all", use_container_width=False):
                    play(items[0]["url"], items[0]["title"], queue=items, pos=0)

            st.write("")

            for ii, item in enumerate(items):
                st.markdown(f"""<div class="pl-item"><div class="pl-item-title">{ii+1}. {item['title']}</div><div class="pl-item-url">{item['url'][:65]}{'...' if len(item['url']) > 65 else ''}</div></div>""", unsafe_allow_html=True)
                ia, ib, ic = st.columns([3, 1, 1])
                with ia:
                    if st.button("▶ 재생", key=f"pli_play_{ii}", use_container_width=True):
                        play(item["url"], item["title"], queue=items, pos=ii)
                with ib:
                    st.markdown('<div class="btn-sm">', unsafe_allow_html=True)
                    if st.button("수정", key=f"pli_edit_{ii}", use_container_width=True):
                        st.session_state[f"pli_editing_{ii}"] = True
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                with ic:
                    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                    if st.button("삭제", key=f"pli_del_{ii}", use_container_width=True):
                        items.pop(ii)
                        sb.table("playlists").update({"items": json.dumps(items, ensure_ascii=False)}).eq("id", pld["id"]).execute()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.get(f"pli_editing_{ii}"):
                    new_t = st.text_input("제목 수정", value=item["title"], key=f"pli_new_t_{ii}")
                    sa, sb2 = st.columns([1, 1])
                    with sa:
                        if st.button("저장", key=f"pli_save_{ii}", use_container_width=True):
                            items[ii]["title"] = new_t
                            sb.table("playlists").update({"items": json.dumps(items, ensure_ascii=False)}).eq("id", pld["id"]).execute()
                            st.session_state[f"pli_editing_{ii}"] = False
                            st.rerun()
                    with sb2:
                        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                        if st.button("취소", key=f"pli_cancel_{ii}", use_container_width=True):
                            st.session_state[f"pli_editing_{ii}"] = False
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                st.write("")

            st.markdown("---")
            st.markdown('<div class="section-label">영상 추가</div>', unsafe_allow_html=True)
            add_url   = st.text_input("", placeholder="URL 붙여넣기", label_visibility="collapsed", key="pl_add_url")
            add_title = st.text_input("", placeholder="제목 (선택)", label_visibility="collapsed", key="pl_add_title")
            if st.button("추가", key="pl_add_btn", use_container_width=False):
                if add_url.strip():
                    t = add_title.strip() if add_title.strip() else f"영상 {len(items)+1}"
                    items.append({"title": t, "url": add_url.strip()})
                    sb.table("playlists").update({"items": json.dumps(items, ensure_ascii=False)}).eq("id", pld["id"]).execute()
                    st.rerun()

            favs = get_favorites()
            if favs:
                st.markdown("---")
                st.markdown('<div class="section-label">즐겨찾기에서 추가</div>', unsafe_allow_html=True)
                for fi, fv in enumerate(favs):
                    fa, fb = st.columns([4, 1])
                    with fa:
                        st.markdown(f'<div style="font-size:0.82rem;color:#8890aa;padding:6px 0">{fv["title"]}</div>', unsafe_allow_html=True)
                    with fb:
                        st.markdown('<div class="btn-sm">', unsafe_allow_html=True)
                        if st.button("추가", key=f"fav_to_pl_{fi}", use_container_width=True):
                            items.append({"title": fv["title"], "url": fv["url"]})
                            sb.table("playlists").update({"items": json.dumps(items, ensure_ascii=False)}).eq("id", pld["id"]).execute()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-label">플레이리스트</div>', unsafe_allow_html=True)
            new_pl_name = st.text_input("", placeholder="새 플레이리스트 이름", label_visibility="collapsed", key="new_pl_name")
            if st.button("+ 만들기", key="create_pl", use_container_width=False):
                if new_pl_name.strip():
                    sb.table("playlists").insert({"user_id": st.session_state.user["id"], "name": new_pl_name.strip(), "items": "[]"}).execute()
                    st.rerun()

            st.write("")

            if not pls:
                st.markdown('<div class="fav-empty">플레이리스트가 없어.<br>위에서 만들어봐.</div>', unsafe_allow_html=True)
            else:
                for pl in pls:
                    items = json.loads(pl["items"] or "[]")
                    st.markdown(f"""<div class="pl-card"><div class="pl-name">{pl['name']}</div><div class="pl-count">{len(items)}개 영상</div></div>""", unsafe_allow_html=True)
                    oa, ob = st.columns([3, 1])
                    with oa:
                        if st.button("열기", key=f"pl_open_{pl['id']}", use_container_width=True):
                            st.session_state.pl_open = pl["id"]
                            st.rerun()
                    with ob:
                        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                        if st.button("삭제", key=f"pl_del_{pl['id']}", use_container_width=True):
                            sb.table("playlists").delete().eq("id", pl["id"]).execute()
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
                    st.write("")

    # ── 탭6: 기록 ────────────────────────────────────────
    with tab6:
        st.markdown('<div class="section-label">재생 기록</div>', unsafe_allow_html=True)
        history = get_history(30)
        if not history:
            st.markdown('<div class="fav-empty">아직 재생 기록이 없어.</div>', unsafe_allow_html=True)
        else:
            if st.button("기록 전체 삭제", key="clear_history"):
                sb.table("history").delete().eq("user_id", st.session_state.user["id"]).execute()
                st.rerun()
            st.write("")
            for idx, h in enumerate(history):
                st.markdown(f"""<div class="fav-card"><div class="fav-title">{h['title']}</div><div class="fav-url">{h['watched_at'][:10]} · {h['url'][:50]}...</div></div>""", unsafe_allow_html=True)
                hc1, hc2 = st.columns([3, 1])
                with hc1:
                    if st.button("▶ 재생", key=f"hist_play_{idx}", use_container_width=True):
                        play(h["url"], h["title"])
                with hc2:
                    st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                    if st.button("삭제", key=f"hist_del_{idx}", use_container_width=True):
                        sb.table("history").delete().eq("id", h["id"]).execute()
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                st.write("")

# ══════════════════════════════════════════════════════
# 플레이어
# ══════════════════════════════════════════════════════
elif st.session_state.view == "player":

    queue = st.session_state.pl_queue
    pos   = st.session_state.pl_pos

    r1, r2 = st.columns([1, 5])
    with r1:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("← 돌아가기", use_container_width=True):
            st.session_state.view = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with r2:
        fav_txt = "★ 즐겨찾기됨" if is_fav(st.session_state.url) else "☆ 즐겨찾기"
        st.markdown('<div class="btn-fav">', unsafe_allow_html=True)
        if st.button(fav_txt, use_container_width=True, key="player_fav"):
            toggle_fav(st.session_state.title, st.session_state.url)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if queue:
        nc1, nc2, nc3 = st.columns([1, 1, 4])
        with nc1:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if pos > 0:
                if st.button("◀ 이전", use_container_width=True, key="prev"):
                    play(queue[pos-1]["url"], queue[pos-1]["title"], queue=queue, pos=pos-1)
            st.markdown('</div>', unsafe_allow_html=True)
        with nc2:
            st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
            if pos < len(queue) - 1:
                if st.button("다음 ▶", use_container_width=True, key="next"):
                    play(queue[pos+1]["url"], queue[pos+1]["title"], queue=queue, pos=pos+1)
            st.markdown('</div>', unsafe_allow_html=True)
        with nc3:
            st.markdown(f'<div style="font-size:0.75rem;color:#3a3f52;padding:10px 0">{pos+1} / {len(queue)}</div>', unsafe_allow_html=True)

    st.write("")

    st.markdown('<div class="player-wrap">', unsafe_allow_html=True)
    try:
        st.video(st.session_state.url)
        st.markdown(f'<div class="player-title">{st.session_state.title}</div>', unsafe_allow_html=True)
        st.markdown('<div class="player-sub">FTUBE · 광고 없음</div>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"재생할 수 없는 URL이야: {e}")
        st.write("")
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("홈으로", use_container_width=False):
            st.session_state.view = "home"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
