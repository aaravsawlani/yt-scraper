from flask import Flask, render_template, request, jsonify, Response
import os
import yt
import json
from datetime import datetime
from queue import Queue
import time
import db

app = Flask(__name__)
result_queue = Queue()

# Initialize the database
db.init_db()

def send_to_all_connections(data):
    """Helper function to send updates to all active connections"""
    print(f"🔄 Queueing update for video: {data.get('title', 'Unknown')}")
    result_queue.put(data)
    time.sleep(2)  # Wait 2 seconds before processing next video

@app.route('/')
def index():
    # Get search history for the sidebar
    history = db.get_search_history()
    return render_template('index.html', history=history)

@app.route('/stream')
def stream():
    def generate():
        while True:
            try:
                result = result_queue.get(timeout=1)
                message = f"data: {json.dumps(result)}\n\n"
                print(f"📤 Sending message for video: {result.get('title', 'Unknown')}")
                yield message
            except:
                yield ":\n\n"  # Keep-alive
                continue
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })

@app.route('/history/<int:search_id>')
def get_history(search_id):
    """Get results for a specific search from history"""
    results = db.get_search_results(search_id)
    if results:
        return jsonify(results)
    return jsonify({'error': 'Search not found'}), 404

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        keyword = request.form.get('keyword')
        max_results = int(request.form.get('max_results', 10))
        order = request.form.get('order', 'relevance')
        max_age = int(request.form.get('max_age', 500))
        
        if not keyword:
            return jsonify({'error': 'Please provide a keyword'}), 400

        # Search for videos
        videos = yt.search_youtube(keyword, max_results, order, max_age)
        print(f"📊 Found {len(videos)} videos to analyze")
        
        if not videos:
            return jsonify({'error': 'No videos found'}), 404

        results = []
        for i, video in enumerate(videos, 1):
            print(f"\n🎥 Processing video {i}/{len(videos)}: {video['title']}")
            # Get transcript and analyze
            transcript = yt.fetch_transcript(video['video_id'])
            if transcript:
                summary = yt.analyze_transcript(transcript)
                if summary:
                    result = {
                        'title': video['title'],
                        'video_id': video['video_id'],
                        'summary': summary,
                        'url': f"https://www.youtube.com/watch?v={video['video_id']}"
                    }
                    results.append(result)
                    # Send live update
                    send_to_all_connections({
                        'type': 'video_complete',
                        **result
                    })
                    print(f"✅ Successfully processed video {i}")
                else:
                    print(f"❌ Failed to analyze video {i} - no summary generated")
            else:
                print(f"❌ Failed to process video {i} - no transcript available")

        print(f"\n📊 Successfully processed {len(results)}/{len(videos)} videos")
        
        if results:
            # Generate final summary
            print("🤖 Generating final summary...")
            final_summary = yt.create_final_summary(results)
            if final_summary:
                print("✅ Final summary generated")
            else:
                print("❌ Failed to generate final summary")
            
            # Save to database
            db.save_search(keyword, max_results, order, max_age, final_summary, results)
            
            return jsonify({
                'success': True,
                'message': 'Analysis complete',
                'results': results,
                'final_summary': final_summary
            })
        else:
            return jsonify({'error': 'No results generated'}), 404

    except Exception as e:
        print(f"❌ Error in analyze route: {type(e).__name__}")
        print(f"  Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 