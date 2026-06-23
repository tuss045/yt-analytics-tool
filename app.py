import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from io import BytesIO
from datetime import date, timedelta

st.set_page_config(
    page_title="VidIQ Nova — YouTube Analytics",
    page_icon="🤖",
    layout="wide"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Page background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Hide default streamlit header */
header[data-testid="stHeader"] { background: transparent; }

/* Hero banner */
.hero {
    background: linear-gradient(120deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid rgba(229, 57, 53, 0.3);
    border-radius: 20px;
    padding: 2.5rem 2rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(229,57,53,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.6rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.3rem;
    letter-spacing: -0.5px;
}
.hero-title span {
    color: #e53935;
}
.hero-sub {
    font-size: 1rem;
    color: rgba(255,255,255,0.55);
    margin: 0;
}
.ai-badge {
    display: inline-block;
    background: rgba(229,57,53,0.15);
    border: 1px solid rgba(229,57,53,0.4);
    color: #e53935;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: 20px;
    margin-bottom: 0.8rem;
}

/* Section headers */
.section-head {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.4);
    margin-bottom: 0.5rem;
}

/* Input panel */
.input-panel {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.5rem 1.5rem 1rem;
    margin-bottom: 1.2rem;
}

/* Metric cards */
.metric-row {
    display: flex;
    gap: 12px;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.metric-card {
    flex: 1;
    min-width: 140px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
}
.metric-card .m-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.4);
    margin-bottom: 6px;
}
.metric-card .m-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1;
}
.metric-card .m-sub {
    font-size: 0.72rem;
    color: rgba(255,255,255,0.3);
    margin-top: 4px;
}
.metric-card.red { border-color: rgba(229,57,53,0.35); }
.metric-card.red .m-value { color: #e57373; }
.metric-card.blue { border-color: rgba(66,165,245,0.35); }
.metric-card.blue .m-value { color: #64b5f6; }
.metric-card.green { border-color: rgba(102,187,106,0.35); }
.metric-card.green .m-value { color: #81c784; }
.metric-card.amber { border-color: rgba(255,183,77,0.35); }
.metric-card.amber .m-value { color: #ffb74d; }

/* Channel tag chips */
.ch-chip {
    display: inline-block;
    background: rgba(229,57,53,0.12);
    border: 1px solid rgba(229,57,53,0.3);
    color: #ef9a9a;
    font-size: 0.75rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px 4px 2px 0;
}

/* Streamlit overrides */
div[data-testid="stTextInput"] > label,
div[data-testid="stDateInput"] > label,
div[data-testid="stRadio"] > label,
div[data-testid="stTextArea"] > label {
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stDateInput"] input {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #fff !important;
}
div[data-testid="stTextArea"] textarea {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-family: 'Inter', monospace !important;
    font-size: 0.85rem !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] label {
    color: rgba(255,255,255,0.75) !important;
    font-size: 0.9rem !important;
}
/* Primary button */
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #e53935, #c62828) !important;
    border: none !important;
    color: white !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    padding: 0.65rem 2rem !important;
    border-radius: 12px !important;
    letter-spacing: 0.02em !important;
    transition: opacity 0.2s !important;
    width: 100%;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: 0.88 !important;
}
/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    width: 100% !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    background: rgba(255,255,255,0.12) !important;
}
/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
/* Success / error / info */
div[data-testid="stAlert"] {
    border-radius: 12px !important;
    border: none !important;
}
/* Divider */
hr { border-color: rgba(255,255,255,0.08) !important; }
/* Spinner text */
div[data-testid="stSpinner"] p { color: rgba(255,255,255,0.6) !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">VidIQ <span>Nova</span></div>
  <p class="hero-sub">Multi-channel intelligence · Date range filter · Shorts, Long Videos & Community Posts</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar — API Key ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-head">🔑 API Configuration</div>', unsafe_allow_html=True)
    api_key = st.secrets.get("YOUTUBE_API_KEY", None)
    if not api_key:
        api_key = st.text_input("YouTube API Key", type="password", placeholder="AIzaSy...")
    else:
        st.success("API Key loaded from secrets ✓")

    st.markdown("---")
    st.markdown('<div class="section-head">ℹ️ About</div>', unsafe_allow_html=True)
    st.markdown(
        "<p style='color:rgba(255,255,255,0.4);font-size:0.78rem;line-height:1.6;'>"
        "VidIQ Nova — fetch YouTube video data across multiple channels, filter by content type & date range, "
        "and export to Excel or CSV."
        "</p>",
        unsafe_allow_html=True
    )

# ── Input Panel ───────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    channel_ids_raw = st.text_area(
        "Channel IDs (one per line)",
        placeholder="UCxxxxxxxxxxxxxxxxxxxxxx\nUCyyyyyyyyyyyyyyyyyyyyyy\nUCzzzzzzzzzzzzzzzzzzzzzz",
        height=120
    )

    st.markdown('<div class="section-head" style="margin-top:1rem;">📂 Content Type</div>', unsafe_allow_html=True)
    content_type = st.radio(
        "Content type",
        options=["🎬 Long Videos", "⚡ Short Videos (Shorts)", "📢 Community Posts"],
        horizontal=True,
        label_visibility="collapsed"
    )

with col_right:
    st.markdown('<div class="section-head">📅 Date Range</div>', unsafe_allow_html=True)
    today = date.today()
    default_start = today - timedelta(days=90)

    date_start = st.date_input("From", value=default_start, max_value=today)
    date_end   = st.date_input("To",   value=today,          max_value=today)

    if date_start > date_end:
        st.error("Start date cannot be after end date.")

st.markdown("---")

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(n):
    try:
        n = int(n)
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.1f}K"
        return str(n)
    except:
        return "—"

def duration_to_seconds(duration):
    m = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not m: return 0
    return (int(m.group(1) or 0) * 3600 +
            int(m.group(2) or 0) * 60  +
            int(m.group(3) or 0))

def convert_duration(duration):
    s = duration_to_seconds(duration)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

def in_date_range(pub_str, start, end):
    try:
        pub = pd.to_datetime(pub_str).date()
        return start <= pub <= end
    except:
        return False

def get_channel_info(yt, cid):
    resp = yt.channels().list(
        part='snippet,contentDetails,statistics', id=cid
    ).execute()
    if not resp.get('items'):
        return None
    item = resp['items'][0]
    return {
        'name':       item['snippet']['title'],
        'playlist':   item['contentDetails']['relatedPlaylists']['uploads'],
        'subscribers': item['statistics'].get('subscriberCount', 0),
        'total_views': item['statistics'].get('viewCount', 0),
        'total_videos': item['statistics'].get('videoCount', 0),
        'channel_id':  item['id'],
    }

def get_all_video_ids(yt, playlist_id):
    ids = []
    req = yt.playlistItems().list(
        part='contentDetails', playlistId=playlist_id, maxResults=50
    )
    while req:
        resp = req.execute()
        for item in resp['items']:
            ids.append(item['contentDetails']['videoId'])
        req = yt.playlistItems().list_next(req, resp)
    return ids

def get_video_details(yt, video_ids, filter_type, channel_name, channel_id, start, end):
    rows = []
    for i in range(0, len(video_ids), 50):
        resp = yt.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids[i:i+50])
        ).execute()
        for v in resp['items']:
            pub = v['snippet']['publishedAt']
            if not in_date_range(pub, start, end):
                continue
            raw_dur = v['contentDetails']['duration']
            secs = duration_to_seconds(raw_dur)
            if filter_type == 'short' and secs > 60:
                continue
            if filter_type == 'long'  and secs <= 60:
                continue
            vid_id = v['id']
            link = (
                f"https://www.youtube.com/shorts/{vid_id}"
                if filter_type == 'short'
                else f"https://www.youtube.com/watch?v={vid_id}"
            )
            rows.append({
                'Date':         pd.to_datetime(pub).date(),
                'Channel Name': channel_name,
                'Title':        v['snippet']['title'],
                'Link':         link,
                'Views':        v['statistics'].get('viewCount',  0),
                'Likes':        v['statistics'].get('likeCount',  0),
                'Comments':     v['statistics'].get('commentCount', 0),
            })
    return rows

def get_community_posts(yt, channel_id, channel_name, start, end):
    posts = []
    try:
        req = yt.activities().list(
            part='snippet,contentDetails', channelId=channel_id, maxResults=50
        )
        while req:
            resp = req.execute()
            for item in resp.get('items', []):
                if item['snippet']['type'] != 'bulletin':
                    continue
                pub = item['snippet']['publishedAt']
                if not in_date_range(pub, start, end):
                    continue
                desc = item['snippet'].get('description', '')
                posts.append({
                    'Date':         pd.to_datetime(pub).date(),
                    'Channel Name': channel_name,
                    'Title':        desc[:120] + ('…' if len(desc) > 120 else ''),
                    'Link':         f"https://www.youtube.com/channel/{channel_id}/community",
                    'Views':        '—',
                    'Likes':        '—',
                    'Comments':     '—',
                })
            npt = resp.get('nextPageToken')
            if npt:
                req = yt.activities().list(
                    part='snippet,contentDetails', channelId=channel_id,
                    maxResults=50, pageToken=npt
                )
            else:
                break
    except Exception as e:
        st.warning(f"Community posts error: {e}")
    return posts

def convert_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Analytics')
    return output.getvalue()

# ── Fetch Button ──────────────────────────────────────────────────────────────
_, btn_col, _ = st.columns([1, 2, 1])
with btn_col:
    fetch = st.button("⚡ Fetch Analytics", type="primary")

if fetch:
    channel_ids = [c.strip() for c in channel_ids_raw.strip().splitlines() if c.strip()]

    if not api_key:
        st.error("🔑 API Key missing — add it in the sidebar or Streamlit Secrets.")
    elif not channel_ids:
        st.error("📺 Please enter at least one Channel ID.")
    elif date_start > date_end:
        st.error("📅 Start date cannot be after end date.")
    else:
        yt = build("youtube", "v3", developerKey=api_key)
        all_rows = []
        channel_names = []

        progress = st.progress(0, text="Fetching channels...")

        for idx, cid in enumerate(channel_ids):
            progress.progress((idx) / len(channel_ids), text=f"Fetching channel {idx+1} of {len(channel_ids)}...")

            info = get_channel_info(yt, cid)
            if not info:
                st.warning(f"Channel not found: `{cid}` — skipping.")
                continue

            channel_names.append(info['name'])
            filter_key = (
                'short' if content_type == "⚡ Short Videos (Shorts)"
                else 'long' if content_type == "🎬 Long Videos"
                else 'community'
            )

            if filter_key == 'community':
                rows = get_community_posts(yt, info['channel_id'], info['name'], date_start, date_end)
            else:
                vids = get_all_video_ids(yt, info['playlist'])
                rows = get_video_details(yt, vids, filter_key, info['name'], info['channel_id'], date_start, date_end)

            all_rows.extend(rows)

        progress.progress(1.0, text="Done!")
        progress.empty()

        if not all_rows:
            st.warning("No data found for this date range. Please check your Channel IDs and date selection.")
        else:
            df = pd.DataFrame(all_rows)

            # Numeric conversion
            for col in ['Views', 'Likes', 'Comments']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('Int64')

            df = df.sort_values('Date', ascending=False).reset_index(drop=True)

            # ── Summary Metrics ────────────────────────────────────────────
            total_videos  = len(df)
            total_views   = df['Views'].sum()   if 'Views'   in df.columns else 0
            total_likes   = df['Likes'].sum()   if 'Likes'   in df.columns else 0
            total_comments= df['Comments'].sum() if 'Comments' in df.columns else 0

            st.markdown(f"""
            <div style="margin:1.5rem 0 0.5rem;">
              <div class="section-head">📊 Summary — {len(channel_names)} channel{'s' if len(channel_names)>1 else ''} · {date_start} → {date_end}</div>
              <div style="margin-bottom:10px;">
                {''.join(f'<span class="ch-chip">📺 {n}</span>' for n in channel_names)}
              </div>
              <div class="metric-row">
                <div class="metric-card amber">
                  <div class="m-label">Videos Found</div>
                  <div class="m-value">{total_videos:,}</div>
                  <div class="m-sub">{content_type.split()[1]} content</div>
                </div>
                <div class="metric-card blue">
                  <div class="m-label">Total Views</div>
                  <div class="m-value">{fmt(total_views)}</div>
                  <div class="m-sub">combined</div>
                </div>
                <div class="metric-card red">
                  <div class="m-label">Total Likes</div>
                  <div class="m-value">{fmt(total_likes)}</div>
                  <div class="m-sub">combined</div>
                </div>
                <div class="metric-card green">
                  <div class="m-label">Comments</div>
                  <div class="m-value">{fmt(total_comments)}</div>
                  <div class="m-sub">combined</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Data Table ─────────────────────────────────────────────────
            st.markdown('<div class="section-head">📋 Video Data</div>', unsafe_allow_html=True)

            display_df = df.copy()
            # Make Link clickable in display
            display_df['Link'] = display_df['Link'].apply(lambda x: f'<a href="{x}" target="_blank">▶ Watch</a>')

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Link": st.column_config.LinkColumn("Link", display_text="▶ Watch"),
                    "Views":    st.column_config.NumberColumn("Views",    format="%d"),
                    "Likes":    st.column_config.NumberColumn("Likes",    format="%d"),
                    "Comments": st.column_config.NumberColumn("Comments", format="%d"),
                    "Date":     st.column_config.DateColumn("Date"),
                }
            )

            # ── Downloads ──────────────────────────────────────────────────
            st.markdown('<div class="section-head" style="margin-top:1.5rem;">📥 Export</div>', unsafe_allow_html=True)
            suffix = (
                "shorts"     if content_type == "⚡ Short Videos (Shorts)"
                else "long"  if content_type == "🎬 Long Videos"
                else "community"
            )
            date_tag = f"{date_start}_to_{date_end}"
            channels_tag = "_".join([n.replace(" ", "-") for n in channel_names])[:40]
            fname = f"VidIQNova_{channels_tag}_{suffix}_{date_tag}"

            dl1, dl2 = st.columns(2)
            with dl1:
                st.download_button(
                    "⬇️ Download Excel",
                    data=convert_to_excel(df),
                    file_name=f"{fname}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with dl2:
                st.download_button(
                    "⬇️ Download CSV",
                    data=df.to_csv(index=False),
                    file_name=f"{fname}.csv",
                    mime="text/csv"
                )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-top:3rem;padding:1rem 0;border-top:1px solid rgba(255,255,255,0.08);">
  <span style="font-size:0.78rem;color:rgba(255,255,255,0.2);letter-spacing:0.08em;">
    VIDIQ NOVA · YOUTUBE ANALYTICS · Built with Streamlit
  </span>
</div>
""", unsafe_allow_html=True)
