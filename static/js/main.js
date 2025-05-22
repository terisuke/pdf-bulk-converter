document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const progressDiv = document.getElementById('progress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultDiv = document.getElementById('result');
    const downloadLink = document.getElementById('downloadLink');

    let currentSessionId = null;
    let jobIds = []; // Store all job IDs
    let eventSource = null;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const files = document.getElementById('pdfFile').files;
        if (!files || files.length === 0) {
            alert('ファイルを選択してください');
            return;
        }

        const dpi = document.getElementById('dpi').value;
        const startNumber = document.getElementById('startNumber').value;

        try {
            // 進捗表示を開始
            progressDiv.classList.remove('hidden');
            resultDiv.classList.add('hidden');

            // セッションIDを取得
            const res_session = await fetch('/api/session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_number: parseInt(startNumber)
                })
            });
            if (!res_session.ok) {
                throw new Error('セッションIDの取得に失敗しました');
            }
            const sessionData = await res_session.json();
            currentSessionId = sessionData.session_id;

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

            // すべてのファイルをアップロード
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                progressText.textContent = `ファイル ${i + 1}/${files.length} を処理中...`;
                progressBar.style.width = `${10.0 + 80.0 * (i / files.length)}%`;

                const uploadURLEndpoint = new URL('/api/upload-url', window.location.origin);
                const res_upload_job = await fetch(uploadURLEndpoint.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        session_id: currentSessionId,
                        filename: file.name,
                        content_type: file.type,
                        dpi: parseInt(dpi),
                        format: "jpeg",
                        start_number: parseInt(startNumber)
                    })
                });
                if (!res_upload_job.ok) {
                    throw new Error('アップロードURLの取得に失敗しました');
                }
                const urlData = await res_upload_job.json();
                uploadUrl = urlData.upload_url;
                jobIds.push(urlData.job_id); // Store each job ID

                // ファイルをアップロード
                const fullUrl = uploadUrl.startsWith('/') ? 
                    window.location.origin + uploadUrl : uploadUrl;
                
                console.log('Debug: Upload URL =', uploadUrl);
                console.log('Debug: Full URL =', fullUrl);
                console.log('Debug: File =', file.name, 'Size =', file.size);

                try {
                    console.log('Debug: Preparing file for direct upload...');
                    
                    console.log('Debug: Sending direct file upload request...');
                    
                    const uploadResponse = await fetch(fullUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        },
                        body: file
                    });
                    
                    console.log('Debug: Upload response status =', uploadResponse.status);
                    
                    if (!uploadResponse.ok) {
                        const errorText = await uploadResponse.text();
                        console.error('Debug: Upload error response =', errorText);
                        throw new Error(`アップロードに失敗しました: ${uploadResponse.status} - ${errorText}`);
                    }
                    
                    console.log('Debug: Upload successful');
                } catch (uploadError) {
                    console.error('Debug: Upload exception =', uploadError);
                    throw uploadError;
                }
            }

            // アップロード完了をバックエンドに通知
            
            const notifyResponse = await fetch(`/api/notify-upload-complete/${currentSessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    job_ids: jobIds,
                    dpi: parseInt(dpi),
                    format: "jpeg",
                    max_retries: 3,
                    start_number: parseInt(startNumber)
                })
            });
            
            if (!notifyResponse.ok) {
                throw new Error('アップロード完了通知に失敗しました');
            }

            // アップロード完了後、変換処理の完了を待つ（変換完了はSSEで通知される）
            progressText.textContent = 'PDFファイルをアップロードしました。変換処理が完了するまでお待ちください...';
            
        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました: ' + error.message);
            progressDiv.classList.add('hidden');
        }
    });

    function updateProgress(data) {
        const { status, progress, message } = data;
        
        if (status === 'processing') {
            progressBar.style.width = `${progress}%`;
            progressText.textContent = message || `変換中... ${progress}%`;
        } else if (status === 'completed') {
            progressBar.style.width = '100%';
            progressText.textContent = '変換が完了しました！';
            eventSource.close();
            progressDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
            downloadLink.style.display = 'none';
            document.querySelector('#result p').textContent = '変換が完了しました。画像はGCS_BUCKET_IMAGEに保存されました。';
        } else if (status === 'error') {
            eventSource.close();
            alert('エラーが発生しました: ' + message);
        }
    }
});                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        

