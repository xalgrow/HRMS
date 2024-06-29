from app import app, db

class Employee(db.Model):
    __tablename__ = 'employees'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)

class Onboarding(db.Model):
    __tablename__ = 'onboardings'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    documents_submitted = db.Column(db.Boolean, default=False, nullable=False)
    training_completed = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Offboarding(db.Model):
    __tablename__ = 'offboardings'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    exit_date = db.Column(db.Date, nullable=False)
    exit_interview_done = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(50), nullable=False)

with app.app_context():
    db.create_all()
    print("Database tables created/updated successfully!")
