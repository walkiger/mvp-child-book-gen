"""
Environment variable management script for the Child Book Generator MVP.

This script helps create and manage the .env file with necessary environment variables.
"""

import os
import sys
import getpass
from pathlib import Path

ENV_FILE = '.env'

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
    """Write environment variables to .env file"""
    with open(ENV_FILE, 'w') as f:
        f.write("# Environment variables for Child Book Generator MVP\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"\nEnvironment variables saved to {ENV_FILE}")

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

def setup_environment():
    """Setup environment variables interactively"""
    print("Child Book Generator MVP - Environment Setup\n")
    
    # Read existing environment variables
    env_vars = read_env_variables()
    env_exists, _ = check_env_file()
    
    if env_exists:
        print(f"Found existing {ENV_FILE} file with the following variables:")
        for key in env_vars:
            value = env_vars[key]
            masked_value = value[:3] + '*' * (len(value) - 3) if len(value) > 3 else '***'
            print(f"  - {key}={masked_value}")
        
        update = input("\nDo you want to update these variables? (y/n): ").strip().lower()
        if update != 'y':
            print("Keeping existing environment variables.")
            return
    
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

def show_current_env():
    """Display current environment variables"""
    env_vars = read_env_variables()
    env_exists, _ = check_env_file()
    
    if not env_exists or not env_vars:
        print("No environment variables found. Run 'python manage_env.py setup' to create them.")
        return
    
    print(f"\nCurrent environment variables in {ENV_FILE}:")
    for key, value in env_vars.items():
        if key == 'OPENAI_API_KEY':
            masked_value = value[:3] + '*' * (len(value) - 3) if len(value) > 3 else '***'
            print(f"  {key}={masked_value}")
        else:
            print(f"  {key}={value}")

def main():
    """Main function to run the script"""
    if len(sys.argv) < 2:
        print("Usage: python manage_env.py [command]")
        print("\nAvailable commands:")
        print("  setup    - Create or update environment variables")
        print("  show     - Display current environment variables")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'setup':
        setup_environment()
    elif command == 'show':
        show_current_env()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: setup, show")

if __name__ == "__main__":
    main() 