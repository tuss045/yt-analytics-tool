import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from io import BytesIO

st.set_page_config(
    page_title="YouTube Analytics Tool",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 YouTube Channel Analytics")
st.caption("Channel ID se video data download karo!")
st.markdown("---")

# API Key
api_key = st.secrets.get("YOUTUBE_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input(
        "YouTube API Key",
        type="password",
        placeholder="AIzaSy..."
    )

# Channel ID input
channel_id = st.text_input(
    "Channel ID daalo",
    placeholder="UCctEsQirgs3hCmq"
)

# ── Content Type Filter ──────────────────────────────────────────────────────
st.markdown("### 📂 Content Type Select Karo")
content_type = st.radio(
    label="Kaunsa data chahiye?",
    options=["🎬 Long Videos", "⚡ Short Videos (Shorts)", "📢 Community Posts"],
    horizontal=True
)
st.markdown("---")

# ── Helper: duration string → total seconds ──────────────────────────────────
def duration_to_seconds(duration: str) -> int:
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    h = int(match.group(1)) if match.group(1) else 0
    m = int(match.group(2)) if match.group(2) else 0
    s = int(match.group(3)) if match.group(3) else 0
    return h * 3600 + m * 60 + s

def convert_duration(duration: str) -> str:
    total = duration_to_seconds(duration)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ── YouTube API helpers ───────────────────────────────────────────────────────
def get_channel_info(youtube, channel_id):
    resp = youtube.channels().list(
        part='snippet,contentDetails,statistics',
        id=channel_id
    ).execute()
    if not resp['items']:
        return None
    item = resp['items'][0]
    return {
        'name':         item['snippet']['title'],
        'playlist':     item['contentDetails']['relatedPlaylists']['uploads'],
        'subscribers':  item['statistics']['subscriberCount'],
        'total_views':  item['statistics']['viewCount'],
        'total_videos': item['statistics']['videoCount'],
        'channel_id':   item['id'],
    }

def get_all_video_ids(youtube, playlist_id):
    ids = []
    request = youtube.playlistItems().list(
        part='contentDetails', playlistId=playlist_id, maxResults=50
    )
    while request:
        resp = request.execute()
        for item in resp['items']:
            ids.append(item['contentDetails']['videoId'])
        request = youtube.playlistItems().list_next(request, resp)
    return ids

def get_video_details(youtube, video_ids, filter_type):
    """
    filter_type: 'short' | 'long'
    Returns list of dicts.
    """
    all_stats = []
    for i in range(0, len(video_ids), 50):
        resp = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids[i:i+50])
        ).execute()
        for video in resp['items']:
            raw_dur = video['contentDetails']['duration']
            secs = duration_to_seconds(raw_dur)

            # Shorts: ≤ 60 seconds; Long: > 60 seconds
            if filter_type == 'short' and secs > 60:
                continue
            if filter_type == 'long' and secs <= 60:
                continue

            all_stats.append({
                'Date':     video['snippet']['publishedAt'],
                'Video_Id': video['id'],
                'Title':    video['snippet']['title'],
                'Views':    video['statistics'].get('viewCount'),
                'Likes':    video['statistics'].get('likeCount'),
                'Comments': video['statistics'].get('commentCount'),
                'Duration': convert_duration(raw_dur),
                'Duration_Sec': secs,
            })
    return all_stats

def get_community_posts(youtube, channel_id):
    """
    Fetch community posts via activities endpoint.
    Note: Only returns posts where the channel has enabled the Community tab.
    """
    posts = []
    try:
        request = youtube.activities().list(
            part='snippet,contentDetails',
            channelId=channel_id,
            maxResults=50
        )
        while request:
            resp = request.execute()
            for item in resp.get('items', []):
                if item['snippet']['type'] != 'bulletin':
                    continue
                desc = item['snippet'].get('description', '')
                posts.append({
                    'Date':        item['snippet']['publishedAt'],
                    'Post_Id':     item['id'],
                    'Description': desc[:300] + ('…' if len(desc) > 300 else ''),
                    'Likes':       None,   # YouTube Data API v3 doesn't expose post likes
                    'Comments':    None,   # Same limitation
                })
            next_page = resp.get('nextPageToken')
            if next_page:
                request = youtube.activities().list(
                    part='snippet,contentDetails',
                    channelId=channel_id,
                    maxResults=50,
                    pageToken=next_page
                )
            else:
                break
    except Exception as e:
        st.warning(f"Community posts fetch mein issue aaya: {e}")
    return posts

def convert_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    return output.getvalue()

# ── Main Fetch Button ─────────────────────────────────────────────────────────
if st.button("🚀 Data Fetch Karo!", type="primary"):
    if not api_key:
        st.error("API Key daalo!")
    elif not channel_id:
        st.error("Channel ID daalo!")
    else:
        youtube = build("youtube", "v3", developerKey=api_key)

        with st.spinner("Channel info fetch ho rahi hai..."):
            channel_info = get_channel_info(youtube, channel_id)

        if not channel_info:
            st.error("Channel nahi mila! Channel ID check karo.")
            st.stop()

        # Channel stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Subscribers",   f"{int(channel_info['subscribers']):,}")
        col2.metric("Total Views",   f"{int(channel_info['total_views']):,}")
        col3.metric("Total Videos",  channel_info['total_videos'])

        channel_name = channel_info['name'].replace(" ", "_")
        df = None

        # ── Community Posts ───────────────────────────────────────────────────
        if content_type == "📢 Community Posts":
            with st.spinner("Community posts fetch ho rahe hain..."):
                posts = get_community_posts(youtube, channel_info['channel_id'])

            if not posts:
                st.warning(
                    "Koi community post nahi mila. "
                    "Possible reasons:\n"
                    "- Channel ka Community tab nahi hai\n"
                    "- YouTube Data API v3 is channel ke posts expose nahi karta\n"
                    "- Channel ID galat hai"
                )
            else:
                df = pd.DataFrame(posts)
                df['Date'] = pd.to_datetime(df['Date']).dt.date
                st.success(f"✅ {len(df)} community posts mile!")
                st.info(
                    "ℹ️ YouTube Data API v3 community posts ke Likes & Comments "
                    "expose nahi karta — woh columns blank rahenge."
                )
                st.dataframe(df, use_container_width=True)

        # ── Short / Long Videos ───────────────────────────────────────────────
        else:
            filter_key = 'short' if content_type == "⚡ Short Videos (Shorts)" else 'long'
            label      = "Shorts" if filter_key == 'short' else "Long Videos"

            with st.spinner(f"Video IDs fetch ho rahe hain..."):
                video_ids = get_all_video_ids(youtube, channel_info['playlist'])

            with st.spinner(f"{label} filter kar rahe hain ({len(video_ids)} total videos)..."):
                details = get_video_details(youtube, video_ids, filter_key)

            if not details:
                st.warning(f"Koi {label} nahi mila is channel mein.")
            else:
                df = pd.DataFrame(details)
                df['Date']     = pd.to_datetime(df['Date']).dt.date
                df['Views']    = pd.to_numeric(df['Views'])
                df['Likes']    = pd.to_numeric(df['Likes'])
                df['Comments'] = pd.to_numeric(df['Comments'])
                # Remove helper column before display/download
                df_display = df.drop(columns=['Duration_Sec'])

                st.success(f"✅ {len(df_display)} {label} mile!")
                st.dataframe(df_display, use_container_width=True)
                df = df_display   # use cleaned df for downloads

        # ── Download Buttons ──────────────────────────────────────────────────
        if df is not None and not df.empty:
            st.subheader("📥 Download karo:")
            col1, col2 = st.columns(2)
            suffix = (
                "shorts"     if content_type == "⚡ Short Videos (Shorts)"
                else "long_videos" if content_type == "🎬 Long Videos"
                else "community_posts"
            )
            with col1:
                st.download_button(
                    label="⬇️ CSV Download",
                    data=df.to_csv(index=False),
                    file_name=f"{channel_name}_{suffix}.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    label="⬇️ Excel Download",
                    data=convert_to_excel(df),
                    file_name=f"{channel_name}_{suffix}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
