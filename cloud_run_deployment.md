# Cloud Runデプロイ手順

## 概要
このアプリケーションはGoogle Cloud RunとCloud Storageを使用してPDFファイルをJPEG画像に変換するサービスです。Cloud Runの32MB制限を回避するために、Cloud Storageを使用して大きなファイルを処理します。

## デプロイ前の準備

1. Google Cloud Storageバケットを作成
   - 画像保存用バケット (例: `pdf-converter-images`)
   - 作業ファイル用バケット (例: `pdf-converter-works`)
   これらのバケット名は、後述のデプロイスクリプト (`scripts/deploy.sh`) 内で設定します。

2. サービスアカウントの設定
   - サービスアカウントに必要な権限を付与 (Storage Object Admin など、アプリケーションが必要とする権限)
   - サービスアカウントキーをJSON形式でダウンロードし、プロジェクトルートの `config/service_account.json` として保存します。
     **注意:** このファイルは `.gitignore` に追加し、リポジトリにコミットしないでください。
     デプロイスクリプトは、このパスにあるサービスアカウントキーを参照しようとします。Cloud Runの実行サービスアカウントが適切な権限を持っている場合は、このキーファイルがなくても動作する可能性があります。

## デプロイスクリプトによるデプロイ

このプロジェクトでは、ビルドからデプロイまでを一貫して行うためのシェルスクリプトを提供しています。

### スクリプトの準備

1.  `scripts/deploy.sh` ファイルを開きます。
2.  スクリプト内の以下の環境変数を、実際の値に置き換えてください:
    *   `GCS_BUCKET_IMAGE`: 作成した画像保存用のCloud Storageバケット名
    *   `GCS_BUCKET_WORKS`: 作成した作業ファイル用のCloud Storageバケット名
    *   (オプション) `PROJECT_ID`, `REGION`, `SERVICE_NAME` など、他の変数も環境に合わせて確認・変更してください。

### スクリプトの実行

ターミナルで以下のコマンドを実行します:

```bash
bash scripts/deploy.sh
```

このスクリプトは以下の処理を自動的に行います:
1.  GCP認証の確認と、必要に応じたログイン処理。
2.  DockerがArtifact Registryにアクセスするための認証設定。
3.  `config/service_account.json` の存在確認（警告のみ）。
4.  現在の `Dockerfile` を使用してコンテナイメージをビルド。
5.  ビルドしたイメージに一意のタグを付与。
6.  イメージをGoogle Cloud Artifact Registryにプッシュ。
7.  Cloud Runサービス (`pdf-bulk-converter`) に新しいイメージでデプロイ。
    - リージョン: `asia-northeast1` (スクリプト内で変更可能)
    - CPU: 2
    - メモリ: 4GiB
    - タイムアウト: 60分
    - 環境変数: `GCP_REGION`, `GCS_BUCKET_IMAGE`, `GCS_BUCKET_WORKS`, `SIGN_URL_EXP` を設定。

デプロイが完了すると、サービスのURLが表示されます。

## (旧) デプロイコマンド (参考情報)

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

これらの設定は、新しい `scripts/deploy.sh` スクリプト内で行われます。

## 注意事項

- ローカル開発環境では `GCP_REGION=local` を使用してください
- Cloud Run環境では必ず実際のリージョン名を指定してください
- サービスアカウントキーはセキュリティのため公開リポジトリにコミットしないでください
