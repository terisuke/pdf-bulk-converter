# PDF Bulk Converter プロジェクト改修依頼書

## プロジェクト概要

「PDF Bulk Converter」は高画質PDF→JPEG変換＆ZIPダウンロードを提供するブラウザアプリケーションです。PDFファイルをアップロードすると、JPEG画像に変換してZIPファイルでダウンロードできます。

## 現在の状況

### mainブランチ (本番環境)
- Cloud Runにデプロイ済み
- 基本的なPDF→JPEG変換機能が動作中
- ファイル名は「PDFファイル名_pageX.jpg」形式で保存
- アップロード上限は32MBまで（Cloud Run制限）

### devブランチ (開発中)
- ローカルで開発中（まだクラウドにはアップロードしていない）
- 複数ファイルのアップロード処理が改善されている
- ジョブステータス管理が強化されている
- process_multiple_pdfs()機能が追加されている

## 実装すべき要件

1. **大容量ファイルアップロード対応**
   - Cloud Runの32MB制限を回避するため、Cloud Storageを経由したアップロード
   - 署名付きURLによる直接Cloud Storageへのアップロード実装

2. **連番リネーム機能**
   - 指定した開始番号からの連番でJPEGファイルをリネーム
   - 既に1000.jpgまでのデータが存在するため、開始番号を指定できること
   - 複数PDFが一度にアップロードされた場合も連番を維持

## 修正が必要なファイル

### mainブランチからの修正

1. **フロントエンド**
   - `templates/index.html`：連番開始番号入力フィールドの追加
   - `static/js/main.js`：Cloud Storage直接アップロード処理の実装

2. **バックエンド**
   - `app/services/storage.py`：コメントアウトされたCloud Storage関連コードを有効化
   - `app/services/converter.py`：リネーム機能の実装
   - `app/models/schemas.py`：連番開始番号パラメータの追加
   - `app/api/upload.py`：Cloud Storage経由アップロード対応の実装

### devブランチ（既に改善されている部分）

devブランチでは以下の改善が既に実装されています：
- 複数ファイル処理の強化：`process_multiple_pdfs()`関数
- 進捗管理の改善：JobStatusManager拡張
- ZIP生成処理の改善：複数PDFファイルを1つのZIPにまとめる機能

## 実装手順

### 1. 環境変数とモデルの整備
- `.env`ファイルにCloud Storage関連設定を追加
```
GCP_PROJECT=your-project-id
REGION=asia-northeast1
BUCKET_RAW=pdf-raw-bucket
BUCKET_ZIP=pdf-zip-bucket
SERVICE_ACCOUNT_KEY=./path/to/service-account-key.json
```

- `app/models/schemas.py`にリネーム設定パラメータ追加
```python
class UploadRequest(BaseModel):
    filename: str
    content_type: str
    dpi: Optional[int] = 300
    format: Optional[str] = "jpeg"
    start_number: Optional[int] = 1  # 連番開始番号
```

### 2. フロントエンド修正
- `templates/index.html`に連番開始番号入力フィールド追加
- `static/js/main.js`にCloud Storage直接アップロード対応の処理追加

### 3. バックエンド修正
- `app/services/storage.py`のCloud Storage連携コード有効化
- `app/services/converter.py`に連番リネーム機能追加
- `app/api/upload.py`のCloud Storage対応実装

## 注意事項

- devブランチの改善点を活かしつつ、Cloud Storage連携とリネーム機能を実装する
- 日本語ファイル名の処理に特に注意
- ローカル環境（environment="local"）でも動作するように互換性を維持
- 実装後はまずローカル環境で十分テストしてからデプロイする

## テスト方法

1. ローカル環境でCloud Storageエミュレータを使用したテスト
2. 小さいファイルでのリネーム機能テスト
3. 大きなファイル（50MB以上）でのCloud Storage経由アップロードテスト
4. 複数ファイルの一括処理における連番リネームの一貫性テスト 