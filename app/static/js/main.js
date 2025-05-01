async function checkSessionStatus(sessionId) {
    const eventSource = new EventSource(`/api/sesion-status/${sessionId}`);
    
    eventSource.onmessage = function(event) {
        const status = JSON.parse(event.data);
        updateStatus(status);
        
        if (status.status === 'error') {
            eventSource.close();
        } else if (status.status === 'completed') {
            eventSource.close();
            showDownloadButton(sessionId);
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        updateStatus({
            status: 'error',
            message: 'ステータスの取得中にエラーが発生しました',
            progress: 0
        });
    };
}

async function checkJobStatus(jobId) {
    const eventSource = new EventSource(`/api/job-status/${jobId}`);
    
    eventSource.onmessage = function(event) {
        const status = JSON.parse(event.data);
        updateStatus(status);
        
        if (status.status === 'error') {
            eventSource.close();
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        updateStatus({
            status: 'error',
            message: 'ステータスの取得中にエラーが発生しました',
            progress: 0
        });
    };
}

function updateStatus(status) {
    const statusElement = document.getElementById('status');
    const progressElement = document.getElementById('progress');
    const progressBarElement = document.getElementById('progress-bar');
    
    if (status.status === 'error') {
        statusElement.textContent = `エラー: ${status.message}`;
        statusElement.className = 'text-red-500';
    } else {
        let statusText = status.message || status.status;
        statusElement.textContent = `変換中... ${statusText}`;
        statusElement.className = 'text-blue-500';
    }
    
    const progress = Math.round(status.progress || 0);
    if (progressBarElement) {
        progressBarElement.style.width = `${progress}%`;
        progressBarElement.setAttribute('aria-valuenow', progress);
    }
    if (progressElement) {
        progressElement.textContent = `${progress}%`;
    }
}

function showDownloadButton(sessionId) {
    const downloadContainer = document.getElementById('download-container');
    const statusElement = document.getElementById('status');
    
    statusElement.textContent = '変換が完了しました！';
    statusElement.className = 'text-green-500';
    
    downloadContainer.innerHTML = `
        <a href="/api/download/${sessionId}" 
           class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
            変換されたファイルをダウンロード
        </a>
    `;
    downloadContainer.classList.remove('hidden');
} 