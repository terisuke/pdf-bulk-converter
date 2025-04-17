# 📘 PDF Bulk Converter on GCP

高画質 PDF → 画像変換 & ZIP ダウンロードをサーバーレスで提供するブラウザアプリケーションの README です。要件定義、アーキテクチャ、セットアップ手順を 1 つにまとめています。

---

## 🎯 目的

* **データセット作成向け**: 高解像度 (DPI 指定可能) なページ画像を一括生成。
* **負荷分散 & 非同期**: ユーザー待ち時間を最小化し、大容量 PDF でも処理落ちしない。
* **サーバーレス & 低運用コスト**: Cloud Run / Cloud Tasks / Cloud Storage の範囲で完結。

---

## ✨ 主な機能

| # | 機能           | 説明                                                                       |
|---|----------------|--------------------------------------------------------------------------|
| 1 | PDF アップロード     | ブラウザ UI から複数 PDF を選択し、Cloud Storage に直接アップロード (Signed URL)           |
| 2 | ZIP アップロード     | 複数 PDF を含む ZIP ファイルをアップロードし、自動展開・一括変換                           |
| 3 | 非同期変換ジョブ  | Cloud Tasks → Cloud Run ワーカー。`pypdfium2` でページ並列レンダリング                    |
| 4 | ストリーミング ZIP    | 画像生成と同時に ZIP 書き込み。完了後に署名付き DL URL 発行                       |
| 5 | リアルタイム進捗通知 | Server‑Sent Events (SSE) でリアルタイム進捗バー更新。FastAPI StreamingResponse を使用 |
| 6 | 自動クリーンアップ    | ZIP と元 PDF を Cloud Storage Lifecycle (24 h) で自動削除                     |

---

## 🏗️ 技術スタック

* **Backend**  
  * Python 3.11 + **FastAPI** (ASGI, SSE, OpenAPI)  
  * **pypdfium2** (Apache‑2.0/BSD‑3) – PDF → PNG/JPEG  
  * `zipstream` – ストリーミング ZIP  
  * Cloud Run (コンテナ) / Cloud Tasks (キュー) / Cloud Scheduler (Cleanup)  
  * Cloud Storage (アップロード／ZIP 保存)
* **Frontend**  
  * Node.js + npm
  * Vanilla JavaScript + HTML5  
  * Fetch API (signed URL PUT) / EventSource (SSE)  
  * Tailwind CSS (簡易 UI)
* **CI/CD**  
  * GitHub Actions → Cloud Build → Cloud Run deploy  
  * Terraform (オプション) でインフラ定義

---

## 📁 プロジェクト構造

```
pdf-bulk-converter/
├── app/                    # バックエンドアプリケーション
├── static/                 # 静的ファイル（CSS, JS, 画像）
├── templates/              # HTMLテンプレート
├── tests/                  # テストコード
├── local_storage/          # ローカル開発用ストレージ
├── .env                    # 環境変数
├── .env.example           # 環境変数テンプレート
├── .gitignore             # Git除外設定
├── Dockerfile             # コンテナビルド設定
├── package.json           # フロントエンド依存関係
├── requirements.txt       # バックエンド依存関係
├── run_test.py           # テスト実行スクリプト
├── issue_summary.md      # 課題管理
├── directorystructure.md # ディレクトリ構造ドキュメント
└── technologystack.md    # 技術スタックドキュメント
```

---

## 🖼️ アーキテクチャ

```text
[Browser]
  │ 1. PUT (signed URL)
  ▼
[Cloud Storage]─────┐
  ▲                 │ 2. Pub/Sub Notification
  │                 ▼
  │           [Cloud Tasks]
  │                 ▼
  │           [Cloud Run: worker]
  │                 ├─ ZIP展開 (オプション)
  │                 ├─ render pages (pypdfium2)
  │                 └─ stream‑zip to GCS
  │
  └─ 5. EventSource  ◀─ 3. progress push (SSE)

4. 完了後：DL URL 返却
```

---

## 📝 API 仕様 (抜粋)

| Method | Path                 | 説明                                                               |
|--------|----------------------|------------------------------------------------------------------|
| `POST` | `/upload-url`        | 署名付き PUT URL (PDF/ZIP 用) を返す。Body: `filename`, `content_type` |
| `GET`  | `/status/{job_id}`   | SSE でジョブ進捗をリアルタイムに返す。`text/event-stream` 形式で配信              |
| `GET`  | `/download/{job_id}` | 署名付き ZIP ダウンロード URL を返す                                        |

---

## 🚀 クイックスタート

```bash
# 0. プロジェクトフォルダを作成して Git 初期化
$ mkdir pdf-bulk-converter
$ cd pdf-bulk-converter
$ git init
# GitHub へリポジトリを作成 & remote 設定 (GitHub CLI 利用例)
$ gh repo create pdf-bulk-converter --public --source=. --remote=origin -y

# 1. 依存関係のインストール
$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate
$ pip install -r requirements.txt
$ npm install

# 2. 環境変数を設定
$ cp .env.example .env
$ vi .env  # GCP プロジェクト ID / バケット名など

# 3. ローカル開発サーバー起動
$ python run_test.py  # テストモード
# または
$ docker build -t pdf-converter .
$ docker run -p 8080:8080 --env-file .env pdf-converter

# 4. GCP デプロイ (Cloud Run)
$ gcloud run deploy pdf-converter \
    --source . \
    --region=asia-northeast1 \
    --set-env-vars="$(cat .env | xargs)"
```

---

## ⚙️ 環境変数 (.env)

| 変数           | 例                | 説明                    |
|----------------|-------------------|-------------------------|
| `GCP_PROJECT`  | `my-project`      | GCP プロジェクト ID           |
| `REGION`       | `asia-northeast1` | Cloud Run / Tasks リージョン |
| `BUCKET_RAW`   | `pdf-raw-bucket`  | PDF アップロード先バケット        |
| `BUCKET_ZIP`   | `pdf-zip-bucket`  | 生成 ZIP 保存バケット       |
| `SIGN_URL_EXP` | `3600`            | 署名 URL 有効秒数       |

---

## 🧹 メンテナンス & コスト最適化

* **Lifecycle Policies**: 24 h 後に ZIP と PDF を削除。
* **Concurrency**: Cloud Run `max-instances` & `cpu-throttling` で自動スケール。
* **Monitoring**: Cloud Logging + Cloud Monitoring ダッシュボードを同梱。

---

## 🛣️ ロードマップ

- [ ] ページ範囲選択 UI (range slider)
- [ ] HEIF/WebP 出力オプション
- [ ] OAuth 連携 (Google Workspace 内での利用向け)
- [ ] ZIP アップロード時のディレクトリ構造保持オプション
- [ ] 大容量 ZIP 処理の最適化 (Cloud Run Jobs 対応)

---

## 📝 ライセンス

ソフトウェアコード: **MIT License**  
PDF レンダリング: **pypdfium2** (Apache‑2.0 / BSD‑3) & PDFium (BSD)

---

## 📮 Contact

* Author: Terada Kousuke (@cor_terisuke)
* Twitter: https://twitter.com/cor_terisuke
* e‑mail: example@example.com

