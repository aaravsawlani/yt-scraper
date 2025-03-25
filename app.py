from flask import Flask, render_template, request, jsonify
import os
import yt
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        keyword = request.form.get('keyword')
        max_results = int(request.form.get('max_results', 10))
        
        if not keyword:
            return jsonify({'error': 'Please provide a keyword'}), 400

        # Search for videos
        videos = yt.search_youtube(keyword, max_results)
        
        if not videos:
            return jsonify({'error': 'No videos found'}), 404

        results = []
        for video in videos:
            # Get transcript and analyze
            transcript = yt.fetch_transcript(video['video_id'])
            if transcript:
                summary = yt.analyze_transcript(transcript)
                if summary:
                    results.append({
                        'title': video['title'],
                        'video_id': video['video_id'],
                        'summary': summary,
                        'url': f"https://www.youtube.com/watch?v={video['video_id']}"
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