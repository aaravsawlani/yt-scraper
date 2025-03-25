from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, make_response
import os
from pathlib import Path
import yt
from datetime import datetime
from io import BytesIO

app = Flask(__name__)

# In-memory storage for PDFs
pdf_storage = {}

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
            # Get PDF file names
            today_date = datetime.now().strftime("%Y-%m-%d")
            summary_pdf = f"YT_{keyword}_{today_date}.pdf"
            action_plan_pdf = f"ActionPlan_{keyword}_{today_date}.pdf"

            # Generate and store PDFs in memory
            summary_buffer = BytesIO()
            action_plan_buffer = BytesIO()
            
            yt.save_to_pdf(keyword, results, summary_buffer)
            yt.create_action_plan(keyword, results, action_plan_buffer)
            
            # Store PDF buffers in memory
            pdf_storage[summary_pdf] = summary_buffer.getvalue()
            pdf_storage[action_plan_pdf] = action_plan_buffer.getvalue()
            
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
        if filename in pdf_storage:
            pdf_data = pdf_storage[filename]
            response = make_response(pdf_data)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add static file handling for Vercel
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(debug=True) 