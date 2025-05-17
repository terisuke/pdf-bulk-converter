# PDF Bulk Converter - デペンデンシー修正ガイド

## 問題の概要

`source venv/bin/activate`の後に`pip install -r requirements.txt`を実行すると失敗が発生しました。

## 問題の原因

調査の結果、以下の原因が特定されました：

1. 既存の仮想環境が Python 3.9.6 で作成されていましたが、プロジェクトは Python 3.11 を要求しています
2. PyMuPDF パッケージのインストールには、システムにインストールされた MuPDF ライブラリに依存している場合があります
3. pip、setuptools、wheel パッケージが最新でない可能性があります

## 解決策

以下の修正を実施しました：

1. `setup.sh` スクリプトを作成し、適切な Python バージョンで仮想環境を再作成するプロセスを自動化
2. `requirements-fix.py` スクリプトを作成し、依存関係のインストールプロセスをスマートに処理
3. README に詳細なインストール手順とトラブルシューティングガイドを追加

## 使用方法

### セットアップスクリプトを使用する方法（推奨）

```bash
# 1. セットアップスクリプトを実行
$ chmod +x setup.sh
$ ./setup.sh

# 2. 環境変数を設定
$ cp .env.local .env

# 3. 仮想環境を有効化
$ source venv/bin/activate

# 4. ローカル開発サーバー起動
$ uvicorn app.main:app --reload
```

### 依存関係のインストールに問題が発生した場合

依存関係のインストールで問題が発生した場合、以下の手順を実行してください：

```bash
# 1. requirements-fix.pyスクリプトを実行
$ chmod +x requirements-fix.py
$ ./requirements-fix.py

# 2. または、MuPDFだけをインストールする場合
$ ./requirements-fix.py --mupdf-only
```

## 修正したファイル

1. **新規作成**: `setup.sh` - セットアップを自動化するスクリプト
2. **新規作成**: `setup.py` - Python バージョンを扱う追加スクリプト（オプション）
3. **新規作成**: `requirements-fix.py` - 依存関係のインストールを改善するスクリプト
4. **修正**: `requirements.txt` - コメントを追加して必要な依存関係を明確化
5. **修正**: `readme.md` - インストール手順を詳細化し、トラブルシューティング情報を追加

## 技術的な詳細

1. **PyMuPDF のインストール**:
   - macOS: `brew install mupdf` が必要
   - Ubuntu: `apt-get install libmupdf-dev` が必要
   - Windows: 通常は自動的にインストールされるが、Visual C++ Redistributable が必要な場合も

2. **Python バージョン**:
   - 3.11 以上が必要（`.python-version` ファイルで指定）
   - 仮想環境は Python 3.11 で作成する必要がある

3. **pip の更新**:
   - `pip`, `setuptools`, `wheel` を最新バージョンに更新することで、依存関係のインストールの問題を軽減
