#!/usr/bin/env python3
import os
import subprocess
import sys
import platform

def main():
    """Set up the project environment and install dependencies."""
    
    print("PDF Bulk Converter Setup Script")
    print("===============================")
    
    # Check Python version
    python_version = sys.version_info
    print(f"Current Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor < 11:
        print("Error: This project requires Python 3.11 or higher")
        print("Please install Python 3.11+ and try again")
        sys.exit(1)
    
    # Directory where this script is located
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to virtual environment
    venv_dir = os.path.join(project_dir, "venv")
    
    # Check if venv exists and recreate it
    if os.path.exists(venv_dir):
        print("既存の仮想環境を削除しますか？ (y/n)")
        choice = input().lower()
        if choice == 'y':
            print("Removing existing virtual environment...")
            import shutil
            shutil.rmtree(venv_dir)
        else:
            print("バックアップを作成しますか？ (y/n)")
            backup_choice = input().lower()
            if backup_choice == 'y':
                print("Creating a backup of the existing virtual environment...")
                shutil.copytree(venv_dir, venv_dir + '_backup')
    
    print("Python 3.11+で新しい仮想環境を作成中...")
    try:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    except subprocess.CalledProcessError as e:
        print("仮想環境の作成に失敗しました。以下の手順を試してみてください:")
        print("1. Python 3.11+をインストールしてください。")
        print("2. 仮想環境を手動で作成してください。")
        print("3. 仮想環境の作成に失敗した場合は、バックアップから復元してください。")
        sys.exit(1)
    # Determine path to pip in the virtual environment
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_path = os.path.join(venv_dir, "bin", "pip")
    
    # Upgrade pip
    print("Upgrading pip...")
    try:
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError:
        print("Failed to upgrade pip")
        sys.exit(1)
    
    # 依存関係をインストール
    print("プロジェクトの依存関係をインストール中...")
    try:
        subprocess.run([pip_path, "install", "-r", os.path.join(project_dir, "requirements.txt")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"依存関係のインストールに失敗しました: {e}")
        
        # MuPDFのインストールが必要かどうかをチェック
        print("\nMuPDFのインストールが必要かどうかをチェック中...")
        system = platform.system()
        if "PyMuPDF" in str(e):
            if system == "Darwin":  # macOS
                print("\nPyMuPDFのインストールに失敗しました。MuPDFを以下の方法でインストールしてください:")
                print("    brew install mupdf")
                print("その後、このスクリプトを再実行してください。")
            elif system == "Linux":
                # Linuxディストリビューションを検出
                try:
                    with open('/etc/os-release', 'r') as f:
                        os_info = dict([line.strip().split('=', 1) for line in f if '=' in line])
                    distro = os_info.get('ID', '').lower()
                    
                    if distro in ['ubuntu', 'debian', 'linuxmint']:
                        print("\nPyMuPDFのインストールに失敗しました。MuPDFを以下の方法でインストールしてください:")
                        print("    apt-get install libmupdf-dev")
                        print("    apt-get install libmupdf")
                    elif distro in ['fedora', 'rhel', 'centos']:
                        print("\nPyMuPDFのインストールに失敗しました。MuPDFを以下の方法でインストールしてください:")
                        print("    dnf install mupdf-devel")
                    elif distro in ['arch', 'manjaro']:
                        print("\nPyMuPDFのインストールに失敗しました。MuPDFを以下の方法でインストールしてください:")
                        print("    pacman -S mupdf")
                    else:
                        print("\nPyMuPDFのインストールに失敗しました。MuPDFの開発ライブラリをシステムのパッケージマネージャーを使用してインストールしてください。")
                except:
                    print("\nPyMuPDFのインストールに失敗しました。MuPDFの開発ライブラリをシステムのパッケージマネージャーを使用してインストールしてください。")
                print("その後、このスクリプトを再実行してください。")
            elif system == "Windows":
                print("\nPyMuPDFのインストールに失敗しました。Windowsでは、")
                print("Microsoft Visual C++ Redistributableがインストールされていることを確認してください。")
        sys.exit(1)
    
    # セットアップ成功
    print("\nセットアップが正常に完了しました！")
    print("\n仮想環境をアクティブにするには、以下を実行してください:")
    if platform.system() == "Windows":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")
    print("\nその後、開発サーバーを以下のコマンドで開始してください:")
    print("    uvicorn app.main:app --reload")

print("\n注意: 環境変数の設定が必要な場合があります。")
print(".env.exampleファイルを.envにコピーして必要に応じて編集してください。")

if __name__ == "__main__":
    main()
