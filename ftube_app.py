# -*- coding: utf-8 -*-
import streamlit as st
import tempfile
import os
import json
import requests
import re
import hashlib
import random
import time
from collections import Counter
from supabase import create_client

# ── 페이지 설정 ─────────────────────────────────────
st.set_page_config(page_title="FTUBE - MP3 Player", page_icon="🎵", layout="wide")

# ── Supabase 연결 ─────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── 세션 상태 초기화 ─────────────────────────────────────
def sinit(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

sinit("user", None)
sinit("auth_mode", "login")
sinit("url", "")
sinit("title", "")
sinit("artist", "")
sinit("is_playing", False)
sinit("queue", [])
sinit("q_pos", 0)
sinit("shuffle", False)
sinit("repeat_mode", "all")
sinit("search_results", [])
sinit("search_query", "")
sinit("show_queue_drawer", False)
sinit("show_lyrics_drawer", False)
sinit("show_theme_selector", False)
sinit("current_lyrics", None)
sinit("lcd_theme", "green")  # green, amber, cyan, purple, ruby

# ── LCD 테마 팔레트 정의 ──────────────────────────────
THEMES = {
    "green": {
        "name": "🟢 Matrix Green (클래식 그린)",
        "bg": "#060e0a",
        "border": "#1a3d24",
        "glow": "rgba(57, 211, 83, 0.4)",
        "text": "#56d364",
        "text_sub": "#7ee787",
        "lyrics_box": "#030805",
        "lyrics_text": "#79c0ff",
        "eq1": "#238636",
        "eq2": "#39d353",
        "accent": "#39d353",
    },
    "amber": {
        "name": "🟠 Retro Amber (진공관 엠버 오렌지)",
        "bg": "#120904",
        "border": "#422006",
        "glow": "rgba(251, 191, 36, 0.45)",
        "text": "#fbbf24",
        "text_sub": "#fcd34d",
        "lyrics_box": "#0a0502",
        "lyrics_text": "#fde68a",
        "eq1": "#d97706",
        "eq2": "#f59e0b",
        "accent": "#f59e0b",
    },
    "cyan": {
        "name": "🔵 Cyber Ice (사이버네틱 아이스 블루)",
        "bg": "#040d14",
        "border": "#0e3a59",
        "glow": "rgba(56, 189, 248, 0.45)",
        "text": "#38bdf8",
        "text_sub": "#7dd3fc",
        "lyrics_box": "#02070b",
        "lyrics_text": "#a5f3fc",
        "eq1": "#0284c7",
        "eq2": "#38bdf8",
        "accent": "#38bdf8",
    },
    "purple": {
        "name": "🟣 Midnight Neon (미드나잇 베이퍼 퍼플)",
        "bg": "#0e0514",
        "border": "#3b1154",
        "glow": "rgba(192, 132, 252, 0.45)",
        "text": "#c084fc",
        "text_sub": "#e879f9",
        "lyrics_box": "#08020c",
        "lyrics_text": "#f0abfc",
        "eq1": "#9333ea",
        "eq2": "#c084fc",
        "accent": "#c084fc",
    },
    "ruby": {
        "name": "🔴 Stealth Ruby (스텔스 다크 루비)",
        "bg": "#140507",
        "border": "#451016",
        "glow": "rgba(244, 63, 94, 0.45)",
        "text": "#fb7185",
        "text_sub": "#fda4af",
        "lyrics_box": "#0b0204",
        "lyrics_text": "#fecdd3",
        "eq1": "#e11d48",
        "eq2": "#f43f5e",
        "accent": "#f43f5e",
    },
}

cur_th = THEMES.get(st.session_state.lcd_theme, THEMES["green"])

# ── CSS & 테마별 MP3 기기 스타일 디자인 시스템 ─────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Share+Tech+Mono&display=swap');

:root {{
    --lcd-bg: {cur_th['bg']};
    --lcd-border: {cur_th['border']};
    --lcd-glow: {cur_th['glow']};
    --lcd-text: {cur_th['text']};
    --lcd-sub: {cur_th['text_sub']};
    --lcd-lbox: {cur_th['lyrics_box']};
    --lcd-ltext: {cur_th['lyrics_text']};
    --lcd-eq1: {cur_th['eq1']};
    --lcd-eq2: {cur_th['eq2']};
    --lcd-acc: {cur_th['accent']};
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stAppViewContainer"], .stApp {{
    background-color: #0d1017 !important;
    color: #c9d1d9;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}
[data-testid="stAppViewContainer"] > .main {{
    max-width: 1060px;
    margin: 0 auto;
    padding: 0 20px;
}}
[data-testid="block-container"] {{
    padding: 20px 0 60px 0 !important;
    max-width: 100% !important;
}}

/* ── 상단 헤더 ── */
.ftube-header {{
    padding: 16px 20px;
    background: linear-gradient(135deg, #161b26 0%, #11141c 100%);
    border: 1px solid #21283b;
    border-radius: 12px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.ftube-logo-wrap {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.ftube-logo {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 0.15em;
    color: #58a6ff;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.ftube-logo span {{ color: var(--lcd-acc); }}
.header-badge {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    background: #1f293d;
    color: #79c0ff;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid #384666;
    letter-spacing: 0.05em;
}}
.header-user {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #8b949e;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.header-user b {{ color: #58a6ff; }}

/* ── MP3 하드웨어 플레이어 덱 (DAP LCD & Deck) ── */
.mp3-device-deck {{
    background: linear-gradient(180deg, #1a202c 0%, #121620 100%);
    border: 2px solid #2d3748;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 12px 36px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08);
    position: relative;
}}
.mp3-device-deck::before {{
    content: "DIGITAL AUDIO PLAYER // MP3-DAP PRO // THEMED LCD";
    position: absolute;
    top: 8px;
    left: 24px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.65rem;
    color: #4a5568;
    letter-spacing: 0.18em;
}}
.mp3-lcd-screen {{
    background: var(--lcd-bg) !important;
    border: 2px solid var(--lcd-border) !important;
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 10px;
    margin-bottom: 20px;
    position: relative;
    box-shadow: inset 0 0 24px var(--lcd-glow), 0 2px 8px rgba(0,0,0,0.8);
    overflow: hidden;
    transition: all 0.3s ease;
}}
.mp3-lcd-screen::after {{
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(0deg, rgba(0,0,0,0.15) 0px, rgba(0,0,0,0.15) 1px, transparent 1px, transparent 2px);
    pointer-events: none;
}}
.lcd-top-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px dashed var(--lcd-border);
    padding-bottom: 8px;
    margin-bottom: 12px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
}}
.lcd-status-playing {{
    color: var(--lcd-acc);
    display: flex;
    align-items: center;
    gap: 6px;
    animation: blink 1.5s infinite;
}}
.lcd-status-idle {{ color: #486551; }}
.lcd-meta-badge {{ color: #58a6ff; letter-spacing: 0.1em; }}
.lcd-codec {{ color: #e3b341; letter-spacing: 0.08em; }}

.lcd-main-info {{
    margin: 10px 0;
}}
.lcd-track-title {{
    font-family: 'Share Tech Mono', 'Inter', monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--lcd-text) !important;
    text-shadow: 0 0 10px var(--lcd-glow);
    letter-spacing: 0.05em;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
}}
.lcd-artist-name {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.88rem;
    color: var(--lcd-sub) !important;
    letter-spacing: 0.08em;
}}

/* ── LCD 실시간 가사 텔레프롬프터 ── */
.lcd-lyrics-box {{
    background: var(--lcd-lbox) !important;
    border: 1px solid var(--lcd-border) !important;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 12px 0 8px 0;
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}}
.lcd-lyrics-text {{
    font-family: 'Share Tech Mono', 'Inter', monospace;
    font-size: 0.92rem;
    color: var(--lcd-ltext) !important;
    text-shadow: 0 0 8px var(--lcd-glow);
    letter-spacing: 0.06em;
    line-height: 1.4;
    animation: fadeIn 0.4s ease-in;
}}

/* EQ 비주얼라이저 바 애니메이션 */
.lcd-eq-wrap {{
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 20px;
    margin: 10px 0 4px 0;
}}
.lcd-eq-bar {{
    flex: 1;
    background: var(--lcd-eq1);
    border-radius: 2px 2px 0 0;
    height: 30%;
}}
.lcd-eq-bar.active:nth-child(1) {{ animation: eq1 0.7s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(2) {{ animation: eq2 0.5s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(3) {{ animation: eq3 0.8s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(4) {{ animation: eq4 0.6s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(5) {{ animation: eq5 0.9s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(6) {{ animation: eq2 0.4s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(7) {{ animation: eq4 0.7s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(8) {{ animation: eq1 0.6s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(9) {{ animation: eq3 0.5s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(10) {{ animation: eq5 0.8s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(11) {{ animation: eq2 0.7s ease-in-out infinite alternate; }}
.lcd-eq-bar.active:nth-child(12) {{ animation: eq4 0.9s ease-in-out infinite alternate; }}

@keyframes eq1 {{ 0% {{ height: 20%; background: var(--lcd-eq1); }} 100% {{ height: 95%; background: var(--lcd-eq2); }} }}
@keyframes eq2 {{ 0% {{ height: 40%; background: var(--lcd-eq1); }} 100% {{ height: 80%; background: var(--lcd-eq2); }} }}
@keyframes eq3 {{ 0% {{ height: 15%; background: var(--lcd-eq1); }} 100% {{ height: 100%; background: var(--lcd-eq2); }} }}
@keyframes eq4 {{ 0% {{ height: 50%; background: var(--lcd-eq1); }} 100% {{ height: 70%; background: var(--lcd-eq2); }} }}
@keyframes eq5 {{ 0% {{ height: 10%; background: var(--lcd-eq1); }} 100% {{ height: 90%; background: var(--lcd-eq2); }} }}
@keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(4px); }} to {{ opacity: 1; transform: translateY(0); }} }}

/* 완전 숨김 유튜브 오디오 엔진 (영상이 절대 보이지 않음) */
.hidden-audio-frame {{
    position: absolute !important;
    left: -9999px !important;
    top: -9999px !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden !important;
}}

/* ── 탭 메뉴 ── */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid #21283b !important;
    gap: 6px !important;
    background: transparent !important;
}}
[data-testid="stTabs"] button[role="tab"] {{
    background: #11151f !important;
    color: #6e7681 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    border: 1px solid #1f2638 !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 8px 8px 0 0 !important;
    transition: all 0.2s !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: var(--lcd-acc) !important;
    border-color: #384666 !important;
    border-bottom: 2px solid var(--lcd-acc) !important;
    background: #161c2b !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{
    color: #c9d1d9 !important;
    background: #181f2f !important;
}}
[data-testid="stTabContent"] {{ padding-top: 20px !important; }}

/* ── 트랙 리스트 바 (영상 썸네일 대신 텍스트/음악 중심 행) ── */
.track-row {{
    background: #131722;
    border: 1px solid #1e2638;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all 0.15s ease;
}}
.track-row:hover {{
    background: #181e2c;
    border-color: #384666;
    transform: translateX(2px);
}}
.track-left {{
    display: flex;
    align-items: center;
    gap: 14px;
    overflow: hidden;
    flex: 1;
}}
.track-num {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.78rem;
    color: var(--lcd-acc);
    min-width: 28px;
}}
.track-info {{
    overflow: hidden;
    flex: 1;
}}
.track-title-text {{
    font-size: 0.88rem;
    font-weight: 500;
    color: #e6edf3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 2px;
}}
.track-artist-text {{
    font-size: 0.75rem;
    color: #8b949e;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.track-tag-badge {{
    display: inline-block;
    font-size: 0.65rem;
    font-family: 'Share Tech Mono', monospace;
    background: #1f293d;
    color: #79c0ff;
    padding: 1px 6px;
    border-radius: 4px;
    margin-right: 6px;
}}
.track-duration {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75rem;
    color: #6e7681;
    margin-left: 10px;
    margin-right: 14px;
}}

/* ── 폼 & 버튼 스타일 ── */
.stTextInput input {{
    background-color: #131722 !important;
    border: 1px solid #21283b !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    padding: 10px 14px !important;
    font-size: 0.88rem !important;
}}
.stTextInput input:focus {{
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}}
.stButton button {{
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    border: 1px solid #21283b !important;
    background: #181f2f !important;
    color: #c9d1d9 !important;
    padding: 8px 14px !important;
    transition: all 0.15s !important;
}}
.stButton button:hover {{
    background: #212b40 !important;
    border-color: #384666 !important;
    color: #ffffff !important;
}}
.btn-primary button {{
    background: #1f6feb !important;
    border-color: #388bfd !important;
    color: #ffffff !important;
}}
.btn-primary button:hover {{
    background: #388bfd !important;
}}
.btn-fav button {{
    color: #e3b341 !important;
    border-color: #384666 !important;
}}

.auth-card {{
    max-width: 380px;
    margin: 40px auto;
    background: #131722;
    border: 1px solid #21283b;
    border-radius: 12px;
    padding: 28px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}}
.auth-title {{
    font-size: 1.1rem;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 20px;
    text-align: center;
    letter-spacing: 0.05em;
}}
.empty-msg {{
    text-align: center;
    padding: 48px 0;
    color: #484f58;
    font-size: 0.85rem;
    font-family: 'Share Tech Mono', monospace;
    line-height: 1.8;
}}
.section-title {{
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    color: #58a6ff;
    text-transform: uppercase;
    margin-bottom: 12px;
}}
</style>
""", unsafe_allow_html=True)

# ── 유틸리티 및 Supabase 연동 함수 ──────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_favorites():
    if not st.session_state.user:
        return []
    res = sb.table("favorites").select("*").eq("user_id", st.session_state.user["id"]).order("id", desc=True).execute()
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
    if not st.session_state.user or not url:
        return False
    uid = st.session_state.user["id"]
    res = sb.table("favorites").select("id").eq("user_id", uid).eq("url", url).execute()
    return bool(res.data)

def get_playlists():
    if not st.session_state.user:
        return []
    res = sb.table("playlists").select("*").eq("user_id", st.session_state.user["id"]).order("id", desc=True).execute()
    return res.data or []

def get_history(limit=50):
    if not st.session_state.user:
        return []
    res = sb.table("history").select("*").eq("user_id", st.session_state.user["id"]).order("watched_at", desc=True).limit(limit).execute()
    return res.data or []

def get_keywords():
    if not st.session_state.user:
        return []
    res = sb.table("keywords").select("*").eq("user_id", st.session_state.user["id"]).execute()
    return res.data or []

def yt_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"

# ── 스마트 제목 & 아티스트 파서 ─────────────────────────
def analyze_title(title):
    tags = []
    t = title.lower()
    if any(x in t for x in ["cover", "커버", "歌ってみた", "우타이테"]): tags.append("COVER")
    if any(x in t for x in ["official", "원곡", "mv", "m/v", "music video"]): tags.append("ORIGINAL")
    if any(x in t for x in ["live", "라이브", "concert", "콘서트"]): tags.append("LIVE")
    if any(x in t for x in ["remix", "리믹스", "mix"]): tags.append("REMIX")
    if any(x in t for x in ["lofi", "로파이", "bgm", "chill"]): tags.append("BGM")
    if any(x in t for x in ["asmr", "acoustic", "어쿠스틱"]): tags.append("ACOUSTIC")
    return tags

def smart_parse_title(raw_title):
    cleaned = raw_title.strip()
    tags = analyze_title(cleaned)
    clean_text = re.sub(r'[\[【\(\「『].*?[\]】\)\」』]', '', cleaned).strip()
    
    cov = re.search(r'^(.*?)\s*(?:covered\s+by|cover\s+by|vocal\s+by|song\s+by)\s*(.*?)$', clean_text, re.IGNORECASE)
    if cov:
        return {"artist": cov.group(2).strip() or "Artist", "song": cov.group(1).strip() or raw_title, "tags": tags}
    
    parts = re.split(r'[-–—/|:~]', clean_text)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 2:
        artist_candidate = re.sub(r'(?i)\b(cover|커버|live|official|mv|full|ver)\b', '', parts[0]).strip()
        song_candidate = re.sub(r'(?i)\b(cover|커버|live|official|mv|full|ver)\b', '', parts[1]).strip()
        if artist_candidate and song_candidate:
            return {"artist": artist_candidate, "song": song_candidate, "tags": tags}
        return {"artist": parts[0], "song": parts[1], "tags": tags}
    
    return {"artist": "Audio Track", "song": clean_text or raw_title, "tags": tags}

# ── 글로벌 실시간 가사 수집 엔진 (LRCLIB API 연동) ────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_lyrics(song, artist):
    if not song or song == "STANDBY MODE" or song == "NO TRACK LOADED":
        return None
    try:
        r = requests.get("https://lrclib.net/api/get", params={"track_name": song, "artist_name": artist}, timeout=3)
        if r.status_code == 200:
            data = r.json()
            synced = data.get("syncedLyrics")
            plain = data.get("plainLyrics")
            if synced or plain:
                return {"synced": synced, "plain": plain, "track": song, "artist": artist}
        
        q = f"{song} {artist}".strip()
        r2 = requests.get("https://lrclib.net/api/search", params={"q": q}, timeout=3)
        if r2.status_code == 200:
            results = r2.json()
            if results and isinstance(results, list):
                first = results[0]
                return {"synced": first.get("syncedLyrics"), "plain": first.get("plainLyrics"), "track": song, "artist": artist}
    except Exception:
        pass
    return None

def parse_lrc_lines(synced_text):
    if not synced_text:
        return []
    lines = []
    for line in synced_text.splitlines():
        m = re.match(r'\[(\d{2}):(\d{2}\.\d{2,3})\](.*)', line)
        if m:
            mins = int(m.group(1))
            secs = float(m.group(2))
            total_sec = mins * 60 + secs
            text = m.group(3).strip()
            if text:
                lines.append({"sec": total_sec, "text": text})
    return lines

# ── YouTube 크롤링 검색 엔진 (오디오 트랙 전용) ─────────────
@st.cache_data(ttl=300, show_spinner=False)
def search_youtube_raw(query, max_items=25):
    if not query or not query.strip():
        return []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query.strip())}&hl=ko&gl=KR"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200: return []
        patterns = [
            r'var ytInitialData\s*=\\s*({.+?});</script>',
            r'window\["ytInitialData"\]\s*=\s*({.+?});',
            r'ytInitialData\s*=\s*({.+?});'
        ]
        raw_json = None
        for pat in patterns:
            m = re.search(pat, resp.text)
            if m:
                try:
                    raw_json = json.loads(m.group(1))
                    break
                except: continue
        if not raw_json: return []
        
        results = []
        seen_ids = set()
        def extract(obj):
            if isinstance(obj, dict):
                if "videoRenderer" in obj:
                    v = obj["videoRenderer"]
                    vid_id = v.get("videoId", "")
                    if vid_id and len(vid_id) == 11 and vid_id not in seen_ids:
                        seen_ids.add(vid_id)
                        title_runs = v.get("title", {}).get("runs", [])
                        title = title_runs[0].get("text", "Untitled") if title_runs else v.get("title", {}).get("simpleText", "Untitled")
                        owner_runs = v.get("ownerText", {}).get("runs", [])
                        channel = owner_runs[0].get("text", "") if owner_runs else ""
                        duration = v.get("lengthText", {}).get("simpleText", "")
                        parsed = smart_parse_title(title)
                        artist = parsed["artist"] if parsed["artist"] != "Audio Track" else (channel or "Unknown Artist")
                        results.append({
                            "id": vid_id,
                            "raw_title": title,
                            "title": parsed["song"],
                            "artist": artist,
                            "tags": parsed["tags"],
                            "channel": channel,
                            "duration": duration,
                            "url": yt_url(vid_id)
                        })
                for _, val in obj.items():
                    if len(results) >= max_items: break
                    extract(val)
            elif isinstance(obj, list):
                for item in obj:
                    if len(results) >= max_items: break
                    extract(item)
        extract(raw_json)
        return results
    except:
        return []

# ── 추천 엔진 ─────────────────────────────────────────
def get_recommendations():
    stopwords = {"이","그","저","것","수","을","를","가","은","는","에","의","로","으로","와","과","도","만","다","에서","하다","있다","없다","하고","했다","한","등","the","a","an","in","of","to","is","on","at","by","for"}
    history = get_history(30)
    favs = get_favorites()
    all_titles = [h["title"] for h in history] + [f["title"] for f in favs]

    user_keywords = get_keywords()
    if user_keywords:
        top_keyword = " ".join([k["keyword"] for k in user_keywords[:3]])
        results = search_youtube_raw(top_keyword, max_items=12)
        if results: return results, top_keyword

    if not all_titles:
        return search_youtube_raw("잔잔한 음악 플레이리스트", max_items=12), "인기 음악 추천"

    words = []
    for t in all_titles:
        words.extend([w for w in t.split() if len(w) > 1 and w.lower() not in stopwords])
    top_words = [w for w, _ in Counter(words).most_common(2)]
    keyword = " ".join(top_words) if top_words else "음악"
    results = search_youtube_raw(f"{keyword} 노래", max_items=12)
    return results, keyword

# ── 재생 제어 함수 ─────────────────────────────────────
def play_track(track, queue_list=None, pos=0):
    st.session_state.url = track["url"]
    st.session_state.title = track.get("title") or track.get("raw_title", "Track")
    st.session_state.artist = track.get("artist", "Unknown Artist")
    st.session_state.is_playing = True
    
    st.session_state.current_lyrics = fetch_lyrics(st.session_state.title, st.session_state.artist)
    
    if queue_list:
        st.session_state.queue = queue_list
        st.session_state.q_pos = pos
    elif not st.session_state.queue:
        st.session_state.queue = [track]
        st.session_state.q_pos = 0

    if st.session_state.user and track["url"]:
        try:
            sb.table("history").insert({
                "user_id": st.session_state.user["id"],
                "title": f"{st.session_state.title} - {st.session_state.artist}",
                "url": track["url"]
            }).execute()
        except: pass
    st.rerun()

def play_next():
    q = st.session_state.queue
    if not q: return
    if st.session_state.repeat_mode == "one":
        st.rerun()
        return
    if st.session_state.shuffle:
        next_pos = random.randint(0, len(q) - 1)
    else:
        next_pos = st.session_state.q_pos + 1
        if next_pos >= len(q):
            if st.session_state.repeat_mode == "all":
                next_pos = 0
            else:
                st.session_state.is_playing = False
                st.rerun()
                return
    play_track(q[next_pos], queue_list=q, pos=next_pos)

def play_prev():
    q = st.session_state.queue
    if not q: return
    prev_pos = max(0, st.session_state.q_pos - 1)
    play_track(q[prev_pos], queue_list=q, pos=prev_pos)

# ══════════════════════════════════════════════════════
# 로그인 / 회원가입 화면
# ══════════════════════════════════════════════════════
if not st.session_state.user:
    st.markdown("""
    <div class="ftube-header">
        <div class="ftube-logo-wrap">
            <div class="ftube-logo">FTUBE<span>.MP3</span></div>
            <div class="header-badge">HARDWARE AUDIO PLAYER</div>
        </div>
        <div class="header-badge">OFFLINE / AD-FREE AUDIO</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    if st.session_state.auth_mode == "login":
        st.markdown('<div class="auth-title">MP3 디바이스 로그인</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("아이디", placeholder="아이디 입력")
            password = st.text_input("비밀번호", placeholder="비밀번호 입력", type="password")
            sub = st.form_submit_button("로그인", use_container_width=True)
            if sub:
                if username and password:
                    res = sb.table("users").select("*").eq("username", username).eq("password", hash_pw(password)).execute()
                    if res.data:
                        st.session_state.user = {"id": res.data[0]["id"], "username": res.data[0]["username"]}
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
                else:
                    st.warning("아이디와 비밀번호를 입력해주세요.")
        st.write("")
        if st.button("계정 생성 (회원가입)", use_container_width=True):
            st.session_state.auth_mode = "register"
            st.rerun()
    else:
        st.markdown('<div class="auth-title">새 계정 등록</div>', unsafe_allow_html=True)
        with st.form("reg_form"):
            username = st.text_input("아이디", placeholder="사용할 아이디")
            password = st.text_input("비밀번호", placeholder="비밀번호", type="password")
            password2 = st.text_input("비밀번호 확인", placeholder="비밀번호 재입력", type="password")
            sub = st.form_submit_button("가입하기", use_container_width=True)
            if sub:
                if not username or not password:
                    st.warning("모든 정보를 입력해주세요.")
                elif password != password2:
                    st.error("비밀번호가 일치하지 않습니다.")
                else:
                    ex = sb.table("users").select("id").eq("username", username).execute()
                    if ex.data:
                        st.error("이미 존재하는 아이디입니다.")
                    else:
                        sb.table("users").insert({"username": username, "password": hash_pw(password)}).execute()
                        st.success("가입이 완료되었습니다.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
        st.write("")
        if st.button("로그인 화면으로", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════
# 메인 헤더
# ══════════════════════════════════════════════════════
col_h1, col_h2 = st.columns([4, 1.2])
with col_h1:
    st.markdown(f"""
    <div class="ftube-header">
        <div class="ftube-logo-wrap">
            <div class="ftube-logo">FTUBE<span>.DAP</span></div>
            <div class="header-badge">THEME: {st.session_state.lcd_theme.upper()}</div>
        </div>
        <div class="header-user">USER: <b>{st.session_state.user['username']}</b></div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    st.write("")
    if st.button("로그아웃", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# ══════════════════════════════════════════════════════
# MP3 하드웨어 오디오 기기 덱 (실시간 가사 & 테마형 LCD 스크린)
# ══════════════════════════════════════════════════════
cur_title = st.session_state.title or "NO TRACK LOADED"
cur_artist = st.session_state.artist or "STANDBY MODE"
is_act = st.session_state.is_playing and bool(st.session_state.url)
q_len = len(st.session_state.queue)
cur_pos_display = f"{st.session_state.q_pos + 1:02d}/{q_len:02d}" if q_len else "00/00"
status_label = "▶ PLAYING" if is_act else "■ STANDBY"
status_class = "lcd-status-playing" if is_act else "lcd-status-idle"
eq_active = "active" if is_act else ""

# 가사 텍스트 준비
lyrics_data = st.session_state.current_lyrics or fetch_lyrics(cur_title, cur_artist)
lrc_display = "♪ (INSTRUMENTAL / NO LYRICS FOUND) ♪"
if lyrics_data:
    if lyrics_data.get("synced"):
        parsed_lines = parse_lrc_lines(lyrics_data["synced"])
        if parsed_lines:
            lrc_display = f"♫ {parsed_lines[0]['text']}"
    elif lyrics_data.get("plain"):
        first_line = [l.strip() for l in lyrics_data["plain"].splitlines() if l.strip()]
        if first_line:
            lrc_display = f"♫ {first_line[0]}"

if not is_act:
    lrc_display = "[ STANDBY // SELECT A TRACK TO PLAY ]"

# LCD 스크린 HTML 렌더링
st.markdown(f"""
<div class="mp3-device-deck">
    <div class="mp3-lcd-screen">
        <div class="lcd-top-bar">
            <div class="{status_class}">{status_label}</div>
            <div class="lcd-meta-badge">TRK [{cur_pos_display}]</div>
            <div class="lcd-codec">AUDIO · 320 KBPS · STEREO</div>
        </div>
        <div class="lcd-main-info">
            <div class="lcd-track-title">🎵 {cur_title}</div>
            <div class="lcd-artist-name">ARTIST // {cur_artist}</div>
        </div>
        <div class="lcd-lyrics-box">
            <div class="lcd-lyrics-text">{lrc_display}</div>
        </div>
        <div class="lcd-eq-wrap">
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
            <div class="lcd-eq-bar {eq_active}"></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 완전 숨김 유튜브 오디오 엔진 (영상이 절대 보이지 않고 소리만 스트리밍) ──
if is_act and st.session_state.url:
    yt_m = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})', st.session_state.url)
    if yt_m:
        vid_id = yt_m.group(1)
        st.markdown(f'''
        <iframe
            class="hidden-audio-frame"
            src="https://www.youtube.com/embed/{vid_id}?autoplay=1&enablejsapi=1"
            allow="autoplay">
        </iframe>
        ''', unsafe_allow_html=True)

# ── MP3 하드웨어 컨트롤 버튼 덱 ──
c_prev, c_play, c_next, c_shuf, c_rep, c_lyric, c_thm, c_fav, c_q = st.columns([1, 1.3, 1, 1, 1, 1.1, 1.2, 1, 1.2])
with c_prev:
    if st.button("⏮ PREV", use_container_width=True, key="d_prev"):
        play_prev()
with c_play:
    play_txt = "⏸ PAUSE" if is_act else "▶ PLAY"
    st.markdown('<div class="btn-primary">', unsafe_allow_html=True)
    if st.button(play_txt, use_container_width=True, key="d_play"):
        st.session_state.is_playing = not st.session_state.is_playing
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
with c_next:
    if st.button("NEXT ⏭", use_container_width=True, key="d_next"):
        play_next()
with c_shuf:
    shuf_label = "🔀 ON" if st.session_state.shuffle else "🔀 SHUF"
    if st.button(shuf_label, use_container_width=True, key="d_shuf"):
        st.session_state.shuffle = not st.session_state.shuffle
        st.rerun()
with c_rep:
    rep_map = {"all": "🔁 ALL", "one": "🔂 ONE", "off": "➡ OFF"}
    if st.button(rep_map.get(st.session_state.repeat_mode, "🔁 ALL"), use_container_width=True, key="d_rep"):
        next_mode = {"all": "one", "one": "off", "off": "all"}[st.session_state.repeat_mode]
        st.session_state.repeat_mode = next_mode
        st.rerun()
with c_lyric:
    lyric_btn_txt = "📜 가사닫기" if st.session_state.show_lyrics_drawer else "📜 가사"
    if st.button(lyric_btn_txt, use_container_width=True, key="d_lyric_toggle"):
        st.session_state.show_lyrics_drawer = not st.session_state.show_lyrics_drawer
        st.rerun()
with c_thm:
    thm_btn_txt = "🎨 테마닫기" if st.session_state.show_theme_selector else "🎨 테마"
    if st.button(thm_btn_txt, use_container_width=True, key="d_theme_toggle"):
        st.session_state.show_theme_selector = not st.session_state.show_theme_selector
        st.rerun()
with c_fav:
    is_f = is_fav(st.session_state.url)
    fav_icon = "★ FAV" if is_f else "☆ FAV"
    st.markdown('<div class="btn-fav">', unsafe_allow_html=True)
    if st.button(fav_icon, use_container_width=True, key="d_fav"):
        if st.session_state.url:
            toggle_fav(st.session_state.title, st.session_state.url)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
with c_q:
    q_txt = f"📋 QUEUE ({q_len})"
    if st.button(q_txt, use_container_width=True, key="d_queue_toggle"):
        st.session_state.show_queue_drawer = not st.session_state.show_queue_drawer
        st.rerun()

# ── 테마 선택기 (LCD Color Switcher Panel) ──
if st.session_state.show_theme_selector:
    st.markdown('<div class="section-title" style="margin-top:16px;">LCD BACKLIGHT THEME SELECTOR</div>', unsafe_allow_html=True)
    th_cols = st.columns(5)
    theme_keys = ["green", "amber", "cyan", "purple", "ruby"]
    for ti, tkey in enumerate(theme_keys):
        tinfo = THEMES[tkey]
        with th_cols[ti]:
            is_active_thm = st.session_state.lcd_theme == tkey
            prefix = "✓ " if is_active_thm else ""
            if st.button(f"{prefix}{tinfo['name'].split()[0]} {tkey.upper()}", key=f"sel_thm_{tkey}", use_container_width=True):
                st.session_state.lcd_theme = tkey
                st.rerun()
    st.markdown("<hr style='border-color:#21283b;margin:16px 0;'>", unsafe_allow_html=True)

# ── 가사 (Lyrics) 전체보기 서랍 ──
if st.session_state.show_lyrics_drawer:
    st.markdown(f'<div class="section-title" style="margin-top:16px;">LYRICS VIEWER // {cur_title}</div>', unsafe_allow_html=True)
    if lyrics_data and (lyrics_data.get("synced") or lyrics_data.get("plain")):
        raw_lrc = lyrics_data.get("synced") or lyrics_data.get("plain")
        cleaned_lyrics = "\n".join([re.sub(r'\[\d{2}:\d{2}\.\d{2,3}\]', '', line).strip() for line in raw_lrc.splitlines() if line.strip()])
        st.markdown(f"""
        <div style="background:{cur_th['bg']};border:1px solid {cur_th['border']};border-radius:10px;padding:20px;font-family:'Share Tech Mono', monospace;color:{cur_th['text_sub']};line-height:2.0;white-space:pre-wrap;max-height:300px;overflow-y:auto;text-align:center;">
{cleaned_lyrics}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-msg">등록된 가사를 찾을 수 없습니다. (Inst/Cover)</div>', unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#21283b;margin:16px 0;'>", unsafe_allow_html=True)

# ── 대기열 (Now Playing Queue) 서랍 ──
if st.session_state.show_queue_drawer and st.session_state.queue:
    st.markdown('<div class="section-title" style="margin-top:16px;">CURRENT AUDIO QUEUE</div>', unsafe_allow_html=True)
    with st.container():
        for qi, qitem in enumerate(st.session_state.queue):
            is_cur = qi == st.session_state.q_pos
            badge_icon = "▶ " if is_cur else f"{qi+1:02d}. "
            t_col, a_col, p_col = st.columns([5, 3, 1])
            with t_col:
                st.markdown(f"<div style='font-family:JetBrains Mono;font-size:0.83rem;color:{cur_th['accent'] if is_cur else '#c9d1d9'};padding:8px 0;'>{badge_icon}{qitem.get('title', qitem.get('raw_title', 'Track'))}</div>", unsafe_allow_html=True)
            with a_col:
                st.markdown(f"<div style='font-size:0.75rem;color:#6e7681;padding:8px 0;'>{qitem.get('artist', 'Artist')}</div>", unsafe_allow_html=True)
            with p_col:
                if st.button("재생", key=f"q_jump_{qi}", use_container_width=True):
                    play_track(qitem, queue_list=st.session_state.queue, pos=qi)
    st.markdown("<hr style='border-color:#21283b;margin:16px 0;'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 트랙 탐색 & 라이브러리 탭
# ══════════════════════════════════════════════════════
fav_cnt = len(get_favorites())
pl_cnt = len(get_playlists())
hist_cnt = len(get_history(30))

tab_rec, tab_mood, tab_search, tab_pl, tab_fav, tab_hist, tab_url = st.tabs([
    "🎧 추천 음악",
    "☕ 무드 스테이션",
    "🔍 음원 검색",
    f"📂 플레이리스트 ({pl_cnt})",
    f"★ 즐겨찾기 ({fav_cnt})",
    f"🕒 청취 기록 ({hist_cnt})",
    "🔗 URL 직접입력",
])

# ── 탭 1: 추천 음악 ─────────────────────────────────────
with tab_rec:
    st.markdown('<div class="section-title">CURATED TRACKS FOR YOU</div>', unsafe_allow_html=True)
    recs, kw_label = get_recommendations()
    if not recs:
        st.markdown('<div class="empty-msg">추천 음원을 불러오지 못했습니다.</div>', unsafe_allow_html=True)
    else:
        st.caption(f"'{kw_label}' 기반 음악 큐레이션 ({len(recs)}곡)")
        for idx, trk in enumerate(recs):
            tags_html = "".join([f"<span class='track-tag-badge'>{t}</span>" for t in trk.get("tags", [])[:2]])
            st.markdown(f"""
            <div class="track-row">
                <div class="track-left">
                    <div class="track-num">{idx+1:02d}</div>
                    <div class="track-info">
                        <div class="track-title-text">{tags_html}{trk['title']}</div>
                        <div class="track-artist-text">{trk['artist']} · {trk.get('channel', '')}</div>
                    </div>
                </div>
                <div class="track-duration">{trk.get('duration', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            b_play, b_fav, b_add = st.columns([2, 1, 1])
            with b_play:
                if st.button("▶ 이 곡부터 전체재생", key=f"rec_p_{idx}", use_container_width=True):
                    play_track(trk, queue_list=recs, pos=idx)
            with b_fav:
                f_state = is_fav(trk["url"])
                if st.button("★ 담기" if not f_state else "★ 해제", key=f"rec_f_{idx}", use_container_width=True):
                    toggle_fav(trk["title"], trk["url"])
                    st.rerun()
            with b_add:
                if st.button("+ 대기열", key=f"rec_q_{idx}", use_container_width=True):
                    st.session_state.queue.append(trk)
                    st.toast(f"'{trk['title']}' 대기열 추가 완료")

# ── 탭 2: 마레 & 세라의 무드 스테이션 ─────────────────────
with tab_mood:
    st.markdown('<div class="section-title">MOOD & AMBIENT STATIONS</div>', unsafe_allow_html=True)
    st.caption("원하는 무드를 선택하면 검색 없이 최적의 테마 음원이 즉시 재생 목록에 로드됩니다.")
    
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown("""
        <div style="background:#131722;border:1px solid #21283b;border-radius:10px;padding:16px;text-align:center;margin-bottom:10px;">
            <div style="font-size:1.8rem;margin-bottom:6px;">☕</div>
            <div style="font-weight:600;font-size:0.95rem;color:#e6edf3;">야근 & 집중 BGM</div>
            <div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">차분하고 잔잔한 로파이/재즈</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 스테이션 재생 (야근 BGM)", key="mood_focus", use_container_width=True):
            m_res = search_youtube_raw("작업용 잔잔한 로파이 lofi bgm", max_items=15)
            if m_res: play_track(m_res[0], queue_list=m_res, pos=0)
    
    with m_col2:
        st.markdown("""
        <div style="background:#131722;border:1px solid #21283b;border-radius:10px;padding:16px;text-align:center;margin-bottom:10px;">
            <div style="font-size:1.8rem;margin-bottom:6px;">🌙</div>
            <div style="font-weight:600;font-size:0.95rem;color:#e6edf3;">새벽 감성 힐링</div>
            <div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">어쿠스틱 & 피아노 선율</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 스테이션 재생 (새벽 힐링)", key="mood_night", use_container_width=True):
            m_res = search_youtube_raw("새벽 감성 잔잔한 어쿠스틱 피아노", max_items=15)
            if m_res: play_track(m_res[0], queue_list=m_res, pos=0)
            
    with m_col3:
        st.markdown("""
        <div style="background:#131722;border:1px solid #21283b;border-radius:10px;padding:16px;text-align:center;margin-bottom:10px;">
            <div style="font-size:1.8rem;margin-bottom:6px;">🎤</div>
            <div style="font-weight:600;font-size:0.95rem;color:#e6edf3;">보컬 커버 명곡</div>
            <div style="font-size:0.75rem;color:#8b949e;margin-top:4px;">우타이테 & 감성 보컬 커버</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("▶ 스테이션 재생 (보컬 커버)", key="mood_cover", use_container_width=True):
            m_res = search_youtube_raw("인기 우타이테 커버곡 플레이리스트", max_items=15)
            if m_res: play_track(m_res[0], queue_list=m_res, pos=0)

# ── 탭 3: 음원 검색 ─────────────────────────────────────
with tab_search:
    st.markdown('<div class="section-title">SEARCH AUDIO DATABASE</div>', unsafe_allow_html=True)
    with st.form("search_music_form"):
        q_in = st.text_input("", placeholder="곡명, 아티스트, 우타이테, 커버곡 등 검색", label_visibility="collapsed")
        submitted = st.form_submit_button("검색 실행", use_container_width=True)
        if submitted and q_in.strip():
            with st.spinner("음원 검색 중..."):
                st.session_state.search_results = search_youtube_raw(q_in.strip(), max_items=25)
                st.session_state.search_query = q_in.strip()
    
    if st.session_state.search_results:
        s_list = st.session_state.search_results
        st.caption(f"'{st.session_state.search_query}' 검색 결과 ({len(s_list)}곡)")
        for idx, trk in enumerate(s_list):
            tags_html = "".join([f"<span class='track-tag-badge'>{t}</span>" for t in trk.get("tags", [])[:2]])
            st.markdown(f"""
            <div class="track-row">
                <div class="track-left">
                    <div class="track-num">{idx+1:02d}</div>
                    <div class="track-info">
                        <div class="track-title-text">{tags_html}{trk['title']}</div>
                        <div class="track-artist-text">{trk['artist']} · {trk.get('channel', '')}</div>
                    </div>
                </div>
                <div class="track-duration">{trk.get('duration', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            b_play, b_fav, b_add = st.columns([2, 1, 1])
            with b_play:
                if st.button("▶ 이 곡부터 전체재생", key=f"s_p_{idx}", use_container_width=True):
                    play_track(trk, queue_list=s_list, pos=idx)
            with b_fav:
                f_state = is_fav(trk["url"])
                if st.button("★ 담기" if not f_state else "★ 해제", key=f"s_f_{idx}", use_container_width=True):
                    toggle_fav(trk["title"], trk["url"])
                    st.rerun()
            with b_add:
                if st.button("+ 대기열", key=f"s_q_{idx}", use_container_width=True):
                    st.session_state.queue.append(trk)
                    st.toast(f"'{trk['title']}' 대기열 추가 완료")

# ── 탭 4: 플레이리스트 ─────────────────────────────────
with tab_pl:
    st.markdown('<div class="section-title">MY PLAYLISTS</div>', unsafe_allow_html=True)
    with st.form("new_pl_form"):
        pl_name_in = st.text_input("", placeholder="새 플레이리스트 이름", label_visibility="collapsed")
        pl_create = st.form_submit_button("+ 새 플레이리스트 만들기", use_container_width=True)
        if pl_create and pl_name_in.strip():
            sb.table("playlists").insert({"user_id": st.session_state.user["id"], "name": pl_name_in.strip(), "items": "[]"}).execute()
            st.rerun()
    
    pls = get_playlists()
    if not pls:
        st.markdown('<div class="empty-msg">생성된 플레이리스트가 없습니다.</div>', unsafe_allow_html=True)
    else:
        for pl in pls:
            items = json.loads(pl.get("items") or "[]")
            st.markdown(f"""
            <div class="track-row" style="border-left: 3px solid var(--lcd-acc);">
                <div class="track-left">
                    <div class="track-info">
                        <div class="track-title-text">📂 {pl['name']}</div>
                        <div class="track-artist-text">수록 음원: {len(items)}곡</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            p_play, p_del = st.columns([4, 1])
            with p_play:
                if items and st.button(f"▶ '{pl['name']}' 전체 재생 ({len(items)}곡)", key=f"pl_play_all_{pl['id']}", use_container_width=True):
                    formatted_items = []
                    for itm in items:
                        parsed = smart_parse_title(itm["title"])
                        formatted_items.append({
                            "title": parsed["song"],
                            "artist": parsed["artist"],
                            "url": itm["url"],
                            "duration": ""
                        })
                    play_track(formatted_items[0], queue_list=formatted_items, pos=0)
            with p_del:
                if st.button("삭제", key=f"pl_del_{pl['id']}", use_container_width=True):
                    sb.table("playlists").delete().eq("id", pl["id"]).execute()
                    st.rerun()
            
            if items:
                with st.expander(f"수록곡 확인 ({len(items)}곡)"):
                    for ii, item in enumerate(items):
                        p_sub1, p_sub2 = st.columns([5, 1])
                        with p_sub1:
                            st.markdown(f"<div style='font-size:0.82rem;color:#c9d1d9;'>{ii+1:02d}. {item['title']}</div>", unsafe_allow_html=True)
                        with p_sub2:
                            if st.button("재생", key=f"pl_sub_p_{pl['id']}_{ii}", use_container_width=True):
                                parsed = smart_parse_title(item["title"])
                                play_track({"title": parsed["song"], "artist": parsed["artist"], "url": item["url"]})

# ── 탭 5: 즐겨찾기 ─────────────────────────────────────
with tab_fav:
    st.markdown('<div class="section-title">FAVORITE TRACKS</div>', unsafe_allow_html=True)
    favs = get_favorites()
    if not favs:
        st.markdown('<div class="empty-msg">즐겨찾기한 음원이 없습니다.</div>', unsafe_allow_html=True)
    else:
        fav_queue = []
        for f in favs:
            parsed = smart_parse_title(f["title"])
            fav_queue.append({"title": parsed["song"], "artist": parsed["artist"], "url": f["url"], "tags": parsed["tags"]})
            
        if st.button(f"▶ 즐겨찾기 전체 재생 ({len(favs)}곡)", use_container_width=True, key="fav_all_play"):
            play_track(fav_queue[0], queue_list=fav_queue, pos=0)
            
        for fi, f in enumerate(fav_queue):
            st.markdown(f"""
            <div class="track-row">
                <div class="track-left">
                    <div class="track-num">{fi+1:02d}</div>
                    <div class="track-info">
                        <div class="track-title-text">{f['title']}</div>
                        <div class="track-artist-text">{f['artist']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            fb_p, fb_del = st.columns([4, 1])
            with fb_p:
                if st.button("▶ 재생", key=f"fav_play_{fi}", use_container_width=True):
                    play_track(f, queue_list=fav_queue, pos=fi)
            with fb_del:
                if st.button("삭제", key=f"fav_del_{fi}", use_container_width=True):
                    toggle_fav(f["title"], f["url"])
                    st.rerun()

# ── 탭 6: 청취 기록 ─────────────────────────────────────
with tab_hist:
    st.markdown('<div class="section-title">PLAYBACK HISTORY</div>', unsafe_allow_html=True)
    history = get_history(30)
    if not history:
        st.markdown('<div class="empty-msg">청취 기록이 없습니다.</div>', unsafe_allow_html=True)
    else:
        if st.button("기록 전체 삭제", key="clear_hist_btn"):
            sb.table("history").delete().eq("user_id", st.session_state.user["id"]).execute()
            st.rerun()
            
        for hi, h in enumerate(history):
            parsed = smart_parse_title(h["title"])
            st.markdown(f"""
            <div class="track-row">
                <div class="track-left">
                    <div class="track-num">{hi+1:02d}</div>
                    <div class="track-info">
                        <div class="track-title-text">{parsed['song']}</div>
                        <div class="track-artist-text">{parsed['artist']} · {h.get('watched_at', '')[:10]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            hb_p, hb_del = st.columns([4, 1])
            with hb_p:
                if st.button("▶ 재생", key=f"hist_p_{hi}", use_container_width=True):
                    play_track({"title": parsed["song"], "artist": parsed["artist"], "url": h["url"]})
            with hb_del:
                if st.button("삭제", key=f"hist_d_{hi}", use_container_width=True):
                    sb.table("history").delete().eq("id", h["id"]).execute()
                    st.rerun()

# ── 탭 7: URL 직접입력 ──────────────────────────────────
with tab_url:
    st.markdown('<div class="section-title">DIRECT AUDIO STREAM LINK</div>', unsafe_allow_html=True)
    with st.form("url_play_form"):
        raw_url = st.text_input("", placeholder="YouTube 링크 (예: https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
        sub_url = st.form_submit_button("오디오 스트림 로드 및 재생", use_container_width=True)
        if sub_url and raw_url.strip():
            play_track({"title": "Direct Stream Audio", "artist": "External Link", "url": raw_url.strip()})
