# 技術スタック

## バックエンド
- Python: 3.11
- FastAPI: 0.109.2
- pypdfium2: 4.24.0 (Apache-2.0/BSD-3)
- uvicorn: 0.27.1
- python-multipart: 0.0.9
- python-dotenv: 1.0.1
- zipstream: 1.1.4

## クラウドサービス
- Google Cloud Platform
  - Cloud Run: コンテナ実行環境
  - Cloud Tasks: 非同期ジョブ管理
  - Cloud Storage: ファイルストレージ
  - Cloud Scheduler: クリーンアップジョブ

## フロントエンド
- HTML5
- JavaScript (Vanilla)
- Tailwind CSS: 3.4.17
- Fetch API: 署名付きURL操作
- EventSource: Server-Sent Events

## 開発ツール
- Docker: コンテナ化
- GitHub Actions: CI/CD
- Cloud Build: コンテナビルド
- Terraform: インフラ定義（オプション）

## 重要な制約事項
- PDFレンダリングは pypdfium2 を使用（バージョン変更禁止）
- Cloud Storage のライフサイクルポリシーは24時間
- 署名付きURLの有効期限は環境変数で設定（デフォルト3600秒）

## 実装規則
- 非同期処理は Cloud Tasks を使用
- ファイル操作は Cloud Storage の署名付きURLを使用
- 進捗通知は Server-Sent Events を使用
- エラーハンドリングは FastAPI の例外処理を使用