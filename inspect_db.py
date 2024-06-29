from app import app, db
from sqlalchemy import inspect

# Create an application context
with app.app_context():
    # Check if the tables exist
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables:", tables)

    # Print the columns of each table
    for table_name in tables:
        columns = inspector.get_columns(table_name)
        print(f"\nColumns in table {table_name}:")
        for column in columns:
            print(f"{column['name']} - {column['type']}")
