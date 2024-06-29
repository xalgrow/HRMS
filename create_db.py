from app import app, db

# Create an application context
with app.app_context():
    # Create the tables
    db.create_all()
    print("Tables created successfully.")