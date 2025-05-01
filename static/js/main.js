document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const progressDiv = document.getElementById('progress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultDiv = document.getElementById('result');
    const downloadLink = document.getElementById('downloadLink');

    let currentSessionId = null;
    let currentJobId = null;
    let eventSource = null;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const files = document.getElementById('pdfFile').files;
        if (!files || files.length === 0) {
            alert('ファイルを選択してください');
            return;
        }

        const dpi = document.getElementById('dpi').value;

        try {
            // 進捗表示を開始
            progressDiv.classList.remove('hidden');
            resultDiv.classList.add('hidden');

            // セッションIDを取得
            const res_session = await fetch('/api/session', {
                method: 'GET'
            });
            if (!res_session.ok) {
                throw new Error('セッションIDの取得に失敗しました');
            }
            const sessionData = await res_session.json();
            currentSessionId = sessionData.session_id;

            // すべてのファイルをアップロード
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                progressText.textContent = `ファイル ${i + 1}/${files.length} をアップロード中...`;

                const res_upload_job = await fetch('/api/upload-url/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        filename: file.name,
                        content_type: file.type,
                        dpi: parseInt(dpi),
                        format: "jpeg"
                    })
                });
                if (!res_upload_job.ok) {
                    throw new Error('アップロードURLの取得に失敗しました');
                }
                const urlData = await res_upload_job.json();
                uploadUrl = urlData.upload_url;
                if (i == 0) {currentJobId = urlData.job_id}

                // ファイルをアップロード
                const formData = new FormData();
                formData.append('file', file);
                formData.append('dpi', dpi);
                formData.append('format', 'jpeg');

                const fullUrl = uploadUrl.startsWith('/') ? 
                    window.location.origin + uploadUrl : uploadUrl;

                const uploadResponse = await fetch(fullUrl, {
                    method: 'POST',
                    body: formData
                });

                if (!uploadResponse.ok) {
                    throw new Error(`アップロードに失敗しました: ${uploadResponse.status}`);
                }
            }

            // アップロード完了後、セッションのステータスを"converting"に更新
            const updateSessionStatus = await fetch(`/api/session-update/${currentSessionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    status: 'converting'
                })
            });
            if (!updateSessionStatus.ok) {
                throw new Error('セッションステータスの更新に失敗しました');
            }

            // Server-Sent Eventsで進捗を監視
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource(`/api/session-status/${currentSessionId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgress(data);
            };
            eventSource.onerror = () => {
                eventSource.close();
            };

            // 変換完了後、ZIPファイルの生成をリクエスト
            const zipResponse = await fetch(`/api/create-zip/${currentSessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!zipResponse.ok) {
                throw new Error('ZIPファイルの生成に失敗しました');
            }

            // ZIPファイル生成の進捗を監視
            if (eventSource) {
                eventSource.close();
            }
            eventSource = new EventSource(`/api/session-status/${currentSessionId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgress(data);
            };
            eventSource.onerror = () => {
                eventSource.close();
            };

            
            // 変換が完了するまで待機
            await new Promise(resolve => {
                const checkStatus = async () => {
                    const statusResponse = await fetch(`/api/job-status/${currentSessionId}`);
                    if (statusResponse.ok) {
                        const statusData = await statusResponse.json();
                        if (statusData.status === 'completed') {
                            resolve();
                        } else if (statusData.status === 'error') {
                            throw new Error(statusData.message || '変換中にエラーが発生しました');
                        } else {
                            setTimeout(checkStatus, 1000);
                        }
                    } else {
                        throw new Error('ステータスの取得に失敗しました');
                    }
                };
                checkStatus();
            });

            // ダウンロードURLを取得
            const downloadResponse = await fetch(`/api/download/${currentSessionId}`);
            
            if (downloadResponse.ok) {
                const downloadData = await downloadResponse.json();
                downloadLink.href = downloadData.download_url;
                progressDiv.classList.add('hidden');
                resultDiv.classList.remove('hidden');
            } else {
                progressText.textContent = '変換は完了しましたが、ダウンロードURLの取得に失敗しました。';
            }
        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました: ' + error.message);
            progressDiv.classList.add('hidden');
        }
    });

    function updateProgress(data) {
        const { status, progress, message } = data;
        
        progressBar.style.width = `${progress}%`;
        progressText.textContent = message || `変換中... ${progress}%`;

        if (status === 'completed') {
            eventSource.close();
            
            // ダウンロードURLを取得
            fetch(`/api/download/${currentJobId}`)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('ダウンロードURLの取得に失敗しました');
                    }
                })
                .then(downloadData => {
                    downloadLink.href = downloadData.download_url;
                    progressDiv.classList.add('hidden');
                    resultDiv.classList.remove('hidden');
                })
                .catch(error => {
                    console.error('Error:', error);
                    progressText.textContent = '変換は完了しましたが、ダウンロードURLの取得に失敗しました。';
                });
        } else if (status === 'error') {
            eventSource.close();
            alert('エラーが発生しました: ' + message);
        }
    }
});                    