"""
Script to set up the project environment with:
1. Virtual environment (if not exists)
2. Project dependencies (backend and frontend)
3. Alembic configuration for database migrations
4. Environment variables (.env file)
"""

import os
import subprocess
import sys
import shutil
import platform
import importlib.util
from pathlib import Path

# Configuration
VENV_DIR = '.venv'
ALEMBIC_DIR = 'alembic'
FRONTEND_DIR = 'frontend'

def run_command(cmd, desc=None, check=True, cwd=None):
    """Run a shell command and print its status"""
    if desc:
        print(f"{desc}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=cwd)
    
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
        print("\n=== Installing Project Dependencies ===")
        
        # Count the number of packages in requirements.txt
        with open('requirements.txt', 'r') as f:
            req_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            num_packages = len(req_lines)
        
        print(f"Found {num_packages} packages to install in requirements.txt")
        
        # Install requirements
        result = run_command([pip, 'install', '-r', 'requirements.txt'], "Installing dependencies")
        
        # Check for successful installation
        if result.returncode == 0:
            print("\n✅ Dependencies installed successfully")
            
            # Verify key packages
            key_packages = ['fastapi', 'sqlalchemy', 'alembic', 'openai', 'pydantic']
            print("\nVerifying key package installations:")
            
            for package in key_packages:
                try:
                    # Try to import the package to verify it's installed
                    check_cmd = [get_venv_python(), '-c', f"import {package}; print('{package} installed successfully')"]
                    verify_result = run_command(check_cmd, check=False)
                    if verify_result.returncode == 0:
                        print(f"  ✓ {package}: {verify_result.stdout.strip()}")
                    else:
                        print(f"  ✗ {package}: Import failed, may not be installed correctly")
                except Exception as e:
                    print(f"  ✗ {package}: Verification error - {str(e)}")
        else:
            print("\n❌ Some dependencies may not have been installed correctly")
            print("You may need to manually install missing packages.")
    else:
        print("\n⚠️ WARNING: requirements.txt not found!")
        print("Dependencies were not installed. Please create a requirements.txt file and run this script again.")

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

def setup_environment():
    """Set up environment variables automatically"""
    # Check if .env already exists
    env_path = os.path.join(os.path.abspath('.'), '.env')
    if os.path.exists(env_path):
        print(f"Environment variables: .env file already exists at {env_path}")
        print("Using existing environment configuration.")
        return
    
    print("Setting up environment variables...")
    
    # Try to import the environment setup function
    try:
        # Add the current directory to the Python path
        sys.path.insert(0, os.path.abspath('.'))
        
        # Try to import auto_setup_environment directly
        try:
            from management.env_commands import auto_setup_environment
            auto_setup_environment()
        except (ImportError, AttributeError):
            # If direct import fails, run the command
            python = get_venv_python()
            run_command([python, 'manage.py', 'env', 'setup', '--auto'], "Running env setup with --auto flag")
    except Exception as e:
        print(f"ERROR setting up environment variables: {str(e)}")
        print("You can set up environment variables manually by running 'python manage.py env setup --auto'")

# Add functions for frontend setup
def check_node_npm():
    """Check if Node.js and npm are installed"""
    try:
        # Check Node.js version
        node_result = run_command(['node', '--version'], check=False)
        npm_result = run_command(['npm', '--version'], check=False)
        
        if node_result.returncode == 0 and npm_result.returncode == 0:
            print(f"✓ Node.js {node_result.stdout.strip()} and npm {npm_result.stdout.strip()} found")
            return True
        else:
            print("❌ Node.js or npm not found")
            print("Please install Node.js and npm from https://nodejs.org/")
            return False
    except Exception as e:
        print(f"Error checking Node.js and npm: {str(e)}")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies using npm"""
    # Check if frontend directory exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Frontend directory '{FRONTEND_DIR}' not found")
        return False
    
    # Check for package.json
    if not os.path.exists(os.path.join(FRONTEND_DIR, 'package.json')):
        print(f"❌ package.json not found in {FRONTEND_DIR} directory")
        return False
    
    # Check node and npm first
    if not check_node_npm():
        return False
    
    print("\n=== Installing Frontend Dependencies ===")
    print(f"Setting up React application in {FRONTEND_DIR}/")
    
    # Install dependencies
    try:
        # Run npm install in the frontend directory
        result = run_command(['npm', 'install'], "Installing npm packages", cwd=FRONTEND_DIR)
        
        if result.returncode == 0:
            print("\n✅ Frontend dependencies installed successfully")
            return True
        else:
            print("\n❌ Failed to install frontend dependencies")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"\n❌ Error installing frontend dependencies: {str(e)}")
        return False

def main():
    """Main entry point to set up the project environment"""
    print("===== Child Book Generator Project Setup =====")
    print("This script will set up your development environment.")
    
    # Track setup status
    setup_status = {
        "virtualenv": False,
        "backend_dependencies": False,
        "frontend_dependencies": False,
        "alembic": False,
        "env_file": False
    }
    
    print("\n[1/5] Setting up virtual environment...")
    setup_virtualenv()
    setup_status["virtualenv"] = os.path.exists(VENV_DIR)
    
    print("\n[2/5] Installing backend dependencies...")
    if setup_status["virtualenv"]:
        install_dependencies()
        # Consider it successful if we got this far
        setup_status["backend_dependencies"] = True
    else:
        print("Skipping dependency installation as virtual environment setup failed.")
    
    print("\n[3/5] Installing frontend dependencies...")
    setup_status["frontend_dependencies"] = install_frontend_dependencies()
    
    print("\n[4/5] Setting up database migrations...")
    if setup_status["backend_dependencies"]:
        setup_alembic()
        setup_status["alembic"] = os.path.exists(ALEMBIC_DIR)
    else:
        print("Skipping Alembic setup as backend dependency installation failed.")
    
    print("\n[5/5] Setting up environment variables...")
    env_path = os.path.join(os.path.abspath('.'), '.env')
    env_exists_before = os.path.exists(env_path)
    setup_environment()
    setup_status["env_file"] = os.path.exists(env_path)
    
    # Print summary
    print("\n===== Setup Summary =====")
    print(f"✓ Virtual Environment: {'Created' if setup_status['virtualenv'] and not os.path.exists(VENV_DIR) else 'Already exists' if setup_status['virtualenv'] else 'Failed'}")
    print(f"✓ Backend Dependencies: {'Installed' if setup_status['backend_dependencies'] else 'Failed'}")
    print(f"✓ Frontend Dependencies: {'Installed' if setup_status['frontend_dependencies'] else 'Failed'}")
    print(f"✓ Database Migrations: {'Configured' if setup_status['alembic'] else 'Failed'}")
    print(f"✓ Environment Variables: {'Created' if setup_status['env_file'] and not env_exists_before else 'Already exists' if setup_status['env_file'] else 'Failed'}")
    
    # Print next steps
    print("\n===== Next Steps =====")
    print("1. Activate the virtual environment:")
    if platform.system() == 'Windows':
        print(f"   .\\{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"   source {VENV_DIR}/bin/activate")
    
    print("2. Update your environment variables in .env (if needed)")
    print("3. Initialize the database: python manage.py init-db")
    print("4. Run migrations: python manage.py migrate")
    print("5. Start the application: python manage.py start")
    
    # Print specific messages if any step failed
    if not all(setup_status.values()):
        print("\n⚠️ WARNING: Some setup steps failed. See the logs above for details.")
        
    if not setup_status["frontend_dependencies"]:
        print("\n⚠️ To manually install frontend dependencies:")
        print(f"   cd {FRONTEND_DIR}")
        print("   npm install")

if __name__ == "__main__":
    main() 