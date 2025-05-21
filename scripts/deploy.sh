#!/bin/bash
set -eo pipefail -u

# ==============================================================================
# デプロイスクリプト for PDF Bulk Converter
#
# このスクリプトは、Dockerイメージをビルドし、Google Artifact Registry に
# プッシュし、Google Cloud Run にデプロイします。
#
# 実行前に、以下の環境変数が正しく設定されていることを確認してください。
# 特に GCS_BUCKET_IMAGE と GCS_BUCKET_WORKS は実際のバケット名に
# 置き換える必要があります。
# ==============================================================================

# --- 環境変数の設定 ---
# Google Cloud Project ID
PROJECT_ID="yolov8environment"
# デプロイするリージョン
REGION="asia-northeast1"
# Cloud Run サービス名
SERVICE_NAME="pdf-bulk-converter"
# Docker イメージ名 (サービス名と同じで良いでしょう)
IMAGE_NAME="pdf-bulk-converter"
# Artifact Registry のリポジトリ名 (Cloud Run Source Deploy のデフォルトに合わせています)
REPOSITORY="cloud-run-source-deploy"

# !!! 重要: 以下のバケット名が実際の値に置き換えてください !!!
# 画像保存用のCloud Storageバケット名 (例: pdf-bulk-converter-images)
GCS_BUCKET_IMAGE="pdf-bulk-converter-images"
# 作業ファイル用のCloud Storageバケット名 (例: pdf-bulk-converter-test)
GCS_BUCKET_WORKS="pdf-bulk-converter-test"
# 署名付きURLの有効期間（秒）
SIGN_URL_EXP="3600" # 1時間

# --- スクリプト本体 ---

# エラーハンドリング関数
handle_error() {
    echo "エラーが発生しました: $1"
    echo "スクリプトを終了します。"
    exit 1
}

# サービスアカウントキーのパス
SERVICE_ACCOUNT_KEY_PATH="config/service_account.json"

echo "------------------------------------------------"
echo "PDF Bulk Converter デプロイ開始"
echo "------------------------------------------------"
echo ""
echo "プロジェクトID: ${PROJECT_ID}"
echo "リージョン: ${REGION}"
echo "サービス名: ${SERVICE_NAME}"
echo "イメージ名: ${IMAGE_NAME}"
echo "Artifact Registry リポジトリ: ${REPOSITORY}"
echo "画像バケット: ${GCS_BUCKET_IMAGE}"
echo "作業バケット: ${GCS_BUCKET_WORKS}"
echo "署名付きURL有効期間: ${SIGN_URL_EXP}秒"
echo ""

# バケット名設定の確認
if [ "${GCS_BUCKET_IMAGE}" = "YOUR_IMAGE_BUCKET_NAME_HERE" ] || [ "${GCS_BUCKET_WORKS}" = "YOUR_WORKS_BUCKET_NAME_HERE" ]; then
    echo "警告: GCS_BUCKET_IMAGE または GCS_BUCKET_WORKS が初期設定のプレースホルダーのままです。"
    echo "スクリプト上部の該当箇所を、実際のCloud Storageバケット名に修正してください。"
    handle_error "バケット名が設定されていないため、処理を中断しました。"
elif [ "${GCS_BUCKET_IMAGE}" = "pdf-bulk-converter-images" ] || [ "${GCS_BUCKET_WORKS}" = "pdf-bulk-converter-test" ]; then
    echo "情報: GCS_BUCKET_IMAGE は現在 '${GCS_BUCKET_IMAGE}' に、GCS_BUCKET_WORKS は '${GCS_BUCKET_WORKS}' に設定されています。"
    echo "これらのバケットが実際にGoogle Cloud Storageに存在し、適切な権限が設定されていることを確認してください。"
    echo "特に、'${GCS_BUCKET_IMAGE}' (画像保存用) バケットが存在しない場合は、事前に作成が必要です。"
    echo "('${GCS_BUCKET_WORKS}' は作業用バケットとして既存のものを利用する想定です)"
    read -p "この設定で続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        handle_error "バケット設定の確認と準備のため、処理を中断しました。"
    fi
fi

# 1. gcloud認証確認
echo "STEP 1: GCP認証を確認しています..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "  gcloudにログインしていません。認証を開始します..."
    gcloud auth login || handle_error "GCP認証に失敗しました"
    echo "  GCP認証が完了しました。"
else
    echo "  GCP認証済みです: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
fi
echo ""

# 2. Docker認証設定
echo "STEP 2: Docker認証を設定します (${REGION}-docker.pkg.dev)..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev || handle_error "Docker認証の設定に失敗しました"
echo "  Docker認証の設定が完了しました。"
echo ""

# 3. サービスアカウントキー確認
echo "STEP 3: サービスアカウントキーの存在を確認しています..."
if [ -f "${SERVICE_ACCOUNT_KEY_PATH}" ]; then
    echo "  サービスアカウントキーが見つかりました: ${SERVICE_ACCOUNT_KEY_PATH}"
else
    echo "  警告: サービスアカウントキーが見つかりません (${SERVICE_ACCOUNT_KEY_PATH})。"
    echo "  Cloud Storageへのアクセスや署名付きURLの生成に問題が発生する可能性があります。"
    echo "  (Cloud Runのサービスアカウントが適切な権限を持っていれば、このキーは不要な場合もあります)"
fi
echo ""

# 4. イメージタグ生成
IMAGE_TAG="$(date +%Y%m%d%H%M%S)-$(LC_ALL=C head /dev/urandom | LC_ALL=C tr -dc A-Za-z0-9 | head -c 8)" # 日付 + 8桁のランダム文字列
ARTIFACT_REGISTRY_IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo "STEP 4: Dockerイメージのビルドとプッシュ準備"
echo "  生成されるイメージタグ: ${IMAGE_TAG}"
echo "  プッシュ先: ${ARTIFACT_REGISTRY_IMAGE_PATH}"
echo ""

# 5. Dockerイメージのビルドとプッシュ
echo "STEP 5: Dockerイメージをビルドし、Artifact Registryにプッシュします..."
echo "  ビルドコンテキスト: ."
echo "  Dockerfile: Dockerfile"

# Dockerfileの存在チェック
if [ ! -f "Dockerfile" ]; then
    handle_error "Dockerfileが見つかりません。カレントディレクトリにDockerfileを配置してください。"
fi

docker buildx build \
  --platform linux/amd64 \
  -t "${ARTIFACT_REGISTRY_IMAGE_PATH}" \
  -f Dockerfile . --push || handle_error "Dockerイメージのビルドまたはプッシュに失敗しました"
echo "  Dockerイメージのビルドとプッシュが完了しました。"
echo ""

# 6. Cloud Runへのデプロイ
echo "STEP 6: Cloud Run (${SERVICE_NAME}) にデプロイします..."
# 環境変数をカンマ区切りで組み立てる
ENV_VARS="GCP_REGION=${REGION}"
ENV_VARS+=",GCS_BUCKET_IMAGE=${GCS_BUCKET_IMAGE}"
ENV_VARS+=",GCS_BUCKET_WORKS=${GCS_BUCKET_WORKS}"
ENV_VARS+=",SIGN_URL_EXP=${SIGN_URL_EXP}"
# サービスアカウントキーがコンテナ内にコピーされる場合は、そのパスも指定できます。
# 今回のDockerfileではコピーしていないため、Cloud Runの実行サービスアカウントの権限に依存します。
# もしコンテナ内にサービスアカウントキーを配置し、それを使用する場合は以下のように追加します。
# (Dockerfileで /app/config/service_account.json にコピーする想定)
# if [ -f "${SERVICE_ACCOUNT_KEY_PATH}" ]; then
#   ENV_VARS+=",GOOGLE_APPLICATION_CREDENTIALS=/app/config/service_account.json"
# fi

gcloud run deploy "${SERVICE_NAME}" \
  --image "${ARTIFACT_REGISTRY_IMAGE_PATH}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 60m \
  --set-env-vars="${ENV_VARS}" \
  --project "${PROJECT_ID}" || handle_error "Cloud Runへのデプロイに失敗しました"

echo "  Cloud Runへのデプロイが完了しました。"
echo ""

# 7. デプロイ完了後の情報表示
echo "STEP 7: デプロイ後の情報を取得しています..."
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --project "${PROJECT_ID}" --format='value(status.url)')

if [ -z "${SERVICE_URL}" ]; then
    echo "  サービスURLの取得に失敗しました。Cloud Consoleで確認してください。"
else
    echo "  デプロイされたサービスURL: ${SERVICE_URL}"
fi
echo ""

echo "================================================"
echo "デプロイプロセスが正常に完了しました！"
echo "新しいイメージ: ${ARTIFACT_REGISTRY_IMAGE_PATH}"
if [ ! -z "${SERVICE_URL}" ]; then
    echo "サービスURL: ${SERVICE_URL}"
fi
echo "================================================"

exit 0 