# -*- coding: utf-8 -*-
import hashlib
import io
import json
import os
import random
import re
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
from supabase import Client, create_client

st.set_page_config(page_title="FTUBE - Audio & Cinema", page_icon="🎵", layout="wide")

SUPABASE_URL: str = st.secrets["SUPABASE_URL"]
SUPABASE_KEY: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DEFAULT_SESSION_STATES: Dict[str, Any] = {
    "user": None,
    "auth_mode": "login",
    "player_mode": "mp3",
    "music_filter_only": True,
    "url": "",
    "title": "",
    "artist": "",
    "channel": "",
    "is_playing": False,
    "queue": [],
    "queue_index": 0,
    "shuffle": False,
    "repeat_mode": "all",
    "search_results": [],
    "search_query": "",
    "show_queue_drawer": False,
    "show_lyrics_drawer": False,
    "show_theme_selector": False,
    "current_lyrics": None,
    "lcd_theme": "green",
    "selected_channel_id": None,
    "cached_playlists": None,
    "cached_favorites": None,
    "cached_history": None,
    "cached_channels": None,
    "cached_keywords": None,
    "cached_recommendations": None,
    "cached_rec_keyword": "",
    "local_channels": [],
}

def init_session_state() -> None:
    for key, default_value in DEFAULT_SESSION_STATES.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

init_session_state()

THEMES: Dict[str, Dict[str, str]] = {
    "green": {
        "name": "🟢 Matrix Green",
        "bg": "#06130d", "border": "#1b4d2e", "glow": "rgba(57, 211, 83, 0.45)",
        "text": "#56d364", "text_sub": "#86efac", "lyrics_box": "#040d09",
        "lyrics_text": "#79c0ff", "eq1": "#22c55e", "eq2": "#4ade80", "accent": "#4ade80",
    },
    "amber": {
        "name": "🟠 Retro Amber",
        "bg": "#170c06", "border": "#542a0a", "glow": "rgba(251, 191, 36, 0.5)",
        "text": "#fbbf24", "text_sub": "#fde047", "lyrics_box": "#0d0603",
        "lyrics_text": "#fde68a", "eq1": "#ea580c", "eq2": "#fbbf24", "accent": "#fbbf24",
    },
    "cyan": {
        "name": "🔵 Cyber Ice",
        "bg": "#061421", "border": "#134e7a", "glow": "rgba(56, 189, 248, 0.5)",
        "text": "#38bdf8", "text_sub": "#bae6fd", "lyrics_box": "#030c14",
        "lyrics_text": "#a5f3fc", "eq1": "#0284c7", "eq2": "#38bdf8", "accent": "#38bdf8",
    },
    "purple": {
        "name": "🟣 Midnight Neon",
        "bg": "#12081c", "border": "#4c1d75", "glow": "rgba(192, 132, 252, 0.5)",
        "text": "#c084fc", "text_sub": "#f0abfc", "lyrics_box": "#0a0410",
        "lyrics_text": "#f5d0fe", "eq1": "#9333ea", "eq2": "#c084fc", "accent": "#c084fc",
    },
    "ruby": {
        "name": "🔴 Stealth Ruby",
        "bg": "#1a080b", "border": "#5c1620", "glow": "rgba(244, 63, 94, 0.5)",
        "text": "#fb7185", "text_sub": "#fecdd3", "lyrics_box": "#0f0305",
        "lyrics_text": "#ffe4e6", "eq1": "#e11d48", "eq2": "#fb7185", "accent": "#fb7185",
    },
}

current_theme = THEMES.get(st.session_state.lcd_theme, THEMES["green"])

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&family=Share+Tech+Mono&display=swap');

:root {{
    --lcd-bg: {current_theme['bg']};
    --lcd-border: {current_theme['border']};
    --lcd-glow: {current_theme['glow']};
    --lcd-text: {current_theme['text']};
    --lcd-sub: {current_theme['text_sub']};
    --lcd-lbox: {current_theme['lyrics_box']};
    --lcd-ltext: {current_theme['lyrics_text']};
    --lcd-eq1: {current_theme['eq1']};
    --lcd-eq2: {current_theme['eq2']};
    --lcd-acc: {current_theme['accent']};
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stAppViewContainer"], .stApp {{
    background: radial-gradient(circle at 50% -10%, rgba(99, 102, 241, 0.16), transparent 45%),
                radial-gradient(circle at 100% 30%, rgba(168, 85, 247, 0.12), transparent 40%),
                radial-gradient(circle at 0% 70%, rgba(56, 189, 248, 0.10), transparent 40%),
                #0f1422 !important;
    color: #e2e8f0;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}}
[data-testid="stAppViewContainer"] > .main {{ max-width: 1080px; margin: 0 auto; padding: 0 20px; }}
[data-testid="block-container"] {{ padding: 20px 0 60px 0 !important; max-width: 100% !important; }}

.ftube-top-bar {{
    background: rgba(22, 30, 48, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    padding: 14px 20px;
    margin-bottom: 20px;
    box-shadow: 0 10px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.12);
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}}
.ftube-top-bar::after {{
    content: "";
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #f472b6);
}}
.brand-group {{ display: flex; align-items: center; gap: 12px; }}
.brand-logo-text {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.3rem; font-weight: 800; letter-spacing: 0.06em;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #f472b6 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: flex; align-items: center; gap: 6px;
}}
.brand-tag {{
    font-family: 'Share Tech Mono', monospace; font-size: 0.72rem;
    padding: 3px 8px; border-radius: 6px;
    background: rgba(30, 41, 67, 0.9); border: 1px solid rgba(125, 211, 252, 0.3); color: #7dd3fc;
    letter-spacing: 0.06em;
}}
.mode-indicator-pill {{
    font-family: 'Share Tech Mono', monospace; font-size: 0.74rem;
    padding: 4px 10px; border-radius: 20px;
    background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(96, 165, 250, 0.3); color: #e2e8f0;
    display: inline-flex; align-items: center; gap: 6px;
}}
.beacon-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    background: #4ade80; box-shadow: 0 0 8px #4ade80;
    animation: pulseBeacon 2s infinite;
}}
.beacon-dot.video-mode {{ background: #c084fc; box-shadow: 0 0 8px #c084fc; }}
@keyframes pulseBeacon {{ 0%, 100% {{ transform: scale(1); opacity: 1; }} 50% {{ transform: scale(1.3); opacity: 0.5; }} }}

.mp3-device-deck {{
    background: linear-gradient(180deg, #182235 0%, #121927 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px; padding: 20px 20px 14px 20px; margin-bottom: 20px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
}}
.mp3-device-deck::before {{
    content: "AUDIO DECK PRO // HIGH-FIDELITY RETRO LCD ENGINE";
    position: absolute; top: 8px; left: 24px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.65rem; color: #64748b; letter-spacing: 0.18em;
}}
.queue-panel-deck {{
    background: linear-gradient(180deg, #182235 0%, #121927 100%);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px; padding: 18px 20px 14px 20px; margin-bottom: 20px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
}}
.queue-panel-deck::before {{
    content: "AUDIO QUEUE // DECK PLAYLIST";
    position: absolute; top: 8px; left: 20px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.65rem; color: #64748b; letter-spacing: 0.18em;
}}
.mp3-lcd-screen {{
    background: var(--lcd-bg) !important; border: 2px solid var(--lcd-border) !important;
    border-radius: 12px; padding: 18px 20px; margin-top: 10px; margin-bottom: 14px;
    position: relative;
    box-shadow: inset 0 0 28px var(--lcd-glow), 0 4px 16px rgba(0,0,0,0.7);
    overflow: hidden; transition: all 0.3s ease;
}}
.mp3-lcd-screen::after {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(0deg, rgba(0,0,0,0.15) 0px, rgba(0,0,0,0.15) 1px, transparent 1px, transparent 2px);
    pointer-events: none;
}}
.lcd-top-bar {{
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px dashed var(--lcd-border);
    padding-bottom: 8px; margin-bottom: 12px;
    font-family: 'Share Tech Mono', monospace; font-size: 0.75rem;
}}
.lcd-status-playing {{ color: var(--lcd-acc); display: flex; align-items: center; gap: 6px; font-weight: bold; animation: blink 1.5s infinite; }}
.lcd-status-idle {{ color: #4b6354; }}
.lcd-meta-badge {{ color: #7dd3fc; letter-spacing: 0.1em; }}
.lcd-codec {{ color: #fde047; letter-spacing: 0.08em; }}
.lcd-main-info {{ margin: 10px 0; }}
.lcd-track-title {{
    font-family: 'Share Tech Mono', 'Plus Jakarta Sans', monospace;
    font-size: 1.3rem; font-weight: 700; color: var(--lcd-text) !important;
    text-shadow: 0 0 12px var(--lcd-glow); letter-spacing: 0.05em;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 4px;
}}
.lcd-artist-name {{
    font-family: 'Share Tech Mono', monospace; font-size: 0.9rem;
    color: var(--lcd-sub) !important; letter-spacing: 0.08em;
}}
.lcd-lyrics-box {{
    background: var(--lcd-lbox) !important; border: 1px solid var(--lcd-border) !important;
    border-radius: 8px; padding: 12px 16px; margin: 12px 0 8px 0;
    min-height: 50px; display: flex; align-items: center; justify-content: center; text-align: center;
}}
.lcd-lyrics-text {{
    font-family: 'Share Tech Mono', 'Plus Jakarta Sans', monospace;
    font-size: 0.95rem; color: var(--lcd-ltext) !important;
    text-shadow: 0 0 10px var(--lcd-glow); letter-spacing: 0.06em; line-height: 1.4;
    animation: fadeIn 0.4s ease-in;
}}
.lcd-eq-wrap {{ display: flex; align-items: flex-end; gap: 4px; height: 22px; margin: 10px 0 4px 0; }}
.lcd-eq-bar {{ flex: 1; background: var(--lcd-eq1); border-radius: 2px 2px 0 0; height: 30%; }}
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

.video-cinema-deck {{
    background: rgba(22, 30, 48, 0.75); backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 18px; padding: 22px; margin-bottom: 20px;
    box-shadow: 0 16px 40px rgba(0,0,0,0.6);
}}
.video-wrapper {{
    position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden;
    border-radius: 14px; background: #000000;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.8);
}}
.video-wrapper iframe {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }}
.video-meta-bar {{ margin-top: 16px; display: flex; justify-content: space-between; align-items: center; }}
.video-title-text {{ font-size: 1.15rem; font-weight: 700; color: #f8fafc; }}
.video-channel-text {{ font-size: 0.85rem; color: #94a3b8; margin-top: 3px; }}

.hidden-audio-frame {{
    position: fixed !important; left: 0 !important; top: 0 !important;
    width: 1px !important; height: 1px !important;
    opacity: 0.01 !important; pointer-events: none !important;
    z-index: -9999 !important; border: none !important;
}}

.track-row {{
    background: rgba(26, 35, 54, 0.6); backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 10px; padding: 13px 18px; margin-bottom: 8px;
    display: flex; align-items: center; justify-content: space-between;
    transition: all 0.2s ease;
}}
.track-row:hover {{
    background: rgba(36, 48, 74, 0.85); border-color: rgba(96, 165, 250, 0.4);
    transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}}
.track-left {{ display: flex; align-items: center; gap: 14px; overflow: hidden; flex: 1; }}
.track-num {{ font-family: 'Share Tech Mono', monospace; font-size: 0.82rem; color: var(--lcd-acc); min-width: 28px; font-weight: 700; }}
.track-info {{ overflow: hidden; flex: 1; }}
.track-title-text {{ font-size: 0.92rem; font-weight: 600; color: #f1f5f9; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 3px; }}
.track-artist-text {{ font-size: 0.78rem; color: #94a3b8; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.track-tag-badge {{
    display: inline-block; font-size: 0.68rem; font-family: 'Share Tech Mono', monospace;
    background: rgba(30, 41, 67, 0.9); color: #7dd3fc;
    padding: 2px 7px; border-radius: 6px; margin-right: 6px;
    border: 1px solid rgba(125, 211, 252, 0.25);
}}
.track-duration {{ font-family: 'Share Tech Mono', monospace; font-size: 0.78rem; color: #94a3b8; margin-left: 10px; margin-right: 14px; }}

[data-testid="stTabs"] [role="tablist"] {{ border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; gap: 8px !important; background: transparent !important; }}
[data-testid="stTabs"] button[role="tab"] {{
    background: rgba(22, 30, 48, 0.6) !important; color: #94a3b8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.85rem !important; font-weight: 600 !important;
    padding: 10px 20px !important; border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-bottom: 2px solid transparent !important; border-radius: 10px 10px 0 0 !important; transition: all 0.2s ease !important;
}}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
    color: #60a5fa !important; border-color: rgba(96, 165, 250, 0.4) !important;
    border-bottom: 2px solid #60a5fa !important; background: rgba(30, 41, 67, 0.9) !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{ color: #f8fafc !important; background: rgba(33, 45, 71, 0.8) !important; }}

.stTextInput input {{
    background-color: rgba(22, 30, 48, 0.7) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important; color: #f8fafc !important; padding: 11px 16px !important; font-size: 0.9rem !important;
}}
.stTextInput input:focus {{ border-color: #60a5fa !important; box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.25) !important; }}
.stButton button, [data-testid="stPopover"] button {{
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-size: 0.82rem !important; font-weight: 600 !important;
    border-radius: 10px !important; border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(30, 41, 67, 0.8) !important; color: #e2e8f0 !important;
    padding: 8px 12px !important; min-height: 38px !important; height: 38px !important;
    display: inline-flex !important; align-items: center !important; justify-content: center !important;
    box-sizing: border-box !important; margin: 0 !important; white-space: nowrap !important;
    transition: all 0.2s ease !important;
}}
.stButton button:hover, [data-testid="stPopover"] button:hover {{
    background: rgba(43, 58, 92, 0.9) !important; border-color: rgba(96, 165, 250, 0.5) !important;
    color: #ffffff !important; transform: translateY(-1px);
}}
.stButton button[kind="primary"], .stButton button[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    border-color: #60a5fa !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
}}
.stButton button[kind="primary"]:hover, .stButton button[data-testid="baseButton-primary"]:hover {{
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
}}
.btn-mode-toggle button {{ background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(168, 85, 247, 0.25)) !important; border-color: rgba(96, 165, 250, 0.4) !important; color: #67e8f9 !important; min-height: 38px !important; height: 38px !important; }}

div[data-testid="stForm"] {{
    background: rgba(22, 30, 48, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    padding: 20px 22px !important;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1) !important;
}}
div[data-testid="stForm"] button {{
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    border-color: #60a5fa !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
}}
div[data-testid="stForm"] button:hover {{
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
}}

.empty-msg {{ text-align: center; padding: 48px 0; color: #64748b; font-size: 0.88rem; font-family: 'Share Tech Mono', monospace; line-height: 1.8; }}
.section-title {{ font-family: 'Share Tech Mono', monospace; font-size: 0.74rem; letter-spacing: 0.15em; color: #60a5fa; text-transform: uppercase; margin-bottom: 12px; }}
</style>
""", unsafe_allow_html=True)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_current_user_id() -> Optional[str]:
    user = st.session_state.get("user")
    return user["id"] if user else None

def get_favorites(force_refresh: bool = False) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    if not user_id:
        return []
    if not force_refresh and st.session_state.get("cached_favorites") is not None:
        return st.session_state.cached_favorites
    try:
        res = supabase.table("favorites").select("*").eq("user_id", user_id).order("id", desc=True).execute()
        st.session_state.cached_favorites = res.data or []
    except Exception:
        st.session_state.cached_favorites = st.session_state.get("cached_favorites") or []
    return st.session_state.cached_favorites

def toggle_favorite(title: str, url: str) -> None:
    user_id = get_current_user_id()
    if not user_id or not url:
        return
    try:
        existing = supabase.table("favorites").select("id").eq("user_id", user_id).eq("url", url).execute()
        if existing.data:
            supabase.table("favorites").delete().eq("id", existing.data[0]["id"]).execute()
        else:
            supabase.table("favorites").insert({"user_id": user_id, "title": title, "url": url}).execute()
    except Exception:
        pass
    get_favorites(force_refresh=True)

def is_favorite(url: str) -> bool:
    if not url:
        return False
    favs = get_favorites()
    return any(f.get("url") == url for f in favs)

def get_playlists(force_refresh: bool = False) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    if not user_id:
        return []
    if not force_refresh and st.session_state.get("cached_playlists") is not None:
        return st.session_state.cached_playlists
    try:
        res = supabase.table("playlists").select("*").eq("user_id", user_id).order("id", desc=True).execute()
        st.session_state.cached_playlists = res.data or []
    except Exception:
        st.session_state.cached_playlists = st.session_state.get("cached_playlists") or []
    return st.session_state.cached_playlists

def add_track_to_playlist(playlist_id: int, track: Dict[str, Any]) -> bool:
    user_id = get_current_user_id()
    if not user_id:
        return False
    res = supabase.table("playlists").select("*").eq("id", playlist_id).eq("user_id", user_id).execute()
    if not res.data:
        return False
    playlist = res.data[0]
    items = json.loads(playlist.get("items") or "[]")
    if any(item.get("url") == track.get("url") for item in items):
        return False
    items.append({
        "title": track.get("title") or track.get("raw_title", "Track"),
        "artist": track.get("artist", "Unknown Artist"),
        "url": track.get("url", ""),
        "duration": track.get("duration", ""),
        "channel": track.get("channel", ""),
    })
    supabase.table("playlists").update({"items": json.dumps(items, ensure_ascii=False)}).eq("id", playlist_id).execute()
    get_playlists(force_refresh=True)
    return True

def remove_track_from_playlist(playlist_id: int, track_url: str) -> None:
    user_id = get_current_user_id()
    if not user_id:
        return
    res = supabase.table("playlists").select("*").eq("id", playlist_id).eq("user_id", user_id).execute()
    if not res.data:
        return
    items = json.loads(res.data[0].get("items") or "[]")
    updated_items = [item for item in items if item.get("url") != track_url]
    supabase.table("playlists").update({"items": json.dumps(updated_items, ensure_ascii=False)}).eq("id", playlist_id).execute()
    get_playlists(force_refresh=True)

def get_history(limit: int = 50, force_refresh: bool = False) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    if not user_id:
        return []
    if not force_refresh and st.session_state.get("cached_history") is not None:
        return st.session_state.cached_history
    try:
        res = supabase.table("history").select("*").eq("user_id", user_id).order("watched_at", desc=True).limit(limit).execute()
        st.session_state.cached_history = res.data or []
    except Exception:
        st.session_state.cached_history = st.session_state.get("cached_history") or []
    return st.session_state.cached_history

def get_keywords(force_refresh: bool = False) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    if not user_id:
        return []
    if not force_refresh and st.session_state.get("cached_keywords") is not None:
        return st.session_state.cached_keywords
    try:
        res = supabase.table("keywords").select("*").eq("user_id", user_id).execute()
        st.session_state.cached_keywords = res.data or []
    except Exception:
        st.session_state.cached_keywords = st.session_state.get("cached_keywords") or []
    return st.session_state.cached_keywords

def get_user_channels(force_refresh: bool = False) -> List[Dict[str, Any]]:
    user_id = get_current_user_id()
    if not user_id:
        return []
    if not force_refresh and st.session_state.get("cached_channels") is not None:
        return st.session_state.cached_channels
    try:
        res = supabase.table("channels").select("*").eq("user_id", user_id).order("id", desc=True).execute()
        st.session_state.cached_channels = res.data or []
    except Exception:
        if "local_channels" not in st.session_state:
            st.session_state.local_channels = []
        st.session_state.cached_channels = st.session_state.local_channels
    return st.session_state.cached_channels

def add_user_channel(channel_info: Dict[str, Any]) -> bool:
    user_id = get_current_user_id()
    if not user_id or not channel_info.get("channel_id"):
        return False
    curr_channels = get_user_channels()
    if any(c.get("channel_id") == channel_info["channel_id"] for c in curr_channels):
        return False
    try:
        supabase.table("channels").insert({
            "user_id": user_id,
            "channel_id": channel_info["channel_id"],
            "channel_name": channel_info.get("name", "Unknown Channel"),
            "handle": channel_info.get("handle", ""),
            "avatar": channel_info.get("avatar", ""),
        }).execute()
    except Exception:
        if "local_channels" not in st.session_state:
            st.session_state.local_channels = []
        st.session_state.local_channels.insert(0, {
            "id": int(time.time()),
            "user_id": user_id,
            "channel_id": channel_info["channel_id"],
            "channel_name": channel_info.get("name", "Unknown Channel"),
            "handle": channel_info.get("handle", ""),
            "avatar": channel_info.get("avatar", ""),
        })
    get_user_channels(force_refresh=True)
    return True

def remove_user_channel(channel_id: str) -> None:
    user_id = get_current_user_id()
    if not user_id:
        return
    try:
        supabase.table("channels").delete().eq("user_id", user_id).eq("channel_id", channel_id).execute()
    except Exception:
        if "local_channels" in st.session_state:
            st.session_state.local_channels = [c for c in st.session_state.local_channels if c.get("channel_id") != channel_id]
    get_user_channels(force_refresh=True)

def resolve_youtube_channel(channel_input: str) -> Optional[Dict[str, Any]]:
    if not channel_input or not channel_input.strip():
        return None
    raw = channel_input.strip()

    # 1. Direct channel ID check (UC...)
    direct_match = re.search(r"(UC[A-Za-z0-9_-]{22})", raw)
    if direct_match:
        channel_id = direct_match.group(1)
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            res = requests.get(rss_url, timeout=5)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                title_elem = root.find("{http://www.w3.org/2005/Atom}title")
                author_elem = root.find("{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name")
                name = (title_elem.text if title_elem is not None else None) or (author_elem.text if author_elem is not None else None) or channel_id
                return {"channel_id": channel_id, "name": name, "handle": f"@{name}", "avatar": ""}
        except Exception:
            return {"channel_id": channel_id, "name": channel_id, "handle": "", "avatar": ""}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    # 2. Handle or URL parsing
    if raw.startswith("http") or raw.startswith("@"):
        handle_match = re.search(r"(@[A-Za-z0-9_.-]+)", raw)
        handle = handle_match.group(1) if handle_match else ("@" + raw.lstrip("@/ "))
        target_url = f"https://www.youtube.com/{handle}" if not raw.startswith("http") else raw
        try:
            res = requests.get(target_url, headers=headers, timeout=5)
            if res.status_code == 200:
                text = res.text
                cid_match = re.search(r'<meta itemprop="channelId" content="(UC[A-Za-z0-9_-]{22})">', text) or \
                            re.search(r'<link rel="canonical" href="https://www.youtube.com/channel/(UC[A-Za-z0-9_-]{22})">', text) or \
                            re.search(r'"channelId":"(UC[A-Za-z0-9_-]{22})"', text)
                if cid_match:
                    channel_id = cid_match.group(1)
                    name_match = re.search(r'<meta property="og:title" content="([^"]+)">', text) or re.search(r'"channelMetadataRenderer":\{"title":"([^"]+)"', text)
                    channel_name = name_match.group(1) if name_match else handle
                    return {"channel_id": channel_id, "name": channel_name, "handle": handle, "avatar": ""}
        except Exception:
            pass

    # 3. Keyword / Name search for Channel
    try:
        encoded = requests.utils.quote(raw)
        search_url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAg%253D%253D&hl=ko&gl=KR"
        res = requests.get(search_url, headers=headers, timeout=5)
        if res.status_code == 200:
            match = re.search(r"var ytInitialData\s*=\s*({.+?});</script>", res.text) or re.search(r'ytInitialData\s*=\s*({.+?});', res.text)
            if match:
                raw_json = json.loads(match.group(1))
                stack = [raw_json]
                while stack:
                    curr = stack.pop()
                    if isinstance(curr, dict):
                        if "channelRenderer" in curr:
                            rend = curr["channelRenderer"]
                            cid = rend.get("channelId")
                            if cid:
                                title = rend.get("title", {}).get("simpleText") or rend.get("title", {}).get("runs", [{}])[0].get("text")
                                handle = rend.get("subscriberCountText", {}).get("simpleText", "")
                                return {"channel_id": cid, "name": title or raw, "handle": handle or f"@{raw}", "avatar": ""}
                        stack.extend(curr.values())
                    elif isinstance(curr, list):
                        stack.extend(curr)
    except Exception:
        pass

    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_channel_videos(channel_id: str, channel_name: str = "") -> List[Dict[str, Any]]:
    if not channel_id:
        return []
    videos = []
    
    # 1. Try YouTube RSS feed
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        res = requests.get(rss_url, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "media": "http://search.yahoo.com/mrss/",
            }
            for entry in root.findall("atom:entry", ns):
                vid_elem = entry.find("yt:videoId", ns)
                if vid_elem is None or not vid_elem.text:
                    continue
                video_id = vid_elem.text
                title_elem = entry.find("atom:title", ns)
                title = title_elem.text if title_elem is not None and title_elem.text else "Untitled"
                author_elem = entry.find("atom:author/atom:name", ns)
                channel = (author_elem.text if author_elem is not None and author_elem.text else "") or channel_name
                
                published_elem = entry.find("atom:published", ns)
                published = published_elem.text[:10] if published_elem is not None and published_elem.text else ""
                
                parsed = smart_parse_title(title)
                artist = parsed["artist"] if parsed["artist"] != "Audio Track" else (channel or "Channel Track")
                is_music = is_music_track(title, channel=channel, tags=parsed["tags"])
                
                videos.append({
                    "id": video_id,
                    "raw_title": title,
                    "title": parsed["song"],
                    "artist": artist,
                    "tags": parsed["tags"],
                    "channel": channel,
                    "duration": published,
                    "url": build_youtube_url(video_id),
                    "is_music": is_music,
                })
    except Exception:
        pass

    # 2. Fallback search if RSS had 0 videos
    if not videos and channel_name:
        fallback_results = search_youtube_raw(f"{channel_name}", max_items=20)
        for trk in fallback_results:
            videos.append(trk)

    return videos

def build_youtube_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


STRONG_MUSIC_KEYWORDS = (
    "cover", "커버", "歌ってみた", "우타이테", "utaite",
    "mv", "m/v", "music video", "뮤직비디오", "official mv", "official audio", "official video",
    "음악", "노래", "song", "album", "앨범", "ost", "soundtrack", "bgm",
    "remix", "리믹스", "lofi", "로파이", "acoustic", "어쿠스틱",
    "flac", "가사", "full ver", "full ver.", "vocal", "보컬",
    "playlist", "플레이리스트", "inst", "instrumental", "singing", "karaoke",
    "노래방", "가창", "작곡", "작사", "음원", "track", "feat.", "feat", "single", "싱글", "ep",
    "노래방송", "우타와꾸", "singing stream",
)

NON_MUSIC_KEYWORDS = (
    "gameplay", "walkthrough", "playthrough", "실황", "게임", "하이라이트", "다시보기",
    "vlog", "브이로그", "리뷰", "review", "먹방", "mukbang", "unboxing", "언박싱",
    "토크", "talk", "잡담", "뉴스", "news", "강의", "lecture", "tutorial", "튜토리얼",
    "반응", "reaction", "shorts", "쇼츠", "q&a", "공지", "notice", "월드컵", "이상형월드컵",
    "챌린지", "challenge", "trailer", "트레일러", "티저", "teaser", "예고편", "영화", "movie",
    "drama", "드라마", "animation", "애니메이션", "highlight", "클립", "clip",
    "생방송", "livestream", "소통",
)

TAG_KEYWORDS = {
    "COVER": ("cover", "커버", "歌ってみた", "우타이테"),
    "ORIGINAL": ("official mv", "official music video", "원곡", "뮤직비디오", "m/v"),
    "LIVE": ("live clip", "라이브 클립", "concert", "콘서트", "live stage", "stage mix"),
    "REMIX": ("remix", "리믹스"),
    "BGM": ("lofi", "로파이", "bgm", "chill hop", "chill beats"),
    "ACOUSTIC": ("acoustic", "어쿠스틱", "unplugged"),
}

def analyze_title(title: str) -> List[str]:
    title_lower = title.lower()
    return [tag for tag, keywords in TAG_KEYWORDS.items() if any(kw in title_lower for kw in keywords)]

def is_music_track(title: str, channel: str = "", tags: Optional[List[str]] = None) -> bool:
    t_lower = title.lower()
    c_lower = channel.lower()
    
    # 1. Check strong music keywords in title
    has_strong_title = any(kw in t_lower for kw in STRONG_MUSIC_KEYWORDS)
    
    # 2. Check non-music keywords in title
    has_non_music = any(kw in t_lower for kw in NON_MUSIC_KEYWORDS)
    
    if has_strong_title:
        return True
    if has_non_music:
        return False
        
    # 3. Check tags
    if tags:
        music_tags = {"COVER", "ORIGINAL", "REMIX", "BGM", "ACOUSTIC", "LIVE"}
        if any(t in music_tags for t in tags):
            return True
            
    # 4. Check typical music title patterns
    if any(sep in title for sep in (" - ", " – ", " — ", " / ", " | ")):
        if any(mkw in c_lower for mkw in ("records", "music", "audio", "vevo", "sound", "band", "orchestra", "topic", "엔터테인먼트", "ent")):
            return True
        if any(mkw in t_lower for mkw in ("feat", "ft.", "prod.", "ver.", "mix", "theme", "op", "ed")):
            return True

    return False

def smart_parse_title(raw_title: str) -> Dict[str, Any]:
    cleaned = raw_title.strip()
    tags = analyze_title(cleaned)
    clean_text = re.sub(r"[\[【\(\「『].*?[\]】\)\」』]", "", cleaned).strip()
    cover_match = re.search(
        r"^(.*?)\s*(?:covered\s+by|cover\s+by|vocal\s+by|song\s+by)\s*(.*?)$",
        clean_text, re.IGNORECASE,
    )
    if cover_match:
        return {
            "artist": cover_match.group(2).strip() or "Artist",
            "song": cover_match.group(1).strip() or raw_title,
            "tags": tags,
        }
    parts = [p.strip() for p in re.split(r"[-–—/|:~]", clean_text) if p.strip()]
    if len(parts) >= 2:
        noise_pattern = r"(?i)\b(cover|커버|live|official|mv|full|ver)\b"
        artist_candidate = re.sub(noise_pattern, "", parts[0]).strip()
        song_candidate = re.sub(noise_pattern, "", parts[1]).strip()
        return {"artist": artist_candidate or parts[0], "song": song_candidate or parts[1], "tags": tags}
    return {"artist": "Audio Track", "song": clean_text or raw_title, "tags": tags}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_lyrics(song: str, artist: str) -> Optional[Dict[str, Any]]:
    if not song or song in {"STANDBY MODE", "NO TRACK LOADED"}:
        return None
    api_base = "https://lrclib.net/api"
    try:
        res = requests.get(f"{api_base}/get", params={"track_name": song, "artist_name": artist}, timeout=3)
        if res.status_code == 200:
            data = res.json()
            if data.get("syncedLyrics") or data.get("plainLyrics"):
                return {"synced": data.get("syncedLyrics"), "plain": data.get("plainLyrics"), "track": song, "artist": artist}
        query = f"{song} {artist}".strip()
        search_res = requests.get(f"{api_base}/search", params={"q": query}, timeout=3)
        if search_res.status_code == 200:
            results = search_res.json()
            if results and isinstance(results, list):
                first_match = results[0]
                return {"synced": first_match.get("syncedLyrics"), "plain": first_match.get("plainLyrics"), "track": song, "artist": artist}
    except requests.RequestException:
        pass
    return None

def parse_lrc_lines(synced_text: Optional[str]) -> List[Dict[str, Any]]:
    if not synced_text:
        return []
    lines = []
    lrc_regex = re.compile(r"\[(\d{2}):(\d{2}\.\d{2,3})\](.*)")
    for line in synced_text.splitlines():
        match = lrc_regex.match(line)
        if not match:
            continue
        minutes, seconds, text = int(match.group(1)), float(match.group(2)), match.group(3).strip()
        if text:
            lines.append({"sec": minutes * 60 + seconds, "text": text})
    return lines


@st.cache_data(ttl=300, show_spinner=False)
def search_youtube_raw(query: str, max_items: int = 25) -> List[Dict[str, Any]]:
    if not query or not query.strip():
        return []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    encoded_query = requests.utils.quote(query.strip())
    url = f"https://www.youtube.com/results?search_query={encoded_query}&hl=ko&gl=KR"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return []
        patterns = [
            r"var ytInitialData\s*=\s*({.+?});</script>",
            r'window\["ytInitialData"\]\s*=\s*({.+?});',
            r"ytInitialData\s*=\s*({.+?});",
        ]
        raw_json = None
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                try:
                    raw_json = json.loads(match.group(1))
                    break
                except json.JSONDecodeError:
                    continue
        if not raw_json:
            return []
        results: List[Dict[str, Any]] = []
        seen_ids = set()

        def parse_video_renderer(renderer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            video_id = renderer.get("videoId", "")
            if not video_id or len(video_id) != 11 or video_id in seen_ids:
                return None
            seen_ids.add(video_id)
            title_runs = renderer.get("title", {}).get("runs", [])
            title = title_runs[0].get("text", "Untitled") if title_runs else renderer.get("title", {}).get("simpleText", "Untitled")
            owner_runs = renderer.get("ownerText", {}).get("runs", [])
            channel = owner_runs[0].get("text", "") if owner_runs else ""
            duration = renderer.get("lengthText", {}).get("simpleText", "")
            parsed = smart_parse_title(title)
            artist = parsed["artist"] if parsed["artist"] != "Audio Track" else (channel or "Unknown Artist")
            is_music = is_music_track(title, channel=channel, tags=parsed["tags"])
            return {
                "id": video_id, "raw_title": title, "title": parsed["song"],
                "artist": artist, "tags": parsed["tags"], "channel": channel,
                "duration": duration, "url": build_youtube_url(video_id), "is_music": is_music,
            }

        stack = [raw_json]
        while stack and len(results) < max_items:
            curr = stack.pop()
            if isinstance(curr, dict):
                if "videoRenderer" in curr:
                    video_info = parse_video_renderer(curr["videoRenderer"])
                    if video_info:
                        results.append(video_info)
                stack.extend(curr.values())
            elif isinstance(curr, list):
                stack.extend(curr)
        return results
    except Exception:
        return []




def download_mp3_from_youtube(youtube_url: str, title: str) -> Optional[bytes]:
    """Download audio from YouTube and return MP3 bytes using yt-dlp with android client."""
    if not YTDLP_AVAILABLE:
        st.error("yt-dlp가 설치되지 않았습니다. requirements.txt에 yt-dlp를 추가해주세요.")
        return None
    safe_title = re.sub(r'[\\/:*?"<>|]', "", title).strip() or "audio"
    tmpdir = tempfile.mkdtemp(prefix="ftube_dl_")
    outtmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            dl_title = re.sub(r'[\\/:*?"<>|]', "", info.get("title", safe_title)).strip()
            mp3_path = os.path.join(tmpdir, f"{dl_title}.mp3")
            # yt-dlp sometimes names it differently, find the .mp3
            if not os.path.exists(mp3_path):
                for fname in os.listdir(tmpdir):
                    if fname.endswith(".mp3"):
                        mp3_path = os.path.join(tmpdir, fname)
                        break
            if os.path.exists(mp3_path):
                with open(mp3_path, "rb") as f:
                    mp3_bytes = f.read()
                # Cleanup
                try:
                    import shutil
                    shutil.rmtree(tmpdir, ignore_errors=True)
                except Exception:
                    pass
                return mp3_bytes
    except Exception as e:
        try:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass
        st.error(f"다운로드 실패: {e}")
    return None


STOPWORDS = {
    "이", "그", "저", "것", "수", "을", "를", "가", "은", "는", "에", "의", "로", "으로",
    "와", "과", "도", "만", "다", "에서", "하다", "있다", "없다", "하고", "했다", "한", "등",
    "the", "a", "an", "in", "of", "to", "is", "on", "at", "by", "for"
}

def get_recommendations(force_refresh: bool = False) -> Tuple[List[Dict[str, Any]], str]:
    if not force_refresh and st.session_state.get("cached_recommendations"):
        return st.session_state.cached_recommendations, st.session_state.get("cached_rec_keyword", "음악")
        
    user_keywords = get_keywords()
    if user_keywords:
        top_keyword = " ".join([k["keyword"] for k in user_keywords[:3]])
        results = search_youtube_raw(top_keyword, max_items=12)
        if results:
            st.session_state.cached_recommendations = results
            st.session_state.cached_rec_keyword = top_keyword
            return results, top_keyword
            
    history = get_history(30)
    favorites = get_favorites()
    all_titles = [h["title"] for h in history] + [f["title"] for f in favorites]
    if not all_titles:
        results = search_youtube_raw("인기 노래 플레이리스트", max_items=12)
        st.session_state.cached_recommendations = results
        st.session_state.cached_rec_keyword = "인기 음악 추천"
        return results, "인기 음악 추천"
        
    words = [
        word for title in all_titles
        for word in title.split()
        if len(word) > 1 and word.lower() not in STOPWORDS
    ]
    top_words = [word for word, _ in Counter(words).most_common(2)]
    keyword = " ".join(top_words) if top_words else "음악"
    results = search_youtube_raw(f"{keyword} 노래", max_items=12)
    st.session_state.cached_recommendations = results
    st.session_state.cached_rec_keyword = keyword
    return results, keyword


def play_track(track: Dict[str, Any], queue_list: Optional[List[Dict[str, Any]]] = None, pos: Optional[int] = None) -> None:
    track_url = track.get("url", "")
    track_title = track.get("title") or track.get("raw_title", "Track")
    track_artist = track.get("artist", "Unknown Artist")
    track_channel = track.get("channel", "")
    st.session_state.url = track_url
    st.session_state.title = track_title
    st.session_state.artist = track_artist
    st.session_state.channel = track_channel
    st.session_state.is_playing = True
    st.session_state.current_lyrics = fetch_lyrics(track_title, track_artist)
    if queue_list is not None:
        st.session_state.queue = queue_list
        st.session_state.queue_index = pos if pos is not None else 0
    else:
        curr_queue = st.session_state.queue
        match_idx = next((i for i, q in enumerate(curr_queue) if q.get("url") == track_url), None)
        if match_idx is not None:
            st.session_state.queue_index = match_idx
        else:
            curr_queue.append(track)
            st.session_state.queue = curr_queue
            st.session_state.queue_index = len(curr_queue) - 1
    user_id = get_current_user_id()
    if user_id and track_url:
        try:
            supabase.table("history").insert({
                "user_id": user_id,
                "title": f"{track_title} - {track_artist}",
                "url": track_url,
            }).execute()
            st.session_state.cached_history = None
        except Exception:
            pass
    st.rerun()

def play_next() -> None:
    queue = st.session_state.queue
    if not queue:
        return
    if st.session_state.repeat_mode == "one":
        st.rerun()
        return
    if st.session_state.shuffle:
        next_pos = random.randint(0, len(queue) - 1)
    else:
        next_pos = st.session_state.queue_index + 1
        if next_pos >= len(queue):
            if st.session_state.repeat_mode == "all":
                next_pos = 0
            else:
                st.session_state.is_playing = False
                st.rerun()
                return
    play_track(queue[next_pos], queue_list=queue, pos=next_pos)

def play_prev() -> None:
    queue = st.session_state.queue
    if not queue:
        return
    prev_pos = max(0, st.session_state.queue_index - 1)
    play_track(queue[prev_pos], queue_list=queue, pos=prev_pos)


def render_track_row(
    index: int, track: Dict[str, Any], key_prefix: str,
    user_playlists: Optional[List[Dict[str, Any]]] = None,
    queue_source: Optional[List[Dict[str, Any]]] = None,
    show_queue_add: bool = True, show_fav_toggle: bool = True,
    show_playlist_add: bool = True, show_delete_btn: bool = False,
    on_delete: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> None:
    tags_html = "".join([f"<span class='track-tag-badge'>{t}</span>" for t in track.get("tags", [])[:2]])
    title = track.get("title") or track.get("raw_title", "Unknown Track")
    artist = track.get("artist", "Unknown Artist")
    channel_info = f" · {track['channel']}" if track.get("channel") else ""
    duration = track.get("duration", "")
    is_music = track.get("is_music")
    if is_music is None:
        is_music = is_music_track(track.get("raw_title") or track.get("title", ""), channel=track.get("channel", ""), tags=track.get("tags"))
    music_badge = (
        "<span class='track-tag-badge' style='color:#4ade80;border-color:rgba(74,222,128,0.3);'>🎵 MUSIC</span>"
        if is_music
        else "<span class='track-tag-badge' style='color:#c084fc;border-color:rgba(192,132,252,0.3);'>🎬 VIDEO</span>"
    )
    st.markdown(f"""
    <div class="track-row">
        <div class="track-left">
            <div class="track-num">{index+1:02d}</div>
            <div class="track-info">
                <div class="track-title-text">{music_badge}{tags_html}{title}</div>
                <div class="track-artist-text">{artist}{channel_info}</div>
            </div>
        </div>
        <div class="track-duration">{duration}</div>
    </div>
    """, unsafe_allow_html=True)

    col_configs = [1.8]
    if show_playlist_add and user_playlists:
        col_configs.append(1.2)
    if show_fav_toggle:
        col_configs.append(1)
    if show_queue_add:
        col_configs.append(1)
    if show_delete_btn:
        col_configs.append(1)

    cols = st.columns(col_configs)
    curr_col = 0

    with cols[curr_col]:
        if st.button("▶ 재생", key=f"{key_prefix}_p_{index}", use_container_width=True):
            play_track(track)
    curr_col += 1

    if show_playlist_add and user_playlists:
        with cols[curr_col]:
            with st.popover("📂 플리 담기", use_container_width=True):
                st.caption(f"'{title[:20]}...' 담을 플레이리스트 선택")
                for pl in user_playlists:
                    if st.button(f"➕ {pl['name']}", key=f"{key_prefix}_pladd_{index}_{pl['id']}", use_container_width=True):
                        success = add_track_to_playlist(pl["id"], track)
                        if success:
                            st.toast(f"'{pl['name']}'에 추가되었습니다.")
                            st.rerun()
                        else:
                            st.toast("이미 등록되어 있거나 추가 실패했습니다.")
        curr_col += 1

    if show_fav_toggle:
        with cols[curr_col]:
            is_fav_track = is_favorite(track.get("url", ""))
            fav_label = "★ 해제" if is_fav_track else "★ 담기"
            if st.button(fav_label, key=f"{key_prefix}_f_{index}", use_container_width=True):
                toggle_favorite(title, track.get("url", ""))
                st.rerun()
        curr_col += 1

    if show_queue_add:
        with cols[curr_col]:
            if st.button("+ 대기열", key=f"{key_prefix}_q_{index}", use_container_width=True):
                st.session_state.queue.append(track)
                st.toast(f"'{title}' 대기열 추가 완료")
        curr_col += 1

    if show_delete_btn and on_delete:
        with cols[curr_col]:
            if st.button("삭제", key=f"{key_prefix}_d_{index}", use_container_width=True):
                on_delete(track)
                st.rerun()


if not st.session_state.user:
    st.markdown("""
    <style>
    /* Lock scrolling on authentication view */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        overflow: hidden !important;
        height: 100vh !important;
        max-height: 100vh !important;
    }
    [data-testid="block-container"] {
        padding-top: 16px !important;
        padding-bottom: 0px !important;
        max-height: 100vh !important;
    }
    .ftube-top-bar {
        margin-bottom: 14px !important;
        padding: 10px 18px !important;
    }
    div[data-testid="stForm"] {
        padding: 16px 20px !important;
    }
    div[data-testid="stForm"] .stTextInput {
        margin-bottom: -6px !important;
    }
    </style>
    <div class="ftube-top-bar">
        <div class="brand-group">
            <div class="brand-logo-text">🎵 FTUBE <span>HYBRID</span></div>
            <div class="brand-tag">AUDIO & CINEMA</div>
        </div>
        <div class="mode-indicator-pill"><div class="beacon-dot"></div>HIGH-RES AUDIO ENGINE</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_auth, col_r = st.columns([1, 1.3, 1])
    with col_auth:
        if st.session_state.auth_mode == "login":
            st.markdown("""
            <div style="text-align: center; margin-top: 4px; margin-bottom: 12px;">
                <div style="font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2px;">✨ 플레이어 로그인</div>
                <div style="font-family: 'Share Tech Mono', monospace; font-size: 0.74rem; color: #94a3b8; letter-spacing: 0.05em;">FTUBE 미디어 엔진에 오신 것을 환영합니다</div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("아이디", placeholder="아이디 입력")
                password = st.text_input("비밀번호", placeholder="비밀번호 입력", type="password")
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                login_btn = st.form_submit_button("로그인", use_container_width=True)
                if login_btn:
                    if not username or not password:
                        st.warning("아이디와 비밀번호를 입력해주세요.")
                    else:
                        res = supabase.table("users").select("*").eq("username", username).eq("password", hash_password(password)).execute()
                        if res.data:
                            st.session_state.user = {"id": res.data[0]["id"], "username": res.data[0]["username"]}
                            st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("계정 생성 (회원가입)", use_container_width=True):
                st.session_state.auth_mode = "register"
                st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; margin-top: 4px; margin-bottom: 12px;">
                <div style="font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2px;">✨ 새 계정 등록</div>
                <div style="font-family: 'Share Tech Mono', monospace; font-size: 0.74rem; color: #94a3b8; letter-spacing: 0.05em;">플레이리스트와 즐겨찾기를 저장하세요</div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("reg_form"):
                username = st.text_input("아이디", placeholder="사용할 아이디")
                password = st.text_input("비밀번호", placeholder="비밀번호", type="password")
                password_confirm = st.text_input("비밀번호 확인", placeholder="비밀번호 재입력", type="password")
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                reg_btn = st.form_submit_button("가입하기", use_container_width=True)
                if reg_btn:
                    if not username or not password:
                        st.warning("모든 정보를 입력해주세요.")
                    elif password != password_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    else:
                        existing_user = supabase.table("users").select("id").eq("username", username).execute()
                        if existing_user.data:
                            st.error("이미 존재하는 아이디입니다.")
                        else:
                            supabase.table("users").insert({"username": username, "password": hash_password(password)}).execute()
                            st.success("가입이 완료되었습니다.")
                            st.session_state.auth_mode = "login"
                            st.rerun()
            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            if st.button("로그인 화면으로", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.rerun()
    st.stop()


is_mp3_mode = st.session_state.player_mode == "mp3"
beacon_cls = "beacon-dot" if is_mp3_mode else "beacon-dot video-mode"
mode_title_badge = "MP3 DAP" if is_mp3_mode else "CINEMA VIDEO"

head_col_logo, head_col_theme, head_col_switch, head_col_user, head_col_out = st.columns([2.0, 1.6, 2.0, 1.8, 0.9], vertical_alignment="center")

with head_col_logo:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;">
        <div class="brand-logo-text">🎵 FTUBE<span>.{mode_title_badge}</span></div>
    </div>
    """, unsafe_allow_html=True)

with head_col_theme:
    with st.popover(f"🎨 THEME: {st.session_state.lcd_theme.upper()}", use_container_width=True):
        st.caption("LCD 백라이트 테마 변경")
        for theme_key, theme_data in THEMES.items():
            is_cur = st.session_state.lcd_theme == theme_key
            mark = "● " if is_cur else "○ "
            if st.button(f"{mark}{theme_data['name']}", key=f"head_theme_{theme_key}", use_container_width=True):
                st.session_state.lcd_theme = theme_key
                st.rerun()

with head_col_switch:
    st.markdown('<div class="btn-mode-toggle">', unsafe_allow_html=True)
    switch_btn_label = "🎬 영상 모드로 전환" if is_mp3_mode else "📻 MP3 오디오 모드로 전환"
    if st.button(switch_btn_label, use_container_width=True, key="header_mode_switch_btn"):
        st.session_state.player_mode = "video" if is_mp3_mode else "mp3"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with head_col_user:
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;">
        <div class="mode-indicator-pill"><div class="{beacon_cls}"></div>{mode_title_badge}</div>
        <div style="font-size:0.82rem;font-family:'JetBrains Mono';color:#94a3b8;">USER: <b style="color:#60a5fa;">{st.session_state.user['username']}</b></div>
    </div>
    """, unsafe_allow_html=True)

with head_col_out:
    if st.button("로그아웃", use_container_width=True, key="header_logout_btn"):
        st.session_state.user = None
        st.rerun()


current_title = st.session_state.title or "NO TRACK LOADED"
current_artist = st.session_state.artist or "STANDBY MODE"
current_channel = st.session_state.channel or ""
is_active = st.session_state.is_playing and bool(st.session_state.url)
queue_len = len(st.session_state.queue)
pos_display = f"{st.session_state.queue_index + 1:02d}/{queue_len:02d}" if queue_len else "00/00"
video_id_match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", st.session_state.url) if st.session_state.url else None
current_vid_id = video_id_match.group(1) if video_id_match else ""
lyrics_data = st.session_state.current_lyrics or fetch_lyrics(current_title, current_artist)

deck_col_player, deck_col_queue = st.columns([1.55, 1.0], gap="medium")

with deck_col_player:
    if is_mp3_mode:
        lyrics_display = "♪ (INSTRUMENTAL / NO LYRICS FOUND) ♪"
        if lyrics_data:
            if lyrics_data.get("synced"):
                parsed_lines = parse_lrc_lines(lyrics_data["synced"])
                if parsed_lines:
                    lyrics_display = f"♫ {parsed_lines[0]['text']}"
            elif lyrics_data.get("plain"):
                first_lines = [l.strip() for l in lyrics_data["plain"].splitlines() if l.strip()]
                if first_lines:
                    lyrics_display = f"♫ {first_lines[0]}"
        if not is_active:
            lyrics_display = "[ STANDBY // SELECT A TRACK TO PLAY ]"

        status_label = "▶ PLAYING" if is_active else "■ STANDBY"
        status_class = "lcd-status-playing" if is_active else "lcd-status-idle"
        eq_class = "active" if is_active else ""

        st.markdown(f"""
        <div class="mp3-device-deck">
            <div class="mp3-lcd-screen">
                <div class="lcd-top-bar">
                    <div class="{status_class}">{status_label}</div>
                    <div class="lcd-meta-badge">TRK [{pos_display}]</div>
                    <div class="lcd-codec">AUDIO · 320 KBPS · STEREO</div>
                </div>
                <div class="lcd-main-info">
                    <div class="lcd-track-title">🎵 {current_title}</div>
                    <div class="lcd-artist-name">ARTIST // {current_artist}</div>
                </div>
                <div class="lcd-lyrics-box">
                    <div class="lcd-lyrics-text">{lyrics_display}</div>
                </div>
                <div class="lcd-eq-wrap">
                    {"".join(['<div class="lcd-eq-bar ' + eq_class + '"></div>' for _ in range(12)])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if is_active and current_vid_id:
            st.markdown(f'''
            <iframe id="ftube_audio_iframe" class="hidden-audio-frame"
                src="https://www.youtube.com/embed/{current_vid_id}?autoplay=1&enablejsapi=1&rel=0&origin=https://ftube.streamlit.app"
                allow="autoplay; encrypted-media">
            </iframe>
            <script>
            (function() {{
                var vid = "{current_vid_id}";
                if (!vid) return;

                function ftube_trigger_next() {{
                    var attempt = 0;
                    function tryClick() {{
                        var doc = (window.parent && window.parent.document !== window.document)
                                  ? window.parent.document : document;
                        var btns = Array.from(doc.querySelectorAll('button'));
                        var nBtn = btns.find(function(b) {{
                            return b.textContent && b.textContent.trim().indexOf('NEXT') !== -1;
                        }});
                        if (nBtn) {{ nBtn.click(); return; }}
                        if (++attempt < 8) setTimeout(tryClick, 400);
                    }}
                    tryClick();
                }}

                // Clear old player if vid changed
                if (window._ftubeVid !== vid) {{
                    window._ftubeVid = vid;
                    window._ftubeYTReady = false;
                    if (window._ftubePlayer) {{
                        try {{ window._ftubePlayer.destroy(); }} catch(e) {{}}
                        window._ftubePlayer = null;
                    }}
                }}

                var savedPos = parseFloat(sessionStorage.getItem("ftube_play_pos_" + vid) || "0");

                function initPlayer() {{
                    if (window._ftubeYTReady) return;
                    var iframe = document.getElementById("ftube_audio_iframe");
                    if (!iframe || !window.YT || !window.YT.Player) return;
                    window._ftubeYTReady = true;
                    window._ftubePlayer = new YT.Player(iframe, {{
                        events: {{
                            onReady: function(e) {{
                                if (savedPos > 1) e.target.seekTo(savedPos, true);
                                if (window._ftubeSaveLoop) clearInterval(window._ftubeSaveLoop);
                                window._ftubeSaveLoop = setInterval(function() {{
                                    try {{
                                        var t = window._ftubePlayer.getCurrentTime();
                                        if (t > 0) sessionStorage.setItem("ftube_play_pos_" + vid, t.toString());
                                    }} catch(e) {{}}
                                }}, 1000);
                            }},
                            onStateChange: function(e) {{
                                if (e.data === 0) {{
                                    sessionStorage.removeItem("ftube_play_pos_" + vid);
                                    if (window._ftubeSaveLoop) clearInterval(window._ftubeSaveLoop);
                                    ftube_trigger_next();
                                }}
                            }}
                        }}
                    }});
                }}

                // Load YT API once
                if (!window._ftubeAPILoaded) {{
                    window._ftubeAPILoaded = true;
                    var tag = document.createElement('script');
                    tag.src = "https://www.youtube.com/iframe_api";
                    document.head.appendChild(tag);
                    var _prev = window.onYouTubeIframeAPIReady;
                    window.onYouTubeIframeAPIReady = function() {{
                        if (_prev) _prev();
                        initPlayer();
                    }};
                }} else if (window.YT && window.YT.Player) {{
                    setTimeout(initPlayer, 300);
                }} else {{
                    var _prev2 = window.onYouTubeIframeAPIReady;
                    window.onYouTubeIframeAPIReady = function() {{
                        if (_prev2) _prev2();
                        initPlayer();
                    }};
                }}
            }})();
            </script>
            ''', unsafe_allow_html=True)

        c_prev, c_play, c_next, c_shuf, c_rep, c_lyr, c_fav = st.columns([1.0, 1.25, 1.0, 1.0, 1.0, 1.0, 0.9], vertical_alignment="center")
        with c_prev:
            if st.button("⏮ PREV", use_container_width=True, key="deck_prev"):
                play_prev()
        with c_play:
            if st.button("⏸ PAUSE" if is_active else "▶ PLAY", use_container_width=True, key="deck_play", type="primary"):
                st.session_state.is_playing = not st.session_state.is_playing
                st.rerun()
        with c_next:
            if st.button("NEXT ⏭", use_container_width=True, key="deck_next"):
                play_next()
        with c_shuf:
            shuf_label = "🔀 ON" if st.session_state.shuffle else "🔀 셔플"
            if st.button(shuf_label, use_container_width=True, key="deck_shuffle", help="셔플 모드"):
                st.session_state.shuffle = not st.session_state.shuffle
                st.rerun()
        with c_rep:
            rep_labels = {"all": "🔁 ALL", "one": "🔂 ONE", "off": "➡ OFF"}
            if st.button(rep_labels.get(st.session_state.repeat_mode, "🔁 ALL"), use_container_width=True, key="deck_repeat", help="반복 모드"):
                next_mode_map = {"all": "one", "one": "off", "off": "all"}
                st.session_state.repeat_mode = next_mode_map[st.session_state.repeat_mode]
                st.rerun()
        with c_lyr:
            lyr_label = "📜 닫기" if st.session_state.show_lyrics_drawer else "📜 가사"
            if st.button(lyr_label, use_container_width=True, key="deck_lyrics_toggle", help="가사 뷰어 토글"):
                st.session_state.show_lyrics_drawer = not st.session_state.show_lyrics_drawer
                st.rerun()
        with c_fav:
            if st.button("★ FAV" if is_favorite(st.session_state.url) else "☆ FAV", use_container_width=True, key="deck_fav", help="즐겨찾기 토글"):
                if st.session_state.url:
                    toggle_favorite(st.session_state.title, st.session_state.url)
                    st.rerun()

        # --- MP3 Download Row ---
        if is_active and st.session_state.url and YTDLP_AVAILABLE:
            st.markdown("""
            <div style="margin-top:10px;padding:10px 14px;background:rgba(15,23,42,0.5);
                        border:1px solid rgba(96,165,250,0.2);border-radius:12px;
                        display:flex;align-items:center;gap:10px;">
                <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#60a5fa;letter-spacing:0.1em;">
                    💾 MP3 EXPORT
                </div>
                <div style="font-size:0.78rem;color:#94a3b8;">
                    현재 트랙을 192kbps MP3로 추출합니다. yt-dlp + FFmpeg 처리 (수십 초 소요)
                </div>
            </div>
            """, unsafe_allow_html=True)
            dl_col_btn, dl_col_info = st.columns([1.2, 3])
            with dl_col_btn:
                if st.button("⬇ MP3 다운로드", use_container_width=True, key="deck_mp3_download_btn", help="현재 재생 중인 트랙을 MP3로 저장"):
                    dl_title = st.session_state.title or "audio"
                    dl_url = st.session_state.url
                    with st.spinner(f"🔄 '{dl_title}' MP3 변환 중... (잠시만 기다려주세요)"):
                        mp3_data = download_mp3_from_youtube(dl_url, dl_title)
                    if mp3_data:
                        safe_name = re.sub(r'[\\/:*?"<>|]', "", dl_title).strip() or "audio"
                        st.download_button(
                            label=f"📥 '{safe_name}.mp3' 저장",
                            data=mp3_data,
                            file_name=f"{safe_name}.mp3",
                            mime="audio/mpeg",
                            key="deck_mp3_save_btn",
                            use_container_width=True,
                        )
                        st.toast(f"'{safe_name}.mp3' 변환 완료! 저장 버튼을 눌러주세요.")


    else:
        st.markdown('<div class="video-cinema-deck">', unsafe_allow_html=True)
        if is_active and current_vid_id:
            st.markdown(f'''
            <div class="video-wrapper">
                <iframe id="ftube_video_iframe"
                    src="https://www.youtube.com/embed/{current_vid_id}?autoplay=1&enablejsapi=1&rel=0&origin=https://ftube.streamlit.app"
                    allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen>
                </iframe>
            </div>
            <script>
            (function() {{
                var vid = "{current_vid_id}";
                if (!vid) return;

                function ftube_trigger_next() {{
                    var attempt = 0;
                    function tryClick() {{
                        var doc = (window.parent && window.parent.document !== window.document)
                                  ? window.parent.document : document;
                        var btns = Array.from(doc.querySelectorAll('button'));
                        var nBtn = btns.find(function(b) {{
                            return b.textContent && b.textContent.trim().indexOf('NEXT') !== -1;
                        }});
                        if (nBtn) {{ nBtn.click(); return; }}
                        if (++attempt < 8) setTimeout(tryClick, 400);
                    }}
                    tryClick();
                }}

                if (window._ftubeVideoVid !== vid) {{
                    window._ftubeVideoVid = vid;
                    window._ftubeVideoReady = false;
                    if (window._ftubeVideoPlayer) {{
                        try {{ window._ftubeVideoPlayer.destroy(); }} catch(e) {{}}
                        window._ftubeVideoPlayer = null;
                    }}
                }}

                var savedPos = parseFloat(sessionStorage.getItem("ftube_play_pos_" + vid) || "0");

                function initVideoPlayer() {{
                    if (window._ftubeVideoReady) return;
                    var iframe = document.getElementById("ftube_video_iframe");
                    if (!iframe || !window.YT || !window.YT.Player) return;
                    window._ftubeVideoReady = true;
                    window._ftubeVideoPlayer = new YT.Player(iframe, {{
                        events: {{
                            onReady: function(e) {{
                                if (savedPos > 1) e.target.seekTo(savedPos, true);
                                if (window._ftubeVideoSaveLoop) clearInterval(window._ftubeVideoSaveLoop);
                                window._ftubeVideoSaveLoop = setInterval(function() {{
                                    try {{
                                        var t = window._ftubeVideoPlayer.getCurrentTime();
                                        if (t > 0) sessionStorage.setItem("ftube_play_pos_" + vid, t.toString());
                                    }} catch(e) {{}}
                                }}, 1000);
                            }},
                            onStateChange: function(e) {{
                                if (e.data === 0) {{
                                    sessionStorage.removeItem("ftube_play_pos_" + vid);
                                    if (window._ftubeVideoSaveLoop) clearInterval(window._ftubeVideoSaveLoop);
                                    ftube_trigger_next();
                                }}
                            }}
                        }}
                    }});
                }}

                if (!window._ftubeAPILoaded) {{
                    window._ftubeAPILoaded = true;
                    var tag = document.createElement('script');
                    tag.src = "https://www.youtube.com/iframe_api";
                    document.head.appendChild(tag);
                    var _prev = window.onYouTubeIframeAPIReady;
                    window.onYouTubeIframeAPIReady = function() {{
                        if (_prev) _prev();
                        initVideoPlayer();
                    }};
                }} else if (window.YT && window.YT.Player) {{
                    setTimeout(initVideoPlayer, 300);
                }} else {{
                    var _prev2 = window.onYouTubeIframeAPIReady;
                    window.onYouTubeIframeAPIReady = function() {{
                        if (_prev2) _prev2();
                        initVideoPlayer();
                    }};
                }}
            }})();
            </script>
            <div class="video-meta-bar">
                <div>
                    <div class="video-title-text">🎬 {current_title}</div>
                    <div class="video-channel-text">{current_artist} {f"· {current_channel}" if current_channel else ""}</div>
                </div>
                <div class="mode-indicator-pill"><div class="beacon-dot video-mode"></div>NOW PLAYING [{pos_display}]</div>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown('''
            <div class="video-wrapper" style="display:flex;align-items:center;justify-content:center;color:#64748b;font-family:\'Share Tech Mono\', monospace;height:240px;">
                <div style="text-align:center;padding-top:80px;">
                    <div style="font-size:2rem;margin-bottom:8px;">🎬</div>
                    <div>NO VIDEO LOADED // SELECT A TRACK BELOW</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        c_v_prev, c_v_play, c_v_next, c_v_shuf, c_v_rep, c_v_fav = st.columns([1.0, 1.35, 1.0, 1.0, 1.0, 0.9], vertical_alignment="center")
        with c_v_prev:
            if st.button("⏮ PREV", use_container_width=True, key="v_deck_prev"):
                play_prev()
        with c_v_play:
            if st.button("⏸ PAUSE" if is_active else "▶ PLAY", use_container_width=True, key="v_deck_play", type="primary"):
                st.session_state.is_playing = not st.session_state.is_playing
                st.rerun()
        with c_v_next:
            if st.button("NEXT ⏭", use_container_width=True, key="v_deck_next"):
                play_next()
        with c_v_shuf:
            shuf_label = "🔀 ON" if st.session_state.shuffle else "🔀 셔플"
            if st.button(shuf_label, use_container_width=True, key="v_deck_shuffle"):
                st.session_state.shuffle = not st.session_state.shuffle
                st.rerun()
        with c_v_rep:
            rep_labels = {"all": "🔁 ALL", "one": "🔂 ONE", "off": "➡ OFF"}
            if st.button(rep_labels.get(st.session_state.repeat_mode, "🔁 ALL"), use_container_width=True, key="v_deck_repeat"):
                next_mode_map = {"all": "one", "one": "off", "off": "all"}
                st.session_state.repeat_mode = next_mode_map[st.session_state.repeat_mode]
                st.rerun()
        with c_v_fav:
            if st.button("★ FAV" if is_favorite(st.session_state.url) else "☆ FAV", use_container_width=True, key="v_deck_fav"):
                if st.session_state.url:
                    toggle_favorite(st.session_state.title, st.session_state.url)
                    st.rerun()

with deck_col_queue:
    st.markdown(f"""
    <div class="queue-panel-deck">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px;padding-bottom:6px;border-bottom:1px dashed rgba(255,255,255,0.12);">
            <div style="font-family:'Share Tech Mono', monospace;font-size:0.85rem;color:var(--lcd-acc);font-weight:700;">
                📋 DECK QUEUE ({queue_len})
            </div>
            <div style="font-family:'Share Tech Mono', monospace;font-size:0.75rem;color:#94a3b8;">
                TRK [{pos_display}]
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.queue:
        with st.container(height=265):
            for q_idx, q_item in enumerate(st.session_state.queue):
                is_cur = q_idx == st.session_state.queue_index
                badge_icon = "▶ " if is_cur else f"{q_idx+1:02d}. "
                q_c_info, q_c_play, q_c_del = st.columns([3.8, 1.1, 0.8])
                with q_c_info:
                    cur_color = current_theme['accent'] if is_cur else '#f1f5f9'
                    st.markdown(f"""
                    <div style="padding:4px 0;overflow:hidden;">
                        <div style="font-family:'JetBrains Mono';font-size:0.80rem;color:{cur_color};font-weight:{'700' if is_cur else '400'};overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                            {badge_icon}{q_item.get('title', q_item.get('raw_title', 'Track'))}
                        </div>
                        <div style="font-size:0.72rem;color:#94a3b8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                            {q_item.get('artist', 'Unknown')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with q_c_play:
                    if st.button("▶", key=f"q_play_side_{q_idx}", use_container_width=True, help="이 곡 재생"):
                        play_track(q_item, queue_list=st.session_state.queue, pos=q_idx)
                with q_c_del:
                    if st.button("✕", key=f"q_del_side_{q_idx}", use_container_width=True, help="대기열에서 제거"):
                        st.session_state.queue.pop(q_idx)
                        if st.session_state.queue_index >= len(st.session_state.queue):
                            st.session_state.queue_index = max(0, len(st.session_state.queue) - 1)
                        st.rerun()

        col_q_save, col_q_shuf, col_q_clear = st.columns([1.2, 0.9, 0.9])
        with col_q_save:
            with st.popover("💾 플리 저장", use_container_width=True):
                st.caption(f"현재 대기열 ({len(st.session_state.queue)}곡) 저장")
                save_pl_name = st.text_input("새 플레이리스트 이름", placeholder="예: 오늘의 믹스", key="save_queue_pl_name")
                if st.button("➕ 새 플리로 생성", use_container_width=True, key="btn_save_queue_pl_submit", type="primary"):
                    if not save_pl_name.strip():
                        st.warning("이름을 입력해주세요.")
                    else:
                        user_id = get_current_user_id()
                        if user_id:
                            formatted_items = []
                            for q_item in st.session_state.queue:
                                formatted_items.append({
                                    "title": q_item.get("title") or q_item.get("raw_title", "Track"),
                                    "artist": q_item.get("artist", "Unknown Artist"),
                                    "url": q_item.get("url", ""),
                                    "duration": q_item.get("duration", ""),
                                    "channel": q_item.get("channel", ""),
                                })
                            supabase.table("playlists").insert({
                                "user_id": user_id,
                                "name": save_pl_name.strip(),
                                "items": json.dumps(formatted_items, ensure_ascii=False),
                            }).execute()
                            get_playlists(force_refresh=True)
                            st.toast(f"'{save_pl_name.strip()}' 플레이리스트로 저장되었습니다!")
                            st.rerun()
        with col_q_shuf:
            if st.button("🔀 섞기", use_container_width=True, key="shuf_deck_queue_btn"):
                random.shuffle(st.session_state.queue)
                st.rerun()
        with col_q_clear:
            if st.button("🗑 비우기", use_container_width=True, key="clear_deck_queue_btn"):
                st.session_state.queue = []
                st.session_state.queue_index = 0
                st.rerun()
    else:
        st.markdown("""
        <div style="background:rgba(15,23,42,0.6);border:1px dashed rgba(255,255,255,0.1);border-radius:12px;padding:65px 16px;text-align:center;margin-top:6px;">
            <div style="font-size:1.6rem;margin-bottom:6px;">🎵</div>
            <div style="font-family:'Share Tech Mono', monospace;font-size:0.80rem;color:#94a3b8;line-height:1.6;">
                [ QUEUE EMPTY ]<br>
                하단 추천/검색에서 곡을<br>선택하여 재생하세요
            </div>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.show_lyrics_drawer:
    st.markdown(f'<div class="section-title" style="margin-top:16px;">LYRICS VIEWER // {current_title}</div>', unsafe_allow_html=True)
    if lyrics_data and (lyrics_data.get("synced") or lyrics_data.get("plain")):
        raw_lrc = lyrics_data.get("synced") or lyrics_data.get("plain")
        cleaned_lyrics = "\n".join([re.sub(r"\[\d{2}:\d{2}\.\d{2,3}\]", "", line).strip() for line in raw_lrc.splitlines() if line.strip()])
        st.markdown(f"""
        <div style="background:{current_theme['bg']};border:1px solid {current_theme['border']};border-radius:12px;padding:20px;font-family:'Share Tech Mono', monospace;color:{current_theme['text_sub']};line-height:2.0;white-space:pre-wrap;max-height:300px;overflow-y:auto;text-align:center;">
{cleaned_lyrics}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-msg">등록된 가사를 찾을 수 없습니다. (Inst/Cover)</div>', unsafe_allow_html=True)
    st.markdown("<hr style='border-color:rgba(255,255,255,0.1);margin:16px 0;'>", unsafe_allow_html=True)


user_playlists = get_playlists()
fav_list = get_favorites()
history_list = get_history(30)
user_channels = get_user_channels()

tab_rec, tab_search, tab_channel, tab_pl, tab_fav, tab_hist, tab_url = st.tabs([
    "🎧 추천 음악", "🔍 음원 & 영상 검색",
    f"📺 채널 피드 ({len(user_channels)})",
    f"📂 플레이리스트 ({len(user_playlists)})", f"★ 즐겨찾기 ({len(fav_list)})",
    f"🕒 청취 기록 ({len(history_list)})", "🔗 URL 직접입력",
])

with tab_rec:
    st.markdown('<div class="section-title">CURATED TRACKS FOR YOU</div>', unsafe_allow_html=True)
    recs, keyword_label = get_recommendations()
    if not recs:
        st.markdown('<div class="empty-msg">추천 음원을 불러오지 못했습니다.</div>', unsafe_allow_html=True)
    else:
        display_recs = [t for t in recs if t.get("is_music", True)] if is_mp3_mode else recs
        st.caption(f"'{keyword_label}' 기반 추천 ({len(display_recs)}곡)")
        for idx, trk in enumerate(display_recs):
            render_track_row(idx, trk, key_prefix="rec", user_playlists=user_playlists)

with tab_search:
    st.markdown('<div class="section-title">SEARCH MEDIA DATABASE</div>', unsafe_allow_html=True)
    col_input, col_filter = st.columns([3.5, 1.5])
    with col_input:
        with st.form("search_music_form"):
            search_input = st.text_input("", placeholder="곡명, 아티스트, 우타이테, 커버곡 또는 영상 검색", label_visibility="collapsed")
            if st.form_submit_button("검색 실행", use_container_width=True) and search_input.strip():
                with st.spinner("미디어 검색 중..."):
                    st.session_state.search_results = search_youtube_raw(search_input.strip(), max_items=30)
                    st.session_state.search_query = search_input.strip()
    with col_filter:
        st.session_state.music_filter_only = st.checkbox("🎵 음악/커버곡만 필터", value=st.session_state.music_filter_only)
    if st.session_state.search_results:
        raw_search = st.session_state.search_results
        filtered_search = [t for t in raw_search if t.get("is_music", True)] if st.session_state.music_filter_only else raw_search
        st.caption(f"'{st.session_state.search_query}' 검색 결과: 총 {len(filtered_search)}건")
        for idx, trk in enumerate(filtered_search):
            render_track_row(idx, trk, key_prefix="search", user_playlists=user_playlists)

with tab_channel:
    st.markdown('<div class="section-title">SUBSCRIBED YOUTUBE CHANNELS & FEEDS</div>', unsafe_allow_html=True)
    with st.form("add_channel_form"):
        col_ch_in, col_ch_btn = st.columns([3.8, 1.2])
        with col_ch_in:
            ch_input = st.text_input("", placeholder="유튜브 채널 @핸들 (예: @yoasobi_staff_, @Ado1024) 또는 채널 링크 입력", label_visibility="collapsed")
        with col_ch_btn:
            add_ch_submit = st.form_submit_button("+ 채널 등록", use_container_width=True)
            
        if add_ch_submit and ch_input.strip():
            with st.spinner("채널 정보 확인 중..."):
                resolved = resolve_youtube_channel(ch_input.strip())
                if resolved:
                    success = add_user_channel(resolved)
                    if success:
                        st.session_state.selected_channel_id = resolved["channel_id"]
                        st.toast(f"'{resolved['name']}' 채널이 등록되었습니다!")
                        st.rerun()
                    else:
                        st.toast("이미 등록된 채널이거나 추가에 실패했습니다.")
                else:
                    st.error("채널을 찾을 수 없습니다. @핸들 또는 채널 링크를 확인해주세요.")

    if not user_channels:
        st.markdown("""
        <div class="empty-msg">
            등록된 유튜브 채널이 없습니다.<br>
            좋아하는 우타이테, 아티스트, 버튜버의 <b>@핸들</b>을 등록하고 최신 음원을 실시간으로 감상하세요!
        </div>
        """, unsafe_allow_html=True)
    else:
        if not st.session_state.selected_channel_id or not any(c["channel_id"] == st.session_state.selected_channel_id for c in user_channels):
            st.session_state.selected_channel_id = user_channels[0]["channel_id"]
            
        col_chips = st.columns(min(len(user_channels), 4))
        for c_idx, ch in enumerate(user_channels):
            col_target = col_chips[c_idx % min(len(user_channels), 4)]
            with col_target:
                is_selected = st.session_state.selected_channel_id == ch["channel_id"]
                btn_type = "primary" if is_selected else "secondary"
                btn_prefix = "▶ " if is_selected else "📺 "
                if st.button(f"{btn_prefix}{ch.get('channel_name', 'Channel')[:12]}", key=f"ch_sel_{ch['channel_id']}", type=btn_type, use_container_width=True):
                    st.session_state.selected_channel_id = ch["channel_id"]
                    st.rerun()
                    
        active_ch = next((c for c in user_channels if c["channel_id"] == st.session_state.selected_channel_id), user_channels[0])
        col_info, col_del = st.columns([4, 1], vertical_alignment="center")
        with col_info:
            st.markdown(f"""
            <div style="background:rgba(22,30,48,0.7);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:12px 16px;margin:10px 0;display:flex;align-items:center;justify-content:space-between;">
                <div>
                    <span style="font-size:1.05rem;font-weight:700;color:var(--lcd-acc);">📺 {active_ch.get('channel_name')}</span>
                    <span style="font-size:0.78rem;color:#94a3b8;margin-left:8px;font-family:'Share Tech Mono';">{active_ch.get('handle', '')}</span>
                </div>
                <div style="font-size:0.75rem;color:#60a5fa;font-family:'Share Tech Mono';">LATEST UPLOADS (RSS FEED)</div>
            </div>
            """, unsafe_allow_html=True)
        with col_del:
            if st.button("🗑 채널 삭제", key=f"del_ch_{active_ch['channel_id']}", use_container_width=True):
                remove_user_channel(active_ch["channel_id"])
                st.session_state.selected_channel_id = None
                st.toast(f"'{active_ch.get('channel_name')}' 채널이 삭제되었습니다.")
                st.rerun()
                
        channel_videos = fetch_channel_videos(active_ch["channel_id"], channel_name=active_ch.get("channel_name", ""))
        if not channel_videos:
            st.markdown('<div class="empty-msg">채널의 최신 영상을 불러오지 못했습니다.</div>', unsafe_allow_html=True)
        else:
            st.caption(f"'{active_ch.get('channel_name')}' 업로드 영상 피드 ({len(channel_videos)}개)")
            for idx, trk in enumerate(channel_videos):
                render_track_row(idx, trk, key_prefix="ch_feed", user_playlists=user_playlists)

with tab_pl:
    st.markdown('<div class="section-title">MY PLAYLISTS</div>', unsafe_allow_html=True)
    with st.form("new_playlist_form"):
        new_pl_name = st.text_input("", placeholder="새 플레이리스트 이름", label_visibility="collapsed")
        if st.form_submit_button("+ 새 플레이리스트 만들기", use_container_width=True) and new_pl_name.strip():
            user_id = get_current_user_id()
            if user_id:
                supabase.table("playlists").insert({"user_id": user_id, "name": new_pl_name.strip(), "items": "[]"}).execute()
                st.rerun()
    if not user_playlists:
        st.markdown('<div class="empty-msg">생성된 플레이리스트가 없습니다.</div>', unsafe_allow_html=True)
    else:
        for pl in user_playlists:
            raw_items = json.loads(pl.get("items") or "[]")
            st.markdown(f"""
            <div class="track-row" style="border-left: 4px solid var(--lcd-acc);">
                <div class="track-left">
                    <div class="track-info">
                        <div class="track-title-text">📂 {pl['name']}</div>
                        <div class="track-artist-text">수록 음원: {len(raw_items)}곡</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            col_play_all, col_delete_pl = st.columns([4, 1])
            with col_play_all:
                if raw_items and st.button(f"▶ '{pl['name']}' 전체 재생 ({len(raw_items)}곡)", key=f"pl_play_all_{pl['id']}", use_container_width=True):
                    formatted_items = []
                    for item in raw_items:
                        parsed = smart_parse_title(item["title"])
                        formatted_items.append({"title": parsed["song"], "artist": parsed["artist"], "url": item["url"], "duration": item.get("duration", ""), "channel": item.get("channel", "")})
                    play_track(formatted_items[0], queue_list=formatted_items, pos=0)
            with col_delete_pl:
                if st.button("삭제", key=f"pl_delete_{pl['id']}", use_container_width=True):
                    supabase.table("playlists").delete().eq("id", pl["id"]).execute()
                    st.rerun()
            if raw_items:
                with st.expander(f"수록곡 관리 ({len(raw_items)}곡)"):
                    for item_idx, item in enumerate(raw_items):
                        sub_col_title, sub_col_play, sub_col_del = st.columns([4, 1, 1])
                        with sub_col_title:
                            st.markdown(f"<div style='font-size:0.85rem;color:#e2e8f0;padding:6px 0;'>{item_idx+1:02d}. {item['title']} - <span style='color:#94a3b8;'>{item.get('artist', '')}</span></div>", unsafe_allow_html=True)
                        with sub_col_play:
                            if st.button("재생", key=f"pl_sub_play_{pl['id']}_{item_idx}", use_container_width=True):
                                parsed = smart_parse_title(item["title"])
                                play_track({"title": parsed["song"], "artist": parsed["artist"], "url": item["url"]})
                        with sub_col_del:
                            if st.button("제거", key=f"pl_sub_del_{pl['id']}_{item_idx}", use_container_width=True):
                                remove_track_from_playlist(pl["id"], item["url"])
                                st.rerun()

with tab_fav:
    st.markdown('<div class="section-title">FAVORITE TRACKS</div>', unsafe_allow_html=True)
    if not fav_list:
        st.markdown('<div class="empty-msg">즐겨찾기한 음원이 없습니다.</div>', unsafe_allow_html=True)
    else:
        fav_queue = []
        for fav_item in fav_list:
            parsed = smart_parse_title(fav_item["title"])
            is_m = is_music_track(fav_item["title"], tags=parsed["tags"])
            fav_queue.append({"title": parsed["song"], "artist": parsed["artist"], "url": fav_item["url"], "tags": parsed["tags"], "is_music": is_m})
        if st.button(f"▶ 즐겨찾기 전체 재생 ({len(fav_list)}곡)", use_container_width=True, key="fav_play_all"):
            play_track(fav_queue[0], queue_list=fav_queue, pos=0)
        for idx, fav_trk in enumerate(fav_queue):
            render_track_row(idx, fav_trk, key_prefix="fav", user_playlists=user_playlists, show_queue_add=True, show_fav_toggle=False, show_playlist_add=True, show_delete_btn=True, on_delete=lambda t: toggle_favorite(t["title"], t["url"]))

with tab_hist:
    st.markdown('<div class="section-title">PLAYBACK HISTORY</div>', unsafe_allow_html=True)
    if not history_list:
        st.markdown('<div class="empty-msg">청취 기록이 없습니다.</div>', unsafe_allow_html=True)
    else:
        if st.button("기록 전체 삭제", key="clear_history_btn"):
            user_id = get_current_user_id()
            if user_id:
                supabase.table("history").delete().eq("user_id", user_id).execute()
                st.rerun()
        for idx, hist_item in enumerate(history_list):
            parsed = smart_parse_title(hist_item["title"])
            is_m = is_music_track(hist_item["title"], tags=parsed["tags"])
            hist_trk = {
                "title": parsed["song"],
                "artist": f"{parsed['artist']} · {hist_item.get('watched_at', '')[:10]}",
                "url": hist_item["url"], "tags": parsed["tags"],
                "is_music": is_m,
            }
            render_track_row(idx, hist_trk, key_prefix="hist", user_playlists=user_playlists, show_queue_add=True, show_fav_toggle=True, show_playlist_add=True, show_delete_btn=True, on_delete=lambda t, h_id=hist_item["id"]: supabase.table("history").delete().eq("id", h_id).execute())

with tab_url:
    st.markdown('<div class="section-title">DIRECT MEDIA STREAM LINK</div>', unsafe_allow_html=True)
    with st.form("url_direct_play_form"):
        raw_url = st.text_input("", placeholder="YouTube 링크 (예: https://www.youtube.com/watch?v=...)", label_visibility="collapsed")
        if st.form_submit_button("미디어 스트림 로드 및 재생", use_container_width=True) and raw_url.strip():
            play_track({"title": "Direct Stream Media", "artist": "External Link", "url": raw_url.strip()})
