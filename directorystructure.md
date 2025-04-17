# ディレクトリ構成

以下のディレクトリ構造に従って実装を行ってください：

```
/
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
│   └── main.py                 # アプリケーションエントリーポイント
├── tests/                      # テストコード
│   ├── api/                   # APIテスト
│   └── services/              # サービステスト
├── static/                    # 静的ファイル
│   ├── css/                  # スタイルシート
│   └── js/                   # フロントエンドスクリプト
├── templates/                 # HTMLテンプレート
├── .env.example              # 環境変数テンプレート
├── .gitignore               # Git除外設定
├── Dockerfile               # コンテナ設定
├── requirements.txt         # Python依存関係
└── README.md               # プロジェクト説明
```

### 配置ルール
- APIエンドポイント → `app/api/`
- ビジネスロジック → `app/services/`
- データモデル → `app/models/`
- 設定関連 → `app/core/`
- フロントエンド → `static/` と `templates/`