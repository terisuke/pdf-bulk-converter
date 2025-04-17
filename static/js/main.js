document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const progressDiv = document.getElementById('progress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultDiv = document.getElementById('result');
    const downloadLink = document.getElementById('downloadLink');

    let currentJobId = null;
    let eventSource = null;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const file = document.getElementById('pdfFile').files[0];
        if (!file) {
            alert('ファイルを選択してください');
            return;
        }

        const dpi = document.getElementById('dpi').value;
        const format = document.getElementById('format').value;

        try {
            // アップロードURLを取得
            const response = await fetch('/api/upload-url', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: file.name,
                    content_type: file.type,
                    dpi: parseInt(dpi),
                    format: format
                })
            });

            if (!response.ok) {
                throw new Error('アップロードURLの取得に失敗しました');
            }

            const { upload_url, job_id } = await response.json();
            currentJobId = job_id;

            // ファイルをアップロード
            const formData = new FormData();
            formData.append('file', file);

            await fetch(upload_url, {
                method: 'PUT',
                body: formData
            });

            // 進捗表示を開始
            progressDiv.classList.remove('hidden');
            resultDiv.classList.add('hidden');
            
            // Server-Sent Eventsで進捗を監視
            if (eventSource) {
                eventSource.close();
            }
            
            eventSource = new EventSource(`/api/status/${job_id}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgress(data);
            };
            eventSource.onerror = () => {
                eventSource.close();
            };

        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました: ' + error.message);
        }
    });

    function updateProgress(data) {
        const { status, progress, error } = data;
        
        progressBar.style.width = `${progress}%`;
        progressText.textContent = `変換中... ${progress}%`;

        if (status === 'completed') {
            eventSource.close();
            showResult();
        } else if (status === 'error') {
            eventSource.close();
            alert('エラーが発生しました: ' + error);
        }
    }

    async function showResult() {
        try {
            const response = await fetch(`/api/download/${currentJobId}`);
            if (!response.ok) {
                throw new Error('ダウンロードURLの取得に失敗しました');
            }

            const { download_url } = await response.json();
            downloadLink.href = download_url;
            
            progressDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました: ' + error.message);
        }
    }
}); 