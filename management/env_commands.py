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
from typing import Dict, Optional

from app.core.errors.base import ErrorContext, ErrorSeverity
from app.core.errors.management import (
    EnvironmentError,
    CommandError,
    ProcessError,
    with_management_error_handling
)
from app.core.logging import setup_logger

# Setup logger
logger = logging.getLogger("management.env_commands")
if not logger.handlers:
    logger = setup_logger(
        name="management.env_commands",
        level="INFO",
        log_file="logs/management.log"
    )

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

@with_management_error_handling
async def auto_setup_environment():
    """Setup environment variables automatically without user interaction"""
    try:
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
    except Exception as e:
        error_context = ErrorContext(
            source="auto_setup_environment",
            severity=ErrorSeverity.ERROR,
            error_id="env_auto_setup_error",
            additional_data={
                "error": str(e),
                "env_exists": env_exists if 'env_exists' in locals() else None
            }
        )
        raise CommandError("Failed to automatically set up environment", error_context) from e

@with_management_error_handling
async def setup_environment(auto_mode: bool = False):
    """Set up environment variables"""
    try:
        env_file = Path(".env")
        
        # Default environment variables
        default_env = {
            "OPENAI_API_KEY": "",
            "SECRET_KEY": "your-secret-key",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "DATABASE_NAME": "storybook.db",
            "DATABASE_DIR": "",
            "ALLOWED_ORIGINS": "http://localhost:3000,http://localhost:5173,http://localhost:3001",
            "UPLOAD_DIR": "uploads",
            "MAX_UPLOAD_SIZE": "5242880",
            "CHAT_RATE_LIMIT_PER_MINUTE": "5",
            "IMAGE_RATE_LIMIT_PER_MINUTE": "3",
            "TOKEN_LIMIT_PER_MINUTE": "20000",
            "DALLE_DEFAULT_VERSION": "dall-e-3",
            "LOG_LEVEL": "INFO"
        }
        
        # If .env exists, read current values
        current_env = {}
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        current_env[key] = value
        
        # Update environment variables
        new_env = {}
        for key, default_value in default_env.items():
            if auto_mode:
                new_env[key] = current_env.get(key, default_value)
            else:
                current = current_env.get(key, default_value)
                if key == "OPENAI_API_KEY" and current:
                    current = "****" + current[-4:]
                value = input(f"{key} [{current}]: ").strip()
                new_env[key] = value if value else current
        
        # Write to .env file
        with open(env_file, 'w') as f:
            for key, value in new_env.items():
                f.write(f"{key}={value}\n")
        
        logger.info("Environment variables updated successfully")
        return True
        
    except Exception as e:
        error_context = ErrorContext(
            source="setup_environment",
            severity=ErrorSeverity.ERROR,
            error_id="env_setup_error",
            additional_data={"error": str(e)}
        )
        raise EnvironmentError("Failed to setup environment", context=error_context)

@with_management_error_handling
async def show_current_env():
    """Display current environment variables"""
    try:
        env_file = Path(".env")
        
        if not env_file.exists():
            logger.warning("No .env file found")
            return False
        
        print("\nCurrent environment variables:")
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if "KEY" in key or "SECRET" in key:
                        # Mask sensitive values
                        print(f"{key}=****{'*' * len(value)}")
                    else:
                        print(f"{key}={value}")
        
        return True
        
    except Exception as e:
        error_context = ErrorContext(
            source="show_current_env",
            severity=ErrorSeverity.ERROR,
            error_id="env_show_error",
            additional_data={"error": str(e)}
        )
        raise EnvironmentError("Failed to show environment variables", context=error_context)

# Project environment setup functions
def run_command(cmd, cwd=None, env=None):
    """Run a shell command and return its output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_context = ErrorContext(
            source="run_command",
            severity=ErrorSeverity.ERROR,
            error_id="command_execution_error",
            additional_data={
                "command": cmd,
                "cwd": cwd,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "return_code": e.returncode
            }
        )
        raise ProcessError(f"Command failed: {cmd}", error_context) from e
    except Exception as e:
        error_context = ErrorContext(
            source="run_command",
            severity=ErrorSeverity.ERROR,
            error_id="command_error",
            additional_data={
                "command": cmd,
                "cwd": cwd,
                "error": str(e)
            }
        )
        raise ProcessError(f"Error running command: {cmd}", error_context) from e

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

@with_management_error_handling
async def setup_virtualenv():
    """Create a virtual environment if it doesn't exist"""
    try:
        if os.path.exists('venv'):
            print("Virtual environment already exists")
            return True
        
        print("Creating virtual environment...")
        run_command(f"{sys.executable} -m venv venv")
        print("Virtual environment created successfully")
        return True
    except Exception as e:
        error_context = ErrorContext(
            source="setup_virtualenv",
            severity=ErrorSeverity.ERROR,
            error_id="venv_setup_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to set up virtual environment", error_context) from e

@with_management_error_handling
async def install_dependencies():
    """Install project dependencies"""
    try:
        print("Installing dependencies...")
        pip = get_venv_pip()
        
        # Install requirements
        if os.path.exists('requirements.txt'):
            print("Installing from requirements.txt...")
            run_command(f"{pip} install -r requirements.txt")
        else:
            print("No requirements.txt found")
            return False
        
        print("Dependencies installed successfully")
        return True
    except Exception as e:
        error_context = ErrorContext(
            source="install_dependencies",
            severity=ErrorSeverity.ERROR,
            error_id="dependency_install_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to install dependencies", error_context) from e

@with_management_error_handling
async def setup_alembic():
    """Set up Alembic for database migrations"""
    try:
        print("Setting up Alembic...")
        
        # Initialize Alembic if not already initialized
        if not os.path.exists('alembic'):
            print("Initializing Alembic...")
            run_command(f"{get_venv_python()} -m alembic init alembic")
            
            # Update alembic.ini and env.py
            update_alembic_config()
            update_alembic_env()
            print("Alembic initialized and configured")
        else:
            print("Alembic already initialized")
        
        return True
    except Exception as e:
        error_context = ErrorContext(
            source="setup_alembic",
            severity=ErrorSeverity.ERROR,
            error_id="alembic_setup_error",
            additional_data={"error": str(e)}
        )
        raise ProcessError("Failed to set up Alembic", error_context) from e

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

@with_management_error_handling
async def setup_project():
    """Set up the project environment"""
    try:
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("uploads", exist_ok=True)
        os.makedirs(".pids", exist_ok=True)
        
        # Initialize environment if not exists
        if not Path(".env").exists():
            await setup_environment(auto_mode=True)
        
        logger.info("Project environment setup completed")
        return True
        
    except Exception as e:
        error_context = ErrorContext(
            source="setup_project",
            severity=ErrorSeverity.ERROR,
            error_id="project_setup_error",
            additional_data={"error": str(e)}
        )
        raise EnvironmentError("Failed to setup project", context=error_context)

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

@with_management_error_handling
async def integrate_migrations():
    """Integrate existing migrations with Alembic"""
    try:
        # Create migrations directory if it doesn't exist
        os.makedirs("migrations", exist_ok=True)
        
        # Create alembic.ini if it doesn't exist
        if not Path("alembic.ini").exists():
            with open("alembic.ini", 'w') as f:
                f.write("""[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///storybook.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")
        
        logger.info("Migration integration completed")
        return True
        
    except Exception as e:
        error_context = ErrorContext(
            source="integrate_migrations",
            severity=ErrorSeverity.ERROR,
            error_id="migration_integration_error",
            additional_data={"error": str(e)}
        )
        raise EnvironmentError("Failed to integrate migrations", context=error_context) 