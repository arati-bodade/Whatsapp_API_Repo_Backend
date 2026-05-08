#!/usr/bin/env python3
"""
Update .env file with correct database credentials
"""

import os

# Correct database URL from user
correct_db_url = "postgresql://whatsapp_platform_fn0k_user:AbHezwfAs553dVCy33wfHzsGMVJbf8M0@dpg-d6oh8tfafjfc7386oii0-a.oregon-postgres.render.com/whatsapp_platform_fn0k"

env_file_path = os.path.join(os.path.dirname(__file__), '.env')

print("🔧 UPDATING .env FILE WITH CORRECT DATABASE URL")
print("=" * 50)

# Read existing .env file
try:
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
    print(f"📖 Read {len(lines)} lines from .env file")
except FileNotFoundError:
    print("❌ .env file not found")
    exit(1)

# Update DATABASE_URL line
updated_lines = []
database_updated = False

for line in lines:
    if line.startswith('DATABASE_URL='):
        updated_lines.append(f'DATABASE_URL={correct_db_url}\n')
        database_updated = True
        print("✅ Updated DATABASE_URL line")
    else:
        updated_lines.append(line)

# If DATABASE_URL not found, add it
if not database_updated:
    updated_lines.insert(0, f'DATABASE_URL={correct_db_url}\n')
    print("✅ Added DATABASE_URL line")

# Write back to .env file
try:
    with open(env_file_path, 'w') as f:
        f.writelines(updated_lines)
    print("✅ .env file updated successfully")
except Exception as e:
    print(f"❌ Error updating .env file: {e}")
    exit(1)

print("")
print("📋 UPDATED .env CONTENT:")
print("-" * 30)
with open(env_file_path, 'r') as f:
    for i, line in enumerate(f, 1):
        if line.strip():
            print(f"{i:2d}: {line.rstrip()}")

print("")
print("🎉 .env file has been updated with the correct database URL!")
print("✅ Backend should now connect to the new database")
