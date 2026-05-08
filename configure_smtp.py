"""
Helper script to configure SMTP credentials in .env file
"""
import os
from pathlib import Path

def configure_smtp():
    env_file = Path(".env")
    
    print("=== SMTP Configuration Helper ===")
    print("\nFor Gmail SMTP:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Go to https://myaccount.google.com/apppasswords")
    print("3. Generate an app password for 'Mail'")
    print("4. Use your Gmail email and the app password below\n")
    
    smtp_host = input("SMTP Host (default: smtp.gmail.com): ") or "smtp.gmail.com"
    smtp_port = input("SMTP Port (default: 587): ") or "587"
    smtp_user = input("SMTP User (your email): ")
    smtp_password = input("SMTP Password (app password): ")
    
    if not smtp_user or not smtp_password:
        print("ERROR: SMTP User and Password are required!")
        return
    
    # Read existing .env file
    env_content = ""
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
    
    # Update or add SMTP settings
    lines = env_content.split('\n')
    updated_lines = []
    smtp_settings = {
        'SMTP_HOST': smtp_host,
        'SMTP_PORT': smtp_port,
        'SMTP_USER': smtp_user,
        'SMTP_PASSWORD': smtp_password
    }
    
    smtp_keys_found = set()
    
    for line in lines:
        updated = False
        for key, value in smtp_settings.items():
            if line.startswith(f'{key}='):
                updated_lines.append(f'{key}={value}')
                smtp_keys_found.add(key)
                updated = True
                break
        if not updated:
            updated_lines.append(line)
    
    # Add missing SMTP settings
    for key, value in smtp_settings.items():
        if key not in smtp_keys_found:
            updated_lines.append(f'{key}={value}')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))
    
    print(f"\n✅ SMTP credentials configured in {env_file}")
    print("\nPlease restart the backend server for changes to take effect.")

if __name__ == "__main__":
    configure_smtp()
