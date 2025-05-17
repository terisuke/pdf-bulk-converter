# PDF Bulk Converter

高画質 PDF → JPEG変換 & ZIP ダウンロードを提供するブラウザアプリケーションの README です。

---

## 🎯 目的

* **データセット作成向け**: 高解像度 (DPI 指定可能) なJPEG画像を一括生成。
* **非同期処理**: ユーザー待ち時間を最小化し、大容量 PDF でも処理落ちしない。
* **シンプルな構成**: FastAPI + PyMuPDF で実装。

---

## ✨ 主な機能

| # | 機能           | 説明                                             |
|---|----------------|------------------------------------------------|
| 1 | PDF アップロード     | ブラウザ UI から複数 PDF を選択してアップロード                 |
| 2 | ZIP アップロード     | 複数 PDF を含む ZIP ファイルをアップロードし、自動展開・一括変換 |
| 3 | 非同期変換処理 | `PyMuPDF` でページ並列レンダリング                         |
| 4 | ストリーミング ZIP    | 画像生成と同時に ZIP 書き込み                        |
| 5 | リアルタイム進捗通知 | Server‑Sent Events (SSE) でリアルタイム進捗バー更新       |

---

## 🏗️ 技術スタック

* **Backend**  
  * Python: 3.11+ (3.12推奨)
  * FastAPI: 0.109.2 (ASGI, SSE, OpenAPI)  
  * PyMuPDF: PDF → JPEG 変換  
  * uvicorn: 0.27.1
  * python-multipart: 0.0.9
  * python-dotenv: 1.0.1
  * zipstream: 1.1.4 – ストリーミング ZIP  
  * pydantic: 2.6.1 – データバリデーション
  * pydantic-settings: 2.1.0 – 設定管理
  * jinja2: 3.1.3 – テンプレートエンジン

* **Frontend**  
  * HTML5
  * JavaScript (Vanilla)
  * Tailwind CSS: 3.4.17
  * Fetch API
  * EventSource: Server-Sent Events

* **開発ツール**
  * Docker: コンテナ化

### 実装規則
- 非同期処理はasync/awaitを使用
- 進捗通知は Server-Sent Events を使用
- エラーハンドリングは FastAPI の例外処理を使用

---

## 📁 プロジェクト構造

```
pdf-bulk-converter/
├── app/                          # FastAPIアプリケーション
│   ├── api/                      # APIエンドポイント
│   │   ├── upload.py            # アップロード関連
│   │   ├── status.py           # ジョブステータス関連
│   │   └── download.py         # ダウンロード関連
│   ├── core/                    # コア機能
│   │   ├── config.py           # 設定管理
│   │   └── job_status.py       # ジョブ状態管理
│   ├── services/               # ビジネスロジック
│   │   ├── converter.py       # PDF変換処理
│   │   └── storage.py         # ストレージ管理
│   ├── models/                 # データモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── static/                # アプリケーション固有の静的ファイル
│   └── main.py                 # アプリケーションエントリーポイント
├── static/                    # グローバルな静的ファイル
│   ├── css/                  # スタイルシート
│   └── js/                   # フロントエンドスクリプト
├── templates/                 # HTMLテンプレート
├── tmp_workspace/            # 作業用スペース
├── .env.local                # ローカル開発用環境変数
├── .env.example           # 環境変数テンプレート
├── .gitignore            # Git除外設定
├── Dockerfile            # コンテナ設定
├── requirements.txt     # Python依存関係
└── README.md         # プロジェクト説明
```

### 配置ルール
- APIエンドポイント → `app/api/`
- ビジネスロジック → `app/services/`
- データモデル → `app/models/`
- 設定関連 → `app/core/`
- アプリケーション固有の静的ファイル → `app/static/`
- グローバルな静的ファイル → `static/`
- HTMLテンプレート → `templates/`

---

## 🖼️ アーキテクチャ

```text
[Browser]
  │ 1. File Upload
  ▼
[FastAPI Server]
  │
  ├─ 2. PDF Processing
  │   └─ JPEG変換 (PyMuPDF)
  │
  └─ 3. Progress Updates (SSE)
      └─ 4. ZIP Download
```

---

## 📝 API 仕様

| Method | Path                     | 説明                    |
|--------|--------------------------|-------------------------|
| `POST` | `/api/session`           | アップロードセッション開始、ファイル連番起点指定  |
| `POST` | `/api/upload-url`        | アップロードURLを取得、ジョブID発行            |
| `GET`  | `/api/session-status/{job_id}`   | SSE でセッション進捗をリアルタイムに返す |
| `GET`  | `/api/job-status/{job_id}`   | SSE でジョブ進捗をリアルタイムに返す |
| `POST` | `/api/local-upload/{session_id}/{job_id}/{filename} | PDFファイルアップロード (ローカル用) |
| `POST` | `/api/create-zip/{session_id} | ZIPファイル作成 |
| `GET`  | `/api/download/{session}` | 変換済みZIPファイルをダウンロード   |

---

## 🚀 クイックスタート (ローカル環境)

### セットアップスクリプトを使用する方法（推奨）
```bash
# 1. セットアップスクリプトを実行（Python 3.11以上が自動で設定されます）
$ chmod +x setup.sh
$ ./setup.sh

# 2. 仮想環境を有効化
$ source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

### pyenvを使用したセットアップ（Pythonバージョン切り替えが必要な場合）
```bash
# 1. pyenvを使用したセットアップスクリプトを実行
$ chmod +x setup_with_pyenv.sh
$ ./setup_with_pyenv.sh

# 2. 仮想環境を有効化
$ source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

### 手動セットアップ（上級者向け）
```bash
# 1. Python 3.11以上がインストールされていることを確認
$ python --version

# 2. 仮想環境を作成
$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate
$ pip install --upgrade pip setuptools wheel

# 3. 依存関係をインストール
$ pip install -r requirements.txt

# 4. 環境変数を設定
$ cp .env.local .env

# 5. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

### インストール時の注意点
- Python 3.11以上が必要です（セットアップスクリプトで自動対応）
- `setup.sh`を実行すると、Pythonのバージョンが自動的にチェックされます
  - Python 3.11以上が利用可能な場合はそのまま使用
  - 3.11未満の場合は自動的に`setup_with_pyenv.sh`が実行され、pyenvを使用して適切なPythonバージョンがインストールされます
- PyMuPDFのインストールには、システムにMuPDFライブラリが必要な場合があります（セットアップスクリプトで自動インストールします）

### トラブルシューティング

#### 自動設定がうまくいかない場合
- 全てのセットアップスクリプトがうまく実行できない場合は　1. `python --version` で現在のバージョンを2. `which python` で使用しているPythonの場所を確認してください

#### 環境変数の問題
- 実行時に `gcp_region` 無し等のエラーが出る場合は、`.env` ファイルが正しく生成されているか確認してください
- 手動で `cp .env.local .env` を実行してみてください

#### PyMuPDFのインストール問題
- macOS: `brew install mupdf`
- Ubuntu: `apt-get install libmupdf-dev`
- Windows: Microsoft Visual C++ Redistributableのインストールが必要な場合があります

#### その他
- 仮想環境の作成に失敗する場合: `python -m venv venv --clear`を試してください
- 環境変数`GCP_REGION`変更後に切替が上手くいかない場合は、 `unset GCP_REGION`を実行してから再試行してください

---

## ⚙️ 環境変数 (.env)

| 変数           | 例                | 説明                           |
|----------------|-------------------|------------------------------|
| `GCP_REGION`  | `local`           | GoogleCloud 接続リージョン (ローカル実行時は`local`) |
| `GCS_KEYPATH` | `"./config/service_account.json"` | CloudCloud サービスアカウント認証鍵JSONの格納場所 |
| `GCS_BUCKET_IMAGE` | `bucket-name-image` | CloudStorage 変換画像ファイル格納バケット名       |
| `GCS_BUCKET_WORKS` | `bucket-name-works` | CloudStorage 作業ファイル格納バケット名       |
| `SIGN_URL_EXP` | `3600`           | 発行URL有効時間(秒数)            |

---

## 📝 最近の更新

### 2025-04-26
- ✅ ダウンロードボタンの表示問題を修正
  - ZIPファイル名の不一致を解消
  - フロントエンドのダウンロードURL取得処理を改善
- ✅ ストレージ管理の改善
  - ローカルモードでのZIPファイル検索ロジックを強化
  - ファイル名のエンコーディング処理を改善

### 2025-04-18
- ✅ 出力形式をJPEGに統一
  - 画質と容量のバランスを最適化
  - UI/UXの簡素化
- ✅ 日本語ファイル名の完全対応
  - URLエンコーディングの改善
  - ファイル名の文字化け解消
- ✅ エラーハンドリングの強化
  - 詳細なエラーメッセージ
  - ログ出力の改善
- ✅ Cloud Runへのデプロイ完了
  - アプリケーションURL: https://pdf-bulk-converter-513507930971.asia-northeast1.run.app
  - リージョン: asia-northeast1
  - ステータス: 正常稼働中

---

## 📝 ライセンス

MIT License

---

## 📮 Contact

* Author: Terada Kousuke (@cor_terisuke)
* Twitter: https://twitter.com/cor_terisuke

---

