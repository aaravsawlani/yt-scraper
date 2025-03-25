document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const resultsDiv = document.getElementById('results');
    const videoResultsDiv = document.getElementById('videoResults');
    const downloadSummaryBtn = document.getElementById('downloadSummary');
    const downloadActionBtn = document.getElementById('downloadAction');

    let currentSummaryPdf = '';
    let currentActionPdf = '';

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Reset UI
        errorDiv.classList.add('d-none');
        resultsDiv.classList.add('d-none');
        loadingDiv.classList.remove('d-none');
        videoResultsDiv.innerHTML = '';

        // Get form data
        const formData = new FormData(searchForm);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'An error occurred');
            }

            // Store PDF filenames
            currentSummaryPdf = data.summary_pdf;
            currentActionPdf = data.action_plan_pdf;

            // Display results
            displayResults(data.results);
            
            // Show results section
            resultsDiv.classList.remove('d-none');

            if (data.videos && Array.isArray(data.videos)) {
                // Only display videos if this is from history
                // For live updates, we use the SSE handler
                if (data.is_history) {
                    data.videos.forEach(video => {
                        const videoCard = document.createElement('div');
                        videoCard.className = 'card video-card';
                        
                        videoCard.innerHTML = `
                            <div class="card-header">
                                <a href="https://www.youtube.com/watch?v=${video.video_id}" 
                                   target="_blank" 
                                   class="video-title">
                                    ${escapeHtml(video.title)}
                                </a>
                            </div>
                            <div class="card-body">
                                <div class="summary-text">${escapeHtml(video.summary)}</div>
                            </div>
                        `;
                        
                        videoResultsDiv.appendChild(videoCard);
                    });
                }
            }

            // Clear previous results only for new searches and if it's not from SSE
            if (!data.is_history && !data.type) {
                liveResultsContent.innerHTML = '';
                processedCount = 0;
                document.getElementById('video-counter').style.display = 'none';
            }
        } catch (error) {
            errorDiv.textContent = error.message;
            errorDiv.classList.remove('d-none');
        } finally {
            loadingDiv.classList.add('d-none');
        }
    });

    function displayResults(results) {
        results.forEach(result => {
            const videoCard = document.createElement('div');
            videoCard.className = 'card video-card';
            
            videoCard.innerHTML = `
                <div class="card-header">
                    <a href="https://www.youtube.com/watch?v=${result.video_id}" 
                       target="_blank" 
                       class="video-title">
                        ${escapeHtml(result.title)}
                    </a>
                </div>
                <div class="card-body">
                    <div class="summary-text">${escapeHtml(result.summary)}</div>
                </div>
            `;
            
            videoResultsDiv.appendChild(videoCard);
        });
    }

    // Handle PDF downloads
    downloadSummaryBtn.addEventListener('click', () => {
        if (currentSummaryPdf) {
            window.location.href = `/download/${currentSummaryPdf}`;
        }
    });

    downloadActionBtn.addEventListener('click', () => {
        if (currentActionPdf) {
            window.location.href = `/download/${currentActionPdf}`;
        }
    });

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}); 