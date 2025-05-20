# ⚠️ アーカイブ済み

このファイルは古いバージョンの参照用として維持されています。
**最新の情報は必ず `README.md` を参照してください。**

---

# 現在のディレクトリ構成

実際のプロジェクト構造は以下の通りです：

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
├── cloud_run_deployment.md        # Cloud Runデプロイ手順
├── requirements.txt               # Python依存関係
├── setup.sh                       # セットアップスクリプト
├── setup_with_pyenv.sh            # pyenvを使用したセットアップスクリプト
└── README.md                      # プロジェクト説明
```

### 配置ルール
- APIエンドポイント → `app/api/`
- ビジネスロジック → `app/services/`
- データモデル → `app/models/`
- 設定関連 → `app/core/`
- アプリケーション固有の静的ファイル → `app/static/`
- グローバルな静的ファイル → `static/`
- HTMLテンプレート → `templates/`
- テスト → `tests/`
- 一時ファイル → `tmp_workspace/`
- アップロードファイル → `uploads/`