async function checkJobStatus(jobId) {
    const eventSource = new EventSource(`/api/status/${jobId}`);
    
    eventSource.onmessage = function(event) {
        const status = JSON.parse(event.data);
        updateStatus(status);
        
        if (status.status === 'completed' || status.status === 'error') {
            eventSource.close();
            if (status.status === 'completed') {
                showDownloadButton(jobId);
            }
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        updateStatus({
            status: 'error',
            error: 'ステータスの取得中にエラーが発生しました'
        });
    };
}

function updateStatus(status) {
    const statusElement = document.getElementById('status');
    const progressElement = document.getElementById('progress');
    
    if (status.error) {
        statusElement.textContent = `エラー: ${status.error}`;
        statusElement.className = 'text-red-500';
    } else {
        statusElement.textContent = `ステータス: ${status.status}`;
        statusElement.className = 'text-blue-500';
    }
    
    if (progressElement) {
        progressElement.style.width = `${status.progress}%`;
        progressElement.textContent = `${Math.round(status.progress)}%`;
    }
}

function showDownloadButton(jobId) {
    const downloadContainer = document.getElementById('download-container');
    downloadContainer.innerHTML = `
        <a href="/api/download/${jobId}" 
           class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
            変換されたファイルをダウンロード
        </a>
    `;
    downloadContainer.classList.remove('hidden');
} 