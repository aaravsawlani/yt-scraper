import os
from dotenv import load_dotenv
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from datetime import datetime, timedelta

load_dotenv("secrets.env")
# 🔑 API KEYS (Replace with your actual API keys)
YOUTUBE_API_KEY = os.getenv("YT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(
    api_key=OPENAI_API_KEY,
    default_headers={"Content-Type": "application/json"},
    timeout=60.0
)

# 🔍 Step 1: Search YouTube for videos based on a keyword
def search_youtube(keyword, max_results=10, order='relevance', max_age=500):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": max_results,
        "order": order,
        "publishedAfter": (datetime.utcnow() - timedelta(days=max_age)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        videos = response.json().get("items", [])
        return [{"title": v["snippet"]["title"], "video_id": v["id"]["videoId"]} for v in videos]
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []
    
# 📜 Step 2: Fetch transcript for a given video ID
def fetch_transcript(video_id):
    print(f"🔍 Attempting to fetch transcript for video {video_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        print(f"✅ Successfully fetched transcript for {video_id}")
        return text
    except Exception as e:
        error_type = type(e).__name__
        print(f"❌ Error fetching transcript for {video_id}")
        print(f"  Error type: {error_type}")
        print(f"  Error message: {str(e)}")
        print(f"  Video URL: https://www.youtube.com/watch?v={video_id}")
        return None

def analyze_transcript(transcript):
    try:
        print(f"🤖 Attempting to analyze transcript...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"""
                    Analyze this YouTube video transcript and provide:
                    1. A single sentence summary (max 30 words)
                    2. Key insights and implications for business/AI
                    3. Recommended actions
                    
                    Format as:
                    QUICK SUMMARY: [one sentence]
                    INSIGHTS: [bullet points]
                    ACTIONS: [bullet points]
                    
                    Transcript:
                    {transcript}
                """}
            ]
        )
        print(f"✅ Successfully analyzed transcript")
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error analyzing transcript: {type(e).__name__}")
        print(f"  Error details: {str(e)}")
        return None

def create_final_summary(results):
    if not results:
        return "No results to summarize."
    
    try:
        # Extract all summaries
        all_summaries = [result['summary'] for result in results]
        combined_summaries = "\n\n".join(all_summaries)
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"""
                    Based on these video summaries, create a comprehensive overview with:
                    
                    1. MAIN THEMES: Key recurring topics and insights
                    2. KEY TAKEAWAYS: Most important points across all videos
                    3. RECOMMENDED ACTIONS: Prioritized list of steps to take
                    
                    Format with clear headings and bullet points.
                    Be concise and actionable.
                    
                    Summaries:
                    {combined_summaries}
                """}
            ]
        )
        
        return completion.choices[0].message.content
    
    except Exception as e:
        print(f"❌ Error creating final summary: {e}")
        return None
