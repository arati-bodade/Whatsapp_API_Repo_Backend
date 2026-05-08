from db.session import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text('SELECT email, status FROM businesses LIMIT 5'))
print('Business users:')
for row in result:
    print(f'  Email: {row[0]}, Status: {row[1]}')
conn.close()
