# PDF Bulk Converter

高画質 PDF → JPEG変換を提供するブラウザアプリケーションのREADMEです。

---

## 🎯 目的

* **データセット作成向け**: 高解像度（DPI指定可能）なJPEG画像を一括生成
* **連番ファイル対応**: 開始番号を指定して連続した番号付けで画像を生成
* **非同期処理**: ユーザー待ち時間を最小化、大容量PDFでも処理落ちしない
* **シンプルな構成**: FastAPI + PyMuPDF で実装

---

## ✨ 主な機能

| # | 機能           | 説明                                             |
|---|----------------|------------------------------------------------|
| 1 | PDF アップロード     | ブラウザ UI から複数 PDF を選択してアップロード                 |
| 2 | 連番ファイル名生成   | 指定した開始番号から7桁ゼロ埋めの連番でファイル名を生成 |
| 3 | 非同期変換処理 | `PyMuPDF` でページ並列レンダリング                         |
| 4 | リアルタイム進捗通知 | Server‑Sent Events (SSE) でリアルタイム進捗バー更新       |

---

## 🏗️ 技術スタック

* **Backend**  
  * Python: 3.11+ (3.12推奨)
  * FastAPI: 0.109.2 (ASGI, SSE, OpenAPI)  
  * PyMuPDF: PDF → JPEG 変換  
  * uvicorn: 0.27.1
  * python-multipart: 0.0.9
  * python-dotenv: 1.0.1
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
│   │   └── upload.py            # アップロード関連・ジョブステータス
│   ├── core/                    # コア機能
│   │   ├── config.py           # 設定管理
│   │   ├── job_status.py       # ジョブ状態管理
│   │   ├── process.py          # 処理ロジック
│   │   └── session_status.py   # セッション状態管理
│   ├── services/               # ビジネスロジック
│   │   ├── converter.py       # PDF変換処理
│   │   ├── storage.py         # ストレージ管理
│   │   ├── job_status.py      # ジョブ状態サービス
│   │   └── cleanup.py         # クリーンアップ処理
│   ├── models/                 # データモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── static/                # アプリケーション固有の静的ファイル
│   │   └── js/
│   │       └── main.js        # アプリケーション固有のJS
│   └── main.py                 # アプリケーションエントリーポイント
├── config/                     # 設定ファイル
│   └── service_account.json    # GCPサービスアカウント認証情報
├── local_storage/              # ローカルストレージ
├── .env                        # 環境変数
├── .gitignore                  # Git除外設定
├── Dockerfile                  # コンテナ設定
├── requirements.txt            # Python依存関係
└── README.md                   # プロジェクト説明
```

### 配置ルール
- APIエンドポイント → `app/api/`
- ビジネスロジック → `app/services/`
- データモデル → `app/models/`
- 設定関連 → `app/core/`
- アプリケーション固有の静的ファイル → `app/static/`
- 作業用ファイル → `local_storage/`

---

## 🖼️ アーキテクチャ

```text
[Browser]
  │ 1. File Upload & Start Number Setting
  ▼
[FastAPI Server]
  │
  ├─ 2. PDF Processing with Sequential Numbering
  │   └─ JPEG変換 (PyMuPDF)
  │
  └─ 3. Progress Updates (SSE)
      └─ 4. Images with Sequential Filenames (0000001.jpeg, 0000002.jpeg, ...)
```

---

## 📝 API 仕様

| Method | Path                     | 説明                    |
|--------|--------------------------|-------------------------|
| `POST` | `/api/session`           | アップロードセッション開始、ファイル連番起点指定  |
| `POST` | `/api/upload-url`        | アップロードURLを取得、ジョブID発行            |
| `GET`  | `/api/session-status/{session_id}`   | SSE でセッション進捗をリアルタイムに返す |
| `GET`  | `/api/job-status/{job_id}`   | SSE でジョブ進捗をリアルタイムに返す |
| `POST` | `/api/local-upload/{session_id}/{job_id}/{filename}` | PDFファイルアップロード (ローカル用) |
| `POST` | `/api/notify-upload-complete/{session_id}` | アップロード完了通知とPDF変換開始 |
| `PUT`  | `/api/session-update/{session_id}` | セッションのステータスを更新 |

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
$ cp .env.example .env  # または既存の.envファイルを確認・編集

# 5. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

---

## 💡 使用方法

1. **セッション開始**: `/api/session` に開始番号（例：100）を指定してPOSTリクエスト
2. **ファイルアップロード**: 取得したセッションIDでPDFファイルをアップロード  
3. **変換処理**: アップロード完了後、自動的にPDF → JPEG変換が開始
4. **ファイル名規則**: 指定した開始番号から連番で生成
   - 開始番号100の場合: `0000100.jpeg`, `0000101.jpeg`, `0000102.jpeg`...
   - 7桁ゼロ埋めで統一された連番ファイル名

---

## ⚙️ 環境変数 (.env)

| 変数           | 例                | 説明                           |
|----------------|-------------------|-------------------------------|
| `GCP_REGION`  | `local`           | GoogleCloud 接続リージョン (ローカル実行時は`local`) |
| `GCP_KEYPATH` | `./config/service_account.json` | GoogleCloud サービスアカウント認証鍵JSONの格納場所 |
| `GCS_BUCKET_IMAGE` | `bucket-name-image` | CloudStorage 変換画像ファイル格納バケット名       |
| `GCS_BUCKET_WORKS` | `bucket-name-works` | CloudStorage 作業ファイル格納バケット名       |
| `SIGN_URL_EXP` | `3600`           | 発行URL有効時間(秒数)            |

---

## 🔧 トラブルシューティング

### セットアップ関連 🚨

#### 自動設定がうまくいかない場合 🔄
- `python --version` で現在のバージョンを確認
- `which python` で使用しているPythonの場所を確認

#### 環境変数の問題 🌐
- `.env` ファイルが正しく設定されているか確認
- 必要に応じて `.env.example` を参考に `.env` ファイルを作成・編集

#### PyMuPDFのインストール問題 📦
- macOS: `brew install mupdf`
- Ubuntu: `apt-get install libmupdf-dev`
- Windows: Microsoft Visual C++ Redistributableのインストールが必要な場合があります

### 機能関連 📱

#### 連番が期待通りにならない場合 🔢
- **問題**: 開始番号を指定しても最初のファイルが `0000000.jpeg` になる
- **原因**: 状態更新時に `image_num=0` が設定されている
- **解決手順**:
  1. ブラウザのデベロッパーツールでAPIレスポンスを確認
  2. サーバーログで `Starting image number` のログを確認
  3. `notify_upload_complete` 関数でのセッション状態更新を確認

#### 変換が完了しない場合 🔄
- ブラウザのコンソールでエラーログを確認
- サーバーログで変換処理の状況を確認
- PDFファイルが破損していないか確認

#### Cloud Run でのログ確認方法 ☁️
```bash
# 最新のログを確認
$ gcloud logging read "resource.type=cloud_run_revision" --limit=50

# 特定のセッションのログを確認
$ gcloud logging read "resource.type=cloud_run_revision AND textPayload:session_id" --limit=20
```

### デバッグ時のチェックポイント 🔍

#### 連番生成のデバッグ
1. **セッション初期化時**: `image_num=request.start_number` が設定されているか
2. **アップロード完了通知時**: 現在の開始番号が保持されているか
3. **変換処理開始時**: `session_status_manager.get_imagenum()` が正しい値を返しているか
4. **ファイル名生成時**: `imagenum_start + page_num` の計算が正しいか

#### 一般的なエラーパターン
- **`image_num=0` が設定される箇所**: エラー処理や状態更新で注意
- **セッション状態がNone**: セッション管理の初期化エラー
- **PDF読み込み失敗**: ファイルパスやアクセス権限の問題

---

## 📝 最近の更新

### 2025-05-22 ⚡
- ✅ **連番ファイル名生成の重要な修正を完了**
  - `notify_upload_complete` 関数で `image_num=0` が設定されていた問題を解決
  - エラー処理時にも開始番号を保持するように修正
  - デバッグログを追加して問題の特定を容易化
- ✅ **状態管理の改善**
  - セッション状態更新時の開始番号保持を徹底
  - エラー処理での連番リセット問題を解決
- ✅ **ドキュメント更新**
  - 実際の問題解決経験を反映したトラブルシューティングガイドを追加
  - 具体的なデバッグ手順とチェックポイントを記載

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
