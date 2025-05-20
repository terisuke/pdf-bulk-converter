# AGENTS.md - PDF Bulk Converter

## はじめに
このプロジェクトはPythonを使用したPDF→JPEG変換サービスで、FastAPI、PyMuPDF、非同期処理を主要技術として採用しています。以下のガイドラインに従ってタスクを実行してください。

## 1. コードベースのナビゲーションとアーキテクチャ

### ディレクトリ構造
```
pdf-bulk-converter/
├── Dockerfile                     # コンテナ設定
├── app.yaml                       # App Engine設定ファイル
├── app/                           # FastAPIアプリケーション
│   ├── api/                       # APIエンドポイント
│   │   └── upload.py              # アップロード関連
│   ├── core/                      # コア機能
│   │   ├── config.py              # 設定管理
│   │   ├── job_status.py          # ジョブ状態管理
│   │   ├── process.py             # 処理ロジック
│   │   └── session_status.py      # セッション状態管理
│   ├── main.py                    # アプリケーションエントリーポイント
│   ├── models/                    # データモデル
│   │   └── schemas.py             # Pydanticモデル
│   ├── services/                  # ビジネスロジック
│   │   ├── cleanup.py             # 一時ファイル削除処理
│   │   ├── converter.py           # PDF変換処理
│   │   ├── job_status.py          # ジョブ状態管理サービス
│   │   └── storage.py             # ストレージ管理
│   └── static/                    # アプリケーション固有の静的ファイル
│       └── js/
│           └── main.js            # アプリケーション固有のJS
├── config/                        # 設定ファイル
│   └── service_account.json       # GCPサービスアカウント認証情報
├── static/                        # グローバルな静的ファイル
│   ├── css/                       # スタイルシート
│   └── js/                        # フロントエンドスクリプト
│       └── main.js                # メインのJavaScriptファイル
├── templates/                     # HTMLテンプレート
│   └── index.html                 # メインページ
├── tests/                         # テストディレクトリ
│   ├── api/                       # APIテスト
│   └── services/                  # サービステスト
├── tmp_workspace/                 # 作業用一時ディレクトリ
├── uploads/                       # アップロードファイル保存ディレクトリ
├── .env.local                     # ローカル開発用環境変数
├── requirements.txt               # Python依存関係
├── setup.sh                       # セットアップスクリプト
└── setup_with_pyenv.sh            # pyenvを使用したセットアップスクリプト
```

### アーキテクチャパターン
- FastAPI による非同期API実装
- Server-Sent Events による進捗通知
- Service Layer による業務ロジック分離
- PyMuPDF によるPDF処理
- ストリーミングZIP生成

## 2. コードスタイルとフォーマット

### Python スタイル（PEP 8準拠）
- 命名規則:
  - 関数・変数: snake_case（process_pdf）
  - クラス: PascalCase（PDFConverter）
  - 定数: UPPER_SNAKE_CASE（MAX_UPLOAD_SIZE）
  - プライベート: _underscore_prefix

### 型ヒント
- 全ての関数でパラメータ・戻り値に型ヒント必須
- `typing` モジュールからインポート
- カスタム型は Pydantic モデルで定義

### 実行コマンド
```bash
# フォーマット・リンター
black .                # Black フォーマット
isort .                # import 整理
flake8 .               # リンター実行
mypy app/              # 型チェック
```

## 3. テストプロトコル

### テスト構成
- pytest：テストフレームワーク
- pytest-cov：カバレッジ測定
- pytest-asyncio：非同期テスト対応

### テスト規則
- APIエンドポイントにはテスト必須
- サービスレイヤーの重要な関数にはテスト必須
- ファイル名: `test_*.py` または `*_test.py`
- テスト関数: `test_*` プレフィックス

### 実行コマンド
```bash
pytest                 # 全テスト実行
pytest -v              # 詳細表示
pytest --cov=app       # カバレッジ測定
pytest -k test_name    # 特定テスト実行
```

## 4. ビルドプロセスと環境設定

### 仮想環境
- `python -m venv venv` で作成
- `source venv/bin/activate` で有効化
- `pip install -r requirements.txt` で依存関係インストール

### 環境変数
```bash
GCP_REGION=local           # GoogleCloud 接続リージョン (ローカル実行時は`local`)
GCS_KEYPATH=./config/service_account.json   # GCP サービスアカウント認証鍵
GCS_BUCKET_IMAGE=bucket-name-image  # CloudStorage 変換画像ファイル格納バケット名
GCS_BUCKET_WORKS=bucket-name-works  # CloudStorage 作業ファイル格納バケット名
SIGN_URL_EXP=3600         # 発行URL有効時間(秒数)
```

### 実行コマンド
```bash
# 開発環境
uvicorn app.main:app --reload    # 開発サーバー起動（リロード有効）

# 本番環境
uvicorn app.main:app --host 0.0.0.0 --port 8080  # 本番サーバー起動

# Docker環境
docker build -t pdf-bulk-converter .  # Dockerイメージ構築
docker run -p 8080:8080 pdf-bulk-converter  # Dockerコンテナ起動
```

## 5. コミットメッセージ規約

### フォーマット（Conventional Commits）
```
type(scope): description

feat(upload): implement multi-file upload
fix(converter): resolve memory leak during PDF processing
docs(api): update API documentation
refactor(services): optimize JPEG conversion
test(api): add upload endpoint tests
chore(deps): update FastAPI to latest version
```

## 6. プルリクエスト（PR）指示

### PRタイトル形式
- `[feat] ファイル分割アップロード機能の実装`
- `[fix] 日本語ファイル名の文字化け問題を解決`

### PR説明テンプレート
```markdown
## 変更内容
- 実装・修正された機能の説明

## 変更理由
- 変更の背景・動機

## テスト方法
- ローカルでの検証手順
- 自動テスト結果

## 破壊的変更
- [ ] API の破壊的変更あり
- [ ] 設定変更が必要

## チェックリスト
- [ ] 全テスト通過
- [ ] 型チェック通過
- [ ] ドキュメント更新

## Closes
- Fixes #issue_number
```

## 7. プロジェクト全般のガイドライン

### FastAPI ベストプラクティス
- 非同期ハンドラの使用
- Pydantic モデルによる入力バリデーション
- 依存性注入システムの活用
- OpenAPIドキュメント自動生成
- 適切なHTTPステータスコード使用

### ファイル処理
- 一時ファイルの適切な管理
- ストリーミング処理による大容量ファイル対応
- PyMuPDF による効率的なPDF処理
- ファイル命名の一貫性維持

### セキュリティ
- ファイル形式のバリデーション
- アップロードサイズの制限
- CORS 設定の適切な管理
- サニタイゼーション（特に日本語ファイル名）

### パフォーマンス
- 非同期処理による並列化
- Server-Sent Eventsによるリアルタイム通知
- ストリーミングZIP生成によるメモリ効率
- 不要な一時ファイルの適切な削除

### エラーハンドリング
- カスタム例外クラス定義
- 適切な HTTP ステータスコード返却
- クライアントへのエラー伝達
- 詳細なログ記録

## 8. レビューチェックリスト

### Python 特有の確認事項
- [ ] 型ヒントが適切に設定されている
- [ ] docstring がコメントとして記述されている
- [ ] 非同期処理が適切に実装されている
- [ ] 例外処理が適切に実装されている

### FastAPI 特有の確認事項
- [ ] エンドポイントの引数が適切に検証されている
- [ ] レスポンスモデルが適切に定義されている
- [ ] 適切な HTTP メソッド使用
- [ ] 非同期処理が効率的に実装されている

### ファイル処理
- [ ] 一時ファイルが適切に管理されている
- [ ] 大きなファイルでもメモリ効率よく処理されている
- [ ] ファイルパスのサニタイゼーションが実施されている
- [ ] 日本語ファイル名が正しく処理されている

### セキュリティ
- [ ] アップロードファイルの検証が実装されている
- [ ] サイズ制限が適切に設定されている
- [ ] 機密情報が環境変数で管理されている
- [ ] CORS設定が適切である

### テスト
- [ ] 重要なファイル処理ロジックにテストがある
- [ ] エラーケースがテストされている
- [ ] 非同期関数が適切にテストされている