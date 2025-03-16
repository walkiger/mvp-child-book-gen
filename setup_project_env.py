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
import re
import argparse
import time
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
VENV_DIR = '.venv'
ALEMBIC_DIR = 'alembic'
FRONTEND_DIR = 'frontend'
MIN_PYTHON_VERSION = (3, 8)  # Minimum Python version required
PIP_TIMEOUT = 300  # Timeout for pip commands in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed commands

# Key packages to verify after installation
KEY_PACKAGES = ['fastapi', 'sqlalchemy', 'alembic', 'openai', 'pydantic']

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Set up project environment")
    parser.add_argument("--force-venv", action="store_true", 
                       help="Force recreation of virtual environment even if it exists")
    parser.add_argument("--python", type=str, 
                       help=f"Path to specific Python interpreter to use (default: {sys.executable})")
    parser.add_argument("--skip-frontend", action="store_true",
                       help="Skip frontend dependencies installation")
    parser.add_argument("--skip-venv-activate", action="store_true",
                       help="Skip virtual environment activation")
    parser.add_argument("--update-dependencies", action="store_true",
                       help="Update all dependencies to their latest versions")
    parser.add_argument("--dev", action="store_true",
                       help="Install development dependencies")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    return parser.parse_args()

def run_command(cmd: List[str], desc: Optional[str] = None, check: bool = True, 
               cwd: Optional[str] = None, timeout: Optional[int] = None, 
               retries: int = 0) -> subprocess.CompletedProcess:
    """Run a shell command with retries and timeout"""
    if desc:
        print(f"{desc}...")
    
    last_error = None
    for attempt in range(retries + 1):
        if attempt > 0:
            print(f"Retry attempt {attempt}/{retries}...")
            time.sleep(2 ** attempt)  # Exponential backoff
        
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=False,  # We'll handle the check ourselves
                cwd=cwd,
                timeout=timeout
            )
            
            if result.returncode == 0 or attempt == retries:
                if result.returncode != 0 and check:
                    logger.error(f"Command failed: {' '.join(cmd)}")
                    logger.error(f"Error output: {result.stderr}")
                    sys.exit(1)
                return result
            
            last_error = result.stderr
            logger.warning(f"Command failed (attempt {attempt + 1}): {last_error}")
            
        except subprocess.TimeoutExpired:
            last_error = f"Command timed out after {timeout} seconds"
            logger.warning(f"Timeout (attempt {attempt + 1}): {last_error}")
            if attempt == retries:
                if check:
                    print(f"Command failed: {last_error}")
                    sys.exit(1)
                return subprocess.CompletedProcess(cmd, -1, "", last_error)
    
    # This should never be reached due to the returns above
    raise RuntimeError("Unexpected control flow in run_command")

def get_python_version(python_executable=None):
    """Get the Python version of the given executable"""
    if not python_executable:
        python_executable = sys.executable
    
    try:
        result = run_command([python_executable, '--version'], check=False)
        if result.returncode == 0:
            # Parse version string like "Python 3.10.0"
            version_str = result.stdout.strip() or result.stderr.strip()
            match = re.search(r'Python (\d+)\.(\d+)\.(\d+)', version_str)
            if match:
                return tuple(map(int, match.groups()))
    except Exception:
        pass
    
    return None

def check_python_compatibility(python_executable=None):
    """Check if Python version is compatible with project requirements"""
    version = get_python_version(python_executable)
    
    if not version:
        print("❌ Could not determine Python version")
        return False
    
    print(f"✓ Found Python {'.'.join(map(str, version))}")
    
    if version < MIN_PYTHON_VERSION:
        print(f"❌ Python {'.'.join(map(str, MIN_PYTHON_VERSION))} or higher is required")
        return False
    
    return True

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

def get_venv_activate():
    """Get the path to the activate script in the virtual environment"""
    if platform.system() == 'Windows':
        return os.path.join(VENV_DIR, 'Scripts', 'activate.bat')
    return os.path.join(VENV_DIR, 'bin', 'activate')

def setup_virtualenv(force_recreate=False, python_path=None):
    """Set up a virtual environment if one doesn't exist or if forced to recreate"""
    # Use specified Python or system Python
    python_executable = python_path or sys.executable
    
    # Check Python compatibility
    if not check_python_compatibility(python_executable):
        print(f"⚠️ WARNING: Your Python version may not be compatible with this project")
        choice = input("Continue anyway? (y/n): ").lower().strip()
        if choice != 'y':
            sys.exit(1)
    
    # Check if venv exists and is valid
    venv_exists = os.path.exists(VENV_DIR)
    venv_python_exists = os.path.exists(get_venv_python())
    venv_is_valid = venv_exists and venv_python_exists
    
    # Determine if we need to create/recreate the venv
    create_venv = False
    if not venv_is_valid:
        if venv_exists and not venv_python_exists:
            print(f"⚠️ Virtual environment at {VENV_DIR} appears to be corrupted")
            create_venv = True
        elif not venv_exists:
            create_venv = True
    elif force_recreate:
        print(f"Forcing recreation of virtual environment at {VENV_DIR}")
        create_venv = True
    
    # Create or recreate the venv if needed
    if create_venv:
        if venv_exists:
            print(f"Removing existing virtual environment at {VENV_DIR}")
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        
        print(f"Creating virtual environment in {VENV_DIR}...")
        result = run_command([python_executable, '-m', 'venv', VENV_DIR], check=False)
        
        if result.returncode != 0:
            print("❌ Failed to create virtual environment")
            print(f"Error: {result.stderr}")
            print("\nTrying with the 'virtualenv' package as a fallback...")
            
            # Try using virtualenv as a fallback
            try:
                run_command([python_executable, '-m', 'pip', 'install', 'virtualenv'], 
                          "Installing virtualenv", check=False)
                run_command([python_executable, '-m', 'virtualenv', VENV_DIR], 
                          "Creating virtual environment with virtualenv")
            except Exception as e:
                print(f"❌ Failed to create virtual environment with virtualenv: {str(e)}")
                print("Please install virtualenv manually with: pip install virtualenv")
                sys.exit(1)
    else:
        print(f"✓ Virtual environment already exists in {VENV_DIR}")
    
    # Verify the virtual environment was created successfully
    if not os.path.exists(get_venv_python()):
        print(f"❌ Virtual environment creation failed - Python interpreter not found at {get_venv_python()}")
        sys.exit(1)
    
    return True

def is_venv_activated():
    """Check if a virtual environment is currently activated using multiple methods"""
    # Method 1: Check VIRTUAL_ENV environment variable
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"✓ Virtual environment detected via VIRTUAL_ENV: {venv_path}")
        return True
    
    # Method 2: Check sys.prefix vs. sys.base_prefix
    if hasattr(sys, 'real_prefix'):
        print(f"✓ Virtual environment detected via sys.real_prefix")
        return True
    
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        print(f"✓ Virtual environment detected via sys.base_prefix")
        return True
    
    print("❌ No virtual environment is currently activated")
    print("Activation status checks:")
    print(f"  • VIRTUAL_ENV env variable: {'set' if venv_path else 'not set'}")
    print(f"  • sys.real_prefix: {'exists' if hasattr(sys, 'real_prefix') else 'not found'}")
    print(f"  • sys.base_prefix != sys.prefix: {'true' if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix else 'false'}")
    return False

def is_correct_venv_activated():
    """Check if the correct virtual environment is activated"""
    if not is_venv_activated():
        return False
    
    # Get the absolute paths for comparison
    active_venv = os.path.normpath(os.environ.get('VIRTUAL_ENV', ''))
    expected_venv = os.path.normpath(os.path.abspath(VENV_DIR))
    
    # Compare the normalized paths
    is_correct = active_venv.lower() == expected_venv.lower()
    
    if is_correct:
        print(f"✓ Correct virtual environment is activated: {active_venv}")
    else:
        print("❌ Wrong virtual environment is activated")
        print(f"  • Active: {active_venv}")
        print(f"  • Expected: {expected_venv}")
        print("\nTo fix this:")
        print("1. Deactivate the current environment: deactivate")
        print(f"2. Activate the correct environment: source {VENV_DIR}/bin/activate")
    
    return is_correct

def activate_virtualenv(skip_activation=False):
    """Activate the virtual environment in the current process"""
    if skip_activation:
        print("Skipping virtual environment activation as requested")
        return True
    
    # If the correct venv is already activated, skip
    if is_correct_venv_activated():
        return True
    
    activate_script = get_venv_activate()
    
    if not os.path.exists(activate_script):
        print(f"❌ Activation script not found at {activate_script}")
        return False
    
    print(f"Activating virtual environment from {activate_script}")
    
    # Set up environment variables for virtual environment
    bin_dir = os.path.dirname(get_venv_python())
    path_sep = ';' if platform.system() == 'Windows' else ':'
    os.environ['PATH'] = bin_dir + path_sep + os.environ.get('PATH', '')
    os.environ['VIRTUAL_ENV'] = os.path.abspath(VENV_DIR)
    
    # Update Python-specific environment
    sys.executable = get_venv_python()
    sys.prefix = os.path.abspath(VENV_DIR)
    
    # Verify the activation was successful
    if is_correct_venv_activated():
        print("✓ Virtual environment activated successfully")
        return True
    else:
        print("⚠️ Virtual environment activation may not be complete")
        print("For full activation, run this command in your shell:")
        if platform.system() == 'Windows':
            print(f"   .\\{VENV_DIR}\\Scripts\\activate")
        else:
            print(f"   source {VENV_DIR}/bin/activate")
        return False

def validate_requirements_file(filename: str) -> Tuple[bool, List[str]]:
    """Validate a requirements file format and return any issues found"""
    if not os.path.exists(filename):
        return False, [f"File {filename} does not exist"]
    
    issues = []
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not lines:
            issues.append(f"WARNING: {filename} is empty")
            return True, issues
        
        for line in lines:
            # Check for basic package name format
            if not re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*', line):
                issues.append(f"Invalid package name format: {line}")
            
            # Check for direct GitHub/URL installations
            if any(s in line.lower() for s in ['git+', 'http://', 'https://']):
                issues.append(f"Note: Direct URL/Git installation found: {line}")
            
            # More permissive version specifier check that allows ranges and extras
            if '[' in line and ']' in line:
                # Handle package with extras like: package[extra]>=1.0
                base = line.split('[')[0]
                if not re.match(r'^[A-Za-z0-9][A-Za-z0-9._-]*$', base):
                    issues.append(f"Invalid package name format: {line}")
            
        return len(issues) == 0, issues
    
    except Exception as e:
        return False, [f"Error reading {filename}: {str(e)}"]

def verify_requirements_files():
    """Verify requirements files exist and are valid"""
    req_file = 'requirements.txt'
    dev_req_file = 'requirements-dev.txt'
    
    # Verify main requirements file
    valid, issues = validate_requirements_file(req_file)
    if not valid:
        print(f"❌ ERROR: Invalid {req_file}:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    
    if issues:  # Warnings but not errors
        print(f"⚠️ Warnings for {req_file}:")
        for issue in issues:
            print(f"  • {issue}")
    
    # Count packages in requirements.txt
    try:
        with open(req_file, 'r') as f:
            req_lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            num_packages = len(req_lines)
        print(f"✓ Found {req_file} with {num_packages} packages")
    except Exception as e:
        logger.error(f"Error reading {req_file}: {str(e)}")
        return False
    
    # Check dev requirements if present
    if os.path.exists(dev_req_file):
        valid, issues = validate_requirements_file(dev_req_file)
        if not valid:
            print(f"⚠️ Issues found in {dev_req_file} (development dependencies may not install correctly):")
            for issue in issues:
                print(f"  • {issue}")
        elif issues:
            print(f"ℹ️ Notes about {dev_req_file}:")
            for issue in issues:
                print(f"  • {issue}")
        
        try:
            with open(dev_req_file, 'r') as f:
                dev_lines = [line.strip() for line in f 
                           if line.strip() and not line.startswith('#') 
                           and not line.startswith('-r')]
                num_dev_packages = len(dev_lines)
            print(f"✓ Found {dev_req_file} with {num_dev_packages} additional development packages")
        except Exception as e:
            logger.warning(f"Error reading {dev_req_file}: {str(e)}")
    else:
        print(f"ℹ️ No {dev_req_file} found - development dependencies will not be installed")
    
    return True

def get_shell_type() -> str:
    """Detect the current shell type"""
    if platform.system() == 'Windows':
        return 'cmd' if os.environ.get('COMSPEC', '').endswith('cmd.exe') else 'powershell'
    
    shell = os.environ.get('SHELL', '').lower()
    if 'bash' in shell:
        return 'bash'
    elif 'zsh' in shell:
        return 'zsh'
    elif 'fish' in shell:
        return 'fish'
    return 'unknown'

def get_activation_command() -> str:
    """Get the appropriate activation command for the current shell"""
    shell = get_shell_type()
    venv_path = os.path.abspath(VENV_DIR)
    
    if platform.system() == 'Windows':
        if shell == 'powershell':
            return f".\\{VENV_DIR}\\Scripts\\Activate.ps1"
        return f".\\{VENV_DIR}\\Scripts\\activate.bat"
    
    # Unix-like systems
    activate_script = os.path.join(venv_path, 'bin', 'activate')
    if shell == 'fish':
        return f"source {activate_script}.fish"
    return f"source {activate_script}"

def install_dependencies(update=False, install_dev=False):
    """Install project dependencies from requirements.txt"""
    # Make sure we're running in a virtual environment
    if not is_venv_activated():
        print("❌ ERROR: No virtual environment is activated")
        print("Dependencies MUST be installed in a virtual environment.")
        print("Please activate the virtual environment using this command:")
        print(f"   {get_activation_command()}")
        return False
    
    # Verify requirements files exist and are valid
    if not verify_requirements_files():
        return False
    
    pip = get_venv_pip()
    
    # First, ensure setuptools is installed in the virtual environment
    print("\nEnsuring setuptools is available...")
    run_command(
        [pip, 'install', 'setuptools'],
        "Installing setuptools in virtual environment",
        timeout=PIP_TIMEOUT,
        retries=MAX_RETRIES
    )
    
    # Now proceed with rest of dependencies
    print("\n=== Installing Project Dependencies ===")
    
    # Ensure pip is up to date
    run_command(
        [pip, 'install', '--upgrade', 'pip'],
        "Upgrading pip",
        timeout=PIP_TIMEOUT,
        retries=MAX_RETRIES
    )
    
    # Install or update dependencies
    req_file = 'requirements.txt'
    
    # Determine install command
    cmd = [pip, 'install']
    if update:
        cmd.append('--upgrade')
    cmd.extend(['-r', req_file])
    
    # Install requirements with progress indication
    print("Installing dependencies (this may take a few minutes)...")
    start_time = time.time()
    result = run_command(
        cmd,
        f"{'Updating' if update else 'Installing'} dependencies",
        timeout=PIP_TIMEOUT,
        retries=MAX_RETRIES
    )
    
    elapsed_time = time.time() - start_time
    
    # Check for successful installation
    if result.returncode == 0:
        print(f"\n✅ Dependencies {'updated' if update else 'installed'} successfully")
        print(f"   Time taken: {elapsed_time:.1f} seconds")
        
        # Verify key packages with version information
        print("\nVerifying key package installations:")
        missing_packages = []
        
        # Use pip list to verify installations first
        pip_list = run_command([pip, 'list', '--format=json'], check=False)
        installed_packages = {}
        
        if pip_list.returncode == 0:
            try:
                import json
                installed_packages = {
                    pkg['name'].lower(): pkg['version'] 
                    for pkg in json.loads(pip_list.stdout)
                }
            except json.JSONDecodeError:
                print("  Could not parse pip list output")
        
        for package in KEY_PACKAGES:
            pkg_lower = package.lower()
            if pkg_lower in installed_packages:
                print(f"  ✓ {package} {installed_packages[pkg_lower]}")
                continue
            
            # Fallback to direct import if pip list didn't show it
            try:
                mod = importlib.import_module(package)
                version = getattr(mod, '__version__', None)
                if version:
                    print(f"  ✓ {package} {version}")
                else:
                    # Try to get version from module attributes
                    version = getattr(mod, 'VERSION', None)
                    if version:
                        print(f"  ✓ {package} {version}")
                    else:
                        print(f"  ✓ {package} (version unknown)")
            except ImportError as e:
                print(f"  ✗ {package}: Not found ({str(e)})")
                missing_packages.append(package)
            except Exception as e:
                logger.debug(f"Error checking {package}: {str(e)}")
                print(f"  ✗ {package}: Error checking version ({str(e)})")
                missing_packages.append(package)
        
        if missing_packages:
            print("\nThe following packages could not be verified:")
            for package in missing_packages:
                print(f"  • {package}")
            print("\nTry running with --update-dependencies if you experience issues.")
        
        # Install development dependencies if requested
        if install_dev:
            dev_req_file = 'requirements-dev.txt'
            if os.path.exists(dev_req_file):
                print("\n=== Installing Development Dependencies ===")
                dev_cmd = [pip, 'install']
                if update:
                    dev_cmd.append('--upgrade')
                dev_cmd.extend(['-r', dev_req_file])
                
                dev_result = run_command(
                    dev_cmd,
                    f"{'Updating' if update else 'Installing'} development dependencies",
                    timeout=PIP_TIMEOUT,
                    retries=MAX_RETRIES
                )
                
                if dev_result.returncode == 0:
                    print(f"\n✅ Development dependencies {'updated' if update else 'installed'} successfully")
                else:
                    print("\n❌ Some development dependencies may not have been installed correctly")
                    print("Try installing them manually with:")
                    print(f"   {pip} install -r {dev_req_file}")
            else:
                print(f"\nℹ️ {dev_req_file} not found. Skipping development dependencies.")
        
        return len(missing_packages) == 0
    else:
        print("\n❌ Some dependencies may not have been installed correctly")
        print("Error details:")
        print(result.stderr)
        print("\nPossible solutions:")
        print("1. Try running with --update-dependencies to resolve conflicts")
        print("2. Check your internet connection")
        print("3. Try installing problematic packages individually")
        print("4. Check the requirements.txt file for invalid entries")
        return False

def check_outdated_packages():
    """Check for outdated packages and suggest updates"""
    if not is_venv_activated():
        print("❌ Cannot check for outdated packages: No virtual environment is activated")
        return False
    
    pip = get_venv_pip()
    
    print("Checking for outdated packages...")
    result = run_command([pip, 'list', '--outdated', '--format=json'], check=False)
    
    if result.returncode != 0:
        print(f"❌ Failed to check for outdated packages: {result.stderr}")
        return False
    
    try:
        import json
        outdated = json.loads(result.stdout)
        
        if outdated:
            print(f"\nFound {len(outdated)} outdated packages:")
            for pkg in outdated:
                print(f"  • {pkg['name']} {pkg['version']} → {pkg['latest_version']}")
            
            print("\nYou can update all packages with: --update-dependencies")
        else:
            print("✓ All packages are up to date.")
        
        return True
    except Exception as e:
        print(f"❌ Error parsing outdated packages: {str(e)}")
        return False

def setup_alembic():
    """Set up Alembic for database migrations"""
    python = get_venv_python()
    
    if os.path.exists(ALEMBIC_DIR):
        print(f"✓ Alembic directory already exists in {ALEMBIC_DIR}")
        return True
    
    # Initialize Alembic
    print("Setting up Alembic for database migrations...")
    try:
        # Initialize Alembic
        result = run_command(
            [python, '-m', 'alembic', 'init', ALEMBIC_DIR],
            timeout=PIP_TIMEOUT,
            retries=1
        )
        
        if result.returncode != 0:
            print("❌ Failed to initialize Alembic")
            print(f"Error: {result.stderr}")
            return False
        
        # Update configurations
        if not update_alembic_config():
            return False
        
        if not update_alembic_env():
            return False
        
        print("✅ Alembic setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up Alembic: {str(e)}")
        print("❌ Failed to set up Alembic")
        print("You can try setting up Alembic manually with:")
        print(f"1. {python} -m alembic init {ALEMBIC_DIR}")
        print("2. Update alembic.ini with your database URL")
        print("3. Update env.py with your models")
        return False

def update_alembic_config():
    """Update the Alembic configuration file"""
    alembic_ini = 'alembic.ini'
    
    if not os.path.exists(alembic_ini):
        print(f"❌ {alembic_ini} not found!")
        return False
    
    print(f"Updating {alembic_ini}...")
    
    try:
        # Read the file
        with open(alembic_ini, 'r') as f:
            lines = f.readlines()
        
        # Update the SQLAlchemy URL
        updated_lines = []
        url_updated = False
        for line in lines:
            if line.startswith('sqlalchemy.url ='):
                updated_lines.append('sqlalchemy.url = sqlite:///storybook.db\n')
                url_updated = True
            else:
                updated_lines.append(line)
        
        if not url_updated:
            print(f"⚠️ Could not find sqlalchemy.url in {alembic_ini}")
            return False
        
        # Write back to the file
        with open(alembic_ini, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✓ Updated database URL in {alembic_ini}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {alembic_ini}: {str(e)}")
        print(f"❌ Failed to update {alembic_ini}")
        print("You may need to manually set sqlalchemy.url = sqlite:///storybook.db")
        return False

def update_alembic_env():
    """Update the Alembic env.py file to use the project models"""
    env_py = os.path.join(ALEMBIC_DIR, 'env.py')
    
    if not os.path.exists(env_py):
        print(f"❌ {env_py} not found!")
        return False
    
    print(f"Updating {env_py}...")
    
    try:
        # Read the file
        with open(env_py, 'r') as f:
            content = f.read()
        
        # Add imports for the models
        import_section = "from app.database.models import Base\ntarget_metadata = Base.metadata\n"
        
        # Check if the import already exists
        if 'from app.database.models import Base' in content:
            print(f"✓ Models already imported in {env_py}")
            return True
        
        # Replace the target_metadata = None line
        if 'target_metadata = None' not in content:
            print(f"⚠️ Could not find target_metadata = None in {env_py}")
            print("You may need to manually update the file to import your models")
            return False
        
        content = content.replace('target_metadata = None', import_section)
        
        # Write back to the file
        with open(env_py, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated model imports in {env_py}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {env_py}: {str(e)}")
        print(f"❌ Failed to update {env_py}")
        print("You may need to manually import your models and set target_metadata")
        return False

def setup_environment():
    """Set up environment variables automatically"""
    env_path = os.path.join(os.path.abspath('.'), '.env')
    
    # Check if .env already exists
    if os.path.exists(env_path):
        print(f"✓ Environment variables: .env file already exists at {env_path}")
        print("Using existing environment configuration.")
        return True
    
    print("Setting up environment variables...")
    
    try:
        # Add the current directory to the Python path
        sys.path.insert(0, os.path.abspath('.'))
        
        # Try to import auto_setup_environment directly
        try:
            from management.env_commands import auto_setup_environment
            auto_setup_environment()
            if os.path.exists(env_path):
                print("✅ Environment variables set up successfully")
                return True
        except (ImportError, AttributeError) as e:
            logger.debug(f"Could not import auto_setup_environment: {str(e)}")
            # If direct import fails, run the command
            python = get_venv_python()
            result = run_command(
                [python, 'manage.py', 'env', 'setup', '--auto'],
                "Running env setup with --auto flag",
                timeout=30,
                retries=1
            )
            
            if result.returncode == 0 and os.path.exists(env_path):
                print("✅ Environment variables set up successfully")
                return True
            else:
                raise Exception(f"Command failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"Error setting up environment variables: {str(e)}")
        print("❌ Failed to set up environment variables automatically")
        print("You can set up environment variables manually by:")
        print("1. Copy .env.example to .env (if it exists)")
        print("2. Run: python manage.py env setup --auto")
        print("3. Or manually edit .env with your configuration")
        return False

# Add functions for frontend setup
def check_node_npm():
    """Check if Node.js and npm are installed and return version information"""
    try:
        # Check Node.js version
        node_result = run_command(['node', '--version'], check=False)
        npm_result = run_command(['npm', '--version'], check=False)
        
        node_version = node_result.stdout.strip() if node_result.returncode == 0 else None
        npm_version = npm_result.stdout.strip() if npm_result.returncode == 0 else None
        
        if node_version and npm_version:
            print(f"✓ Found Node.js {node_version} and npm {npm_version}")
            
            # Check minimum versions (adjust these as needed)
            node_ver = tuple(map(int, node_version.lstrip('v').split('.')))
            npm_ver = tuple(map(int, npm_version.split('.')))
            
            if node_ver < (14, 0, 0):  # Example minimum version
                print("⚠️ WARNING: Node.js version 14 or higher is recommended")
            if npm_ver < (6, 0, 0):    # Example minimum version
                print("⚠️ WARNING: npm version 6 or higher is recommended")
            
            return True
        else:
            missing = []
            if not node_version:
                missing.append("Node.js")
            if not npm_version:
                missing.append("npm")
            
            print(f"❌ Missing required tools: {', '.join(missing)}")
            print("\nTo install Node.js and npm:")
            print("1. Visit https://nodejs.org/")
            print("2. Download and install the LTS version")
            print("3. Restart your terminal after installation")
            return False
            
    except Exception as e:
        logger.error(f"Error checking Node.js and npm: {str(e)}")
        print("❌ Could not verify Node.js and npm installation")
        print("Please ensure Node.js and npm are installed and in your PATH")
        return False

def install_frontend_dependencies():
    """Install frontend dependencies using npm"""
    # Check if frontend directory exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"❌ Frontend directory '{FRONTEND_DIR}' not found")
        print(f"Please ensure the {FRONTEND_DIR} directory exists and contains a package.json file")
        return False
    
    # Check for package.json
    package_json = os.path.join(FRONTEND_DIR, 'package.json')
    if not os.path.exists(package_json):
        print(f"❌ package.json not found in {FRONTEND_DIR} directory")
        print("Please ensure your frontend project is properly initialized")
        return False
    
    # Check node and npm first
    if not check_node_npm():
        return False
    
    print("\n=== Installing Frontend Dependencies ===")
    print(f"Setting up React application in {FRONTEND_DIR}/")
    
    try:
        # Clean install to ensure consistent dependencies
        print("Running clean install of dependencies...")
        start_time = time.time()
        
        # First, try with clean install
        result = run_command(
            ['npm', 'ci'],
            "Installing npm packages (clean install)",
            cwd=FRONTEND_DIR,
            timeout=300,  # 5 minutes timeout
            retries=1,
            check=False
        )
        
        # If ci fails, fall back to regular install
        if result.returncode != 0:
            print("Clean install failed, falling back to regular install...")
            result = run_command(
                ['npm', 'install'],
                "Installing npm packages",
                cwd=FRONTEND_DIR,
                timeout=300,
                retries=2
            )
        
        elapsed_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ Frontend dependencies installed successfully")
            print(f"   Time taken: {elapsed_time:.1f} seconds")
            
            # Verify key frontend packages
            try:
                with open(package_json, 'r') as f:
                    import json
                    pkg_data = json.load(f)
                    deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                    
                    print("\nKey frontend packages:")
                    for pkg in ['react', 'react-dom', '@types/react']:
                        version = deps.get(pkg, 'not found')
                        print(f"  {'✓' if version != 'not found' else '✗'} {pkg}: {version}")
            except Exception as e:
                logger.warning(f"Could not verify frontend packages: {str(e)}")
            
            return True
        else:
            print("\n❌ Failed to install frontend dependencies")
            print("Error details:")
            print(result.stderr)
            print("\nPossible solutions:")
            print("1. Clear npm cache: npm cache clean --force")
            print("2. Delete node_modules and package-lock.json")
            print("3. Try installing packages individually")
            print("4. Check your internet connection")
            return False
            
    except Exception as e:
        logger.error(f"Error installing frontend dependencies: {str(e)}")
        print("\n❌ Error during frontend setup")
        print("Try the following:")
        print(f"1. cd {FRONTEND_DIR}")
        print("2. Delete node_modules directory")
        print("3. Delete package-lock.json")
        print("4. Run: npm install")
        return False

def main():
    """Main entry point to set up the project environment"""
    # Parse command line arguments
    args = parse_args()
    
    print("===== Child Book Generator Project Setup =====")
    print("This script will set up your development environment.")
    
    # Track setup status
    setup_status = {
        "virtualenv": False,
        "virtualenv_activated": False,
        "backend_dependencies": False,
        "frontend_dependencies": False,
        "alembic": False,
        "env_file": False
    }
    
    # Step 1: Set up virtual environment
    print("\n[1/5] Setting up virtual environment...")
    setup_status["virtualenv"] = setup_virtualenv(
        force_recreate=args.force_venv,
        python_path=args.python
    )
    
    if not setup_status["virtualenv"]:
        print("❌ Virtual environment setup failed")
        print("Please fix the issues above and try again")
        return
    
    # Step 2: Activate the virtual environment
    print("\n[2/5] Activating virtual environment...")
    if args.skip_venv_activate:
        print("Skipping virtual environment activation as requested")
        setup_status["virtualenv_activated"] = True
    else:
        # Check if already activated
        if is_correct_venv_activated():
            setup_status["virtualenv_activated"] = True
        else:
            setup_status["virtualenv_activated"] = activate_virtualenv()
            
            if not setup_status["virtualenv_activated"]:
                print("\n⚠️ Virtual environment activation was not complete")
                print("You may need to activate it manually:")
                print(f"   source {VENV_DIR}/bin/activate")
                choice = input("Continue with setup anyway? (y/n): ").lower().strip()
                if choice != 'y':
                    return
    
    # Step 3: Install backend dependencies
    print("\n[3/5] Installing backend dependencies...")
    if setup_status["virtualenv_activated"]:
        setup_status["backend_dependencies"] = install_dependencies(
            update=args.update_dependencies,
            install_dev=args.dev
        )
    else:
        print("❌ Skipping dependency installation as virtual environment is not activated")
        print("Please activate the virtual environment and try again:")
        print(f"   source {VENV_DIR}/bin/activate")
        return
    
    # Step 4: Install frontend dependencies
    print("\n[4/5] Installing frontend dependencies...")
    if args.skip_frontend:
        print("Skipping frontend dependencies installation as requested")
        setup_status["frontend_dependencies"] = True
    else:
        setup_status["frontend_dependencies"] = install_frontend_dependencies()
    
    # Step 5: Set up database migrations
    print("\n[5/5] Setting up database migrations...")
    if setup_status["backend_dependencies"]:
        setup_alembic()
        setup_status["alembic"] = os.path.exists(ALEMBIC_DIR)
    else:
        print("❌ Skipping Alembic setup as backend dependency installation failed.")
    
    # Step 6: Set up environment variables
    print("\n[6/6] Setting up environment variables...")
    env_path = os.path.join(os.path.abspath('.'), '.env')
    env_exists_before = os.path.exists(env_path)
    setup_environment()
    setup_status["env_file"] = os.path.exists(env_path)
    
    # Check for outdated packages if dependencies were installed
    if setup_status["backend_dependencies"] and not args.update_dependencies:
        print("\n=== Checking for package updates ===")
        check_outdated_packages()
    
    # Print summary
    print("\n===== Setup Summary =====")
    print(f"✓ Virtual Environment: {'Created/Updated' if setup_status['virtualenv'] else 'Failed'}")
    print(f"✓ Virtual Environment Activation: {'Successful' if setup_status['virtualenv_activated'] else 'Failed'}")
    print(f"✓ Backend Dependencies: {'Updated' if args.update_dependencies and setup_status['backend_dependencies'] else 'Installed' if setup_status['backend_dependencies'] else 'Failed'}")
    print(f"✓ Frontend Dependencies: {'Installed' if setup_status['frontend_dependencies'] else 'Skipped' if args.skip_frontend else 'Failed'}")
    print(f"✓ Database Migrations: {'Configured' if setup_status['alembic'] else 'Failed'}")
    print(f"✓ Environment Variables: {'Created' if setup_status['env_file'] and not env_exists_before else 'Already exists' if setup_status['env_file'] else 'Failed'}")
    
    # Print next steps
    print("\n===== Next Steps =====")
    if not setup_status["virtualenv_activated"]:
        print("1. Activate the virtual environment:")
        print(f"   {get_activation_command()}")
    
    print(f"{'2' if not setup_status['virtualenv_activated'] else '1'}. Update your environment variables in .env (if needed)")
    print(f"{'3' if not setup_status['virtualenv_activated'] else '2'}. Initialize the database: python manage.py init-db")
    print(f"{'4' if not setup_status['virtualenv_activated'] else '3'}. Run migrations: python manage.py migrate")
    print(f"{'5' if not setup_status['virtualenv_activated'] else '4'}. Start the application: python manage.py start")
    
    # Print specific messages if any step failed
    if not all(setup_status.values()):
        print("\n⚠️ WARNING: Some setup steps failed. See the logs above for details.")
        
    if not setup_status["backend_dependencies"]:
        print("\n⚠️ To manually install backend dependencies:")
        print("1. Activate the virtual environment")
        print("2. Run: pip install -r requirements.txt")
        
    if not setup_status["frontend_dependencies"] and not args.skip_frontend:
        print("\n⚠️ To manually install frontend dependencies:")
        print(f"   cd {FRONTEND_DIR}")
        print("   npm install")

if __name__ == "__main__":
    main() 