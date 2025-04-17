# �� PDF Bulk Converter

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
  * Python: 3.11
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
│   │   └── converter.py       # PDF変換処理
│   ├── models/                 # データモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── static/                # アプリケーション固有の静的ファイル
│   └── main.py                 # アプリケーションエントリーポイント
├── static/                    # グローバルな静的ファイル
│   ├── css/                  # スタイルシート
│   └── js/                   # フロントエンドスクリプト
├── templates/                 # HTMLテンプレート
├── local_storage/            # ローカル開発用ストレージ
├── .env                    # 環境変数
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
  │   ├─ ZIP展開 (オプション)
  │   └─ JPEG変換 (PyMuPDF)
  │
  └─ 3. Progress Updates (SSE)
      └─ 4. ZIP Download
```

---

## 📝 API 仕様

| Method | Path                     | 説明                    |
|--------|--------------------------|-------------------------|
| `POST` | `/api/upload`            | PDFまたはZIPファイルをアップロード    |
| `GET`  | `/api/status/{job_id}`   | SSE でジョブ進捗をリアルタイムに返す |
| `GET`  | `/api/download/{job_id}` | 変換済みZIPファイルをダウンロード   |

---

## 🚀 クイックスタート

```bash
# 1. 依存関係のインストール
$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate
$ pip install -r requirements.txt

# 2. 環境変数を設定
$ cp .env.example .env

# 3. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

---

## ⚙️ 環境変数 (.env)

| 変数           | 例                | 説明       |
|----------------|-------------------|----------|
| `STORAGE_PATH` | `./local_storage` | ファイル保存パス |

---

## 📝 最近の更新

### 2024-04-18
- ✅ 出力形式をJPEGに統一
  - 画質と容量のバランスを最適化
  - UI/UXの簡素化
- ✅ 日本語ファイル名の完全対応
  - URLエンコーディングの改善
  - ファイル名の文字化け解消
- ✅ エラーハンドリングの強化
  - 詳細なエラーメッセージ
  - ログ出力の改善

---

## 📝 ライセンス

MIT License

---

## 📮 Contact

* Author: Terada Kousuke (@cor_terisuke)
* Twitter: https://twitter.com/cor_terisuke

---

