import os
from app import db, app

# Ensure the database path is persistent
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hrms.db')
if os.path.exists(db_path):
    os.remove(db_path)

with app.app_context():
    db.drop_all()
    db.create_all()

print("Database tables dropped and recreated successfully!")
