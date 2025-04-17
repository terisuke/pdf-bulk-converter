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
                    format: "jpeg"  // 常にJPEG
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
            formData.append('dpi', dpi);
            formData.append('format', 'jpeg');  // 常にJPEG

            const fullUrl = upload_url.startsWith('/') ? 
                window.location.origin + upload_url : upload_url;
            
            console.log('Uploading to URL:', fullUrl);
            console.log('FormData contents:', Array.from(formData.entries()));
                
            try {
                console.log('Starting fetch to:', fullUrl);
                console.log('With method:', 'POST');
                console.log('With body:', formData);
                
                const uploadResponse = await fetch(fullUrl, {
                    method: 'POST',
                    body: formData
                });
                
                console.log('Upload response received:', uploadResponse);
                console.log('Response status:', uploadResponse.status);
                console.log('Response ok:', uploadResponse.ok);
                
                if (!uploadResponse.ok) {
                    throw new Error(`Upload failed with status: ${uploadResponse.status}`);
                }
                
                // 進捗表示を開始
                progressDiv.classList.remove('hidden');
                progressText.textContent = 'アップロード完了、変換処理中...';
                
                try {
                    console.log('Parsing response as JSON...');
                    const responseData = await uploadResponse.json();
                    console.log('Upload response data:', responseData);
                    
                    if (responseData && responseData.message && responseData.message.includes('successfully')) {
                        console.log('Conversion completed successfully');
                        
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        try {
                            console.log('Getting download URL for job:', currentJobId);
                            const downloadResponse = await fetch(`/api/download/${currentJobId}`);
                            console.log('Download response:', downloadResponse);
                            
                            if (downloadResponse.ok) {
                                const downloadData = await downloadResponse.json();
                                console.log('Download data:', downloadData);
                                
                                downloadLink.href = downloadData.download_url;
                                progressDiv.classList.add('hidden');
                                resultDiv.classList.remove('hidden');
                            } else {
                                console.error('Failed to get download URL');
                                progressText.textContent = '変換は完了しましたが、ダウンロードURLの取得に失敗しました。';
                            }
                        } catch (downloadError) {
                            console.error('Download error:', downloadError);
                            progressText.textContent = '変換は完了しましたが、ダウンロードURLの取得に失敗しました。';
                        }
                    }
                } catch (parseError) {
                    console.error('Error parsing response:', parseError);
                }
            } catch (uploadError) {
                console.error('Upload error details:', uploadError);
                console.error('Error name:', uploadError.name);
                console.error('Error message:', uploadError.message);
                console.error('Error stack:', uploadError.stack);
                alert('アップロードエラー: ' + uploadError.message);
                throw uploadError;
            }

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
            console.log('Getting download URL for job:', currentJobId);
            const response = await fetch(`/api/download/${currentJobId}`);
            console.log('Download URL response:', response);
            
            if (!response.ok) {
                throw new Error('ダウンロードURLの取得に失敗しました');
            }

            const data = await response.json();
            console.log('Download URL data:', data);
            
            const download_url = data.download_url;
            console.log('Setting download link to:', download_url);
            
            downloadLink.href = download_url;
            
            progressDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
        } catch (error) {
            console.error('Error:', error);
            alert('エラーが発生しました: ' + error.message);
        }
    }
});                    