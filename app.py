from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import datetime
from flask_migrate import Migrate
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Ensure the database path is persistent
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'hrms.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

@app.errorhandler(Exception)
def handle_exception(e):
    response = {
        "message": str(e),
        "type": type(e).__name__
    }
    print(f"Error: {e}")
    return jsonify(response), 500

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Role(db.Model):
    __tablename__ = 'role'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f'<Role {self.name}>'

class Payroll(db.Model):
    __tablename__ = 'payroll'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Payroll {self.employee_id} - {self.amount}>'

class Attendance(db.Model):
    __tablename__ = 'attendance'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Attendance {self.employee_id} - {self.date} - {self.status}>'

class Employee(db.Model):
    __tablename__ = 'employee'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<Employee {self.name}>'

class Offboarding(db.Model):
    __tablename__ = 'offboarding'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    offboarding_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Offboarding {self.employee_id}>'

@app.route('/')
def home():
    return "Server is running!"

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role_id = data.get('role_id')

    if not username or not email or not password or not role_id:
        return jsonify({'message': 'Missing fields'}), 400

    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'message': 'Username already exists'}), 400

    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(
        username=username,
        email=email,
        password=password,
        role_id=role_id
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    access_token = create_access_token(identity={'email': user.email, 'role_id': user.role_id})
    return jsonify({'message': 'Login successful', 'access_token': access_token}), 200

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/admin', methods=['GET'])
@jwt_required()
def admin():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if current_user.role.name != 'Admin':
        return jsonify({"msg": "Admins only!"}), 403
    return jsonify({"msg": "Welcome, Admin!"}), 200

@app.route('/employee/<int:id>', methods=['PUT'])
@jwt_required()
def update_employee(id):
    data = request.get_json()
    employee = User.query.get(id)
    if not employee:
        return jsonify({"msg": "Employee not found"}), 404
    employee.username = data['username']
    employee.email = data['email']
    db.session.commit()
    return jsonify({"msg": "Employee updated successfully"}), 200

@app.route('/employee/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_employee(id):
    employee = User.query.get(id)
    if not employee:
        return jsonify({"msg": "Employee not found"}), 404
    db.session.delete(employee)
    db.session.commit()
    return jsonify({"msg": "Employee deleted successfully"}), 200

@app.route('/role', methods=['POST'])
@jwt_required()
def create_role():
    data = request.get_json()
    if Role.query.filter_by(name=data['name']).first():
        return jsonify({"msg": "Role already exists"}), 400
    new_role = Role(name=data['name'])
    db.session.add(new_role)
    db.session.commit()
    return jsonify({"msg": "Role created successfully"}), 201

@app.route('/role/<int:role_id>', methods=['PUT'])
@jwt_required()
def update_role(role_id):
    role = Role.query.get_or_404(role_id)
    data = request.get_json()
    if 'name' in data:
        role.name = data['name']
    db.session.commit()
    return jsonify({'message': 'Role updated successfully!'})

@app.route('/role/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_role(id):
    role = Role.query.get(id)
    if not role:
        return jsonify({"msg": "Role not found"}), 404
    db.session.delete(role)
    db.session.commit()
    return jsonify({"msg": "Role deleted successfully"}), 200

@app.route('/payroll', methods=['POST'])
@jwt_required()
def create_payroll():
    data = request.get_json()
    new_payroll = Payroll(employee_id=data['employee_id'], amount=data['amount'], payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d'))
    db.session.add(new_payroll)
    db.session.commit()
    return jsonify({"msg": "Payroll created successfully"}), 201

@app.route('/payroll/<int:id>', methods=['PUT'])
@jwt_required()
def update_payroll(id):
    data = request.get_json()
    payroll = Payroll.query.get(id)
    if not payroll:
        return jsonify({"msg": "Payroll record not found"}), 404
    payroll.amount = data['amount']
    payroll.payment_date = datetime.strptime(data['payment_date'], '%Y-%m-%d')
    db.session.commit()
    return jsonify({"msg": "Payroll updated successfully"}), 200

@app.route('/payroll/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_payroll(id):
    payroll = Payroll.query.get(id)
    if not payroll:
        return jsonify({"msg": "Payroll record not found"}), 404
    db.session.delete(payroll)
    db.session.commit()
    return jsonify({"msg": "Payroll deleted successfully"}), 200

@app.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    data = request.get_json()
    new_attendance = Attendance(employee_id=data['employee_id'], date=datetime.strptime(data['date'], '%Y-%m-%d'), status=data['status'])
    db.session.add(new_attendance)
    db.session.commit()
    return jsonify({"msg": "Attendance marked successfully"}), 201

@app.route('/attendance', methods=['GET'])
@jwt_required()
def view_attendance():
    employee_id = request.args.get('employee_id')
    attendance_records = Attendance.query.filter_by(employee_id=employee_id).all()
    result = [{"date": record.date.strftime('%Y-%m-%d'), "status": record.status} for record in attendance_records]
    return jsonify(result), 200

@app.route('/attendance/report', methods=['GET'])
@jwt_required()
def attendance_report():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    attendance_records = Attendance.query.filter(Attendance.date >= start_date, Attendance.date <= end_date).all()
    result = {}
    for record in attendance_records:
        if record.employee_id not in result:
            result[record.employee_id] = {'Present': 0, 'Absent': 0}
        result[record.employee_id][record.status] += 1
    return jsonify(result), 200

@app.route('/payroll/report', methods=['GET'])
@jwt_required()
def payroll_report():
    start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
    payroll_records = Payroll.query.filter(Payroll.payment_date >= start_date, Payroll.payment_date <= end_date).all()
    result = {}
    for record in payroll_records:
        if record.employee_id not in result:
            result[record.employee_id] = 0
        result[record.employee_id] += record.amount
    return jsonify(result), 200

@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    result = [{"id": user.id, "username": user.username, "email": user.email, "role_id": user.role_id} for user in users]
    return jsonify(result), 200

@app.route('/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    result = {"id": user.id, "username": user.username, "email": user.email, "role_id": user.role_id}
    return jsonify(result), 200

@app.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    data = request.get_json()
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.role_id = data.get('role_id', user.role_id)

    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

@app.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

@app.route('/onboarding', methods=['POST'])
@jwt_required()
def create_onboarding():
    data = request.get_json()
    new_onboarding = Onboarding(
        employee_id=data['employee_id'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d'),
        documents_submitted=data['documents_submitted'],
        training_completed=data['training_completed'],
        status=data['status']
    )
    db.session.add(new_onboarding)
    db.session.commit()
    return jsonify({"msg": "Onboarding created successfully"}), 201

@app.route('/onboarding/<int:id>', methods=['PUT'])
@jwt_required()
def update_onboarding(id):
    data = request.get_json()
    onboarding = Onboarding.query.get(id)
    if not onboarding:
        return jsonify({"msg": "Onboarding record not found"}), 404
    onboarding.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    onboarding.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    onboarding.documents_submitted = data['documents_submitted']
    onboarding.training_completed = data['training_completed']
    onboarding.status = data['status']
    db.session.commit()
    return jsonify({"msg": "Onboarding updated successfully"}), 200

@app.route('/onboarding/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_onboarding(id):
    onboarding = Onboarding.query.get(id)
    if not onboarding:
        return jsonify({"msg": "Onboarding record not found"}), 404
    db.session.delete(onboarding)
    db.session.commit()
    return jsonify({"msg": "Onboarding deleted successfully"}), 200

@app.route('/offboarding', methods=['POST'])
@jwt_required()
def create_offboarding():
    data = request.get_json()
    new_offboarding = Offboarding(
        employee_id=data['employee_id'],
        offboarding_date=datetime.strptime(data['offboarding_date'], '%Y-%m-%d'),
        reason=data['reason']
    )
    db.session.add(new_offboarding)
    db.session.commit()
    return jsonify({"msg": "Offboarding created successfully"}), 201

@app.route('/offboarding/<int:id>', methods=['PUT'])
@jwt_required()
def update_offboarding(id):
    data = request.get_json()
    offboarding = Offboarding.query.get(id)
    if not offboarding:
        return jsonify({"msg": "Offboarding record not found"}), 404
    offboarding.offboarding_date = datetime.strptime(data['offboarding_date'], '%Y-%m-%d')
    offboarding.reason = data['reason']
    db.session.commit()
    return jsonify({"msg": "Offboarding updated successfully"}), 200

@app.route('/offboarding/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_offboarding(id):
    offboarding = Offboarding.query.get(id)
    if not offboarding:
        return jsonify({"msg": "Offboarding record not found"}), 404
    db.session.delete(offboarding)
    db.session.commit()
    return jsonify({"msg": "Offboarding deleted successfully"}), 200

@app.route('/onboarding/<int:id>', methods=['GET'])
@jwt_required()
def get_onboarding(id):
    onboarding = Onboarding.query.get(id)
    if not onboarding:
        return jsonify({"msg": "Onboarding record not found"}), 404
    result = {
        "employee_id": onboarding.employee_id,
        "start_date": onboarding.start_date.strftime('%Y-%m-%d'),
        "end_date": onboarding.end_date.strftime('%Y-%m-%d'),
        "documents_submitted": onboarding.documents_submitted,
        "training_completed": onboarding.training_completed,
        "status": onboarding.status
    }
    return jsonify(result), 200

@app.route('/offboarding/<int:id>', methods=['GET'])
@jwt_required()
def get_offboarding(id):
    offboarding = Offboarding.query.get(id)
    if not offboarding:
        return jsonify({"msg": "Offboarding record not found"}), 404
    result = {
        "employee_id": offboarding.employee_id,
        "offboarding_date": offboarding.offboarding_date.strftime('%Y-%m-%d'),
        "reason": offboarding.reason
    }
    return jsonify(result), 200

if __name__ == '__main__':
    app.config['DEBUG'] = True  # Enable debug mode
    app.run()
