import os
from dotenv import load_dotenv
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from fpdf import FPDF
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

load_dotenv("secrets.env")
# 🔑 API KEYS (Replace with your actual API keys)
YOUTUBE_API_KEY = os.getenv("YT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Get the Downloads folder path
downloads_path = str(Path.home() / "Downloads")

# 🔍 Step 1: Search YouTube for videos based on a keyword
def search_youtube(keyword, max_results=10):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",  # Sort by relevance instead of views
        "publishedAfter": (datetime.utcnow() - timedelta(days=500)).strftime("%Y-%m-%dT%H:%M:%SZ"),  # Only videos from the last week
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
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        print(f"❌ No transcript for video {video_id}: {e}")
        return None

def analyze_transcript(transcript):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"""
                    You are an AI assistant designed to extract key insights from YouTube videos and transform them into actionable intelligence. 
                    Given the transcript of a YouTube video, perform the following:
                    
                    1 **Concise Summary**: Provide a brief but detailed summary of the videos key points. 
                    
                    2 **Implications for Business & AI Capabilities**: Analyze how the information in this video affects businesses, industries, or the development of AI. Consider:
                        - Does this indicate a shift in AI capabilities?
                        - Are there new opportunities or risks for businesses?
                        - What industries or sectors are most affected by these insights?
                    
                    3 **Recommended Actions**: If warranted, suggest specific, practical steps that businesses, AI practitioners, or decision-makers should take based on the video's insights. Consider:
                        - **Adoption strategies** (Should businesses integrate this technology or trend? Why?)
                        - **Investment opportunities** (Is this something worth exploring further?)
                        - **Risk mitigation** (Are there any concerns to be aware of?)
                        - **Personal or professional development** (Should someone in AI or business learn new skills, tools, or strategies?)
                    
                    Format the response clearly with bold headings for each section. Be direct, actionable, and insightful.

                    The entire summary per transcript should be no longer than 200 words, at maximum.
                    
                    Here is the transcript:
                    {transcript}
                """}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return None

# 📝 Step 4: Save results to a PDF
def save_to_pdf(keyword, results, buffer=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    # Ensure we remove emojis/special characters before writing
    def remove_unsupported_chars(text):
        return text.encode("ascii", "ignore").decode("ascii")

    pdf.cell(200, 10, remove_unsupported_chars(f"YouTube Summaries for: {keyword}"), ln=True, align="C")
    pdf.set_font("Arial", size=12)
    pdf.ln(10)  # Line break

    for result in results:
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, remove_unsupported_chars(f"🎥 {result['title']}"))
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 6, remove_unsupported_chars(f"🔗 Link: https://www.youtube.com/watch?v={result['video_id']}"))
        pdf.ln(2)
        pdf.multi_cell(0, 6, remove_unsupported_chars(f"📄 Summary: {result['summary']}"))
        pdf.ln(8)  # Add some space between summaries

    if buffer:
        pdf.output(buffer, 'F')
        buffer.seek(0)
    else:
        # Fallback to file system for local development
        today_date = datetime.now().strftime("%Y-%m-%d")
        filename = f"YT_{keyword}_{today_date}.pdf"
        file_path = os.path.join(os.getcwd(), filename)
        pdf.output(file_path, "F")

def create_action_plan(keyword, results, buffer=None):
    if not results:
        print("\n❌ No results to create an action plan from.")
        return
    
    # Extract all summaries
    all_summaries = [result['summary'] for result in results]
    combined_summaries = "\n\n".join(all_summaries)
    
    try:
        print("\n🔄 Generating comprehensive action plan...")
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"""
                    Based on the following summaries of YouTube videos about "{keyword}", create a comprehensive action plan.
                    
                    Your response should have two main sections:
                    
                    1. **KEY INSIGHTS SUMMARY**:
                       Provide a concise, consolidated summary of the most important points from all videos.
                       Highlight common themes, contradictions, and unique perspectives.
                       Focus on actionable information and significant trends.
                    
                    2. **ACTION PLAN**:
                       Create a step-by-step action plan based on the insights.
                       Include specific, practical steps that someone should take to implement the knowledge.
                       Prioritize actions by importance and sequence them logically.
                       When applicable, include timeframes or milestones.
                       
                    Format your response with clear headings and bullet points for readability.
                    Be direct, practical, and focused on implementation.
                    
                    Here are the summaries:
                    {combined_summaries}
                """}
            ]
        )
        
        action_plan = completion.choices[0].message.content
        
        # Create PDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        
        # Ensure we remove emojis/special characters before writing
        def remove_unsupported_chars(text):
            return text.encode("ascii", "ignore").decode("ascii")
        
        # Add title
        pdf.cell(200, 10, remove_unsupported_chars(f"ACTION PLAN FOR: {keyword.upper()}"), ln=True, align="C")
        pdf.set_font("Arial", "I", 12)
        pdf.cell(200, 10, remove_unsupported_chars(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}"), ln=True, align="C")
        pdf.ln(10)
        
        # Add content
        pdf.set_font("Arial", size=12)
        
        # Split the action plan by lines to handle formatting
        for line in action_plan.split('\n'):
            # Check if line is a heading (starts with # or contains **)
            if line.strip().startswith('#') or '**' in line:
                pdf.set_font("Arial", "B", 14)
                pdf.multi_cell(0, 8, remove_unsupported_chars(line))
                pdf.set_font("Arial", size=12)
            else:
                pdf.multi_cell(0, 6, remove_unsupported_chars(line))
        
        if buffer:
            pdf.output(buffer, 'F')
            buffer.seek(0)
        else:
            # Fallback to file system for local development
            today_date = datetime.now().strftime("%Y-%m-%d")
            filename = f"ActionPlan_{keyword}_{today_date}.pdf"
            file_path = os.path.join(os.getcwd(), filename)
            pdf.output(file_path, "F")
        
        return action_plan
    
    except Exception as e:
        print(f"❌ Error creating action plan: {e}")
        return None

# 🔄 Step 5: Run the full workflow
def main(keyword, max_results=50):
    print(f"\n🔎 Searching YouTube for: {keyword}")
    videos = search_youtube(keyword, max_results)
    results = []

    for video in videos:
        print(f"\n🎥 Processing: {video['title']} (https://www.youtube.com/watch?v={video['video_id']})")
        
        # Fetch transcript
        transcript = fetch_transcript(video["video_id"])
        if not transcript:
            print(f"⏩ Skipping {video['title']} (No transcript available)")
            continue

        # Analyze transcript
        summary = analyze_transcript(transcript)
        if summary:
            results.append({
                "title": video["title"],
                "video_id": video["video_id"],
                "summary": summary
            })
        else:
            print(f"⏩ Skipping {video['title']} (OpenAI error)")

    if results:
        save_to_pdf(keyword, results)
        # Create and save action plan
        create_action_plan(keyword, results)
    else:
        print("\n❌ No results to save.")

# Run program
if __name__ == "__main__":
    search_term = input("\n🔍 Enter search keyword: ")
    num_results = int(input("📌 How many videos? (Max 10 recommended): "))
    main(search_term, num_results)
