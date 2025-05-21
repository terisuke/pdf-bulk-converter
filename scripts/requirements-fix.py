#!/usr/bin/env python3
"""
PDF Bulk Converter - Requirements Fix Script
This script helps install the project requirements with special handling for problematic packages.
"""

import os
import sys
import subprocess
import platform
import argparse

def check_python_version():
    """Check if the Python version is compatible with the project."""
    required_version = (3, 11)
    current_version = sys.version_info
    
    print(f"Current Python version: {current_version.major}.{current_version.minor}.{current_version.micro}")
    
    if current_version.major < required_version[0] or \
       (current_version.major == required_version[0] and current_version.minor < required_version[1]):
        print(f"Error: This project requires Python {required_version[0]}.{required_version[1]}+ but you have "
              f"Python {current_version.major}.{current_version.minor}.{current_version.micro}")
        return False
    
    return True

def install_mupdf():
    """Install MuPDF library based on the operating system."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        print("Installing MuPDF on macOS using Homebrew...")
        try:
            # Check if Homebrew is installed
            subprocess.run(["which", "brew"], check=True, capture_output=True)
            
            # Check if MuPDF is already installed
            result = subprocess.run(["brew", "list", "mupdf"], capture_output=True)
            if result.returncode == 0:
                print("MuPDF is already installed.")
                return True
            
            # Install MuPDF
            subprocess.run(["brew", "install", "mupdf"], check=True)
            print("MuPDF installed successfully.")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install MuPDF. Please install it manually:")
            print("    brew install mupdf")
            return False
    elif system == "Linux":
        # Try to determine the Linux distribution
        try:
            # Check if it's Debian/Ubuntu
            if os.path.exists("/etc/debian_version"):
                print("Installing MuPDF on Debian/Ubuntu...")
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "libmupdf-dev"], check=True)
                print("MuPDF installed successfully.")
                return True
            # Check if it's Red Hat/Fedora
            elif os.path.exists("/etc/redhat-release"):
                print("Installing MuPDF on Red Hat/Fedora...")
                subprocess.run(["sudo", "dnf", "install", "-y", "mupdf-devel"], check=True)
                print("MuPDF installed successfully.")
                return True
            else:
                print("Unsupported Linux distribution. Please install MuPDF manually.")
                return False
        except subprocess.CalledProcessError:
            print("Failed to install MuPDF. Please install it manually.")
            print("For Debian/Ubuntu: sudo apt-get install libmupdf-dev")
            print("For Red Hat/Fedora: sudo dnf install mupdf-devel")
            return False
    elif system == "Windows":
        print("On Windows, MuPDF dependencies are usually bundled with PyMuPDF.")
        print("If installation fails, ensure you have the Microsoft Visual C++ Redistributable installed.")
        return True
    else:
        print(f"Unsupported operating system: {system}")
        print("Please install MuPDF manually for your system.")
        return False

def install_requirements():
    """Install the project requirements."""
    print("\nInstalling base dependencies...")
    try:
        # Upgrade pip, setuptools, and wheel
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
        
        # First, try to install everything except PyMuPDF
        with open("../requirements.txt", "r") as f: # Corrected path
            requirements = f.read().splitlines()
        
        non_mupdf_requirements = [req for req in requirements if not req.startswith("PyMuPDF")]
        if non_mupdf_requirements:
            print("\nInstalling dependencies excluding PyMuPDF...")
            subprocess.run([sys.executable, "-m", "pip", "install"] + non_mupdf_requirements, check=True)
        
        # Now try to install PyMuPDF
        mupdf_requirements = [req for req in requirements if req.startswith("PyMuPDF")]
        if mupdf_requirements:
            print("\nInstalling PyMuPDF...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install"] + mupdf_requirements, check=True)
                print("PyMuPDF installed successfully.")
            except subprocess.CalledProcessError:
                print("\nPyMuPDF installation failed. Attempting to install system dependencies...")
                install_mupdf()
                
                print("\nRetrying PyMuPDF installation...")
                try:
                    subprocess.run([sys.executable, "-m", "pip", "install"] + mupdf_requirements, check=True)
                    print("PyMuPDF installed successfully after installing MuPDF.")
                except subprocess.CalledProcessError:
                    # Extract the version specifier from the mupdf_requirements list
                    version_specifier = mupdf_requirements[0].split("==")[1]
                    print(f"\nWarning: Failed to install PyMuPDF. You may need to install it manually.")
                    print(f"Try running: pip install PyMuPDF=={version_specifier}")
                    return False
        
        print("\nAll dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError: Failed to install dependencies: {e}")
        return False

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description="PDF Bulk Converter - Requirements Fix Script")
    parser.add_argument("--mupdf-only", action="store_true", help="Only install MuPDF system dependencies")
    args = parser.parse_args()
    
    print("PDF Bulk Converter - Requirements Fix Script")
    print("===========================================")
    
    if args.mupdf_only:
        print("Installing MuPDF system dependencies only...")
        install_mupdf()
        return
    
    if not check_python_version():
        sys.exit(1)
    
    if not install_requirements():
        sys.exit(1)
    
    print("\nSetup completed successfully!")
    print("You can now run the application using:")
    print("    uvicorn app.main:app --reload")

if __name__ == "__main__":
    main() 