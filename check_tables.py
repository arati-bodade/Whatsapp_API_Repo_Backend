from db.session import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
print('Existing tables:')
for row in result:
    print(f'  {row[0]}')
conn.close()
