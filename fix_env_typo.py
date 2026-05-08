import os

env_path = os.path.join(os.path.dirname(__file__), '.env')

# Read the .env file
with open(env_path, 'r') as f:
    content = f.read()

# Fix the typo
fixed_content = content.replace('http://localhosst:3002', 'http://localhost:3002')

# Write back
with open(env_path, 'w') as f:
    f.write(fixed_content)

print("✅ Fixed engine URL typo in .env file")
