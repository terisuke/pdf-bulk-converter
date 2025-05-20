#!/usr/bin/env bash
set -euo pipefail

# PDF Bulk Converter Setup Script

echo "PDF Bulk Converter Setup Script"
echo "==============================="

# Check Python version
python_version=$(python3 --version 2>&1)
echo "検出: $python_version"

# Check if Python version is at least 3.11
python_info=$(python3 - <<'EOF'
import sys, json
print(json.dumps({"major": sys.version_info.major, "minor": sys.version_info.minor}))
EOF
)
major=$(echo "$python_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['major'])")
minor=$(echo "$python_info" | python3 -c "import sys, json; print(json.load(sys.stdin)['minor'])")
if (( major < 3 || (major == 3 && minor < 11) )); then
    echo "警告: このプロジェクトはPython 3.11+を必要とします"
    echo "現在のシステムPythonバージョン $python_version は互換性がありません。"
    echo ""
    echo "正しいPythonバージョンをインストールするためにsetup_with_pyenv.shを使用してみます..."

    # Make setup_with_pyenv.sh executable
    chmod +x setup_with_pyenv.sh

    # Run setup_with_pyenv.sh
    ./setup_with_pyenv.sh

    # Exit this script after setup_with_pyenv.sh is run
    exit $?
fi

echo "Python $python_version はこのプロジェクトと互換性があります。"

# Check if venv directory exists and delete it
if [ -d "venv" ]; then
    echo "既存の仮想環境を削除します..."
    rm -rf venv
fi

# Create a new virtual environment
echo "新しい仮想環境を作成します..."
python3 -m venv venv

# Activate the virtual environment
echo "仮想環境をアクティブ化します..."
source venv/bin/activate

# Add execute permissions to the requirements-fix.py script
chmod +x requirements-fix.py

# Use our custom requirements-fix.py script to install dependencies
echo "requirements-fix.py を使用して依存関係をインストールします..."

# Attempt installation with requirements-fix.py
if ./requirements-fix.py; then
    echo "依存関係のインストールに成功しました。"
else
    echo "エラー: requirements-fix.py の実行に失敗しました。MuPDF専用オプションで再試行します..."
    # Attempt installation with requirements-fix.py --mupdf-only
    if ./requirements-fix.py --mupdf-only; then
        echo "依存関係のインストールに成功しました (MuPDF専用オプションを使用)。"
    else
        echo "エラー: MuPDF専用オプションでも失敗したため、リクワイアメントからインストールを試行します..."
        # Attempt installation with pip install -r requirements.txt
        if python3 -m pip install -r requirements.txt; then
            echo "依存関係のインストールに成功しました (requirements.txt から)。"
        else
            echo "エラー: 依存関係のインストールに最終的に失敗しました。"
            echo ""
            echo "可能な解決策:"
            echo "1. PyMuPDFの問題について:"
            echo "   - macOS: brew install mupdf"
            echo "   - Ubuntu: apt-get install libmupdf-dev"
            echo "   - Windows: Microsoft Visual C++ Redistributableがインストールされていることを確認してください。"
            echo "2. 問題のあるパッケージを手動でインストールしてみてください:"
            echo "   - pip install PyMuPDF==1.23.26" # バージョンはrequirements.txtに合わせてください
            echo "3. Pythonバージョンの互換性を確認してください。"
            echo ""
            exit 1
        fi
    fi
fi


# 環境変数ファイルをコピー
echo ""
echo "環境変数を設定しています..."
if [ -f ".env.local" ]; then
    cp .env.local .env
    echo ".env.localを.envにコピーしました"
else
    echo "WARNING: .env.localファイルが見つかりません。環境変数を手動で設定する必要があります。"
fi

# Setup successful
echo ""
echo "セットアップが正常に完了しました！"
echo ""
echo "仮想環境をアクティブにするには、以下を実行してください:"
echo "    source venv/bin/activate"
echo "    python3 -m pip install --upgrade pip"
echo ""
echo "その後、開発サーバーを以下のコマンドで開始してください:"
echo "    uvicorn app.main:app --reload"
echo ""
echo "注意: 仮想環境をアクティブにするには、`source venv/bin/activate`を実行してください。"
