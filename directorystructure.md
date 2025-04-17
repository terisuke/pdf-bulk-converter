# ⚠️ 参照用ドキュメント

このファイルは参照用として維持されています。
最新の情報は `README.md` を参照してください。

---

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
└── README.md           # プロジェクト説明
```

### 配置ルール
- APIエンドポイント → `app/api/`
- ビジネスロジック → `app/services/`
- データモデル → `app/models/`
- 設定関連 → `app/core/`
- アプリケーション固有の静的ファイル → `app/static/`
- グローバルな静的ファイル → `static/`
- HTMLテンプレート → `templates/`