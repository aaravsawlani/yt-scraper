from flask import Flask, render_template, request, jsonify, send_file
import os
from pathlib import Path
import yt
from datetime import datetime

app = Flask(__name__)

# Get the Downloads folder path
downloads_path = str(Path.home() / "Downloads")

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
                        'summary': summary
                    })

        # Generate PDFs
        if results:
            yt.save_to_pdf(keyword, results)
            yt.create_action_plan(keyword, results)
            
            # Get PDF file paths
            today_date = datetime.now().strftime("%Y-%m-%d")
            summary_pdf = f"YT_{keyword}_{today_date}.pdf"
            action_plan_pdf = f"ActionPlan_{keyword}_{today_date}.pdf"
            
            return jsonify({
                'success': True,
                'message': 'Analysis complete',
                'summary_pdf': summary_pdf,
                'action_plan_pdf': action_plan_pdf,
                'results': results
            })
        else:
            return jsonify({'error': 'No results generated'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    try:
        file_path = os.path.join(downloads_path, filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True) 