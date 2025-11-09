#!/usr/bin/env python3
"""
Cross-platform setup script for AI Journal App
Works on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform

def run_command(command, shell=False):
    """Run a command and return success status"""
    try:
        subprocess.run(command, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=" * 50)
    print("AI Journal App - Cross-Platform Setup")
    print("=" * 50)
    print()
    
    # Detect OS
    os_name = platform.system()
    print(f"Detected OS: {os_name}")
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    print()
    
    # Step 1: Check if virtual environment already exists
    venv_exists = os.path.exists("venv")
    
    if venv_exists:
        print("Step 1: Virtual environment already exists")
        print("✅ Skipping venv creation")
    else:
        print("Step 1: Creating virtual environment...")
        venv_command = [sys.executable, "-m", "venv", "venv"]
        if run_command(venv_command):
            print("✅ Virtual environment created successfully")
        else:
            print("❌ Failed to create virtual environment")
            sys.exit(1)
    print()
    
    # Step 2: Determine activation script path
    if os_name == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:  # macOS and Linux
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    # Step 3: Upgrade pip
    print("Step 2: Upgrading pip...")
    upgrade_command = [python_path, "-m", "pip", "install", "--upgrade", "pip"]
    if run_command(upgrade_command):
        print("✅ Pip upgraded successfully")
    else:
        print("⚠️  Warning: Could not upgrade pip (continuing anyway)")
    print()
    
    # Step 4: Install requirements
    print("Step 3: Installing dependencies...")
    install_command = [pip_path, "install", "-r", "requirements.txt"]
    if run_command(install_command):
        print("✅ Dependencies installed successfully")
    else:
        print("❌ Failed to install dependencies")
        sys.exit(1)
    print()
    
    # Success message with OS-specific instructions
    print("=" * 50)
    print("✨ Setup completed successfully!")
    print("=" * 50)
    print()
    print("To run the app:")
    print()
    
    if os_name == "Windows":
        print("  python run.py")
    else:
        print("  python3 run.py")
    
    print()
    print("Make sure your .env file contains:")
    print("  GOOGLE_API_KEY=your_api_key_here")
    print()

if __name__ == "__main__":
    main()