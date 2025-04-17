# 📘 PDF Bulk Converter on GCP

高画質 PDF → JPEG変換 & ZIP ダウンロードをサーバーレスで提供するブラウザアプリケーションの README です。要件定義、アーキテクチャ、セットアップ手順を 1 つにまとめています。

---

## 🎯 目的

* **データセット作成向け**: 高解像度 (DPI 指定可能) なJPEG画像を一括生成。
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
  * Python: 3.11
  * FastAPI: 0.109.2 (ASGI, SSE, OpenAPI)  
  * pypdfium2: 4.24.0 (Apache‑2.0/BSD‑3) – PDF → PNG/JPEG  
  * uvicorn: 0.27.1
  * python-multipart: 0.0.9
  * python-dotenv: 1.0.1
  * zipstream: 1.1.4 – ストリーミング ZIP  
  * Cloud Run: コンテナ実行環境
  * Cloud Tasks: 非同期ジョブ管理
  * Cloud Storage: ファイルストレージ
  * Cloud Scheduler: クリーンアップジョブ

* **Frontend**  
  * HTML5
  * JavaScript (Vanilla)
  * Tailwind CSS: 3.4.17
  * Fetch API: 署名付きURL操作
  * EventSource: Server-Sent Events

* **開発ツール**
  * Docker: コンテナ化
  * GitHub Actions: CI/CD
  * Cloud Build: コンテナビルド
  * Terraform: インフラ定義（オプション）

### 重要な制約事項
- PDFレンダリングは pypdfium2 を使用（バージョン変更禁止）
- Cloud Storage のライフサイクルポリシーは24時間
- 署名付きURLの有効期限は環境変数で設定（デフォルト3600秒）

### 実装規則
- 非同期処理は Cloud Tasks を使用
- ファイル操作は Cloud Storage の署名付きURLを使用
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
│   │   └── security.py         # セキュリティ関連
│   ├── services/               # ビジネスロジック
│   │   ├── storage.py          # Cloud Storage操作
│   │   ├── tasks.py           # Cloud Tasks操作
│   │   └── converter.py       # PDF変換処理
│   ├── models/                 # データモデル
│   │   └── schemas.py         # Pydanticモデル
│   ├── static/                # アプリケーション固有の静的ファイル
│   └── main.py                 # アプリケーションエントリーポイント
├── tests/                      # テストコード
│   ├── api/                   # APIテスト
│   └── services/              # サービステスト
├── static/                    # グローバルな静的ファイル
│   ├── css/                  # スタイルシート
│   └── js/                   # フロントエンドスクリプト
├── templates/                 # HTMLテンプレート
├── local_storage/            # ローカル開発用ストレージ
├── node_modules/            # npm依存関係（自動生成）
├── .cursor/                # Cursor IDE設定
├── .env                    # 環境変数
├── .env.example           # 環境変数テンプレート
├── .gitignore            # Git除外設定
├── Dockerfile            # コンテナ設定
├── package.json         # フロントエンド依存関係定義
├── package-lock.json    # フロントエンド依存関係ロック
├── requirements.txt     # Python依存関係
├── run_test.py        # テスト実行スクリプト
├── issue_summary.md   # 課題管理
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
- テストコード → `tests/`（APIとサービスごとに分類）

### ディレクトリの役割
- `app/`: FastAPIアプリケーションのメインディレクトリ
- `static/`: グローバルに使用される静的ファイル（CSS、JavaScript、画像など）
- `app/static/`: アプリケーション固有の静的ファイル
- `templates/`: HTMLテンプレートファイル
- `local_storage/`: ローカル開発時の一時ファイル保存用
- `tests/`: テストコード
- `node_modules/`: npm依存関係（自動生成、Git管理対象外）
- `.cursor/`: Cursor IDEの設定ファイル

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

### フェーズ1: 基本機能の強化（現在）
- [x] JPEG形式への統一（画質と容量の最適化）
- [x] 日本語ファイル名の完全対応
- [x] エラーハンドリングの改善
- [ ] 変換設定のプリセット機能
  - DPI: 150/300/600
  - JPEG品質: 85%/90%/95%
- [ ] 進捗表示の詳細化
  - 残り時間の予測
  - ページ単位の進捗表示

### フェーズ2: ユーザビリティの向上
- [ ] ドラッグ&ドロップによるファイルアップロード
- [ ] プレビュー機能の追加
  - サムネイル表示
  - 変換前プレビュー
- [ ] バッチ処理の強化
  - 複数PDFの一括アップロード
  - キュー管理システム
- [ ] レスポンシブデザインの改善
  - モバイル対応の強化
  - タブレット向けレイアウト

### フェーズ3: 拡張機能
- [ ] 変換オプションの拡張
  - ページ範囲選択
  - 画像サイズの指定
  - 出力ファイル名のカスタマイズ
- [ ] バッチ処理の高度化
  - ZIP内のディレクトリ構造保持
  - 出力形式のカスタマイズ
- [ ] セキュリティ強化
  - アクセス制御の実装
  - ファイルの暗号化オプション

### フェーズ4: エンタープライズ機能
- [ ] ユーザー管理システム
  - Google Workspace連携
  - アクセス権限管理
- [ ] API提供
  - RESTful API
  - WebHook対応
- [ ] 監視・分析機能
  - 使用状況の分析
  - エラー追跡システム
- [ ] カスタマイズ可能なワークフロー
  - 前処理・後処理の設定
  - 自動化ルールの設定

### フェーズ5: クラウド最適化
- [ ] マルチリージョン対応
- [ ] 自動スケーリングの最適化
- [ ] コスト最適化
  - リソース使用量の最適化
  - キャッシュシステムの導入
- [ ] 災害対策
  - バックアップシステム
  - フェイルオーバー機能

---

## 📝 最近の更新

### 2024-04-18
- ✅ 出力形式をJPEGに統一
  - 画質と容量のバランスを最適化（品質95%）
  - UI/UXの簡素化
- ✅ 日本語ファイル名の完全対応
  - URLエンコーディングの改善
  - ファイル名の文字化け解消
- ✅ エラーハンドリングの強化
  - 詳細なエラーメッセージ
  - ログ出力の改善

---

## 📝 ライセンス

ソフトウェアコード: **MIT License**  
PDF レンダリング: **pypdfium2** (Apache‑2.0 / BSD‑3) & PDFium (BSD)

---

## 📮 Contact

* Author: Terada Kousuke (@cor_terisuke)
* Twitter: https://twitter.com/cor_terisuke
* e‑mail: example@example.com

---

## ⚠️ 既知の問題と解決策

### 現在の問題点

1. **ファイルアップロードの問題**:
   - フロントエンドからのアップロードリクエストがサーバーに到達していない
   - ブラウザコンソールログではリクエストが送信されているが、サーバーログには表示されていない
   - アップロードURLは正しく生成され、ローカルストレージディレクトリも作成されている

2. **日本語ファイル名の問題**:
   - 日本語ファイル名（例：「面集　2戸のコピー.pdf」）の処理に問題がある
   - `os.path.exists`が日本語ファイル名を正しく認識できない場合がある
   - ファイル名をASCII文字のみに変更することで回避可能

### 実装済みの修正

1. **環境設定**:
   - `.env`ファイルの作成とローカル環境変数の設定
   - ローカルストレージディレクトリの作成

2. **GCP関連コードの修正**:
   - `storage.py`のGoogle Cloud Storage関連コードをコメントアウト
   - ローカルモードでの動作を優先

3. **APIエンドポイントの実装**:
   - ダウンロードURLを取得するエンドポイントの追加
   - ローカルアップロードエンドポイントのHTTPメソッドをPUTからPOSTに変更
   - 詳細なログ出力の追加

4. **PDF変換機能の修正**:
   - `converter.py`の`bitmap.to_pil()`メソッドの追加
   - 画像フォーマット処理の修正

5. **直接テスト**:
   - `run_test.py`スクリプトを作成してPDF変換機能を直接テスト
   - テスト結果：**PDF変換機能は正常に動作することを確認**
   - 2ページのPDFが正常に画像に変換され、ZIPファイルが生成された

### 今後の対応

1. **ネットワーク問題の調査**:
   - ブラウザのネットワークタブでアップロードリクエストの詳細を確認
   - CORSの設定を確認し、必要に応じて修正
   - FastAPIのミドルウェアを確認し、リクエストが正しく処理されているか確認

2. **フロントエンド修正**:
   - `main.js`のアップロード処理を簡素化し、デバッグを容易にする
   - フォームデータの送信方法を見直す
   - アップロードURLの構築方法を確認

3. **サーバー設定**:
   - 絶対パスを使用するように`config.py`を修正
   - ログレベルを詳細に設定して問題の特定を容易にする
   - FastAPIのデバッグモードを有効にする

4. **ファイル名の処理**:
   - アップロード時に日本語ファイル名を英数字に変換する処理を追加
   - ファイル名のエンコーディングを適切に処理する

