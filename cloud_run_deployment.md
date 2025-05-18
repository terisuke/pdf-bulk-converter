# Cloud Runデプロイ手順

## 概要
このアプリケーションはGoogle Cloud RunとCloud Storageを使用してPDFファイルをJPEG画像に変換するサービスです。Cloud Runの32MB制限を回避するために、Cloud Storageを使用して大きなファイルを処理します。

## デプロイ前の準備

1. Google Cloud Storageバケットを作成
   - 画像保存用バケット (例: `pdf-converter-images`)
   - 作業ファイル用バケット (例: `pdf-converter-works`)

2. サービスアカウントの設定
   - サービスアカウントに必要な権限を付与 (Storage Object Admin)
   - サービスアカウントキーをJSON形式でダウンロード
   - `config/service_account.json`として保存

## デプロイコマンド

```bash
gcloud run deploy pdf-bulk-converter \
  --source . \
  --region asia-northeast1 \
  --platform managed \
  --memory 1Gi \
  --timeout 60m \
  --set-env-vars="GCP_REGION=asia-northeast1,GCS_BUCKET_IMAGE=YOUR_IMAGE_BUCKET_NAME,GCS_BUCKET_WORKS=YOUR_WORKS_BUCKET_NAME,SIGN_URL_EXP=3600" \
  --allow-unauthenticated
```

環境変数を適切な値に置き換えてください:
- `GCP_REGION`: デプロイするリージョン (例: asia-northeast1)
- `GCS_BUCKET_IMAGE`: 画像保存用のCloud Storageバケット名
- `GCS_BUCKET_WORKS`: 作業ファイル用のCloud Storageバケット名
- `SIGN_URL_EXP`: 署名付きURLの有効期間（秒）

## 注意事項

- ローカル開発環境では `GCP_REGION=local` を使用してください
- Cloud Run環境では必ず実際のリージョン名を指定してください
- サービスアカウントキーはセキュリティのため公開リポジトリにコミットしないでください
