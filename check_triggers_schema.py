from db.base import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('google_sheet_triggers')
print('Columns in google_sheet_triggers:')
for c in columns:
    print(f'  {c["name"]}: {c["type"]}')
