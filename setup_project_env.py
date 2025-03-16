"""
Script to set up the project environment with:
1. Virtual environment (if not exists)
2. Project dependencies
3. Alembic configuration for database migrations
"""

import os
import subprocess
import sys
import shutil
import platform
from pathlib import Path

# Configuration
VENV_DIR = '.venv'
ALEMBIC_DIR = 'alembic'

def run_command(cmd, desc=None, check=True):
    """Run a shell command and print its status"""
    if desc:
        print(f"{desc}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    
    if result.returncode != 0:
        print(f"Command failed with error: {result.stderr}")
        if check:
            sys.exit(1)
    
    return result

def get_venv_python():
    """Get the path to the Python executable in the virtual environment"""
    if platform.system() == 'Windows':
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    return os.path.join(VENV_DIR, 'bin', 'python')

def get_venv_pip():
    """Get the path to the pip executable in the virtual environment"""
    if platform.system() == 'Windows':
        return os.path.join(VENV_DIR, 'Scripts', 'pip.exe')
    return os.path.join(VENV_DIR, 'bin', 'pip')

def setup_virtualenv():
    """Set up a virtual environment if one doesn't exist"""
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        run_command([sys.executable, '-m', 'venv', VENV_DIR])
    else:
        print(f"Virtual environment already exists in {VENV_DIR}")

def install_dependencies():
    """Install project dependencies from requirements.txt"""
    pip = get_venv_pip()
    
    # Ensure pip is up to date
    run_command([pip, 'install', '--upgrade', 'pip'], "Upgrading pip")
    
    # Install dependencies
    if os.path.exists('requirements.txt'):
        run_command([pip, 'install', '-r', 'requirements.txt'], "Installing dependencies")
    else:
        print("WARNING: requirements.txt not found!")

def setup_alembic():
    """Set up Alembic for database migrations"""
    python = get_venv_python()
    
    if os.path.exists(ALEMBIC_DIR):
        print(f"Alembic directory already exists in {ALEMBIC_DIR}")
        return
    
    # Initialize Alembic
    print("Setting up Alembic for database migrations...")
    run_command([python, '-m', 'alembic', 'init', ALEMBIC_DIR])
    
    # Update alembic.ini to use the project database
    update_alembic_config()
    
    # Update env.py to use the project models
    update_alembic_env()

def update_alembic_config():
    """Update the Alembic configuration file"""
    alembic_ini = 'alembic.ini'
    
    if not os.path.exists(alembic_ini):
        print(f"WARNING: {alembic_ini} not found!")
        return
    
    print(f"Updating {alembic_ini}...")
    
    # Read the file
    with open(alembic_ini, 'r') as f:
        lines = f.readlines()
    
    # Update the SQLAlchemy URL
    updated_lines = []
    for line in lines:
        if line.startswith('sqlalchemy.url ='):
            updated_lines.append('sqlalchemy.url = sqlite:///storybook.db\n')
        else:
            updated_lines.append(line)
    
    # Write back to the file
    with open(alembic_ini, 'w') as f:
        f.writelines(updated_lines)

def update_alembic_env():
    """Update the Alembic env.py file to use the project models"""
    env_py = os.path.join(ALEMBIC_DIR, 'env.py')
    
    if not os.path.exists(env_py):
        print(f"WARNING: {env_py} not found!")
        return
    
    print(f"Updating {env_py}...")
    
    # Read the file
    with open(env_py, 'r') as f:
        content = f.read()
    
    # Add imports for the models
    import_section = "from app.database.models import Base\ntarget_metadata = Base.metadata\n"
    
    # Replace the target_metadata = None line
    content = content.replace('target_metadata = None', import_section)
    
    # Write back to the file
    with open(env_py, 'w') as f:
        f.write(content)

def main():
    print("Setting up project environment...")
    
    setup_virtualenv()
    install_dependencies()
    setup_alembic()
    
    print("\nProject environment setup completed!")
    print("\nTo activate the virtual environment:")
    if platform.system() == 'Windows':
        print(f".\\{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"source {VENV_DIR}/bin/activate")

if __name__ == "__main__":
    main() 