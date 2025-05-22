# PDF Bulk Converter - テスト実行ガイド

## 📁 テストファイル構造

```
tests/
├── api/              # API関連のテスト
├── services/         # サービス関連のテスト
├── test_api.py       # API統合テスト
├── test_gcs.py       # GCS接続テスト
├── test_gcs_upload.py # GCSアップロードテスト
├── test_numbering.py # 連番生成テスト
├── test_storage.py   # ストレージテスト
└── run_test.py       # 変換処理統合テスト
```

## 🧪 テスト実行方法

### 1. 個別テストの実行

```bash
# testsディレクトリに移動
cd tests

# API統合テスト
python test_api.py

# GCS接続テスト
python test_gcs.py

# 連番生成テスト
python test_numbering.py

# 変換処理統合テスト
python run_test.py
```

### 2. pytestでの実行

```bash
# プロジェクトルートから
pytest tests/

# 特定のテストファイル
pytest tests/test_gcs_upload.py

# verboseモード
pytest tests/ -v
```

### 3. プロジェクトルートからの実行

```bash
# プロジェクトルートから直接実行する場合
python -m pytest tests/
python tests/test_api.py
python tests/test_numbering.py
```

## 📋 テストファイル詳細

### test_api.py
- API エンドポイントの統合テスト
- セッション作成、ファイルアップロード、変換処理の全体フローをテスト

### test_gcs.py
- Google Cloud Storage の接続テスト
- バケットアクセス、ファイルアップロードの基本機能をテスト

### test_gcs_upload.py
- GCS アップロード機能の詳細テスト
- pytest形式で記述されたテスト

### test_numbering.py
- 連番ファイル名生成機能のテスト
- 異なる開始番号での動作確認

### run_test.py
- PDF変換処理の統合テスト
- 実際の変換フローをエンドツーエンドでテスト

## ⚙️ テスト環境の準備

### 必要なファイル
- `test.pdf`: テスト用のPDFファイル（プロジェクトルートに配置）
- `.env`: 環境変数設定ファイル

### 環境変数
```bash
GCP_KEYPATH=path/to/service-account.json
GCS_BUCKET_WORKS=your-works-bucket
GCS_BUCKET_IMAGE=your-image-bucket
```

## 🔧 トラブルシューティング

### ImportError が発生する場合
```bash
# PYTHONPATHを設定
export PYTHONPATH=$PWD:$PYTHONPATH
python tests/test_api.py
```

### テストファイルが見つからない場合
- `test.pdf` がプロジェクトルートに存在することを確認
- 相対パスが正しく設定されていることを確認

### GCS接続エラーが発生する場合
- サービスアカウントキーファイルのパスを確認
- バケット名とアクセス権限を確認
