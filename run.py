#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def main():
    # Get the directory of this script
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to project directory
    os.chdir(project_dir)

    # Detect OS and set paths
    os_name = platform.system()
    
    if os_name == "Windows":
        venv_path = os.path.join(project_dir, "venv")
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:  # macOS and Linux
        venv_path = os.path.join(project_dir, "venv")
        activate_script = os.path.join(venv_path, "bin", "activate")
        python_path = os.path.join(venv_path, "bin", "python")

    journal_app = os.path.join(project_dir, "journal_app.py")

    # Check if venv exists
    if not os.path.exists(python_path):
        print("❌ Virtual environment not found!")
        print("   Please run setup.py first:")
        print()
        if os_name == "Windows":
            print("   python setup.py")
        else:
            print("   python3 setup.py")
        sys.exit(1)

    # Run streamlit with activated venv
    print("Starting AI Journal App...")
    print("Press Ctrl+C to stop the server")
    print()

    try:
        if os_name == "Windows":
            # On Windows, we need to run activate.bat first
            process = subprocess.Popen(
                f'"{activate_script}" && "{python_path}" -m streamlit run "{journal_app}"',
                shell=True
            )
            process.wait()
        else:
            # On Unix systems, source the activate script
            process = subprocess.Popen(
                f'source "{activate_script}" && "{python_path}" -m streamlit run "{journal_app}"',
                shell=True,
                executable='/bin/bash'
            )
            process.wait()
    except KeyboardInterrupt:
        print("\n\nApp stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()