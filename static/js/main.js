document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('pdfFile');
    const fileSelectBtn = document.getElementById('fileSelectBtn');
    const convertBtn = document.getElementById('convertBtn');
    const fileList = document.getElementById('fileList');
    const fileItems = document.getElementById('fileItems');
    const progressDiv = document.getElementById('progress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    const resultDiv = document.getElementById('result');
    const idleStatus = document.getElementById('idleStatus');

    let currentSessionId = null;
    let jobIds = []; // Store all job IDs
    let eventSource = null;
    let selectedFiles = [];

    // ドラッグ&ドロップ機能
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files);
        const validFiles = files.filter(file => 
            file.type === 'application/pdf' || 
            file.name.toLowerCase().endsWith('.pdf') ||
            file.type === 'application/zip' ||
            file.name.toLowerCase().endsWith('.zip')
        );
        
        if (validFiles.length === 0) {
            alert('PDFまたはZIPファイルを選択してください');
            return;
        }
        
        if (validFiles.length !== files.length) {
            alert('一部のファイルがPDFまたはZIP形式ではないため、除外されました');
        }
        
        updateSelectedFiles(validFiles);
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        updateSelectedFiles(files);
    });

    function updateSelectedFiles(files) {
        selectedFiles = files;
        updateFileList();
        updateConvertButton();
    }

    function updateFileList() {
        if (selectedFiles.length === 0) {
            fileList.classList.add('hidden');
            return;
        }

        fileList.classList.remove('hidden');
        fileItems.innerHTML = '';

        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'flex items-center justify-between bg-gray-50 p-3 rounded-lg border';
            fileItem.innerHTML = `
                <div class="flex items-center space-x-3">
                    <svg class="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                        <p class="font-medium text-gray-900">${file.name}</p>
                        <p class="text-sm text-gray-500">${formatFileSize(file.size)}</p>
                    </div>
                </div>
                <button onclick="removeFile(${index})" class="text-red-500 hover:text-red-700 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            `;
            fileItems.appendChild(fileItem);
        });
    }

    function updateConvertButton() {
        const hasFiles = selectedFiles.length > 0;
        convertBtn.disabled = !hasFiles;
        
        if (hasFiles) {
            convertBtn.textContent = `${selectedFiles.length}個のファイルを変換開始`;
            convertBtn.parentElement.querySelector('p').textContent = `${selectedFiles.length}個のファイルが選択されています`;
        } else {
            convertBtn.textContent = '変換開始';
            convertBtn.parentElement.querySelector('p').textContent = 'ファイルを選択してから変換を開始してください';
        }
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // グローバル関数として定義（HTMLから呼び出されるため）
    window.removeFile = function(index) {
        selectedFiles.splice(index, 1);
        updateFileList();
        updateConvertButton();
        
        // ファイル入力をリセット
        fileInput.value = '';
    };

    convertBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        
        if (selectedFiles.length === 0) {
            alert('ファイルを選択してください');
            return;
        }

        const dpi = document.getElementById('dpi').value;
        const startNumber = document.getElementById('startNumber').value;

        try {
            // 進捗表示を開始
            idleStatus.classList.add('hidden');
            progressDiv.classList.remove('hidden');
            resultDiv.classList.add('hidden');
            
            // UIを無効化
            convertBtn.disabled = true;
            dropZone.style.pointerEvents = 'none';
            dropZone.classList.add('opacity-50');

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
            jobIds = []; // リセット
            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                progressText.textContent = `ファイル ${i + 1}/${selectedFiles.length} をアップロード中...`;
                const uploadProgress = 10.0 + 80.0 * (i / selectedFiles.length);
                progressBar.style.width = `${uploadProgress}%`;
                progressPercent.textContent = `${Math.round(uploadProgress)}%`;

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

                const uploadResponse = await fetch(fullUrl, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': file.type
                    },
                    body: file
                });

                if (!uploadResponse.ok) {
                    throw new Error(`アップロードに失敗しました: ${uploadResponse.status}`);
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
                    max_retries: 3
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
            resetUI();
        }
    });

    function updateProgress(data) {
        const { status, progress, message } = data;
        
        progressBar.style.width = `${progress}%`;
        progressPercent.textContent = `${Math.round(progress)}%`;
        progressText.textContent = message || `変換中... ${Math.round(progress)}%`;

        if (status === 'completed') {
            eventSource.close();
            progressDiv.classList.add('hidden');
            resultDiv.classList.remove('hidden');
            document.querySelector('#result p').textContent = '変換が完了しました。画像はGCS_BUCKET_IMAGEに保存されました。';
            resetUI();
        } else if (status === 'error') {
            eventSource.close();
            alert('エラーが発生しました: ' + message);
            resetUI();
        }
    }

    function resetUI() {
        // UIを元に戻す
        convertBtn.disabled = selectedFiles.length === 0;
        dropZone.style.pointerEvents = 'auto';
        dropZone.classList.remove('opacity-50');
        
        // サイドバーの状態をリセット
        if (!resultDiv.classList.contains('hidden')) {
            // 結果が表示されている場合はそのままにする
            return;
        }
        
        progressDiv.classList.add('hidden');
        idleStatus.classList.remove('hidden');
    }

    // 初期化
    updateConvertButton();
});