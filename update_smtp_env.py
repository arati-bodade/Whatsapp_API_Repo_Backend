"""
Script to copy SMTP credentials from .env.example to .env
"""
from pathlib import Path

def update_smtp_credentials():
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_example.exists():
        print("ERROR: .env.example not found!")
        return
    
    # Read SMTP credentials from .env.example
    smtp_credentials = {}
    with open(env_example, 'r') as f:
        for line in f:
            if line.startswith('SMTP_'):
                key, value = line.strip().split('=', 1)
                smtp_credentials[key] = value
    
    if not smtp_credentials:
        print("ERROR: No SMTP credentials found in .env.example!")
        return
    
    print(f"Found SMTP credentials in .env.example:")
    for key, value in smtp_credentials.items():
        print(f"  {key}={value}")
    
    # Read existing .env file
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add SMTP settings in .env
    lines = env_content.split('\n')
    updated_lines = []
    smtp_keys_found = set()
    
    for line in lines:
        updated = False
        for key, value in smtp_credentials.items():
            if line.startswith(f'{key}='):
                updated_lines.append(f'{key}={value}')
                smtp_keys_found.add(key)
                updated = True
                break
        if not updated:
            updated_lines.append(line)
    
    # Add missing SMTP settings
    for key, value in smtp_credentials.items():
        if key not in smtp_keys_found:
            updated_lines.append(f'{key}={value}')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"\n✅ SMTP credentials updated in {env_file}")
    print("\nPlease restart the backend server for changes to take effect.")

if __name__ == "__main__":
    update_smtp_credentials()
