#!/bin/bash

# PDF Bulk Converter Setup Script with pyenv
echo "PDF Bulk Converter Setup Script with pyenv"
echo "========================================="

# pyenvがインストールされているか確認
if ! command -v pyenv &> /dev/null; then
    echo "pyenvがインストールされていません。インストールします..."
    # macOSの場合はHomebrewでインストール
    if [[ "$OSTYPE" == "darwin"* ]]; then
       if ! command -v brew &> /dev/null; then
           echo "Homebrewがインストールされていません。インストールが必要です。"
           echo "https://brew.sh/index_ja からインストール手順を確認してください。"
           exit 1
       fi
        brew install pyenv
       # .zshrcのバックアップを作成
       cp ~/.zshrc ~/.zshrc.backup
       # 設定が存在しない場合のみ追加
       if ! grep -q "PYENV_ROOT" ~/.zshrc; then
           echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
           echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
       fi
       if ! grep -q "pyenv init" ~/.zshrc; then
           echo 'eval "$(pyenv init --path)"' >> ~/.zshrc
           echo 'eval "$(pyenv init -)"' >> ~/.zshrc
       fi
        source ~/.zshrc
    else
        # Linuxの場合はgitからインストール
        curl https://pyenv.run | bash
       # .bashrcのバックアップを作成
       cp ~/.bashrc ~/.bashrc.backup
       # 設定が存在しない場合のみ追加
       if ! grep -q "PYENV_ROOT" ~/.bashrc; then
           echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
           echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
       fi
       if ! grep -q "pyenv init" ~/.bashrc; then
           echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
           echo 'eval "$(pyenv init -)"' >> ~/.bashrc
       fi
        source ~/.bashrc
    fi
fi

# Python 3.12.9がインストールされているか確認
if ! pyenv versions | grep -q 3.12.9; then
    echo "Python 3.12.9がインストールされていません。インストールします..."
    pyenv install 3.12.9
fi

# プロジェクトディレクトリにPython 3.12.9を設定
echo "プロジェクトディレクトリにPython 3.12.9を設定します..."
pyenv local 3.12.9

# 現在のPythonバージョンを確認
python_version=$(python --version 2>&1)
echo "使用するPythonバージョン: $python_version"

# 仮想環境が存在する場合は削除
if [ -d "venv" ]; then
    echo "既存の仮想環境を削除します..."
    rm -rf venv
fi

# 仮想環境を作成
echo "Python 3.12.9で仮想環境を作成します..."
python -m venv venv

# 仮想環境をアクティベート
echo "仮想環境をアクティベートします..."
source venv/bin/activate

# pipとsetuptoolsを最新バージョンにアップグレード
echo "pipとsetuptoolsをアップグレードします..."
pip install --upgrade pip setuptools wheel

# MuPDFがインストールされているか確認（macOSの場合）
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "MuPDFの依存関係を確認します..."
    if ! brew list mupdf &> /dev/null; then
        echo "MuPDFをインストールします..."
        brew install mupdf
    else
        echo "MuPDFは既にインストールされています"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linuxでの依存関係を確認します..."
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        if ! dpkg -l | grep -q libmupdf-dev; then
            echo "MuPDFをインストールします（sudo権限が必要です）..."
            sudo apt-get update && sudo apt-get install -y libmupdf-dev
        else
            echo "MuPDFは既にインストールされています"
        fi
    elif [ -f /etc/redhat-release ]; then
        # Red Hat/Fedora
        if ! rpm -qa | grep -q mupdf-devel; then
            echo "MuPDFをインストールします（sudo権限が必要です）..."
            sudo dnf install -y mupdf-devel
        else
            echo "MuPDFは既にインストールされています"
        fi
    else
        echo "現在のLinuxディストリビューションは自動インストールに対応していません。"
        echo "必要に応じて手動でMuPDFをインストールしてください。"
    fi
fi

# 依存関係をインストール
echo "プロジェクトの依存関係をインストールします..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "依存関係のインストールに失敗しました。"
    echo ""
    echo "可能な解決策:"
    echo "1. PyMuPDFの問題の場合:"
    echo "   - macOS: brew install mupdf"
    echo "   - Ubuntu: apt-get install libmupdf-dev"
    echo "   - Windows: Microsoft Visual C++ Redistributableがインストールされていることを確認"
    echo "2. 問題のあるパッケージを個別にインストール:"
    echo "   - pip install PyMuPDF==1.23.26"
    echo ""
    exit 1
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

# セットアップ成功
echo ""
echo "セットアップが完了しました！"
echo ""
echo "仮想環境をアクティベートするには以下を実行してください:"
echo "    source venv/bin/activate"
echo ""
echo "開発サーバーを起動するには以下を実行してください:"
echo "    uvicorn app.main:app --reload"

# 仮想環境を終了
deactivate
