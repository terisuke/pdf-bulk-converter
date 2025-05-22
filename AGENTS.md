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
│   │   └── upload.py              # アップロード・ステータス管理関連
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
│   │   ├── converter.py           # PDF変換処理（重要）
│   │   ├── job_status.py          # ジョブ状態管理サービス
│   │   └── storage.py             # ストレージ管理
│   └── static/                    # アプリケーション固有の静的ファイル
│       └── js/
│           └── main.js            # アプリケーション固有のJS
├── config/                        # 設定ファイル
│   └── service_account.json       # GCPサービスアカウント認証情報
├── local_storage/                 # ローカルストレージ
├── .env                           # 環境変数
├── .env.example                   # 環境変数テンプレート
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
- 連番ファイル名生成による統一されたファイル管理

### 重要なファイルとその役割
- `app/services/converter.py`: PDF→JPEG変換の核心ロジック
- `app/core/session_status.py`: セッション管理と連番管理
- `app/api/upload.py`: APIエンドポイントとバックグラウンド処理
- `app/models/schemas.py`: データモデル定義

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
- 特に連番生成機能のテストは重要
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
GCP_KEYPATH=./config/service_account.json   # GCP サービスアカウント認証鍵
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
fix(converter): resolve sequential numbering issue  
docs(api): update API documentation
refactor(services): optimize JPEG conversion
test(api): add upload endpoint tests
chore(deps): update FastAPI to latest version
```

## 6. プルリクエスト（PR）指示

### PRタイトル形式
- `[feat] ファイル分割アップロード機能の実装`
- `[fix] 連番ファイル名生成の問題を解決`

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

### ファイル処理と連番管理
- 一時ファイルの適切な管理
- ストリーミング処理による大容量ファイル対応
- PyMuPDF による効率的なPDF処理
- **重要**: 連番ファイル名生成の一貫性維持
  - 7桁ゼロ埋め形式（0000001.jpeg）
  - セッション状態での連番管理
  - 開始番号の正確な反映

### セキュリティ
- ファイル形式のバリデーション
- アップロードサイズの制限
- CORS 設定の適切な管理
- サニタイゼーション（特に日本語ファイル名）

### パフォーマンス
- 非同期処理による並列化
- Server-Sent Eventsによるリアルタイム通知
- 不要な一時ファイルの適切な削除

### エラーハンドリング
- カスタム例外クラス定義
- 適切な HTTP ステータスコード返却
- クライアントへのエラー伝達
- 詳細なログ記録

## 8. 重要な実装詳細

### 連番ファイル名生成のロジック
- `session_status_manager.get_imagenum(session_id)` で開始番号を取得
- `page_num` (0から開始) と開始番号を加算
- `f"{imagenum_current:07d}.{format}"` で7桁ゼロ埋めファイル名生成
- 各PDF処理後に `session_status_manager.add_imagenum()` で連番を更新

### 変換処理フロー
1. セッション開始時に開始番号を設定
2. PDFアップロード
3. `convert_pdfs_to_images()` で一括変換開始
4. `convert_1pdf_to_images()` で個別PDF処理
5. 各ページごとに連番ファイル名生成・保存
6. セッション状態の連番カウンタ更新

### 状態管理の重要な注意点
- `SessionStatus`: セッション全体の状態管理
- `JobStatus`: 個別ジョブの進捗管理
- `session_status_manager`: セッション状態とファイル連番の管理
- **重要**: 状態更新時に `image_num=0` を設定しない
  - エラー処理でも現在の開始番号を保持する
  - `notify_upload_complete` 等で既存の開始番号を維持する

## 9. デバッグとトラブルシューティング

### デバッグログの活用
- セッション状態の詳細ログを確認
- 連番生成の計算過程を記録
- PDF処理の各段階での状態チェック

### 問題特定の手順
1. **ログレベルの確認**: `logger.info` が出力されているか
2. **セッション状態の確認**: `get_status()` の返り値をチェック
3. **開始番号の追跡**: 各処理段階での `image_num` の値を確認
4. **エラー処理の確認**: エラー時の状態保持が正しく動作しているか

### 一般的なトラブルシューティング
- Cloud Run のログを確認してエラーの詳細を特定
- ローカル環境でのテスト実行による問題の再現
- デバッグログを使用した処理フローの追跡

## 10. レビューチェックリスト

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

### ファイル処理と連番生成
- [ ] 一時ファイルが適切に管理されている
- [ ] 大きなファイルでもメモリ効率よく処理されている
- [ ] ファイルパスのサニタイゼーションが実施されている
- [ ] 日本語ファイル名が正しく処理されている
- [ ] **重要**: 連番ファイル名が正しく生成されている
- [ ] **重要**: 開始番号が正確に反映されている
- [ ] **重要**: セッション状態の連番管理が適切に動作している
- [ ] **重要**: エラー処理で開始番号が保持されている

### セキュリティ
- [ ] アップロードファイルの検証が実装されている
- [ ] サイズ制限が適切に設定されている
- [ ] 機密情報が環境変数で管理されている
- [ ] CORS設定が適切である

### テスト
- [ ] 重要なファイル処理ロジックにテストがある
- [ ] **重要**: 連番生成機能のテストがある
- [ ] エラーケースがテストされている
- [ ] 非同期関数が適切にテストされている

## 11. よくある問題と解決策

### 連番生成に関する問題

#### 問題: 最初のファイルが0000000.jpegになる
- **原因**: 状態更新時に `image_num=0` が設定されている（特に `notify_upload_complete` 関数）
- **確認方法**: 
  ```python
  # セッション状態を確認
  current_session_status = session_status_manager.get_status(session_id)
  logger.info(f"Current session status image_num: {current_session_status.image_num}")
  ```
- **解決策**: 
  ```python
  # 現在の状態を取得して開始番号を保持
  current_session_status = session_status_manager.get_status(session_id)
  start_image_num = current_session_status.image_num if current_session_status else 0
  
  # StatusStatus作成時にstart_image_numを使用
  SessionStatus(
      # ...
      image_num=start_image_num,  # 0ではなく現在の番号を保持
      # ...
  )
  ```

#### 問題: セッション間でファイル番号が重複する
- **原因**: セッション状態が適切に管理されていない
- **解決**: セッション初期化時の `image_num` 設定を確認

#### 問題: エラー後に連番がリセットされる
- **原因**: エラー処理で `image_num=0` を設定している
- **解決**: エラー処理でも現在の開始番号を保持する

### PDFの変換処理
- **問題**: 大きなPDFで処理が止まる
- **原因**: メモリ不足またはタイムアウト
- **解決**: ページ単位での処理と適切なエラーハンドリング

### ログ分析のポイント
- セッション初期化時の `image_num` 値
- `notify_upload_complete` での状態更新
- `convert_1pdf_to_images` での開始番号取得
- 各ページ処理時の連番計算

### Cloud Run 特有の問題
- **問題**: ログが途切れる
- **解決**: Cloud Run のログを時系列で確認し、処理の流れを追跡

この知識を活用して、連番ファイル名生成機能の品質を維持し、問題の早期発見・解決を図ってください。
