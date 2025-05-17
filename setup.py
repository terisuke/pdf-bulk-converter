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
        print("Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_dir)
    
    print("Creating a new virtual environment with Python 3.11+...")
    try:
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
    except subprocess.CalledProcessError:
        print("Failed to create virtual environment")
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
    
    # Install dependencies
    print("Installing project dependencies...")
    try:
        subprocess.run([pip_path, "install", "-r", os.path.join(project_dir, "requirements.txt")], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        
        # Check for MuPDF installation
        print("\nChecking if MuPDF installation is required...")
        system = platform.system()
        if "PyMuPDF" in str(e):
            if system == "Darwin":  # macOS
                print("\nPyMuPDF installation failed. Please install MuPDF using:")
                print("    brew install mupdf")
                print("Then run this script again.")
            elif system == "Linux":
                print("\nPyMuPDF installation failed. Please install MuPDF using:")
                print("    apt-get install libmupdf-dev")
                print("    apt-get install libmupdf")
                print("Then run this script again.")
            elif system == "Windows":
                print("\nPyMuPDF installation failed on Windows.")
                print("Please ensure you have the Microsoft Visual C++ Redistributable installed.")
        sys.exit(1)
    
    # Setup successful
    print("\nSetup completed successfully!")
    print("\nTo activate the virtual environment, run:")
    if platform.system() == "Windows":
        print("    venv\\Scripts\\activate")
    else:
        print("    source venv/bin/activate")
    print("\nThen start the development server with:")
    print("    uvicorn app.main:app --reload")

if __name__ == "__main__":
    main()
