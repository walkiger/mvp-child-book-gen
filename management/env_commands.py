"""
Environment variable management module for the Child Book Generator MVP.

This module helps create and manage the .env file with necessary environment variables,
and provides utilities for setting up the project environment.
"""

import os
import sys
import getpass
import subprocess
from pathlib import Path
import logging
import re
import datetime
import importlib.util
import shutil

from utils.error_handling import ConfigError, ErrorSeverity, BaseError, handle_error, setup_logger
from .errors import ProcessError, with_error_handling

# Setup logger
logger = setup_logger("management.env_commands", "logs/management.log")

# Constants
ENV_FILE = '.env'
ALEMBIC_VERSIONS_DIR = os.path.join('alembic', 'versions')
MIGRATIONS_DIR = os.path.join('app', 'database', 'migrations')

# Environment management functions
def check_env_file():
    """Check if .env file exists and return its path"""
    env_path = Path(ENV_FILE)
    return env_path.exists(), env_path

def read_env_variables():
    """Read existing environment variables from .env file"""
    env_vars = {}
    env_exists, env_path = check_env_file()
    
    if env_exists:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

def write_env_file(env_vars):
    """Write environment variables to .env file with organized sections and comments"""
    # Create a copy of the dictionary to avoid modifying the original
    env_copy = env_vars.copy()

    with open(ENV_FILE, 'w') as f:
        f.write("# Environment variables for Child Book Generator MVP\n\n")
        
        # OpenAI API Configuration section
        f.write("# OpenAI API Configuration\n")
        if 'OPENAI_API_KEY' in env_copy:
            f.write(f"OPENAI_API_KEY={env_copy['OPENAI_API_KEY']}\n")
            f.write("# Get your API key from https://platform.openai.com/api-keys\n\n")
        
        # Application Security section
        f.write("# Application Security\n")
        if 'SECRET_KEY' in env_copy:
            f.write(f"SECRET_KEY={env_copy['SECRET_KEY']}\n")
            f.write("# Use a strong, unique secret key for security\n")
        if 'ALGORITHM' in env_copy:
            f.write(f"ALGORITHM={env_copy['ALGORITHM']}\n")
        if 'ACCESS_TOKEN_EXPIRE_MINUTES' in env_copy:
            f.write(f"ACCESS_TOKEN_EXPIRE_MINUTES={env_copy['ACCESS_TOKEN_EXPIRE_MINUTES']}\n")
        f.write("\n")
        
        # Database Configuration section
        f.write("# Database Configuration\n")
        if 'DATABASE_NAME' in env_copy:
            f.write(f"DATABASE_NAME={env_copy['DATABASE_NAME']}\n")
        if 'DATABASE_DIR' in env_copy:
            f.write(f"DATABASE_DIR={env_copy['DATABASE_DIR']}\n")
        if 'DATABASE_URL' in env_copy:
            f.write(f"DATABASE_URL={env_copy['DATABASE_URL']}\n")
        f.write("\n")
        
        # CORS Configuration section
        f.write("# CORS Configuration\n")
        if 'ALLOWED_ORIGINS' in env_copy:
            f.write(f"ALLOWED_ORIGINS={env_copy['ALLOWED_ORIGINS']}\n")
        f.write("\n")
        
        # File Storage section
        f.write("# File Storage\n")
        if 'UPLOAD_DIR' in env_copy:
            f.write(f"UPLOAD_DIR={env_copy['UPLOAD_DIR']}\n")
        if 'MAX_UPLOAD_SIZE' in env_copy:
            f.write(f"MAX_UPLOAD_SIZE={env_copy['MAX_UPLOAD_SIZE']}  # 5MB in bytes\n")
        f.write("\n")
        
        # Rate Limiting section
        f.write("# Rate Limiting\n")
        if 'CHAT_RATE_LIMIT_PER_MINUTE' in env_copy:
            f.write(f"CHAT_RATE_LIMIT_PER_MINUTE={env_copy['CHAT_RATE_LIMIT_PER_MINUTE']}\n")
        if 'IMAGE_RATE_LIMIT_PER_MINUTE' in env_copy:
            f.write(f"IMAGE_RATE_LIMIT_PER_MINUTE={env_copy['IMAGE_RATE_LIMIT_PER_MINUTE']}\n")
        if 'TOKEN_LIMIT_PER_MINUTE' in env_copy:
            f.write(f"TOKEN_LIMIT_PER_MINUTE={env_copy['TOKEN_LIMIT_PER_MINUTE']}\n")
        f.write("\n")
        
        # Other Settings section
        f.write("# Other Settings\n")
        if 'DALLE_DEFAULT_VERSION' in env_copy:
            f.write(f"DALLE_DEFAULT_VERSION={env_copy['DALLE_DEFAULT_VERSION']}\n")
        if 'LOG_LEVEL' in env_copy:
            f.write(f"LOG_LEVEL={env_copy['LOG_LEVEL']}\n")
        f.write("\n")
        
        # Any remaining variables
        remaining_keys = set(env_copy.keys()) - {
            'OPENAI_API_KEY', 'SECRET_KEY', 'ALGORITHM', 'ACCESS_TOKEN_EXPIRE_MINUTES',
            'DATABASE_NAME', 'DATABASE_DIR', 'DATABASE_URL', 'ALLOWED_ORIGINS',
            'UPLOAD_DIR', 'MAX_UPLOAD_SIZE', 'CHAT_RATE_LIMIT_PER_MINUTE',
            'IMAGE_RATE_LIMIT_PER_MINUTE', 'TOKEN_LIMIT_PER_MINUTE',
            'DALLE_DEFAULT_VERSION', 'LOG_LEVEL'
        }
        
        if remaining_keys:
            f.write("# Additional Settings\n")
            for key in remaining_keys:
                f.write(f"{key}={env_copy[key]}\n")
    
    logger.info(f"Environment variables saved to {ENV_FILE}")

def get_required_variables():
    """List of required environment variables with descriptions"""
    return {
        'OPENAI_API_KEY': 'Your OpenAI API key for accessing DALL-E',
        'DATABASE_URL': 'Database connection URL (e.g., sqlite:///./app.db)',
    }

def get_optional_variables():
    """List of optional environment variables with descriptions"""
    return {
        'DALLE_DEFAULT_VERSION': 'Default DALL-E version to use (dall-e-2 or dall-e-3)',
        'LOG_LEVEL': 'Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)',
        'FRONTEND_URL': 'URL of the frontend (for CORS settings)',
    }

@with_error_handling(context="auto_setup_environment")
def auto_setup_environment():
    """Setup environment variables automatically without user interaction"""
    print("Child Book Generator MVP - Automatic Environment Setup\n")
    
    # Check if .env already exists
    env_exists, env_path = check_env_file()
    if env_exists:
        print(f".env file already exists at {env_path.absolute()}")
        print("Using existing environment configuration.")
        print("To create a new .env file, delete the existing one first.")
        return read_env_variables()
    
    # Create a fresh .env file with default placeholder values
    print("Creating new .env file with default values...")
    default_env = {
        # OpenAI API Configuration
        'OPENAI_API_KEY': 'your-openai-api-key-here',
        
        # Application Security
        'SECRET_KEY': 'your-secure-secret-key-here',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        
        # Database Configuration
        'DATABASE_NAME': 'storybook.db',
        'DATABASE_DIR': '',
        
        # CORS Configuration
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:5173,http://localhost:3001',
        
        # File Storage
        'UPLOAD_DIR': 'uploads',
        'MAX_UPLOAD_SIZE': '5242880',  # 5MB in bytes
        
        # Rate Limiting
        'CHAT_RATE_LIMIT_PER_MINUTE': '5',
        'IMAGE_RATE_LIMIT_PER_MINUTE': '3',
        'TOKEN_LIMIT_PER_MINUTE': '20000',
        
        # Other Settings
        'DALLE_DEFAULT_VERSION': 'dall-e-3',
        'LOG_LEVEL': 'DEBUG',
    }
    
    # Write the environment file
    write_env_file(default_env)
    
    logger.info("Environment variables automatically set up")
    print("Environment variables automatically set up")
    print("\nNOTE: The .env file has been created with placeholder values for sensitive data.")
    print("      Please update the OPENAI_API_KEY and SECRET_KEY with your actual values before using the application.")
    return default_env

@with_error_handling(context="setup_environment")
def setup_environment(auto_mode=False):
    """Setup environment variables interactively or automatically"""
    if auto_mode:
        # In auto mode, check existing .env file but don't overwrite it
        env_exists, env_path = check_env_file()
        if env_exists:
            print("Setting up environment variables in automatic mode")
            print(f"Found existing .env file at {env_path.absolute()}")
            print("Using existing environment configuration.")
            print("To create a new .env file, delete the existing one first.")
            return read_env_variables()
        else:
            print("Setting up environment variables in automatic mode")
            print("No existing .env file found. Creating one with default values.")
            return auto_setup_environment()
        
    print("Child Book Generator MVP - Environment Setup\n")
    
    # Read existing environment variables
    env_vars = read_env_variables()
    env_exists, _ = check_env_file()
    
    if not env_exists:
        # If no .env file exists, create it automatically
        print("No .env file found. Creating with default values.")
        return auto_setup_environment()
        
    # If an .env file exists, show its contents and ask if the user wants to update it
    print(f"Found existing {ENV_FILE} file with the following variables:")
    for key in env_vars:
        value = env_vars[key]
        # Mask sensitive data
        if key in ['OPENAI_API_KEY', 'SECRET_KEY'] and len(value) > 3:
            masked_value = value[:3] + '*' * (len(value) - 3)
        else:
            masked_value = value
        print(f"  - {key}={masked_value}")
    
    # Ask user if they want to update the existing variables
    update = input("\nDo you want to update these variables? (y/n): ").strip().lower()
    if update != 'y':
        print("Keeping existing environment variables.")
        return env_vars
        
    # Ask if the user wants to start fresh (auto setup) or update existing values
    fresh_start = input("\nDo you want to start with a fresh configuration? (y/n): ").strip().lower()
    if fresh_start == 'y':
        print("Starting with fresh default configuration.")
        # Here we'll handle the special case of explicitly asking for a fresh start
        # First backup the old .env file
        backup_path = f"{ENV_FILE}.bak"
        print(f"Backing up existing {ENV_FILE} to {backup_path}")
        try:
            shutil.copy2(ENV_FILE, backup_path)
        except Exception as e:
            print(f"Warning: Could not create backup: {str(e)}")
        
        # Then remove the existing file to allow auto_setup_environment to create a new one
        try:
            os.remove(ENV_FILE)
        except Exception as e:
            print(f"Error: Could not remove existing {ENV_FILE}: {str(e)}")
            return env_vars
        
        return auto_setup_environment()
    
    # Update the existing variables interactively
    # Required variables
    print("\nSetting up required environment variables:")
    required_vars = get_required_variables()
    
    for key, description in required_vars.items():
        default = env_vars.get(key, '')
        masked_default = default[:3] + '*' * (len(default) - 3) if len(default) > 3 and key == 'OPENAI_API_KEY' else default
        
        if key == 'OPENAI_API_KEY':
            print(f"\n{key} - {description}")
            if default:
                keep_default = input(f"Current value exists. Keep it? (y/n): ").strip().lower()
                if keep_default == 'y':
                    continue
            value = getpass.getpass("Enter value (input will be hidden): ")
        else:
            prompt = f"\n{key} - {description}"
            if default:
                prompt += f" [current: {masked_default}]"
            prompt += ": "
            value = input(prompt).strip()
        
        if value:
            env_vars[key] = value
        elif not default:
            print(f"WARNING: No value provided for {key}")
    
    # Optional variables
    print("\nSetting up optional environment variables (press Enter to skip):")
    optional_vars = get_optional_variables()
    
    for key, description in optional_vars.items():
        default = env_vars.get(key, '')
        
        if key == 'DALLE_DEFAULT_VERSION' and not default:
            default = 'dall-e-3'
        
        prompt = f"\n{key} - {description}"
        if default:
            prompt += f" [current/default: {default}]"
        prompt += ": "
        
        value = input(prompt).strip()
        
        if value:
            env_vars[key] = value
        elif default and key not in env_vars:
            env_vars[key] = default
    
    # Write to .env file
    write_env_file(env_vars)
    print("Environment setup complete!")
    return env_vars

@with_error_handling(context="show_current_env")
def show_current_env():
    """Display current environment variables"""
    env_vars = read_env_variables()
    env_exists, _ = check_env_file()
    
    if not env_exists or not env_vars:
        print("No environment variables found. Run 'python manage.py env setup' to create them.")
        return
    
    print(f"\nCurrent environment variables in {ENV_FILE}:")
    for key, value in env_vars.items():
        if key == 'OPENAI_API_KEY':
            masked_value = value[:3] + '*' * (len(value) - 3) if len(value) > 3 else '***'
            print(f"  {key}={masked_value}")
        else:
            print(f"  {key}={value}")

# Project environment setup functions
def run_command(cmd, cwd=None, env=None):
    """Run a command and return the result"""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            env=env,
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command completed with exit code {result.returncode}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        raise ProcessError(f"Command failed: {' '.join(cmd)}", severity=ErrorSeverity.ERROR)

def get_venv_python():
    """Get the Python executable from the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join('venv', 'Scripts', 'python.exe')
    else:  # Unix-like
        return os.path.join('venv', 'bin', 'python')

def get_venv_pip():
    """Get the pip executable from the virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join('venv', 'Scripts', 'pip.exe')
    else:  # Unix-like
        return os.path.join('venv', 'bin', 'pip')

@with_error_handling(context="setup_virtualenv")
def setup_virtualenv():
    """Create a virtual environment if it doesn't exist"""
    if os.path.exists('venv'):
        print("Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        run_command([sys.executable, '-m', 'venv', 'venv'])
        print("Virtual environment created")
        return True
    except Exception as e:
        logger.error(f"Failed to create virtual environment: {str(e)}")
        print(f"Error: {str(e)}")
        return False

@with_error_handling(context="install_dependencies")
def install_dependencies():
    """Install project dependencies"""
    print("Installing dependencies...")
    
    pip = get_venv_pip()
    
    # Install requirements
    if os.path.exists('requirements.txt'):
        try:
            run_command([pip, 'install', '-r', 'requirements.txt'])
            print("Dependencies installed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to install dependencies: {str(e)}")
            print(f"Error: {str(e)}")
            return False
    else:
        error_msg = "requirements.txt file not found"
        logger.error(error_msg)
        print(f"Error: {error_msg}")
        return False

@with_error_handling(context="setup_alembic")
def setup_alembic():
    """Set up Alembic for database migrations"""
    print("Setting up Alembic for database migrations...")
    
    # Check if alembic is already set up
    if os.path.exists('alembic.ini') and os.path.exists('alembic'):
        print("Alembic is already set up")
        
        # Update config even if already set up
        update_alembic_config()
        update_alembic_env()
        return True
    
    # Initialize alembic
    python = get_venv_python()
    try:
        run_command([python, '-m', 'alembic', 'init', 'alembic'])
        print("Alembic initialized")
        
        # Update alembic configuration
        update_alembic_config()
        update_alembic_env()
        
        print("Alembic setup complete")
        return True
    except Exception as e:
        logger.error(f"Failed to set up Alembic: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def update_alembic_config():
    """Update alembic.ini with project-specific settings"""
    print("Updating Alembic configuration...")
    
    config_path = 'alembic.ini'
    
    # Read the current config
    with open(config_path, 'r') as f:
        config_lines = f.readlines()
    
    # Update the config
    for i, line in enumerate(config_lines):
        # Update sqlalchemy.url line
        if line.startswith('sqlalchemy.url ='):
            # Read from .env file if available
            env_vars = read_env_variables()
            db_url = env_vars.get('DATABASE_URL', 'sqlite:///./storybook.db')
            config_lines[i] = f'sqlalchemy.url = {db_url}\n'
    
    # Write the updated config
    with open(config_path, 'w') as f:
        f.writelines(config_lines)
    
    print("Alembic configuration updated")

def update_alembic_env():
    """Update alembic/env.py with project-specific settings"""
    print("Updating Alembic environment...")
    
    env_path = os.path.join('alembic', 'env.py')
    
    # Read the current env.py
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Update import section to include models
    import_section = """
# Import models to ensure they're registered with the metadata
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import all models
from app.database.models import *
"""
    
    # Add import section after the imports
    if 'from app.database.models import' not in env_content:
        env_content = env_content.replace(
            'from alembic import context',
            'from alembic import context\n' + import_section
        )
    
    # Update run_migrations_online function to support SQLite
    if 'render_as_batch=True' not in env_content:
        env_content = env_content.replace(
            'with context.begin_transaction():',
            '    with context.begin_transaction():\n'
            '        context.run_migrations()'
        )
        
        env_content = env_content.replace(
            'def run_migrations_online():',
            'def run_migrations_online():\n'
            '    # Add batch support for SQLite\n'
            '    is_sqlite = config.get_main_option("sqlalchemy.url").startswith("sqlite")\n'
            '    if is_sqlite:\n'
            '        connectable = engine_from_config(\n'
            '            config.get_section(config.config_ini_section),\n'
            '            prefix="sqlalchemy.",\n'
            '            poolclass=pool.NullPool,\n'
            '        )\n'
            '        with connectable.connect() as connection:\n'
            '            context.configure(\n'
            '                connection=connection,\n'
            '                target_metadata=target_metadata,\n'
            '                process_revision_directives=process_revision_directives,\n'
            '                **current_app.extensions[\'migrate\'].configure_args,\n'
            '                render_as_batch=True\n'
            '            )\n'
            '            with context.begin_transaction():\n'
            '                context.run_migrations()\n'
            '        return'
        )
    
    # Write the updated env.py
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("Alembic environment updated")

@with_error_handling(context="setup_project")
def setup_project():
    """Set up the project environment"""
    print("Setting up project environment...\n")
    
    success = True
    
    # Create virtual environment
    if not setup_virtualenv():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Set up Alembic
    if success and not setup_alembic():
        success = False
    
    if success:
        print("\nProject environment setup complete!")
        print("\nNext steps:")
        print("1. Initialize the database: python manage.py init-db")
        print("2. Run migrations: python manage.py migrate")
        print("3. Start the application: python manage.py start")
    else:
        print("\nProject environment setup failed. Check the errors above.")

# Migration integration functions
def ensure_alembic_setup():
    """Ensure Alembic is set up correctly"""
    if not os.path.exists(ALEMBIC_VERSIONS_DIR):
        error_msg = f"Alembic versions directory not found at {ALEMBIC_VERSIONS_DIR}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}")
        print("Please run 'python manage.py setup-project' first to set up Alembic")
        return False
    return True

def get_existing_migrations():
    """Get list of existing migrations from the app/database/migrations directory"""
    if not os.path.exists(MIGRATIONS_DIR):
        logger.info(f"No existing migrations found in {MIGRATIONS_DIR}")
        print(f"No existing migrations found in {MIGRATIONS_DIR}")
        return []
    
    migration_files = [f for f in os.listdir(MIGRATIONS_DIR) 
                      if f.endswith('.py') and f != '__init__.py']
    
    return sorted(migration_files)

def extract_timestamp_from_migration(filename):
    """Extract timestamp from migration filename if possible"""
    match = re.search(r'migration_(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            hour = int(time_str[:2])
            minute = int(time_str[2:4])
            second = int(time_str[4:6])
            return datetime.datetime(year, month, day, hour, minute, second)
        except ValueError:
            pass
    
    # If no valid timestamp found, use file creation time
    file_path = os.path.join(MIGRATIONS_DIR, filename)
    file_ctime = os.path.getctime(file_path)
    return datetime.datetime.fromtimestamp(file_ctime)

def generate_alembic_version_for_migration(migration_file, timestamp):
    """Generate an Alembic version file for an existing migration"""
    # Generate a unique revision ID
    revision_id = timestamp.strftime('%Y%m%d%H%M%S')
    
    # Load the migration module to get its content
    migration_path = os.path.join(MIGRATIONS_DIR, migration_file)
    module_name = f"app.database.migrations.{migration_file[:-3]}"
    
    spec = importlib.util.spec_from_file_location(module_name, migration_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    # Extract upgrade and downgrade functions
    has_upgrade = hasattr(migration_module, 'upgrade')
    has_downgrade = hasattr(migration_module, 'downgrade')
    
    if not has_upgrade:
        logger.warning(f"Migration {migration_file} has no upgrade function!")
        print(f"WARNING: Migration {migration_file} has no upgrade function!")
        return None
    
    # Create alembic version file
    version_filename = f"{revision_id}_{migration_file[:-3]}.py"
    version_path = os.path.join(ALEMBIC_VERSIONS_DIR, version_filename)
    
    with open(version_path, 'w') as f:
        f.write(f'''"""
Migration converted from {migration_file}
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Call the original upgrade function with the required connection
    conn = op.get_bind()
    # The original function expects an engine, but bind should work
    from app.database.migrations.{migration_file[:-3]} import upgrade as original_upgrade
    original_upgrade(conn)

''')
        if has_downgrade:
            f.write(f'''
def downgrade():
    conn = op.get_bind()
    from app.database.migrations.{migration_file[:-3]} import downgrade as original_downgrade
    original_downgrade(conn)
''')
        else:
            f.write('''
def downgrade():
    # No downgrade function in original migration
    pass
''')
    
    logger.info(f"Created Alembic version file: {version_filename}")
    print(f"Created Alembic version file: {version_filename}")
    return version_filename

def mark_migration_as_applied(version_file):
    """Mark a migration as applied in Alembic's version table"""
    # Extract revision ID from filename
    match = re.search(r'^(\w+)_', version_file)
    if not match:
        logger.warning(f"Could not extract revision ID from {version_file}")
        print(f"WARNING: Could not extract revision ID from {version_file}")
        return
    
    revision_id = match.group(1)
    
    # Run alembic stamp command
    python = get_venv_python()
    cmd = [python, '-m', 'alembic', 'stamp', revision_id]
    
    try:
        result = run_command(cmd)
        logger.info(f"Marked migration {version_file} as applied (revision {revision_id})")
        print(f"Marked migration {version_file} as applied (revision {revision_id})")
    except Exception as e:
        logger.error(f"Failed to mark migration {version_file} as applied: {str(e)}")
        print(f"ERROR: Failed to mark migration {version_file} as applied: {str(e)}")

@with_error_handling(context="integrate_migrations")
def integrate_migrations():
    """Integrate existing migrations with Alembic"""
    print("Integrating existing migrations with Alembic...")
    
    if not ensure_alembic_setup():
        return
    
    # Get existing migrations
    migrations = get_existing_migrations()
    
    if not migrations:
        print("No migrations to integrate")
        return
    
    print(f"Found {len(migrations)} existing migrations")
    
    # Process each migration
    for migration_file in migrations:
        print(f"\nProcessing migration: {migration_file}")
        
        # Extract timestamp
        timestamp = extract_timestamp_from_migration(migration_file)
        
        # Create Alembic version
        version_file = generate_alembic_version_for_migration(migration_file, timestamp)
        
        if version_file:
            # Mark as applied
            mark_migration_as_applied(version_file)
    
    print("\nMigration integration completed")
    print("\nYou can now use Alembic for future migrations:")
    print("  python -m alembic revision --autogenerate -m \"your migration description\"")
    print("  python -m alembic upgrade head") 