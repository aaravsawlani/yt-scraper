from flask import Flask, render_template, request, jsonify, Response
import os
import yt
import json
from datetime import datetime
from queue import Queue
from threading import Thread

app = Flask(__name__)
result_queue = Queue()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        while True:
            result = result_queue.get()
            yield f"data: {json.dumps(result)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

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
        
        if not videos:
            return jsonify({'error': 'No videos found'}), 404

        results = []
        for video in videos:
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
                    result_queue.put({
                        'type': 'video_complete',
                        **result
                    })

        if results:
            # Generate final summary
            final_summary = yt.create_final_summary(results)
            
            return jsonify({
                'success': True,
                'message': 'Analysis complete',
                'results': results,
                'final_summary': final_summary
            })
        else:
            return jsonify({'error': 'No results generated'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 